"""Focused safe CSV/XLSX inspection tests."""

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from openpyxl import Workbook

from app.services.import_parser import ImportParseError, ImportParser, ImportParserLimits


def xlsx_bytes() -> bytes:
    workbook = Workbook()
    active = workbook.active
    assert active is not None
    active.title = "People"
    active.append(["Name", "Score", "Formula"])
    active.append(["Ali", 4, "=1+1"])
    active.append(["Sara", 5, "=2+2"])
    second = workbook.create_sheet("Teams")
    second.append(["Team"])
    second.append(["Architecture"])
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def test_csv_inspection_returns_columns_rows_and_bounded_samples() -> None:
    parser = ImportParser(ImportParserLimits(sample_values_per_column=2))
    result = parser.inspect(BytesIO(b"Name,Score\nAli,4\nSara,5\nReza,6\n"), filename="people.csv")
    sheet = result.sheets[0]
    assert sheet.name == "people.csv"
    assert sheet.row_count == 3
    assert [column.name for column in sheet.columns] == ["Name", "Score"]
    assert sheet.columns[0].sample_values == ("Ali", "Sara")
    assert sheet.columns[1].sample_values == ("4", "5")


def test_xlsx_inspection_lists_sheets_and_never_evaluates_formulas() -> None:
    result = ImportParser().inspect(BytesIO(xlsx_bytes()), filename="people.xlsx")
    assert [(sheet.name, sheet.row_count) for sheet in result.sheets] == [
        ("People", 2),
        ("Teams", 1),
    ]
    assert [column.name for column in result.sheets[0].columns] == [
        "Name",
        "Score",
        "Formula",
    ]
    assert result.sheets[0].columns[0].sample_values == ("Ali", "Sara")
    assert result.sheets[0].columns[2].sample_values == ()


@pytest.mark.parametrize(
    ("payload", "filename", "reason"),
    [
        (b"not a workbook", "bad.xlsx", "MALFORMED_XLSX"),
        (b"\xff\xfe\x00", "bad.csv", "CSV_INVALID_ENCODING"),
        (b"A,A\n1,2\n", "duplicate.csv", "DUPLICATE_HEADER"),
        (b"", "empty.csv", "EMPTY_FILE"),
    ],
)
def test_malformed_inputs_fail_with_safe_reason(payload: bytes, filename: str, reason: str) -> None:
    with pytest.raises(ImportParseError, match=reason) as raised:
        ImportParser().inspect(BytesIO(payload), filename=filename)
    assert raised.value.reason == reason


def test_limits_reject_file_row_and_zip_bomb_shapes() -> None:
    with pytest.raises(ImportParseError, match="FILE_TOO_LARGE"):
        ImportParser(ImportParserLimits(max_file_bytes=3)).inspect(
            BytesIO(b"A\n123"), filename="large.csv"
        )
    with pytest.raises(ImportParseError, match="TOO_MANY_ROWS"):
        ImportParser(ImportParserLimits(max_rows_per_sheet=1)).inspect(
            BytesIO(b"A\n1\n2\n"), filename="rows.csv"
        )

    archive = BytesIO()
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as workbook:
        workbook.writestr("xl/worksheets/sheet1.xml", "0" * 100_000)
    with pytest.raises(ImportParseError, match="XLSX_SUSPICIOUS_COMPRESSION"):
        ImportParser(ImportParserLimits(max_compression_ratio=2)).inspect(
            BytesIO(archive.getvalue()), filename="bomb.xlsx"
        )


def test_unsupported_extension_is_rejected_before_parsing() -> None:
    with pytest.raises(ImportParseError, match="UNSUPPORTED_FILE_TYPE"):
        ImportParser().inspect(BytesIO(b"A\n1"), filename="people.xls")
