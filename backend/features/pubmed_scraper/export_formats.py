"""Convert a reviewed PubMed workbook without losing sheets or leading zeros."""
import csv
from io import BytesIO, StringIO
from openpyxl import load_workbook


def convert_workbook(raw, export_format):
    if export_format not in {"xlsx", "csv"}:
        raise ValueError("Choose Excel or CSV.")
    workbook = load_workbook(BytesIO(raw))
    if "PubMed Data" not in workbook.sheetnames:
        raise ValueError("The workbook has no PubMed Data sheet.")
    if export_format == "csv":
        text = StringIO(newline="")
        writer = csv.writer(text)
        for row in workbook["PubMed Data"].iter_rows(values_only=True):
            writer.writerow(["" if value is None else str(value) for value in row])
        return BytesIO(text.getvalue().encode("utf-8-sig"))
    for sheet in workbook:
        for row in sheet:
            for cell in row:
                if cell.value is not None:
                    cell.value = str(cell.value)
                    cell.data_type = "s"
                cell.number_format = "@"
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output
