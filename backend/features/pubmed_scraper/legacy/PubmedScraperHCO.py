import pandas as pd

from .PubmedScraper import PubmedScraper
from .LocaleNormaliser import LocaleNormaliser
from .HCONormaliser import HCONormaliser
from .utilities import *


class PubmedScraperHCO:
    def __init__(self, search, country, numyears=5, rare=False):
        self.search = search
        self.country = country.lower().title()
        self.numyears = numyears
        self.rare = rare

        self.df = pd.DataFrame()

        self.pubmed_scraper = PubmedScraper(self.search, self.country, rare=self.rare, numyears=self.numyears)
        self.locale_normaliser = LocaleNormaliser(self.country, self.rare)
        self.hco_normaliser = HCONormaliser(self.df, self.country)

        self.country_aliases = self.locale_normaliser.build_country_aliases()
        self.rows = [] #[ {"Author":, "AuthorKey":, "Title":, "Country":, "Affiliations":, "Other affiliations":,"PMID":,"URL":,"Source":}, ...]
        self.first_cols = ["HCO", "Department", "Title", "Publication Type", "City", "Country"]





    def _get_pubmedsHCO(self):
        if self.country.lower() in ["usa","uk","uae"]:
            self.country = self.country.upper()

        fixed_query = fix_query_affil(self.search, self.country)
        pubmeds = self.pubmed_scraper.get_pubmeds(fixed_query)


        for pubmed in pubmeds:
            publication_affs = set()
            for author in pubmed["author_list"]:
                if not author:
                    continue

                author_affs = author.get("AffiliationInfo", [])

                if (len(author_affs) == 1) and ";" in author_affs[0].get("Affiliation", ""):
                    author_affs_list = (author_affs[0].get("Affiliation", "") or "").split("; ")
                else:
                    author_affs_list = [aff.get("Affiliation", "") for aff in author_affs]

                for aff in author_affs_list:
                    publication_affs.add(aff.strip())

            # one row per publication + in-country affiliation
            for aff in publication_affs:
                country, cities = self.locale_normaliser.extract_countries_cities(aff,not_target_country=True,)
                if country.lower() in self.country_aliases:
                    country=self.country

                self.rows.append({
                    "Title": pubmed["title"],
                    "Publication Type": pubmed["publication_types"],
                    "NCT Code": pubmed["nct_codes"],
                    "Collaborators": pubmed["collaborators"],
                    "Study Groups": pubmed["study_group_names"],
                    "City": cities,
                    "Country": country if country else "",
                    "Affiliations": aff,
                    "COI Statements All": pubmed["coi_statements_all"],
                    "Year": pubmed["year"] if pubmed["year"] is not None else "",
                    "doi": f"https://doi.org/{pubmed['doi']}" if pubmed["doi"] else "",
                    "URL": pubmed["url"]
                })


    def _extract(self):
        self._get_pubmedsHCO()

        self.df = pd.DataFrame(self.rows)

    def _clean_affs(self):
        countries = (self.df["Country"].astype("string").str.strip().str.casefold())

        target_aliases = {str(alias).strip().casefold()for alias in self.country_aliases}
        target_aliases.add(self.country.strip().casefold())

        is_target_country = countries.isin(target_aliases)
        is_unknown_country = countries.isna() | countries.eq("").fillna(False)

        keep = is_target_country

        if self.rare:
            keep = keep | is_unknown_country

        self.df = self.df.loc[keep].reset_index(drop=True)

    def main(self):
        print("Starting Pubmed extraction...")
        self._extract()

        if self.df.empty:
            print("NO PUBMEDS WERE FOUND")
            return
        
        self._clean_affs()

        self.df = self.hco_normaliser.get_HCO_and_dept(self.df, self.first_cols)

        self.df = self.df.drop_duplicates(subset=["HCO", "URL"]).reset_index(drop=True)
        
        
            


        print("Writing Excel output...")
        self.pubmed_scraper.write_excel(self.df,scraper="hco")




