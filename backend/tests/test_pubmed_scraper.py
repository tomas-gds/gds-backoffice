import unittest

from backend.features.pubmed_scraper.engine import PubMedSearch


class PubMedSearchTests(unittest.TestCase):
    def test_country_query_includes_aliases(self):
        search = PubMedSearch(
            search="asthma",
            country="UK",
            years=5,
            mode="hcp",
            email="test@example.com",
        )
        term = search._term()
        self.assertIn('"uk"[Affiliation]', term)
        self.assertIn('"united kingdom"[Affiliation]', term)

    def test_hco_rows_include_affiliation_and_trial_code(self):
        search = PubMedSearch(
            search="asthma",
            country="France",
            years=5,
            mode="hco",
            email="test@example.com",
        )
        article = {
            "MedlineCitation": {
                "PMID": "12345",
                "Article": {
                    "ArticleTitle": "A trial NCT01234567",
                    "Journal": {"Title": "Example Journal", "JournalIssue": {"PubDate": {"Year": "2026"}}},
                    "PublicationTypeList": ["Clinical Trial"],
                    "AuthorList": [
                        {"ForeName": "Anne", "LastName": "Martin", "AffiliationInfo": [{"Affiliation": "Hospital Example, Paris, France"}]}
                    ],
                },
            },
            "PubmedData": {"ArticleIdList": []},
        }
        rows = search._records_for_article(article)
        self.assertEqual(rows[0]["PMID"], "12345")
        self.assertEqual(rows[0]["NCT Code"], "NCT01234567")
        self.assertEqual(rows[0]["HCO / Affiliation"], "Hospital Example, Paris, France")


if __name__ == "__main__":
    unittest.main()
