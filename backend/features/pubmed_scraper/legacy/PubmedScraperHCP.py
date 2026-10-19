import os
import pandas as pd
import time

from .PubmedScraper import PubmedScraper
from .PubmedScraperAuthors import PubmedScraperAuthors
from .HCONormaliser import HCONormaliser
from .utilities import *
class PubmedScraperHCP:
    def __init__(self, search, country, numyears=5, rare=False):
        self.search = search
        self.country = country.lower().title()
        self.numyears = numyears
        self.rare = rare

        self.rows = []  # [ {"Author":, "AuthorKey":, "Title":, "Country":, "Affiliations":, "Other affiliations":,"PMID":,"URL":,"Source":}, ...]
        self.author_keys = None  # [ "de Roux A", ...]
        self.authors_name_key = None  # [ "de Roux A", ...]
        self.seen_pmid_author = set()  # (pmid, author_key)
        self.first_cols = ["Author","Author Role","Client File Name","Title","Publication Type","HCO","Department","City","Country"]

        self.client_author_keys = set()
        self.client_author_names = set()
        self.client_author_names_norm = set()
        self.client_author_signature_to_name = {}

        self.input_df = pd.DataFrame()
        self.df = pd.DataFrame()
        self.author_keys_df = pd.DataFrame()
        self.author_names_mapping_df = pd.DataFrame()
        self.potential_names_mapping_df = pd.DataFrame()
        self.collaborators_df = pd.DataFrame()

        self.pubmed_scraper = PubmedScraper(self.search, self.country, rare=self.rare, numyears=self.numyears)
        self.pubmed_scraper_authors = PubmedScraperAuthors(self.search, self.country, numyears=self.numyears, rare=self.rare)
        self.hco_normaliser = HCONormaliser(self.df, self.country)

    def _ask_for_name_column(self, df):
        while True:
            choice = input(
                "\nEnter the column number or exact column name containing clinician names: "
            ).strip()

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(df.columns):
                    return df.columns[idx]

            if choice in df.columns:
                return choice

            print("Invalid choice. Please try again.")

    def _load_file_and_build_author_keys(self):
        file_path = input("Enter the path to your file: ").strip().strip('"').strip("'")
        ext = os.path.splitext(file_path)[1].lower()

        # --- Handle Excel with multiple sheets ---
        if ext in [".xlsx", ".xls"]:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            excel_file.close()

            if len(sheet_names) == 1:
                print(f"\nOnly one worksheet found: {sheet_names[0]}")
                selected_sheet = sheet_names[0]
            else:
                print("\nAvailable worksheets:")
                for i, sheet in enumerate(sheet_names, start=1):
                    print(f"{i}. {sheet}")

                while True:
                    choice = input("\nSelect worksheet (number or name): ").strip()

                    if choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(sheet_names):
                            selected_sheet = sheet_names[idx]
                            break

                    if choice in sheet_names:
                        selected_sheet = choice
                        break

                    print("Invalid choice. Please try again.")

            self.input_df = pd.read_excel(file_path, sheet_name=selected_sheet)
            self.input_df.columns = (
                self.input_df.columns
                .astype(str)
                .str.replace("\n", " ", regex=False)
                .str.strip()
            )

        elif ext == ".csv":
            self.input_df = pd.read_csv(file_path)
            self.input_df.columns = (
                self.input_df.columns
                .astype(str)
                .str.replace("\n", " ", regex=False)
                .str.strip()
            )

        else:
            raise ValueError("Unsupported file type. Use CSV or Excel.")

        # --- Ask user which column contains clinician names ---
        print("\nAvailable columns:")
        for i, col in enumerate(self.input_df.columns, start=1):
            print(f"{i}. {col}")

        selected_column = self._ask_for_name_column(self.input_df)

        # --- Build helper columns ---
        self.input_df = self.input_df.copy()
        self.input_df["Original Name"] = self.input_df[selected_column]
        self.input_df["PubMed Author Key"] = self.input_df[selected_column].apply(build_author_key_from_name)

        # Clean values
        self.input_df["Original Name"] = self.input_df["Original Name"].astype(str).str.strip()
        self.input_df["PubMed Author Key"] = self.input_df["PubMed Author Key"].astype(str).str.strip()

        # Convert fake missing strings back to NA
        self.input_df.loc[self.input_df["Original Name"].isin(["", "nan", "None"]),"Original Name"] = pd.NA
        self.input_df.loc[self.input_df["PubMed Author Key"].isin(["", "nan", "None"]),"PubMed Author Key"] = pd.NA

        # --- Remove duplicate authors from input file ---
        # Deduplicate by normalized original name
        self.input_df["_name_norm"] = (self.input_df["Original Name"].fillna("").astype(str).str.strip().str.lower())

        self.input_df = self.input_df[self.input_df["_name_norm"] != ""].drop_duplicates(subset=["_name_norm"]).drop(columns=["_name_norm"]).reset_index(drop=True)

        # --- Build final author collections ---
        author_keys = self.input_df["PubMed Author Key"].dropna().astype(str).str.strip()
        author_names = self.input_df["Original Name"].dropna().astype(str).str.strip()

        self.author_keys = [x for x in author_keys.unique().tolist() if x]

        self.authors_name_key = {
            str(name).strip(): str(key).strip()
            for name, key in zip(self.input_df["Original Name"], self.input_df["PubMed Author Key"])
            if pd.notna(name) and pd.notna(key) and str(name).strip() and str(key).strip()
        }

        self.client_author_keys = set(self.author_keys)
        self.client_author_names = set(author_names.unique().tolist())

        self.client_author_signature_to_name = {}

        for client_name in self.client_author_names:
            if pd.isna(client_name) or not str(client_name).strip():
                continue

            sig = parse_name(client_name, strict=True)
            if sig != ("", "", ""):
                self.client_author_signature_to_name[sig] = client_name

        return self.input_df, selected_column, self.author_keys

    def _get_client_file_name_match(self, pubmed_name):
        """
        Return the matching client-file name for a PubMed author.
        If no match is found, return "".
        """
        pub_last, pub_first, pub_middle = parse_name(pubmed_name, strict=True)

        if not pub_last:
            return ""

        candidates = []

        for (cli_last, cli_first, cli_middle), client_name in self.client_author_signature_to_name.items():
            if cli_last != pub_last:
                continue

            if not first_names_compatible(pub_first, cli_first):
                continue

            score = 0

            # exact first-name match better than partial compatibility
            if pub_first == cli_first:
                score += 3
            else:
                score += 2

            cli_middle_n = normalize_initials(cli_middle)
            pub_middle_n = normalize_initials(pub_middle)

            if cli_middle_n and pub_middle_n:
                if cli_middle_n == pub_middle_n:
                    score += 2
                else:
                    continue
            elif not cli_middle_n or not pub_middle_n:
                score += 1

            candidates.append((score, client_name))

        if not candidates:
            return ""

        # highest score wins
        candidates.sort(key=lambda x: (-x[0], x[1]))
        return candidates[0][1]


    def _add_client_file_name_columns(self):
        """
        Add 'Client File Name' column to all relevant DataFrames.
        """

        # --- Main DF ---
        if not self.df.empty and "Author" in self.df.columns:
            self.df["Client File Name"] = self.df["Author"].apply(self._get_client_file_name_match)

        # --- Collaborators DF ---
        if not self.collaborators_df.empty and "Name" in self.collaborators_df.columns:
            self.collaborators_df["Client File Name"] = self.collaborators_df["Name"].apply(self._get_client_file_name_match)

        # --- Author Names Mapping DF ---
        if not self.author_names_mapping_df.empty:
            col0 = self.author_names_mapping_df.columns[0]
            col1 = self.author_names_mapping_df.columns[1]

            self.author_names_mapping_df["Client File Name"] = self.author_names_mapping_df[col1].apply(self._get_client_file_name_match)

        # --- Potential Names Mapping DF ---
        if not self.potential_names_mapping_df.empty:
            col0 = self.potential_names_mapping_df.columns[0]
            col1 = self.potential_names_mapping_df.columns[1]

            # You can choose which side to map — better to map BOTH for visibility
            self.potential_names_mapping_df["Client File Name 1"] = self.potential_names_mapping_df[col0].apply(self._get_client_file_name_match)

            self.potential_names_mapping_df["Client File Name 2"] = self.potential_names_mapping_df[col1].apply(self._get_client_file_name_match)


    def get_pubmeds_HCP(self, query, allowed_author_keys=None):
        temp_df = self.pubmed_scraper_authors.get_pubmeds_Author(query,allowed_author_keys=allowed_author_keys).copy()

        if temp_df.empty:
            return pd.DataFrame()

        temp_df["Client File Name"] = temp_df["Author"].apply(self._get_client_file_name_match)

        return temp_df

    def extract(self):
        client_author_keys = sorted(self.client_author_keys)


        self.df = pd.DataFrame()
        coauthor_keys = set()

        # PASS 1:
        # Search by client-file clinician keys.
        # Keep all authors from matched papers.
        print("     Running first query...")
        for author_batch in chunked(client_author_keys, 30):

            authors_clause = self.pubmed_scraper_authors.author_query_builder(author_batch)
            query = f'({self.search}) AND {authors_clause}'

            batch_df = self.get_pubmeds_HCP(query,allowed_author_keys=None)

            if batch_df.empty:
                continue

            matched_urls = set(batch_df.loc[batch_df["Author key"].astype(str).str.strip().isin(set(author_batch)),"URL"].dropna().astype(str).str.strip())

            if not matched_urls:
                continue

            kept_df = batch_df[batch_df["URL"].astype(str).str.strip().isin(matched_urls)].copy()

            self.df = pd.concat([self.df, kept_df], ignore_index=True)

            batch_keys = set(kept_df["Author key"].dropna().astype(str).str.strip())
            coauthor_keys.update(batch_keys - self.client_author_keys)
            time.sleep(10)  # wait 3 seconds before next query

        if self.df.empty:
            return

        self.df = self.df.drop_duplicates(subset=["Author", "URL"]).reset_index(drop=True)

        # PASS 2:
        # Search by newly found co-authors.
        # Keep only those co-author names.
        run_second_query = input("Would you like to get the full network? (y/n)")
        if run_second_query.lower() == "y":
            new_author_keys = sorted(coauthor_keys)
            print("     Running second query...")

            for author_batch in chunked(new_author_keys, 30):
                authors_clause = self.pubmed_scraper_authors.author_query_builder(author_batch)
                query = f'({self.search}) AND {authors_clause}'

                batch_df = self.get_pubmeds_HCP(
                    query,
                    allowed_author_keys=set(author_batch)
                )

                if batch_df.empty:
                    continue

                self.df = pd.concat([self.df, batch_df], ignore_index=True)

            self.df = (
                self.df
                .drop_duplicates(subset=["Author", "URL"])
                .reset_index(drop=True)
            )

        else:
            # Keep only the original client clinicians
            self.df = (
                self.df[
                    self.df["Author key"]
                    .astype(str)
                    .str.strip()
                    .isin(client_author_keys)
                ]
                    .drop_duplicates(subset=["Author", "URL"])
                    .reset_index(drop=True)
            )

    def main(self):
        self._load_file_and_build_author_keys()

        print("Starting Pubmed extraction...")
        self.extract()

        if self.df.empty:
            print("NO PUBMEDS WERE FOUND")
            return

        print("Cleaning author names...")
        self.pubmed_scraper_authors.df = self.df.copy()

        self.df, self.author_names_mapping_df, self.potential_names_mapping_df = self.pubmed_scraper_authors.build_names_mappings()

        print("Normalizing HCO and departments...")
        self.df = self.hco_normaliser.get_HCO_and_dept(self.df,self.first_cols,dedupe_level="author")

        # keep both objects aligned again
        self.pubmed_scraper_authors.df = self.df.copy()

        print("Extracting collaborators...")
        self.pubmed_scraper_authors.df = self.df.copy()
        self.collaborators_df = self.pubmed_scraper_authors.get_collaborators_tab()

        self._add_client_file_name_columns()

        print("Writing Excel output...")
        self.pubmed_scraper.write_excel(self.df, self.author_names_mapping_df, self.potential_names_mapping_df,self.collaborators_df,scraper="hcp")



