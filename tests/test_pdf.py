import pymupdf
import pytest

from orderscribe.pdf import PDFConversionError, pdf_to_markdown


def test_sample_preserves_order_values(sample_pdf):
    markdown = pdf_to_markdown(sample_pdf)
    assert "## Page 1" in markdown
    for value in (
        "PO39793",
        "53432",
        "2026-09-10",
        "739.58",
        "1.3920",
        "Encitech",
        "Ouneva",
        "VC05-0013",
        "VA01-0031",
        "VA01-0034",
        "VA01-0046",
        "VA01-0052",
        "VA01-0054",
        "VA01-0122",
        "VA01-0127",
        "4260-0100-09",
        "4260-0001-46",
    ):
        assert value in markdown


def test_missing_pdf(tmp_path):
    with pytest.raises(FileNotFoundError):
        pdf_to_markdown(tmp_path / "missing.pdf")


def test_invalid_pdf(tmp_path):
    source = tmp_path / "broken.pdf"
    source.write_text("not a pdf")
    with pytest.raises(PDFConversionError, match="Could not convert"):
        pdf_to_markdown(source)


def test_textless_page_requires_ocr(tmp_path):
    source = tmp_path / "scan.pdf"
    with pymupdf.open() as document:
        document.new_page()
        document.save(source)
    with pytest.raises(PDFConversionError, match="Page 1.*OCR"):
        pdf_to_markdown(source)


def test_multiple_pages(tmp_path):
    source = tmp_path / "multiple.pdf"
    with pymupdf.open() as document:
        for text in ("Order 123", "Continuation item 456"):
            page = document.new_page()
            page.insert_text((72, 72), text)
        document.save(source)
    markdown = pdf_to_markdown(source)
    assert "## Page 1" in markdown
    assert "## Page 2" in markdown
    assert "Order 123" in markdown
    assert "Continuation item 456" in markdown
