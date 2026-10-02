import os
import datetime
import time
import pandas as pd
from Bio import Entrez
import re
import unicodedata
import io
import http.client
from urllib.error import HTTPError, URLError

from LocaleNormaliser import LocaleNormaliser


class PubmedScraper:
    def __init__(self, search, country, numyears=5, email="", api_key=""):
        self.search = search
        self.country = country.lower().title()
        self.numyears = numyears

        Entrez.email = email
        Entrez.api_key = api_key

        self.locale_normaliser = LocaleNormaliser(self.country)

    def _norm_spaces(self, s):
        return re.sub(r"\s+", " ", (s or "")).strip()

    def _sanitize_input_string(self, text, max_length=120):
        if not text:
            return "unknown"

        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        text = re.sub(r'[<>:"/\\|?*]', "_", text)
        text = re.sub(r"[\s]+", "_", text.strip())
        text = re.sub(r"[^A-Za-z0-9._-]", "_", text)
        text = re.sub(r"_+", "_", text).strip("._")

        if not text:
            text = "unknown"

        return text[:max_length]

    def _entrez_read_with_retry2(self, handle_func, max_retries=None, base_sleep=5, max_sleep=60):
        """
        Retries PubMed/Entrez requests.

        max_retries=None means keep trying forever.
        base_sleep controls the first wait time.
        max_sleep prevents waits from becoming too long.
        """

        attempt = 0

        while True:
            attempt += 1
            data = b""

            try:
                with handle_func() as h:
                    data = h.read()

                raw_text = data[:1000].decode("utf-8", errors="replace")

                # Catch PubMed XML error responses before Entrez.read()
                if "<ERROR>" in raw_text:
                    error_msg = re.sub(r"\s+", " ", raw_text)
                    raise RuntimeError(error_msg)

                return Entrez.read(io.BytesIO(data))

            except (
                    http.client.IncompleteRead,
                    HTTPError,
                    URLError,
                    OSError,
                    RuntimeError,
                    EOFError,
                    ValueError,
            ) as e:

                if max_retries is not None and attempt >= max_retries:
                    raise RuntimeError(
                        f"PubMed request failed after {max_retries} attempts."
                    ) from e

                sleep_time = min(base_sleep * attempt, max_sleep)

                print(
                    f"⚠️ PubMed temporarily unavailable. "
                    f"Retrying in {sleep_time} seconds..."
                )

                time.sleep(sleep_time)

    def _entrez_read_with_retry(
            self,
            handle_func,
            max_retries=None,
            base_sleep=5,
            max_sleep=60,
            request_delay=0.4,
    ):
        """
        Run an Entrez request with rate limiting and retries.

        request_delay:
            Around 0.4 seconds without an API key.
            Around 0.12 seconds with an API key.
        """

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

            except (
                    http.client.IncompleteRead,
                    HTTPError,
                    URLError,
                    OSError,
                    RuntimeError,
                    EOFError,
                    ValueError,
            ) as e:

                print(
                    f"⚠️ PubMed request failed on attempt {attempt}: "
                    f"{type(e).__name__}: {e}"
                )

                if max_retries is not None and attempt >= max_retries:
                    raise RuntimeError(
                        f"PubMed request failed after {max_retries} attempts."
                    ) from e

                sleep_time = min(base_sleep * attempt, max_sleep)

                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
    def esearch_pmids(self, term, reldate_days, batch_size=5000):
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

    def get_pubmeds2(self, query):
        country_aliases = {self.country.lower()}
        translated_country_name = self.locale_normaliser.translated_country_name

        if translated_country_name:
            country_aliases.add(translated_country_name.lower())

        pmids = self.esearch_pmids(query, 365 * self.numyears)

        if not pmids:
            return

        batch_size = 100

        pubmeds = []
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]

            fetched = self._entrez_read_with_retry(
                lambda batch=batch: Entrez.efetch(
                    db="pubmed",
                    id=",".join(batch),
                    retmode="xml"
                )
            )

            for pubmed in fetched.get("PubmedArticle", []):
                pubmeds.append(self._parse_pubmed_article(pubmed))

            time.sleep(0.34)

        return pubmeds

    def get_pubmeds(self, query):
        country_aliases = {self.country.lower()}
        translated_country_name = self.locale_normaliser.translated_country_name

        if translated_country_name:
            country_aliases.add(translated_country_name.lower())

        pmids = self.esearch_pmids(query, 365 * self.numyears)

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
                pubmeds.append(self._parse_pubmed_article(pubmed))

            time.sleep(0.4)

        return pubmeds
    def _display_name_from_xml(self, author):
        fn = self._norm_spaces(author.get("ForeName", "") or "")
        ln = self._norm_spaces(author.get("LastName", "") or "")
        name = self._norm_spaces(f"{fn} {ln}") or ln or fn
        return self._norm_spaces(name)

    # def get_initials(self, author_name):
    #     return " ".join(f"{name[0].upper()}." for name in author_name.split() if name)

    def _build_author_patterns(self, author):
        display_name = self._display_name_from_xml(author).strip()
        parts = display_name.split()

        if not parts:
            return []

        last_name = parts[-1]
        initials = [p[0].upper() for p in parts if p]

        patterns = []

        # Full name
        patterns.append(re.escape(display_name))

        # Last name only
        patterns.append(rf"\b{re.escape(last_name)}\b")

        # F. Lastname
        if initials:
            patterns.append(rf"\b{initials[0]}\.\s*{re.escape(last_name)}\b")

        # Initials with dots/spaces: F. C. R. / F.C.R. / F C R/ FCR
        if initials:
            letters = [re.escape(c) for c in initials if c.isalpha()]
            initials_pattern = r"[.\s]*".join(letters) + r"\.?"
            patterns.append(rf"\b{initials_pattern}\b")

        # Lastname F (rare but happens)
        if initials:
            patterns.append(rf"\b{re.escape(last_name)}\s*{initials[0]}\b")

        return patterns

    def get_coi_statement(self, author_list, coi_statement):
        if not coi_statement:
            return [""] * len(author_list)

        text = re.sub(r"\s+", " ", str(coi_statement)).strip()
        matches = []

        for i, author in enumerate(author_list):
            start = None
            patterns = self._build_author_patterns(author)

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

    def get_author_role_list(self, author_list):
        n = len(author_list)

        if n <= 1:
            return ["Author"]
        if n == 2:
            return ["First Author", "Last Author"]

        return ["First Author"] + ["Author"] * (n - 2) + ["Last Author"]

    def get_publication_types(self,article):
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

        publication_types = []

        for keyword, label in mapping.items():
            if keyword in pub_type_lower:
                publication_types.append(label)
            elif keyword in title_lower:
                publication_types.append(f"Potential {label}")

        if not publication_types:
            publication_types.append("Publication")

        return ", ".join(publication_types)

    def get_doi(self,pubmed):
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

    def get_year(self,article):
        year = None
        pubdate = article.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})

        if "Year" in pubdate:
            year = str(pubdate["Year"])
        elif "MedlineDate" in pubdate:
            match = re.search(r"\b(19|20)\d{2}\b", str(pubdate["MedlineDate"]))
            if match:
                year = match.group(0)

        return year

    def get_nct_codes(self,article,title,publication_types):
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

    def get_groups_collaborators(self,mc):
        article = mc.get("Article", {})
        author_list = article.get("AuthorList", [])

        study_group_names = ", ".join(
            [str(author.get("CollectiveName", "")).strip() for author in author_list if author.get("CollectiveName")])


        collaborators = []
        for block in mc.get("InvestigatorList", []):
            for author in block:
                collaborators.append(self._display_name_from_xml(author))

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

        author_role_list = self.get_author_role_list(author_list)
        title = str(article.get("ArticleTitle", ""))
        publication_types = self.get_publication_types(article)

        nct_codes = self.get_nct_codes(article, title, publication_types)
        if nct_codes and "Clinical Trial" not in publication_types:
            publication_types = publication_types + ", Potential Clinical Trial"

        coi_statements = self.get_coi_statement(author_list,str(mc.get("CoiStatement", "")).strip())

        study_group_names, collaborators = self.get_groups_collaborators(mc)

        doi = self.get_doi(pubmed)
        year = self.get_year(article)
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



    def write_excel(self,df,author_names_mapping_df=None,potential_names_mapping_df=None,collaborators_df=None,scraper=None):
        if df is None or df.empty:
            print("❌ Error: No data to write. The DataFrame is empty.")
            return

        if scraper in ["author","hcp","company"]:
            df["No. Publications"] = df.groupby("Author")["URL"].transform("nunique")
        else:
            df["No. Publications"] = df.groupby(["HCO", "City"])["URL"].transform("nunique")

        df = df.sort_values(by="No. Publications", ascending=False)

        safe_search = self._sanitize_input_string(self.search, max_length=50)
        safe_country = self._sanitize_input_string(self.country, max_length=40)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)

        output_dir = os.path.join(parent_dir, "0. Output")
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
        if scraper == "author":
            out_path = os.path.join(output_dir, f"pubmed_Authors_{safe_search}_{safe_country}_{timestamp}.xlsx")
            df = df.drop(columns=["Author key"], errors="ignore")
        elif scraper == "hcp":
            out_path = os.path.join(output_dir, f"pubmed_HCP_{safe_search}_{safe_country}_{timestamp}.xlsx")
        else:
            out_path = os.path.join(output_dir, f"pubmed_HCO_{safe_search}_{safe_country}_{timestamp}.xlsx")


        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="PubMed Data", index=False)
            if scraper in ["author","hcp"]:
                collaborators_df.to_excel(writer, sheet_name="Collaborators", index=False)
                author_names_mapping_df.to_excel(writer, sheet_name="Names Mapping", index=False)
                potential_names_mapping_df.to_excel(writer, sheet_name="Potential Mappings", index=False)


        print("\n✅ Your file is now available.")







