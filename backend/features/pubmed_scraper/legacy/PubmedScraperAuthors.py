import pandas as pd
import re
import unicodedata

from .PubmedScraper import PubmedScraper
from .LocaleNormaliser import LocaleNormaliser
from .NameNormaliser import NameNormaliser
from .HCONormaliser import HCONormaliser


class PubmedScraperAuthors:
    VALID_SHORT = {"USA", "UK", "UAE"}

    def __init__(self, search, country, numyears=5, rare=True):
        self.search = search
        self.country = country.lower().title()
        self.numyears = numyears
        self.rare = rare

        self.country_aliases = set()
        self.rows = [] #[ {"Author":, "AuthorKey":, "Title":, "Country":, "Affiliations":, "Other affiliations":,"PMID":,"URL":,"Source":}, ...]
        self.author_keys = set() # [ "de Roux A", ...]
        self.seen_pmid_author = set() # (pmid, author_key)
        self.first_cols = ["Author", "Author Role","Title", "Publication Type", "HCO", "Department", "City", "Country"]

        self.df = pd.DataFrame()
        self.names_mapping_df = pd.DataFrame()
        self.potential_mapping_df = pd.DataFrame()
        self.collaborators_df = pd.DataFrame()

        self.pubmed_scraper = PubmedScraper(self.search, self.country, self.numyears)
        self.locale_normaliser = LocaleNormaliser(self.country)
        self.name_normaliser = NameNormaliser(self.rare)
        self.hco_normaliser = HCONormaliser(self.df, self.country)

    ##########    HELPER FUNCTIONS    ###########
    #############################################
    def _strip_accents(self,s):
        return "".join(
            c for c in unicodedata.normalize("NFKD", s or "")
            if not unicodedata.combining(c)
        )
    def _norm_spaces(self,s):
        return re.sub(r"\s+", " ", (s or "")).strip()
    def _display_name_from_xml(self,author):
        fn = self._norm_spaces(author.get("ForeName", "") or "")
        ln = self._norm_spaces(author.get("LastName", "") or "")
        name = self._norm_spaces(f"{fn} {ln}") or ln or fn
        return self._norm_spaces(name)
    def _pubmed_author_key(self,author):
        """
        PubMed-friendly author key: 'LastName Initials' (e.g., 'de Roux A').
        """
        if not author:
            return ""

        ln = self._norm_spaces(author.get("LastName", "") or "")
        initials = self._norm_spaces(author.get("Initials", "") or "")

        if not initials:
            fn = self._norm_spaces(author.get("ForeName", "") or "")
            initials = "".join(p[0] for p in re.split(r"[\s\-]+", fn) if p)

        key = self._norm_spaces(f"{ln} {initials}")
        key = self._strip_accents(key)
        key = self._norm_spaces(key)
        return key
    def _author_query_builder(self,author_keys):
        # author_keys are PubMed-style keys: "LastName Initials" (e.g., "de Roux A")
        parts = []
        for k in author_keys:
            if not k:
                continue
            k = self._norm_spaces(self._strip_accents(k))
            parts.append(f'"{k}"[Author]')
        return "(" + " OR ".join(parts) + ")"
    def _chunked(self,iterable, n):
        it = list(iterable)
        for i in range(0, len(it), n):
            yield it[i:i + n]

    def _build_country_aliases(self):
        if self.country.lower() in ["usa", "uk", "uae"]:
            self.country = self.country.upper()

        self.country_aliases.add(self.country.lower())
        translated_country_name = self.locale_normaliser.translated_country_name

        if translated_country_name:
            self.country_aliases.add(translated_country_name.lower())
        if self.country.lower() in ["uk", "united kingdom"]:
            self.country_aliases.add("united kingdom")
            self.country_aliases.add("uk")
            self.country_aliases.add("scotland")
            self.country_aliases.add("nothern ireland")

        if self.country.lower() == "germany":
            self.country_aliases.add("deutschland")

        if self.country.lower() == "italy":
            self.country_aliases.add("italia")

        if self.country.lower() == "spain":
            self.country_aliases.add("españa")

        if "netherlands" in self.country.lower():
            self.country_aliases.add("the netherlands")
            self.country_aliases.add("netherlands")

        if self.country.lower() == "switzerland":
            self.country_aliases.add("schweiz")
            self.country_aliases.add("suisse")
            self.country_aliases.add("svizzera")

        self.name_normaliser.country_aliases = self.country_aliases


    ###############    PUBMED    ################
    #############################################

    def get_pubmeds_Author(self,query,allowed_author_keys=None):


        pubmeds = self.pubmed_scraper.get_pubmeds(query)

        if not pubmeds:
            return pd.DataFrame()

        new_rows = []

        for pubmed in pubmeds:

            for i,author in enumerate(pubmed["author_list"]):
                if not author:
                    continue

                display_name = self._display_name_from_xml(author)
                author_key = self._pubmed_author_key(author)
                author_role = pubmed["author_role_list"][i]


                if not author_key:
                    continue


                if allowed_author_keys is not None and author_key not in allowed_author_keys:

                    continue


                pair = (pubmed["pmid"], author_key)

                if pair in self.seen_pmid_author:
                    continue

                self.seen_pmid_author.add(pair)

                author_affs = author.get("AffiliationInfo", [])

                if (len(author_affs) == 1) and ";" in author_affs[0].get("Affiliation", ""):
                    author_affs_list = (author_affs[0].get("Affiliation", "") or "").split("; ")
                else:
                    author_affs_list = [aff.get("Affiliation", "") for aff in author_affs]

                in_country = "; ".join(
                    aff for aff in author_affs_list
                    # to avoid China-Germany affiliations
                    if aff and any(alias in aff.lower() for alias in self.country_aliases) and not any(f"-{alias}" in aff.lower() for alias in self.country_aliases)
                )

                other_aff = "; ".join(
                    aff for aff in author_affs_list
                    if aff and not any(alias in aff.lower() for alias in self.country_aliases)
                )


                country, cities = self.locale_normaliser.extract_countries_cities(in_country) if in_country else [
                    self.country, ""]

                other_country, other_cities = self.locale_normaliser.extract_countries_cities(other_aff,
                                                                                         not_original_country=True) if other_aff else [
                    "", ""]



                if allowed_author_keys is None and "" not in [in_country, author_key, display_name]:
                    self.author_keys.add(author_key)



                row = {
                    "Author": display_name,
                    "Author Role": author_role,
                    "Author key": author_key,
                    "Title": pubmed["title"],
                    "Publication Type": pubmed["publication_types"],
                    "NCT Code": pubmed["nct_codes"],
                    "Collaborators": pubmed["collaborators"],
                    "Study Groups": pubmed["study_group_names"],
                    "City": cities,
                    "Country": self.country if in_country else other_country,
                    "Affiliations": in_country,
                    "COI Statement": pubmed["coi_statements"][i],
                    "COI Statements All": pubmed["coi_statements_all"],
                    "Other Cities": other_cities,
                    "Other affiliations": other_aff,
                    "Year": pubmed["year"] if pubmed["year"] is not None else "",
                    "doi": f"https://doi.org/{pubmed['doi']}" if pubmed["doi"] else "",
                    "URL": pubmed["url"],
                }

                new_rows.append(row)
                self.rows.append(row)

        self.df = pd.DataFrame(self.rows)
        return pd.DataFrame(new_rows)


    def extract(self):
        self._build_country_aliases()

        if self.country.lower() in ["united kingdom", "uk"]:
            first_query = f"""({self.search}) AND (UK[Affiliation] OR "United Kingdom"[Affiliation] OR "Scotland"[Affiliation] OR "Nothern Ireland"[Affiliation])"""
        elif "netherlands"in self.country.lower():
            first_query = f"""({self.search}) AND (Netherlands[Affiliation] OR "The Netherlands"[Affiliation])"""
        elif "spain"in self.country.lower():
            first_query = f"""({self.search}) AND (Spain[Affiliation] OR España[Affiliation])"""
        elif "germany"in self.country.lower():
            first_query = f"""({self.search}) AND (Germany[Affiliation] OR Deutschland[Affiliation])"""
        elif "italy"in self.country.lower():
            first_query = f"""({self.search}) AND (Italy[Affiliation] OR Italia[Affiliation])"""
        elif "switzerland"in self.country.lower():
            first_query = f"""({self.search}) AND (Switzerland[Affiliation] OR Schweiz[Affiliation]) OR Suisse[Affiliation]) OR Svizzera[Affiliation])"""
        else:
            first_query = f"({self.search}) AND ({self.country}[Affiliation])"

        print("     Running first query...")
        # first query: build author/article list only from in-country affiliations
        self.get_pubmeds_Author(first_query)

        author_keys = sorted(self.author_keys)

        print("     Running second query...")
        for author_batch in self._chunked(author_keys, 30):
            authors_clause = self._author_query_builder(author_batch)
            second_query = f'(({self.search})[Title/Abstract]) AND {authors_clause}'

            # second query: get all relevant publications of the authors found in query #1 even if not in the country of interest
            self.get_pubmeds_Author(second_query,allowed_author_keys=set(author_batch))


        self.hco_normaliser.df = self.df.copy()




    def clean_author_names(self, delete=True):
        # 1. Names Mapping
        self.df,self.names_mapping_df, mapping = self.name_normaliser.build_name_mapping(self.df)

        # 2. Potential Mappings
        self.potential_mapping_df = self.name_normaliser.build_potential_mappings_df(self.df)

        # 3. If we want to keep all the names (HCP scraper), just return the mappings
        if not delete:
            return self.df, self.names_mapping_df, self.potential_mapping_df

        # 4. Clean the three dfs to (carefully) delete authors that are not in the country if not a rare disease
        self.df, self.names_mapping_df, self.potential_mapping_df = self.name_normaliser.clean_dfs()

        return self.df, self.names_mapping_df, self.potential_mapping_df

    def get_collaborators(self):
        expanded_rows = []

        for _, row in self.df.iterrows():
            study_group = row["Study Groups"]

            if pd.isna(study_group) or str(study_group).strip() == "":
                continue

            author = row["Author"]
            collaborators = row["Collaborators"]
            title = row["Title"]
            pub_type = row["Publication Type"]
            year = row["Year"]
            url = row["URL"]

            rows = []

            # --- Author ---
            if pd.notna(author):
                rows.append({
                    "Name": str(author).strip(),
                    "Role": "Author",
                    "Study Group": study_group,
                    "Title": title,
                    "Publication Type": pub_type,
                    "Year": year,
                    "URL": url,
                })

            # --- Collaborators ---
            if pd.notna(collaborators):
                for name in str(collaborators).split(","):
                    name = name.strip()
                    if name:
                        rows.append({
                            "Name": name,
                            "Role": "Collaborator",
                            "Study Group": study_group,
                            "Title": title,
                            "Publication Type": pub_type,
                            "Year": year,
                            "URL": url,
                        })

            expanded_rows.extend(rows)

        expected_cols = ["Name", "Role", "Study Group", "Title", "Publication Type", "Year", "URL"]
        self.collaborators_df = pd.DataFrame(expanded_rows, columns=expected_cols)

        if self.collaborators_df.empty:
            return self.collaborators_df

        self.collaborators_df = self.collaborators_df.drop_duplicates(
            subset=["Name", "Study Group", "Title"]
        )
        self.collaborators_df = self.collaborators_df[
            self.collaborators_df["Name"].isin(self.df["Author"])
        ]

        return self.collaborators_df
    def main(self):
        print("\n🔍 Starting Pubmed extraction...")
        self.extract()

        if self.df.empty:
            print("❗ NO PUBMEDS WERE FOUND ❗")
            return

        print("🧹 Cleaning author names...")
        self.clean_author_names(delete=True)

        print("🏥 Normalizing HCO and departments...")
        self.df = self.hco_normaliser.get_HCO_and_dept(self.df,self.first_cols,dedupe_level="author")

        if not self.df.empty:
            self.df = self.df.drop_duplicates(subset=["Author", "URL"]).reset_index(drop=True)

        print("👥 Extracting collaborators...")
        self.get_collaborators()

        print("💾 Writing Excel output...")
        self.pubmed_scraper.write_excel(self.df,self.names_mapping_df,self.potential_mapping_df,self.collaborators_df,scraper="author")



