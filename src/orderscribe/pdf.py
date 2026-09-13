"""Local PDF conversion with page boundaries and Markdown formatting."""

from pathlib import Path

import pymupdf
import pymupdf4llm


class PDFConversionError(ValueError):
    pass


def pdf_to_markdown(source: str | Path) -> str:
    source = Path(source)
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() != ".pdf":
        raise PDFConversionError("Input must be a PDF file")
    try:
        with pymupdf.open(source) as document:
            if document.needs_pass:
                raise PDFConversionError("Password-protected PDFs are not supported")
            if not document.page_count:
                raise PDFConversionError("PDF has no pages")
            for index, page in enumerate(document, start=1):
                if not page.get_text().strip():
                    raise PDFConversionError(
                        f"Page {index} has no extractable text. Run OCR on the PDF first."
                    )
            chunks = pymupdf4llm.to_markdown(
                document,
                page_chunks=True,
                show_progress=False,
                write_images=False,
                # Order forms often wrap text in large vector rectangles. Without this,
                # the converter can classify the entire item area as a graphic and omit it.
                ignore_graphics=True,
            )
    except PDFConversionError:
        raise
    except Exception as exc:
        raise PDFConversionError(f"Could not convert {source.name}: {exc}") from exc

    sections = ["# Purchase order document", f"Source: {source.name}"]
    for index, chunk in enumerate(chunks, start=1):
        content = chunk["text"].strip()
        if not content:
            raise PDFConversionError(f"Markdown extraction produced no text for page {index}")
        sections.append(f"## Page {index}\n\n{content}")
    return "\n\n".join(sections) + "\n"
