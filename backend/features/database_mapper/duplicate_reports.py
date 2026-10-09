"""Duplicate-validation payloads and downloadable workbooks for Database Mapper."""

from .exporter import create_text_excel_workbook
from .matcher import duplicate_summary


def validate_mapping_duplicates(source_frame, target_frame, source_columns, target_columns):
    source = duplicate_summary(source_frame, source_columns)
    target = duplicate_summary(target_frame, target_columns)

    source_exact = source["exact"]
    target_exact = target["exact"]
    source_almost = source["almost"]
    target_almost = target["almost"]
    has_exact_duplicates = not source_exact.empty or not target_exact.empty

    return {
        # Only exact duplicates block matching.
        "valid": not has_exact_duplicates,
        "has_exact_duplicates": has_exact_duplicates,
        "has_almost_duplicates": not source_almost.empty or not target_almost.empty,
        "source_exact_duplicate_rows": len(source_exact),
        "target_exact_duplicate_rows": len(target_exact),
        "source_almost_duplicate_rows": len(source_almost),
        "target_almost_duplicate_rows": len(target_almost),
    }


def create_duplicate_report(source_frame, target_frame, source_columns, target_columns, kind):
    if kind not in {"exact", "almost"}:
        raise ValueError("duplicate_kind must be 'exact' or 'almost'.")

    source_rows = duplicate_summary(source_frame, source_columns)[kind]
    target_rows = duplicate_summary(target_frame, target_columns)[kind]
    return create_text_excel_workbook(
        [
            ("File A", source_rows.columns, source_rows.fillna("").astype(str).values.tolist()),
            ("File B", target_rows.columns, target_rows.fillna("").astype(str).values.tolist()),
        ]
    )
