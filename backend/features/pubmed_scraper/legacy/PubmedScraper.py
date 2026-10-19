import datetime
import time
import pandas as pd
from Bio import Entrez
import io
import os
import http.client
from urllib.error import HTTPError, URLError

from .LocaleNormaliser import LocaleNormaliser
from .utilities import *


class PubmedScraper:
    def __init__(self, search, country, rare, numyears=5, email="", api_key=""):
        self.search = search
        self.country = country.lower().title()
        self.rare = rare

        self.numyears = numyears
        Entrez.email = email
        Entrez.api_key = api_key
        self.locale_normaliser = LocaleNormaliser(self.country,self.rare)
    
    def _entrez_read_with_retry(self,handle_func,max_retries=None,base_sleep=5,max_sleep=60,request_delay=0.4):
        attempt = 0

        while True:
            attempt += 1

            try:
                # Rate-limit every individual Entrez request.
                time.sleep(request_delay)

                with handle_func() as handle:
                    data = handle.read()

                raw_text = data[:1000].decode("utf-8", errors="replace")

                if "<ERROR>" in raw_text.upper():
                    error_msg = re.sub(r"\s+", " ", raw_text).strip()
                    raise RuntimeError(error_msg)

                return Entrez.read(io.BytesIO(data))

            except (http.client.IncompleteRead,HTTPError,URLError,OSError,RuntimeError,EOFError,ValueError) as e:

                print(f"⚠️ PubMed request failed on attempt {attempt}: " f"{type(e).__name__}: {e}" )

                if max_retries is not None and attempt >= max_retries:
                    raise RuntimeError(f"PubMed request failed after {max_retries} attempts.") from e

                sleep_time = min(base_sleep * attempt, max_sleep)

                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
    
    def _esearch_pmids(self, term, reldate_days, batch_size=5000):
        rec = self._entrez_read_with_retry(
            lambda: Entrez.esearch(
                db="pubmed",
                term=term,
                reldate=reldate_days,
                retmax=0,
                usehistory="y",
                retmode="xml",
            )
        )

        count = int(rec["Count"])
        webenv = rec["WebEnv"]
        query_key = rec["QueryKey"]

        pmids = []
        for start in range(0, count, batch_size):
            r = self._entrez_read_with_retry(
                lambda start=start: Entrez.esearch(
                    db="pubmed",
                    term=term,
                    reldate=reldate_days,
                    retstart=start,
                    retmax=batch_size,
                    webenv=webenv,
                    query_key=query_key,
                    retmode="xml",
                )
            )
            pmids.extend(r.get("IdList", []))
            time.sleep(0.15)

        return pmids

    def _get_coi_statement(self, author_list, coi_statement):
        if not coi_statement:
            return [""] * len(author_list)

        text = re.sub(r"\s+", " ", str(coi_statement)).strip()
        matches = []

        for i, author in enumerate(author_list):
            start = None
            patterns = build_author_patterns(author)

            for pattern in patterns:
                m = re.search(pattern, text, flags=re.IGNORECASE)
                if m:
                    start = m.start()
                    break

            matches.append((i, start))

        found = [(i, start) for i, start in matches if start is not None]
        found.sort(key=lambda x: x[1])

        result = [""] * len(author_list)


        for j, (i, start) in enumerate(found):
            end = found[j + 1][1] if j + 1 < len(found) else len(text)
            section = text[start:end].strip(" ;,.")

            if section and len(section) < 9:# in case the coi statement only has e.g. F. C. R., bcs we might have smth like A.S.A., M.E., M.H., R.W.H., T.R., C.S., and A.K.H.H. have filed patent WO2020007938 (EP18181475) “PqsR Inverse Agonists”, which claims intellectual property for the structures published herein.
                result[i] = text
            else:
                result[i] = section

        return result

    def _get_author_role_list(self, author_list):
        n = len(author_list)

        if n <= 1:
            return ["Author"]
        if n == 2:
            return ["First Author", "Last Author"]

        return ["First Author"] + ["Author"] * (n - 2) + ["Last Author"]

    def _get_publication_types(self,article):
        title = str(article.get("ArticleTitle", ""))

        raw_pub_types = "; ".join(
            str(pt) for pt in article.get("PublicationTypeList", [])
            if str(pt) != "Journal Article"
        )

        title_lower = title.lower()
        pub_type_lower = raw_pub_types.lower()

        mapping = {
            "trial": "Clinical Trial",
            "guideline": "Guideline",
            "study": "Study",
        }

        if "case report" in title_lower or "case report" in pub_type_lower:
            publication_types = ["Case Report"]
        else:
            publication_types = []

            for keyword, label in mapping.items():
                if keyword in pub_type_lower:
                    publication_types.append(label)
                elif keyword in title_lower:
                    publication_types.append(f"Potential {label}")

        if not publication_types:
            publication_types.append("Publication")

        return ", ".join(publication_types)

    def _get_doi(self,pubmed):
        mc = pubmed.get("MedlineCitation", {})
        article = mc.get("Article", {})

        doi = next(
            (
                str(x)
                for x in pubmed.get("PubmedData", {}).get("ArticleIdList", [])
                if getattr(x, "attributes", {}).get("IdType") == "doi"
            ),
            None
        )

        if not doi:
            doi = next(
                (
                    str(x)
                    for x in article.get("ELocationID", [])
                    if getattr(x, "attributes", {}).get("EIdType") == "doi"
                ),
                None
            )

        return doi

    def _get_year(self,article):
        year = None
        pubdate = article.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})

        if "Year" in pubdate:
            year = str(pubdate["Year"])
        elif "MedlineDate" in pubdate:
            match = re.search(r"\b(19|20)\d{2}\b", str(pubdate["MedlineDate"]))
            if match:
                year = match.group(0)

        return year

    def _get_nct_codes(self,article,title,publication_types):
        nct_codes = []

        # 1. Preferred source: DataBankList
        for databank in article.get("DataBankList", []):
            databank_name = str(databank.get("DataBankName", "")).lower()
            accession_numbers = databank.get("AccessionNumberList", [])

            if "clinicaltrials.gov" in databank_name:
                for acc in accession_numbers:
                    acc_str = str(acc).strip().upper()
                    if re.fullmatch(r"NCT\d{8}", acc_str):
                        nct_codes.append(acc_str)

        # 2. Fallback: scan abstract + title
        if not nct_codes:
            abstract_texts = article.get("Abstract", {}).get("AbstractText", [])
            abstract_text = " ".join(str(x) for x in abstract_texts)
            combined_text = f"{title} {abstract_text}"

            nct_codes = re.findall(r"\bNCT\d{8}\b", combined_text, flags=re.IGNORECASE)
            nct_codes = [code.upper() for code in nct_codes]

        # 3. Deduplicate while preserving order
        nct_codes = ", ".join(list(dict.fromkeys(nct_codes)))

        return nct_codes

    def _get_groups_collaborators(self,mc):
        article = mc.get("Article", {})
        author_list = article.get("AuthorList", [])

        study_group_names = ", ".join(
            [str(author.get("CollectiveName", "")).strip() for author in author_list if author.get("CollectiveName")])


        collaborators = []
        for block in mc.get("InvestigatorList", []):
            investigators = [block] if isinstance(block, dict) else block
            for author in investigators:
                name = display_name_from_xml(author)
                if name:
                    collaborators.append(name)

        collaborators = ",".join(collaborators)
        if len(collaborators) > 32766:
            collaborators = "CELL IS FULL"

        return study_group_names,collaborators

    def _parse_pubmed_article(self, pubmed):
        mc = pubmed.get("MedlineCitation", {})
        pmid = str(mc.get("PMID", "")).strip()
        article = mc.get("Article", {})
        author_list = article.get("AuthorList", [])


        if not pmid or not author_list:
            return None

        author_role_list = self._get_author_role_list(author_list)
        title = str(article.get("ArticleTitle", ""))
        publication_types = self._get_publication_types(article)

        nct_codes = self._get_nct_codes(article, title, publication_types)
        if nct_codes and "Clinical Trial" not in publication_types:
            publication_types = publication_types + ", Potential Clinical Trial"

        coi_statements = self._get_coi_statement(author_list,str(mc.get("CoiStatement", "")).strip())

        study_group_names, collaborators = self._get_groups_collaborators(mc)

        doi = self._get_doi(pubmed)
        year = self._get_year(article)
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        return {
            "pmid": pmid,
            "article": article,
            "author_list": author_list,
            "author_role_list": author_role_list,
            "title": title,
            "url": url,
            "publication_types": publication_types,
            "doi": doi,
            "year": year if year is not None else "",
            "nct_codes": nct_codes,
            "coi_statements": coi_statements,
            "coi_statements_all": str(mc.get("CoiStatement", "")).strip(),
            "study_group_names": study_group_names,
            "collaborators": collaborators,
            # "pubmed": pubmed,
        }

    def get_pubmeds(self, query):
        country_aliases = {self.country.lower()}
        translated_country_name = self.locale_normaliser.translated_country_name

        if translated_country_name:
            country_aliases.add(translated_country_name.lower())

        pmids = self._esearch_pmids(query, 365 * self.numyears)

        if not pmids:
            return []

        batch_size = 100
        pubmeds = []

        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]

            fetched = self._entrez_read_with_retry(
                lambda batch=batch: Entrez.efetch(
                    db="pubmed",
                    id=",".join(map(str, batch)),
                    rettype="pubmed",
                    retmode="xml",
                )
            )

            for pubmed in fetched.get("PubmedArticle", []):
                parsed = self._parse_pubmed_article(pubmed)
                if parsed is not None:
                    pubmeds.append(parsed)

            time.sleep(0.4)

        return pubmeds
    
    def write_excel(self, df, author_names_mapping_df=None, potential_names_mapping_df=None, collaborators_df=None, scraper=None, output=None):
        """Return app workbooks in memory; use a local file only in standalone mode."""
        if df is None or df.empty:
            return
        df = df.copy()
        if scraper in {"author", "hcp", "company"}:
            df["No. Publications"] = df.groupby("Author")["URL"].transform("nunique")
        else:
            df["No. Publications"] = df.groupby(["HCO", "City"])["URL"].transform("nunique")
        df = df.sort_values(by="No. Publications", ascending=False)
        if scraper in {"author", "company"}:
            df = df.drop(columns=["Author key"], errors="ignore")
        if output is None:
            safe_search = sanitize_input_string(self.search, max_length=50)
            safe_country = sanitize_input_string(self.country, max_length=40)
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "0. Output")
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%d-%m-%y_%H_%M")
            label = {"author": "Authors", "company": "Authors", "hcp": "HCP"}.get(scraper, "HCO")
            rare_label = "_RARE" if self.rare else ""
            output = os.path.join(output_dir, f"pubmed_{label}_{safe_search}_{safe_country}{rare_label}_{timestamp}.xlsx")
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="PubMed Data", index=False)
            if scraper in {"author", "hcp", "company"}:
                if collaborators_df is not None:
                    collaborators_df.to_excel(writer, sheet_name="Collaborators", index=False)
                if author_names_mapping_df is not None:
                    mapping = author_names_mapping_df if len(author_names_mapping_df.columns) else pd.DataFrame(columns=["Original", "Canonical"])
                    mapping.to_excel(writer, sheet_name="Names Mapping", index=False)
                if potential_names_mapping_df is not None and not potential_names_mapping_df.empty:
                    potential_names_mapping_df.to_excel(writer, sheet_name="Potential Mappings", index=False)
