"""Review and apply PubMed potential-name mappings in an in-memory workbook."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import OrderedDict
from io import BytesIO

import pandas as pd
from openpyxl import load_workbook


def normalize_name(value: object) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _sheet_name(workbook, requested: str) -> str | None:
    return next((name for name in workbook.sheetnames if name.lower() == requested.lower()), None)


def _name_columns(frame: pd.DataFrame) -> tuple[str, str] | None:
    candidates = [column for column in frame.columns if any(word in str(column).lower() for word in ("name", "author"))]
    if len(candidates) >= 2:
        return str(candidates[0]), str(candidates[1])
    if len(frame.columns) >= 2:
        return str(frame.columns[0]), str(frame.columns[1])
    return None


def _author_column(frame: pd.DataFrame) -> str | None:
    return next((str(column) for column in frame.columns if str(column).strip().lower() in {"author", "name"}), None)


def _evidence(frame: pd.DataFrame, author_column: str | None, name: str) -> dict:
    if not author_column or author_column not in frame.columns:
        return {"publications": 0, "affiliations": []}
    target = normalize_name(name)
    rows = frame[frame[author_column].map(normalize_name) == target]
    fields = [column for column in ("HCO", "Department", "City", "Affiliations") if column in rows.columns]
    affiliations = []
    for _, row in rows[fields].fillna("").iterrows():
        value = " · ".join(str(row[column]).strip() for column in fields if str(row[column]).strip())
        if value and value not in affiliations:
            affiliations.append(value)
    publications = rows["URL"].nunique() if "URL" in rows.columns else len(rows)
    return {"publications": int(publications), "affiliations": affiliations[:12]}


def potential_mapping_review(raw: bytes) -> dict:
    """Return grouped potential name pairs and evidence from the source workbook."""
    workbook = load_workbook(BytesIO(raw), read_only=True, data_only=True)
    potential_sheet = _sheet_name(workbook, "Potential Mappings")
    data_sheet = _sheet_name(workbook, "PubMed Data")
    if not potential_sheet or not data_sheet:
        return {"pairs": [], "message": "This workbook has no Potential Mappings sheet."}
    potential = pd.read_excel(BytesIO(raw), sheet_name=potential_sheet, dtype=str).fillna("")
    data = pd.read_excel(BytesIO(raw), sheet_name=data_sheet, dtype=str).fillna("")
    columns = _name_columns(potential)
    if not columns:
        return {"pairs": [], "message": "Potential Mappings does not contain two name columns."}
    left_column, right_column = columns
    author_column = _author_column(data)
    grouped: OrderedDict[str, dict] = OrderedDict()
    for _, row in potential.iterrows():
        left, right = str(row[left_column]).strip(), str(row[right_column]).strip()
        if not left or not right or normalize_name(left) == normalize_name(right):
            continue
        key = "|".join(sorted((normalize_name(left), normalize_name(right))))
        if key not in grouped:
            grouped[key] = {"id": str(len(grouped) + 1), "name_a": left, "name_b": right}
    pairs = []
    for pair in grouped.values():
        pairs.append({**pair, "evidence_a": _evidence(data, author_column, pair["name_a"]), "evidence_b": _evidence(data, author_column, pair["name_b"])})
    return {"pairs": pairs, "message": ""}


def apply_name_decisions(raw: bytes, decisions_json: str) -> BytesIO:
    """Merge approved aliases and move them from Potential to Names Mapping."""
    try:
        decisions = json.loads(decisions_json)
    except json.JSONDecodeError as exc:
        raise ValueError("Name-review decisions are not valid JSON.") from exc
    if not isinstance(decisions, list):
        raise ValueError("Name-review decisions must be a list.")

    replacements: dict[str, str] = {}
    merged_pairs: dict[str, tuple[str, str]] = {}
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        name_a, name_b = str(decision.get("name_a", "")).strip(), str(decision.get("name_b", "")).strip()
        action = decision.get("action")
        canonical = str(decision.get("canonical_name", "")).strip()
        if action == "merge" and name_a and name_b and canonical:
            replacements[normalize_name(name_a)] = canonical
            replacements[normalize_name(name_b)] = canonical
            other_name = name_b if normalize_name(canonical) == normalize_name(name_a) else name_a
            key = "|".join(sorted((normalize_name(name_a), normalize_name(name_b))))
            merged_pairs[key] = (other_name, canonical)

    workbook = load_workbook(BytesIO(raw))
    data_sheet = _sheet_name(workbook, "PubMed Data")
    if not data_sheet:
        raise ValueError("The workbook has no PubMed Data sheet.")
    worksheet = workbook[data_sheet]
    headers = {str(cell.value).strip().lower(): cell.column for cell in worksheet[1] if cell.value is not None}
    author_column = headers.get("author") or headers.get("name")
    if author_column:
        for row in range(2, worksheet.max_row + 1):
            cell = worksheet.cell(row=row, column=author_column)
            replacement = replacements.get(normalize_name(cell.value))
            if replacement:
                cell.value = replacement

    # Keep the original Names Mapping layout. The first two fields are the
    # alias and canonical name; the third field marks decisions made here.
    names_mapping_name = _sheet_name(workbook, "Names Mapping")
    if names_mapping_name:
        names_mapping_sheet = workbook[names_mapping_name]
        if names_mapping_sheet.max_row == 0:
            names_mapping_sheet.append(["Source name", "Mapped name", "Mapping type"])
    else:
        names_mapping_sheet = workbook.create_sheet("Names Mapping")
        names_mapping_sheet.append(["Source name", "Mapped name", "Mapping type"])
    for source_name, canonical_name in merged_pairs.values():
        names_mapping_sheet.append([source_name, canonical_name, "Potential Map"])

    # A confirmed merge no longer needs to appear in Potential Mappings.
    potential_mapping_name = _sheet_name(workbook, "Potential Mappings")
    if potential_mapping_name and merged_pairs:
        potential_sheet = workbook[potential_mapping_name]
        header_values = [cell.value for cell in potential_sheet[1]]
        potential_frame = pd.DataFrame(
            potential_sheet.iter_rows(min_row=2, values_only=True),
            columns=header_values,
        ).fillna("")
        pair_columns = _name_columns(potential_frame)
        if pair_columns:
            left_column, right_column = pair_columns
            keep_rows = []
            for _, row in potential_frame.iterrows():
                key = "|".join(sorted((normalize_name(row[left_column]), normalize_name(row[right_column]))))
                if key not in merged_pairs:
                    keep_rows.append(row.tolist())
            potential_sheet.delete_rows(2, potential_sheet.max_row)
            for row in keep_rows:
                potential_sheet.append(row)

    review_name = _sheet_name(workbook, "Name Review")
    if review_name:
        del workbook[review_name]
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output
