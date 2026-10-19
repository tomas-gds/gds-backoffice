import json
import os
from io import BytesIO

import pandas as pd
from python_calamine import CalamineWorkbook
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.features.database_mapper.exporter import (
    append_unmapped_target_rows,
    create_csv_file,
    create_excel_workbook,
    create_text_excel_workbook,
)
from backend.features.database_mapper.duplicate_reports import (
    create_duplicate_report,
    validate_mapping_duplicates,
)

from backend.features.database_mapper.matcher import (
    CANDIDATE_LIMIT,
    detect_columns,
    duplicated_rows,
    match_frames,
    matching_strategy,
    prepare_search_columns,
    search_rows,
)
from backend.features.database_mapper.jobs import JobCancelled, JobConflict, JobFailed, mapper_jobs
from backend.features.pubmed_scraper.legacy_adapter import (
    inspect_hcp_file,
    run_legacy_workflow,
)
from backend.features.pubmed_scraper.jobs import pubmed_jobs, JobCancelled as PubmedJobCancelled, JobConflict as PubmedJobConflict
from backend.features.pubmed_scraper.export_formats import convert_workbook
from backend.features.pubmed_scraper.review import (
    apply_name_decisions,
    potential_mapping_review,
)


# Shared Account settings are sent by the desktop app. These optional code
# defaults are retained for local development and environment-variable use.
PUBMED_DEFAULT_EMAIL = ""
PUBMED_DEFAULT_API_KEY = ""


app = FastAPI(title="Provider Mapping Engine", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:1420", "http://127.0.0.1:1420",
        "http://tauri.localhost", "tauri://localhost",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    expose_headers=["X-Unmapped-Target-Rows"],
)


async def read_table(upload: UploadFile):
    raw = await upload.read()
    name = (upload.filename or "").lower()
    try:
        if name.endswith(".csv"):
            frame = pd.read_csv(
                BytesIO(raw), dtype=str, keep_default_na=False, na_filter=False
            )
        elif name.endswith((".xlsx", ".xls")):
            frame = pd.read_excel(
                BytesIO(raw), engine="calamine", dtype=str,
                keep_default_na=False, na_filter=False,
            )
        else:
            raise HTTPException(400, "Only CSV, XLSX, and XLS files are supported.")
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(400, f"Could not read {upload.filename}: {exc}") from exc

    return frame


async def inspect_table(upload: UploadFile):
    """Read column names and row count without sampling data values."""
    raw = await upload.read()
    name = (upload.filename or "").lower()
    try:
        if name.endswith(".csv"):
            frame = pd.read_csv(BytesIO(raw), nrows=0)
            # Exact CSV row counting would require parsing the complete file. This
            # fast estimate is replaced by the exact count when matching runs.
            row_count = max(raw.count(b"\n") - 1, 0)
        elif name.endswith((".xlsx", ".xls")):
            with CalamineWorkbook.from_filelike(BytesIO(raw)) as workbook:
                sheet = workbook.get_sheet_by_index(0)
                first_row = sheet.to_python(nrows=1)
                raw_headers = first_row[0] if first_row else []
                headers = []
                counts = {}
                for column_index, value in enumerate(raw_headers):
                    base = str(value).strip() if value not in (None, "") else f"Unnamed: {column_index}"
                    occurrence = counts.get(base, 0)
                    counts[base] = occurrence + 1
                    headers.append(base if occurrence == 0 else f"{base}.{occurrence}")
                frame = pd.DataFrame(columns=headers)
                row_count = max(sheet.height - 1, 0)
        else:
            raise HTTPException(400, "Only CSV, XLSX, and XLS files are supported.")
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(400, f"Could not read {upload.filename}: {exc}") from exc
    return frame, row_count


def validate_columns(frame, columns, label):
    if not isinstance(columns, list) or not columns:
        raise HTTPException(400, f"Select at least one {label} column.")
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise HTTPException(400, f'{label} column "{missing[0]}" does not exist.')


def parse_columns(raw_columns, label):
    try:
        columns = json.loads(raw_columns)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, f"{label} columns are not valid JSON.") from exc
    if not isinstance(columns, list) or not all(isinstance(column, str) for column in columns):
        raise HTTPException(400, f"{label} columns must be a list of headers.")
    return columns


def validate_pairs(raw_pairs, source_frame, target_frame):
    if not isinstance(raw_pairs, list) or not raw_pairs:
        raise HTTPException(400, "Select at least one column pair before matching.")
    validated = []
    for index, pair in enumerate(raw_pairs):
        source = pair.get("source")
        target = pair.get("target")
        method = pair.get("method", "similarity")
        weight = pair.get("weight", 1)
        if source not in source_frame.columns or target not in target_frame.columns:
            raise HTTPException(400, f"Column pair {index + 1} contains an unknown header.")
        if method not in {"exact", "similarity"}:
            raise HTTPException(400, f"Column pair {index + 1} has an invalid comparison method.")
        try:
            weight = float(weight)
        except (TypeError, ValueError) as exc:
            raise HTTPException(400, f"Column pair {index + 1} has an invalid weight.") from exc
        if weight <= 0:
            raise HTTPException(400, "Every selected column pair must have a positive weight.")
        validated.append({"source": source, "target": target, "method": method, "weight": weight})
    return validated


@app.get("/health")
def health():
    return {"status": "ok"}


def pubmed_defaults():
    email = PUBMED_DEFAULT_EMAIL.strip() or os.getenv("PUBMED_EMAIL", "").strip()
    api_key = PUBMED_DEFAULT_API_KEY.strip() or os.getenv("PUBMED_API_KEY", "").strip()
    return {
        "email": email,
        "default_years": 5,
        "api_key_configured": bool(api_key),
    }


@app.get("/pubmed/config")
def pubmed_config():
    return pubmed_defaults()


@app.post("/pubmed/inspect-hcp-file")
async def pubmed_inspect_hcp_file(file: UploadFile = File(...)):
    try:
        return inspect_hcp_file(await file.read(), file.filename or "")
    except Exception as exc:
        raise HTTPException(400, f"Could not read the HCP file: {exc}") from exc


@app.post("/pubmed/cancel/{job_id}")
async def cancel_pubmed(job_id: str):
    try:
        return await pubmed_jobs.cancel(job_id)
    except ValueError as exc:
        raise HTTPException(400, "Invalid PubMed job ID.") from exc


@app.on_event("shutdown")
async def stop_pubmed_workers():
    await pubmed_jobs.shutdown()



@app.post("/pubmed/export")
async def pubmed_export(
    request: Request,
    job_id: str = Form(""),
    search: str = Form(...),
    country: str = Form(...),
    years: int = Form(5),
    mode: str = Form("author"),
    email: str = Form(""),
    api_key: str = Form(""),
    hcp_file: UploadFile | None = File(None),
    sheet: str = Form(""),
    name_column: str = Form(""),
    include_full_network: bool = Form(False),
    rare_disease: bool = Form(True),
):
    search, country = search.strip(), country.strip()
    defaults = pubmed_defaults()
    email = email.strip() or defaults["email"]
    api_key = api_key.strip() or (PUBMED_DEFAULT_API_KEY.strip() or os.getenv("PUBMED_API_KEY", "").strip())
    if not search or not country:
        raise HTTPException(400, "Search terms and country are required.")
    if not email:
        raise HTTPException(400, "Set a PubMed email in Account before running the scraper.")
    if mode not in {"author", "hco", "company", "hcp_file"}:
        raise HTTPException(400, "Choose HCPs, HCOs, company, or an HCP-file scraper.")
    if not 1 <= years <= 30:
        raise HTTPException(400, "Years must be between 1 and 30.")
    try:
        workbook = await pubmed_jobs.run(dict(
            mode=mode, search=search, country=country, years=years,
            email=email, api_key=api_key,
            hcp_file=await hcp_file.read() if hcp_file else None,
            hcp_filename=hcp_file.filename if hcp_file else "",
            sheet=sheet, name_column=name_column,
            include_full_network=include_full_network,
            rare_disease=rare_disease,
        ), job_id=job_id or None, request=request)
    except PubmedJobCancelled as exc:
        raise HTTPException(409, "PubMed search stopped.") from exc
    except (PubmedJobConflict, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"PubMed could not complete the search: {exc}") from exc
    safe_search = "".join(char if char.isalnum() else "_" for char in search).strip("_") or "search"
    safe_country = "".join(char if char.isalnum() else "_" for char in country).strip("_") or "country"
    return StreamingResponse(
        workbook,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="pubmed_{mode}_{safe_search}_{safe_country}.xlsx"'},
    )


@app.post("/pubmed/review-potential-mappings")
async def review_pubmed_potential_mappings(workbook: UploadFile = File(...)):
    try:
        return potential_mapping_review(await workbook.read())
    except Exception as exc:
        raise HTTPException(400, f"Could not read the PubMed workbook: {exc}") from exc


@app.post("/pubmed/apply-name-decisions")
async def apply_pubmed_name_decisions(
    workbook: UploadFile = File(...),
    decisions: str = Form("[]"),
):
    try:
        output = apply_name_decisions(await workbook.read(), decisions)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(400, f"Could not update the PubMed workbook: {exc}") from exc
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="pubmed-reviewed.xlsx"'},
    )


@app.post("/inspect")
async def inspect(file: UploadFile = File(...)):
    frame, row_count = await inspect_table(file)
    return {
        "filename": file.filename,
        "rows": row_count,
        "columns": list(map(str, frame.columns)),
        "detected": detect_columns(frame),
    }


@app.post("/database-mapper/cancel/{job_id}")
async def cancel_database_mapper(job_id: str):
    try:
        return await mapper_jobs.cancel(job_id)
    except ValueError as exc:
        raise HTTPException(400, "Invalid Database Mapper job ID.") from exc


@app.on_event("shutdown")
async def stop_database_mapper_workers():
    await mapper_jobs.shutdown()


@app.post("/inspect-pair")
async def inspect_pair(source: UploadFile = File(...), target: UploadFile = File(...)):
    source_frame, source_rows = await inspect_table(source)
    target_frame, target_rows = await inspect_table(target)
    return {
        "source": {"filename": source.filename, "rows": source_rows, "columns": list(map(str, source_frame.columns))},
        "target": {"filename": target.filename, "rows": target_rows, "columns": list(map(str, target_frame.columns))},
        "suggested_pairs": [],
    }


@app.post("/match")
async def match(
    request: Request,
    source: UploadFile = File(...),
    target: UploadFile = File(...),
    column_pairs: str = Form(...),
    job_id: str = Form(...),
):
    try:
        raw_pairs = json.loads(column_pairs)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "Column-pair configuration is not valid JSON.") from exc
    if not isinstance(raw_pairs, list):
        raise HTTPException(400, "Column-pair configuration is not valid JSON.")
    try:
        return await mapper_jobs.run({"source": await source.read(), "source_name": source.filename or "",
                                      "target": await target.read(), "target_name": target.filename or "",
                                      "pairs": raw_pairs}, job_id, request)
    except JobCancelled as exc:
        raise HTTPException(409, "Matching stopped.") from exc
    except JobConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except JobFailed as exc:
        raise HTTPException(exc.status, exc.detail) from exc


@app.post("/validate-primary")
async def validate_primary(
    source: UploadFile = File(...),
    target: UploadFile = File(...),
    source_columns: str = Form(...),
    target_columns: str = Form(...),
):
    source_frame = await read_table(source)
    target_frame = await read_table(target)
    parsed_source_columns = parse_columns(source_columns, "File A")
    parsed_target_columns = parse_columns(target_columns, "File B")
    validate_columns(source_frame, parsed_source_columns, "File A")
    validate_columns(target_frame, parsed_target_columns, "File B")
    return validate_mapping_duplicates(
        source_frame,
        target_frame,
        parsed_source_columns,
        parsed_target_columns,
    )


@app.post("/duplicate-report")
async def duplicate_report(
    source: UploadFile = File(...),
    target: UploadFile = File(...),
    source_columns: str = Form(...),
    target_columns: str = Form(...),
    duplicate_kind: str = Form("exact"),
):
    source_frame = await read_table(source)
    target_frame = await read_table(target)
    parsed_source_columns = parse_columns(source_columns, "File A")
    parsed_target_columns = parse_columns(target_columns, "File B")
    validate_columns(source_frame, parsed_source_columns, "File A")
    validate_columns(target_frame, parsed_target_columns, "File B")
    try:
        output = create_duplicate_report(
            source_frame,
            target_frame,
            parsed_source_columns,
            parsed_target_columns,
            duplicate_kind,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{duplicate_kind}-duplicate-values.xlsx"'
        },
    )


@app.post("/search-candidates")
async def search_candidates(
    target: UploadFile = File(...),
    primary_column: str = Form(...),
    target_columns: str = Form(...),
    query: str = Form(""),
    filters: str = Form(""),
):
    target_frame = await read_table(target)
    parsed_target_columns = parse_columns(target_columns, "File B")
    validate_columns(target_frame, parsed_target_columns, "File B")
    validate_columns(target_frame, [primary_column], "File B")
    parsed_filters = None
    if filters:
        try:
            parsed_filters = json.loads(filters)
        except json.JSONDecodeError as exc:
            raise HTTPException(400, "Search filters are not valid JSON.") from exc
        if not isinstance(parsed_filters, dict):
            raise HTTPException(400, "Search filters must be an object.")
    return {
        "results": search_rows(
            target_frame,
            primary_column,
            parsed_target_columns,
            query,
            filters=parsed_filters,
        )
    }


@app.post("/create-export")
async def create_export(
    export_payload: str = Form(...),
    include_unmapped_target: bool = Form(False),
    mapped_target_indices: str = Form("[]"),
    target_columns: str = Form("[]"),
    source_column_count: int = Form(0),
    source: UploadFile | None = File(None),
    target: UploadFile | None = File(None),
    export_format: str = Form("xlsx"),
):
    unmapped_rows_appended = 0
    source_frame = None
    target_frame = None
    try:
        payload = json.loads(export_payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "Export data is not valid JSON.") from exc

    headers = payload.get("headers")
    rows = payload.get("rows")
    include_unmapped_target = bool(
        include_unmapped_target or payload.get("include_unmapped_target") is True
    )
    expected_unmapped_target_count = payload.get("expected_unmapped_target_count")
    if not isinstance(headers, list) or not headers:
        raise HTTPException(400, "Export headers are missing.")
    if not isinstance(rows, list):
        raise HTTPException(400, "Export rows are missing.")
    if any(not isinstance(row, list) or len(row) != len(headers) for row in rows):
        raise HTTPException(400, "Export rows do not match the selected columns.")

    source_extra_columns = payload.get("source_extra_columns", [])
    target_extra_columns = payload.get("target_extra_columns", [])
    row_indices = payload.get("row_indices", [])
    source_mapping_column_count = payload.get("source_mapping_column_count", 0)
    target_mapping_column_count = payload.get("target_mapping_column_count", 0)
    if not isinstance(source_extra_columns, list) or not all(
        isinstance(column, str) for column in source_extra_columns
    ):
        raise HTTPException(400, "Additional File A columns are not valid.")
    if not isinstance(target_extra_columns, list) or not all(
        isinstance(column, str) for column in target_extra_columns
    ):
        raise HTTPException(400, "Additional File B columns are not valid.")

    if source_extra_columns or target_extra_columns:
        if source is None or target is None:
            raise HTTPException(
                400,
                "Both input files are required to include additional export columns.",
            )
        if not isinstance(row_indices, list) or len(row_indices) != len(rows):
            raise HTTPException(400, "Export row indexes are not valid.")
        if not isinstance(source_mapping_column_count, int) or not isinstance(
            target_mapping_column_count, int
        ):
            raise HTTPException(400, "Export column configuration is not valid.")

        source_frame = await read_table(source)
        target_frame = await read_table(target)
        if source_extra_columns:
            validate_columns(source_frame, source_extra_columns, "File A")
        if target_extra_columns:
            validate_columns(target_frame, target_extra_columns, "File B")

        target_start = source_mapping_column_count + len(source_extra_columns)
        for row, indexes in zip(rows, row_indices):
            if not isinstance(indexes, dict) or not isinstance(
                indexes.get("source_index"), int
            ):
                raise HTTPException(400, "Export row indexes are not valid.")
            source_index = indexes["source_index"]
            if source_index < 0 or source_index >= len(source_frame):
                raise HTTPException(400, "A File A row index is out of range.")
            source_row = source_frame.iloc[source_index]
            for offset, column in enumerate(source_extra_columns):
                value = source_row[column]
                row[source_mapping_column_count + offset] = "" if pd.isna(value) else str(value)

            target_index = indexes.get("target_index")
            if target_index is None:
                continue
            if not isinstance(target_index, int) or target_index < 0 or target_index >= len(target_frame):
                raise HTTPException(400, "A File B row index is out of range.")
            target_row = target_frame.iloc[target_index]
            for offset, column in enumerate(target_extra_columns):
                value = target_row[column]
                row[target_start + target_mapping_column_count + offset] = "" if pd.isna(value) else str(value)

    if include_unmapped_target:
        if target is None:
            raise HTTPException(400, "File B is required to include its unused rows.")
        parsed_target_columns = parse_columns(target_columns, "File B")
        try:
            parsed_indices = json.loads(mapped_target_indices)
        except json.JSONDecodeError as exc:
            raise HTTPException(400, "Mapped File B row indexes are invalid.") from exc
        if not isinstance(parsed_indices, list):
            raise HTTPException(400, "Mapped File B row indexes must be a list.")
        if target_frame is None:
            target_frame = await read_table(target)
        validate_columns(target_frame, parsed_target_columns, "File B")
        if source_column_count < 1:
            raise HTTPException(400, "The File A column count is invalid.")
        original_row_count = len(rows)
        rows = append_unmapped_target_rows(
            rows,
            target_frame,
            parsed_target_columns,
            parsed_indices,
            source_column_count,
        )
        unmapped_rows_appended = len(rows) - original_row_count
        if (
            isinstance(expected_unmapped_target_count, int)
            and unmapped_rows_appended != expected_unmapped_target_count
        ):
            raise HTTPException(
                500,
                "The export could not include every unused File B row: "
                f"expected {expected_unmapped_target_count}, appended {unmapped_rows_appended}.",
            )

    if export_format == "csv":
        output = create_csv_file(headers, rows)
        media_type = "text/csv; charset=utf-8"
        download_name = "matching.csv"
    else:
        output = create_excel_workbook(headers, rows)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        download_name = "matching.xlsx"
    return StreamingResponse(
        output,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
            "X-Unmapped-Target-Rows": str(unmapped_rows_appended),
        },
    )


@app.post("/pubmed/convert-export")
async def convert_pubmed_export(workbook: UploadFile = File(...), export_format: str = Form("xlsx")):
    try:
        output = convert_workbook(await workbook.read(), export_format)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    media_type = "text/csv; charset=utf-8" if export_format == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(output, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="pubmed.{export_format}"'})

