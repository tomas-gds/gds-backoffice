"""Non-interactive PubMed extraction adapted from the supplied scraper.

The original scripts prompt in the terminal and write files beside the script.
This module returns plain records instead, so the desktop interface can collect
the choices and decide when and where a user downloads the results.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

from Bio import Entrez


COUNTRY_ALIASES = {
    "uk": {"uk", "united kingdom", "england", "scotland", "wales", "northern ireland"},
    "united kingdom": {"uk", "united kingdom", "england", "scotland", "wales", "northern ireland"},
    "usa": {"usa", "u.s.a", "united states", "united states of america"},
    "united states": {"usa", "u.s.a", "united states", "united states of america"},
    "netherlands": {"netherlands", "the netherlands"},
    "spain": {"spain", "españa"},
    "italy": {"italy", "italia"},
    "germany": {"germany", "italia"},
}


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _article_year(article: dict[str, Any]) -> str:
    journal = article.get("Journal", {})
    journal_issue = journal.get("JournalIssue", {})
    pub_date = journal_issue.get("PubDate", {})
    return _clean(pub_date.get("Year") or article.get("ArticleDate", [{}])[0].get("Year"))


def _doi(article_data: dict[str, Any]) -> str:
    for item in article_data.get("PubmedData", {}).get("ArticleIdList", []):
        if getattr(item, "attributes", {}).get("IdType") == "doi":
            return _clean(item)
    return ""


def _nct_codes(title: str, abstract: str) -> str:
    return ", ".join(dict.fromkeys(match.upper() for match in re.findall(
        r"\bNCT\d{8}\b", f"{title} {abstract}", flags=re.IGNORECASE,
    )))


def _author_name(author: dict[str, Any]) -> str:
    if author.get("CollectiveName"):
        return _clean(author["CollectiveName"])
    return " ".join(part for part in (_clean(author.get("ForeName")), _clean(author.get("LastName"))) if part)


def _affiliations(author: dict[str, Any]) -> list[str]:
    values = []
    for affiliation in author.get("AffiliationInfo", []):
        text = _clean(affiliation.get("Affiliation"))
        if text:
            values.extend(part.strip() for part in text.split("; ") if part.strip())
    return values


def _country_matches(affiliation: str, country: str) -> bool:
    aliases = COUNTRY_ALIASES.get(country.lower(), {country.lower()})
    normalized = affiliation.lower()
    return any(alias in normalized for alias in aliases)


@dataclass
class PubMedSearch:
    search: str
    country: str
    years: int
    mode: str
    email: str
    api_key: str = ""

    @property
    def request_delay(self) -> float:
        return 0.12 if self.api_key else 0.36

    def run(self) -> tuple[int, list[dict[str, str]]]:
        Entrez.email = self.email
        Entrez.api_key = self.api_key or None
        term = self._term()
        with Entrez.esearch(
            db="pubmed",
            term=term,
            reldate=self.years * 365,
            datetype="pdat",
            retmax=0,
            usehistory="y",
            sort="pub date",
        ) as handle:
            search_result = Entrez.read(handle)

        found = int(search_result.get("Count", 0))
        if not found:
            return 0, []
        webenv = search_result["WebEnv"]
        query_key = search_result["QueryKey"]
        records: list[dict[str, str]] = []
        for start in range(0, found, 100):
            time.sleep(self.request_delay)
            with Entrez.efetch(
                db="pubmed",
                webenv=webenv,
                query_key=query_key,
                retstart=start,
                retmax=100,
                retmode="xml",
            ) as handle:
                fetched = Entrez.read(handle)
            for article_data in fetched.get("PubmedArticle", []):
                records.extend(self._records_for_article(article_data))
        return found, records

    def _term(self) -> str:
        country_terms = COUNTRY_ALIASES.get(self.country.lower(), {self.country})
        country_clause = " OR ".join(f'"{term}"[Affiliation]' for term in sorted(country_terms))
        return f"({self.search}) AND ({country_clause})"

    def _records_for_article(self, article_data: dict[str, Any]) -> list[dict[str, str]]:
        citation = article_data.get("MedlineCitation", {})
        article = citation.get("Article", {})
        pmid = _clean(citation.get("PMID"))
        title = _clean(article.get("ArticleTitle"))
        abstract = " ".join(_clean(value) for value in article.get("Abstract", {}).get("AbstractText", []))
        publication_types = ", ".join(_clean(item) for item in article.get("PublicationTypeList", []))
        year = _article_year(article)
        journal = _clean(article.get("Journal", {}).get("Title"))
        doi = _doi(article_data)
        base = {
            "PMID": pmid,
            "Title": title,
            "Journal": journal,
            "Year": year,
            "Publication Type": publication_types,
            "NCT Code": _nct_codes(title, abstract),
            "DOI": f"https://doi.org/{doi}" if doi else "",
            "URL": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
        }
        authors = article.get("AuthorList", [])
        if self.mode == "hco":
            rows = []
            for author in authors:
                for affiliation in _affiliations(author):
                    if _country_matches(affiliation, self.country):
                        rows.append({**base, "HCO / Affiliation": affiliation, "Author": _author_name(author)})
            return rows or [{**base, "HCO / Affiliation": "", "Author": ""}]

        return [
            {**base, "Author": _author_name(author), "Affiliations": " | ".join(_affiliations(author))}
            for author in authors
            if _author_name(author)
        ] or [{**base, "Author": "", "Affiliations": ""}]
