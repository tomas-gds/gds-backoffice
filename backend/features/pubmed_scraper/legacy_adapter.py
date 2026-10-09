"""Translate app inputs/downloads into the original CMD scraper workflows.

Processing lives in legacy/*.py. Keep this layer free of search, normalization,
filtering, deduplication and workbook-layout decisions.
"""
from __future__ import annotations

import importlib
import os
import tempfile
import threading
from contextlib import contextmanager
from io import BytesIO

import pandas as pd
from Bio import Entrez

from .legacy.PubmedScraperAuthors import PubmedScraperAuthors
from .legacy.PubmedScraperHCO import PubmedScraperHCO
from .legacy.PubmedScraperHCP import PubmedScraperHCP

# Entrez credentials are process globals. Serialize workflows so concurrent
# requests cannot change another request's credentials or terminal answers.
_WORKFLOW_LOCK = threading.RLock()


def _headers(columns):
    return columns.astype(str).str.replace("\n", " ", regex=False).str.strip().tolist()


def inspect_hcp_file(raw: bytes, filename: str) -> dict:
    suffix = os.path.splitext(filename)[1].lower()
    if suffix == ".csv":
        columns = _headers(pd.read_csv(BytesIO(raw), nrows=0).columns)
        return {"sheets": [{"name": "CSV", "columns": columns}]}
    if suffix not in {".xlsx", ".xls"}:
        raise ValueError("Upload a CSV, XLSX, or XLS file.")
    with pd.ExcelFile(BytesIO(raw)) as workbook:
        return {"sheets": [
            {"name": sheet, "columns": _headers(pd.read_excel(workbook, sheet_name=sheet, nrows=0).columns)}
            for sheet in workbook.sheet_names
        ]}


@contextmanager
def _hcp_answers(path: str, sheet: str, name_column: str, full_network: bool):
    # Shadow input only inside the HCP module, not Python's global builtins.
    # Dispatch by prompt because one-sheet Excel files omit the sheet prompt.
    module = importlib.import_module(PubmedScraperHCP.__module__)
    missing = object()
    previous = module.__dict__.get("input", missing)
    def answer(prompt=""):
        prompt = prompt.lower()
        if "path to your file" in prompt:
            return path
        if "worksheet" in prompt:
            return sheet
        if "column" in prompt:
            return name_column
        if "full network" in prompt:
            return "y" if full_network else "n"
        raise RuntimeError(f"Unsupported legacy input prompt: {prompt}")
    module.input = answer
    try:
        yield
    finally:
        if previous is missing:
            del module.input
        else:
            module.input = previous


def run_legacy_workflow(
    mode: str, search: str, country: str, years: int, email: str, api_key: str,
    hcp_file: bytes | None = None, hcp_filename: str = "", sheet: str = "",
    name_column: str = "", include_full_network: bool = False,
    rare_disease: bool = True,
) -> BytesIO:
    """Run the CMD main() method with app inputs and an in-memory download.

    rare_disease is passed to the selected scraper and its normalizers.
    """
    classes = {"author": PubmedScraperAuthors, "company": PubmedScraperAuthors,
               "hco": PubmedScraperHCO, "hcp_file": PubmedScraperHCP}
    if mode not in classes:
        raise ValueError("Choose authors, HCOs, company, or an HCP file workflow.")
    country = country.strip()
    if country.lower() in {"united kingdom", "uk"}:
        country = "UK"  # Same conversion as the CMD menu.
    temporary_path = None
    with _WORKFLOW_LOCK:
        previous_credentials = Entrez.email, Entrez.api_key
        try:
            scraper = classes[mode](search=search.strip(), country=country, numyears=years,rare=rare_disease)
            # Set these after construction: nested legacy scrapers set Entrez.
            Entrez.email, Entrez.api_key = email, api_key or None
            output = BytesIO()
            writer = scraper.pubmed_scraper.write_excel
            scraper.pubmed_scraper.write_excel = lambda *args, **kwargs: writer(*args, **kwargs, output=output)
            if mode == "hcp_file":
                if not hcp_file or not hcp_filename or not name_column:
                    raise ValueError("Upload an HCP file and choose its name column.")
                inspected = inspect_hcp_file(hcp_file, hcp_filename)
                sheets = inspected["sheets"]
                selected = next((item for item in sheets if item["name"] == sheet), None)
                if len(sheets) == 1:
                    selected = sheets[0]
                if selected is None:
                    raise ValueError("Choose an existing HCP worksheet.")
                name_column = name_column.replace("\n", " ").strip()
                if name_column not in selected["columns"]:
                    raise ValueError("Choose an existing clinician-name column.")
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(hcp_filename)[1]) as temporary:
                    temporary.write(hcp_file)
                    temporary_path = temporary.name
                with _hcp_answers(temporary_path, selected["name"], name_column, include_full_network):
                    scraper.main()
            else:
                scraper.main()
            if not output.getbuffer().nbytes:
                # CMD produces no file for no results; preserve the app's
                # download contract with an empty workbook in that case.
                with pd.ExcelWriter(output, engine="openpyxl") as empty_writer:
                    pd.DataFrame().to_excel(empty_writer, sheet_name="PubMed Data", index=False)
            output.seek(0)
            return output
        finally:
            Entrez.email, Entrez.api_key = previous_credentials
            if temporary_path is not None:
                os.unlink(temporary_path)
