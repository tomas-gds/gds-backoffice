import pandas as pd

from .PubmedScraper import PubmedScraper
from .LocaleNormaliser import LocaleNormaliser
from .HCONormaliser import HCONormaliser
from .utilities import *


class PubmedScraperHCO:
    def __init__(self, search, country, numyears=5, rare=True):
        self.search = search
        self.country = country.lower().title()
        self.numyears = numyears
        self.rare = rare

        self.country_aliases = set()
        self.rows = [] #[ {"Author":, "AuthorKey":, "Title":, "Country":, "Affiliations":, "Other affiliations":,"PMID":,"URL":,"Source":}, ...]
        # self.first_cols = ["Comment","HCO", "Department", "Title", "Publication Type", "City", "Country"]
        self.first_cols = ["HCO", "Department", "Title", "Publication Type", "City", "Country"]

        self.df = pd.DataFrame()

        self.pubmed_scraper = PubmedScraper(self.search ,self.country,self.numyears)
        self.locale_normaliser = LocaleNormaliser(self.country)
        self.hco_normaliser = HCONormaliser(self.df, self.country)

    def get_pubmedsHCO(self, query):
        if self.country.lower() in ["usa","uk","uae"]:
            self.country = self.country.upper()

        self.country_aliases, self.locale_normaliser = build_country_aliases(self.country, self.locale_normaliser)

        fixed_query = fix_query_affil(self.search, self.country)
        pubmeds = self.pubmed_scraper.get_pubmeds(fixed_query)


        for pubmed in pubmeds:
            # comment = self.pubmed_scraper.add_relevance_comment(pubmed)
            publication_in_country_affs = set()
            for author in pubmed["author_list"]:
                if not author:
                    continue

                author_affs = author.get("AffiliationInfo", [])

                if (len(author_affs) == 1) and ";" in author_affs[0].get("Affiliation", ""):
                    author_affs_list = (author_affs[0].get("Affiliation", "") or "").split("; ")
                else:
                    author_affs_list = [aff.get("Affiliation", "") for aff in author_affs]


                for aff in author_affs_list:
                    if not self.rare:
                        if aff and any(alias in aff.lower() for alias in self.country_aliases):
                            publication_in_country_affs.add(aff.strip())
                    else:
                        publication_in_country_affs.add(aff.strip())
            # one row per publication + in-country affiliation
            for in_country_aff in publication_in_country_affs:
                country, cities = self.locale_normaliser.extract_countries_cities(in_country_aff)

                self.rows.append({
                    # "Comment": comment,
                    "Title": pubmed["title"],
                    "Publication Type": pubmed["publication_types"],
                    "NCT Code": pubmed["nct_codes"],
                    "Collaborators": pubmed["collaborators"],
                    "Study Groups": pubmed["study_group_names"],
                    "City": cities,
                    "Country": country if country else self.country,
                    "Affiliations": in_country_aff,
                    "COI Statements All": pubmed["coi_statements_all"],
                    "Year": pubmed["year"] if pubmed["year"] is not None else "",
                    "doi": f"https://doi.org/{pubmed["doi"]}" if pubmed["doi"] else "",
                    "URL": pubmed["url"],
                    # "pubmed": pubmed
                })


    def extract(self):
        query = fix_query_affil(self.search, self.country)
        # query = f"({self.search}) AND ({self.country}[Affiliation])"

        self.get_pubmedsHCO(query)

        self.df = pd.DataFrame(self.rows)


    def main(self):
        print("\n🔍 Starting Pubmed extraction...")
        self.extract()

        if self.df.empty:
            print("❗ NO PUBMEDS WERE FOUND ❗")
            return

        print("🏥 Normalizing HCO and departments...")
        self.df = self.hco_normaliser.get_HCO_and_dept(self.df,self.first_cols)

        if not self.df.empty:
            self.df = self.df.drop_duplicates(subset=["HCO", "URL"]).reset_index(drop=True)

        print("💾 Writing Excel output...")
        self.pubmed_scraper.write_excel(self.df,scraper="hco")




