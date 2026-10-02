import os
import pandas as pd
import re
import unicodedata
import time

from .PubmedScraper import PubmedScraper
from .PubmedScraperAuthors import PubmedScraperAuthors
from .LocaleNormaliser import LocaleNormaliser
from .NameNormaliser import NameNormaliser
from .HCONormaliser import HCONormaliser
class PubmedScraperHCP:
    def __init__(self, search, country, numyears=5, rare=True):
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

        self.pubmed_scraper = PubmedScraper(self.search, self.country, self.numyears)
        self.pubmed_scraper_authors = PubmedScraperAuthors(self.search, self.country, self.numyears)
        self.locale_normaliser = LocaleNormaliser(self.country)
        self.name_normaliser = NameNormaliser()
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

    def _normalize_text(self, text):
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))
        # text = text.replace("-", " ")
        return text.strip()


    def _smart_title(self, text):
        """
        Title-case names while preserving surname particles,
        hyphens, and apostrophes.
        """
        lower_particles = {
            "da", "de", "del", "della", "der", "di", "la", "le",
            "van", "von", "den", "ten", "ter", "du"
        }

        words = text.split()
        result = []

        for word in words:
            if word.lower() in lower_particles:
                result.append(word.lower())
                continue

            # Split while retaining hyphens and apostrophes.
            parts = re.split(r"([-'])", word)

            formatted = "".join(
                part if part in {"-", "'"} else part.capitalize()
                for part in parts
            )

            result.append(formatted)

        return " ".join(result)

    def _parse_name(self, name):
        """
        Supports:
        - 'John Adam Smith'
        - 'Smith, John Adam'
        - 'J Smith'
        - 'Smith J'
        - 'M van den Berg'
        """

        surname_particles = {
            "da", "de", "del", "della", "der", "di", "la", "le",
            "van", "von", "den", "ten", "ter", "du", "st", "st."
        }

        # Case 1: Last, First Middle
        if "," in name:
            parts = [p.strip() for p in name.split(",", 1)]
            last_name = self._smart_title(parts[0])
            given_names = parts[1].split() if len(parts) > 1 else []
            initials = "".join(token[0].upper() for token in given_names if token and token[0].isalpha())
            return last_name, initials

        tokens = name.split()

        if len(tokens) == 1:
            return self._smart_title(tokens[0]), ""

        # Detect surname at end, including particles like "van den Berg"
        surname_start = len(tokens) - 1
        i = len(tokens) - 2

        while i >= 0 and tokens[i].lower() in surname_particles:
            surname_start = i
            i -= 1

        last_name_tokens = tokens[surname_start:]
        given_tokens = tokens[:surname_start]

        # Heuristic:
        # if first token looks like surname and second token is initial-only, e.g. "Smith J"
        # then interpret as surname first
        if len(tokens) == 2 and len(tokens[1].replace(".", "")) == 1:
            last_name_tokens = [tokens[0]]
            given_tokens = [tokens[1]]

        last_name = self._smart_title(" ".join(last_name_tokens))
        initials = "".join(
            token[0].upper()
            for token in given_tokens
            if token and token[0].isalpha()
        )

        return last_name, initials

    def _build_author_key_from_name(self, name):
        """
        Convert a person name into a PubMed-style author key.
        Examples:
            'John A. Smith' -> 'Smith JA'
            'Smith, John A.' -> 'Smith JA'
            'M. van den Berg' -> 'Van Den Berg M'
        """

        if pd.isna(name):
            return None

        name = str(name).strip()
        if not name:
            return None

        name = self._normalize_text(name)

        # remove common titles/suffixes
        name = re.sub(
            r"\b(dr|prof|mr|mrs|ms|md|phd|professor)\b\.?",
            "",
            name,
            flags=re.IGNORECASE,
        ).strip()

        # collapse whitespace
        name = re.sub(r"\s+", " ", name)

        if not name:
            return None

        last_name, initials = self._parse_name(name)

        if not last_name:
            return None

        if initials:
            return f"{last_name} {initials}".strip()

        return last_name

    def _normalize_name_for_match(self, name):
        if pd.isna(name):
            return ""
        name = str(name).strip()
        name = unicodedata.normalize("NFKD", name)
        name = "".join(c for c in name if not unicodedata.combining(c))
        name = re.sub(r"\s+", " ", name).strip().lower()
        return name

    def _strip_titles_suffixes(self, name):
        if not name:
            return ""

        name = re.sub(
            r"\b(dr|prof|mr|mrs|ms|md|phd|professor)\b\.?",
            "",
            name,
            flags=re.IGNORECASE,
        )
        name = re.sub(
            r"\b(jr|sr|ii|iii|iv)\b\.?",
            "",
            name,
            flags=re.IGNORECASE,
        )
        name = re.sub(r"\s+", " ", name).strip()
        return name

    def _normalize_for_person_match(self, text):
        if pd.isna(text):
            return ""

        text = str(text).strip()
        if not text:
            return ""

        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))
        text = text.lower()
        text = text.replace("-", " ")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _parse_full_name_strict(self, name):
        """
        Returns:
            (last_name, first_name, middle_initials)

        Examples:
            'Anne-Marie Sophie Kirsten' -> ('kirsten', 'anne marie', 's')
            'Anne Kirsten'              -> ('kirsten', 'anne', '')
            'Sven P Aries'              -> ('aries', 'sven', 'p')
            'Aries, Sven P'             -> ('aries', 'sven', 'p')
        """
        if pd.isna(name):
            return ("", "", "")

        raw_name = str(name).strip()
        if not raw_name:
            return ("", "", "")

        raw_name = self._strip_titles_suffixes(raw_name)
        has_comma = "," in raw_name

        surname_particles = {
            "da", "de", "del", "della", "der", "di", "la", "le",
            "van", "von", "den", "ten", "ter", "du", "st", "st."
        }

        if has_comma:
            parts = [p.strip() for p in raw_name.split(",", 1)]
            last_name = self._normalize_for_person_match(parts[0])

            given_part = parts[1] if len(parts) > 1 else ""
            given_part = self._normalize_for_person_match(given_part)
            given_tokens = given_part.split() if given_part else []

            if not given_tokens:
                return (last_name, "", "")

            first_name = given_tokens[0]
            middle_initials = "".join(
                t[0] for t in given_tokens[1:] if t and t[0].isalpha()
            )
            return (last_name, first_name, middle_initials)

        name_norm = self._normalize_for_person_match(raw_name)
        tokens = name_norm.split()

        if not tokens:
            return ("", "", "")

        if len(tokens) == 1:
            return (tokens[0], "", "")

        if len(tokens) == 2 and len(tokens[1].replace(".", "")) == 1:
            last_name = tokens[0]
            first_name = tokens[1].replace(".", "")
            return (last_name, first_name, "")

        surname_start = len(tokens) - 1
        i = len(tokens) - 2

        while i >= 0 and tokens[i] in surname_particles:
            surname_start = i
            i -= 1

        last_name_tokens = tokens[surname_start:]
        given_tokens = tokens[:surname_start]
        last_name = " ".join(last_name_tokens)

        if not given_tokens:
            return (last_name, "", "")

        # Handle hyphenated/compound first names:
        # if there are 2+ non-initial tokens at the start, keep them together as first name
        first_name_tokens = []
        middle_tokens = []

        for idx, tok in enumerate(given_tokens):
            clean_tok = tok.replace(".", "")
            if idx == 0:
                first_name_tokens.append(tok)
            elif len(clean_tok) > 1 and len(first_name_tokens) == 1:
                # second full token likely part of compound first name, e.g. anne marie
                first_name_tokens.append(tok)
            else:
                middle_tokens = given_tokens[idx:]
                break

        first_name = " ".join(first_name_tokens)
        middle_initials = "".join(
            t[0] for t in middle_tokens if t and t[0].isalpha()
        )

        return (last_name, first_name, middle_initials)

    def load_file_and_build_author_keys(self):
        """
        Load a CSV or Excel file, ask which column contains clinician names,
        remove duplicate authors from the input file, and build PubMed-ready author keys.

        Returns:
            df (pd.DataFrame): deduplicated dataframe with extra columns
            selected_column (str): column chosen by user
            author_keys (list[str]): unique PubMed-ready author keys
        """

        file_path = input("Enter the path to your file: ").strip().strip('"').strip("'")
        # file_path = r"C:\Users\TomásCarrilho\OneDrive - Global Data Support B.V\GDS-Clients - Documents\1.0 Global\GSK\Gordelroos_GSK workfile.xlsx"
        ext = os.path.splitext(file_path)[1].lower()

        # --- Handle Excel with multiple sheets ---
        if ext in [".xlsx", ".xls"]:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names

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
        self.input_df["PubMed Author Key"] = self.input_df[selected_column].apply(self._build_author_key_from_name)

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

        # Keep if you still use it elsewhere
        self.client_author_names_norm = {self._normalize_name_for_match(x)for x in self.client_author_names if str(x).strip()}

        self.client_author_signature_to_name = {}

        for client_name in self.client_author_names:
            if pd.isna(client_name) or not str(client_name).strip():
                continue

            sig = self._parse_full_name_strict(client_name)
            if sig != ("", "", ""):
                self.client_author_signature_to_name[sig] = client_name

        return self.input_df, selected_column, self.author_keys

    def _split_first_name_tokens(self, first_name):
        if pd.isna(first_name):
            return []

        first_name = str(first_name).strip().lower()
        if not first_name:
            return []

        first_name = unicodedata.normalize("NFKD", first_name)
        first_name = "".join(c for c in first_name if not unicodedata.combining(c))
        first_name = first_name.replace("-", " ")
        first_name = re.sub(r"\s+", " ", first_name).strip()

        return [t for t in first_name.split() if t]

    def _token_is_initial(self, tok):
        tok = str(tok).strip().replace(".", "")
        return len(tok) == 1 and tok.isalpha()

    def _first_names_compatible(self, a, b):
        """
        Accepts:
            anne vs anne -> True
            anne vs anne marie -> True
            anne marie vs anne -> True
            t vs tomas -> True
            tomas vs t -> True
            t a vs tomas antonio -> handled through first + middle logic elsewhere
            sven vs steven -> False
        """
        a_tokens = self._split_first_name_tokens(a)
        b_tokens = self._split_first_name_tokens(b)

        if not a_tokens or not b_tokens:
            return False

        # exact token match
        if a_tokens == b_tokens:
            return True

        # prefix compatibility for compound first names
        min_len = min(len(a_tokens), len(b_tokens))
        if a_tokens[:min_len] == b_tokens[:min_len]:
            return True

        # single-token initial vs full first name
        if len(a_tokens) == 1 and len(b_tokens) == 1:
            a0 = a_tokens[0].replace(".", "")
            b0 = b_tokens[0].replace(".", "")

            if a0 == b0:
                return True

            if self._token_is_initial(a0) and b0 and a0 == b0[0]:
                return True

            if self._token_is_initial(b0) and a0 and b0 == a0[0]:
                return True

        return False


    def _normalize_initials(self, text):
        if pd.isna(text) or not text:
            return ""
        text = str(text).upper().replace(".", "").strip()
        return "".join(ch for ch in text if ch.isalpha())

    def _get_client_file_name_match(self, pubmed_name):
        """
        Return the matching client-file name for a PubMed author.
        If no match is found, return "".
        """
        pub_last, pub_first, pub_middle = self._parse_full_name_strict(pubmed_name)

        if not pub_last:
            return ""

        candidates = []

        for (cli_last, cli_first, cli_middle), client_name in self.client_author_signature_to_name.items():
            if cli_last != pub_last:
                continue

            if not self._first_names_compatible(pub_first, cli_first):
                continue

            score = 0

            # exact first-name match better than partial compatibility
            if pub_first == cli_first:
                score += 3
            else:
                score += 2

            cli_middle_n = self._normalize_initials(cli_middle)
            pub_middle_n = self._normalize_initials(pub_middle)

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
            self.df["Client File Name"] = self.df["Author"].apply(
                self._get_client_file_name_match
            )

        # --- Collaborators DF ---
        if not self.collaborators_df.empty and "Name" in self.collaborators_df.columns:
            self.collaborators_df["Client File Name"] = self.collaborators_df["Name"].apply(
                self._get_client_file_name_match
            )

        # --- Author Names Mapping DF ---
        if not self.author_names_mapping_df.empty:
            col0 = self.author_names_mapping_df.columns[0]
            col1 = self.author_names_mapping_df.columns[1]

            self.author_names_mapping_df["Client File Name"] = (
                self.author_names_mapping_df[col1].apply(self._get_client_file_name_match)
            )

        # --- Potential Names Mapping DF ---
        if not self.potential_names_mapping_df.empty:
            col0 = self.potential_names_mapping_df.columns[0]
            col1 = self.potential_names_mapping_df.columns[1]

            # You can choose which side to map — better to map BOTH for visibility
            self.potential_names_mapping_df["Client File Name 1"] = (
                self.potential_names_mapping_df[col0].apply(self._get_client_file_name_match)
            )

            self.potential_names_mapping_df["Client File Name 2"] = (
                self.potential_names_mapping_df[col1].apply(self._get_client_file_name_match)
            )

    def get_pubmeds_HCP(self, query, allowed_author_keys=None):
        temp_df = self.pubmed_scraper_authors.get_pubmeds_Author(query,allowed_author_keys=allowed_author_keys,rare=self.rare).copy()

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
        for author_batch in self.pubmed_scraper_authors._chunked(client_author_keys, 30):

            authors_clause = self.pubmed_scraper_authors._author_query_builder(author_batch)
            query = f'(({self.search})[Title/Abstract]) AND {authors_clause}'

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

            for author_batch in self.pubmed_scraper_authors._chunked(new_author_keys, 30):
                authors_clause = self.pubmed_scraper_authors._author_query_builder(author_batch)
                query = f'(({self.search})[Title/Abstract]) AND {authors_clause}'

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
        self.load_file_and_build_author_keys()

        print("🔍 Starting Pubmed extraction...")
        self.extract()

        if self.df.empty:
            print("❗ NO PUBMEDS WERE FOUND ❗")
            return

        print("🧹 Cleaning author names...")
        self.pubmed_scraper_authors.df = self.df.copy()

        self.df, self.author_names_mapping_df, self.potential_names_mapping_df = (self.pubmed_scraper_authors.clean_author_names(delete=False))

        print("🏥 Normalizing HCO and departments...")
        self.df = self.hco_normaliser.get_HCO_and_dept(self.df,self.first_cols,dedupe_level="author")

        # keep both objects aligned again
        self.pubmed_scraper_authors.df = self.df.copy()

        print("👥 Extracting collaborators...")
        self.pubmed_scraper_authors.df = self.df.copy()
        self.collaborators_df = self.pubmed_scraper_authors.get_collaborators()

        self._add_client_file_name_columns()

        print("💾 Writing Excel output...")
        self.pubmed_scraper.write_excel(self.df, self.author_names_mapping_df, self.potential_names_mapping_df,self.collaborators_df,scraper="hcp")



