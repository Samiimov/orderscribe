# OrderScribe

Convert a purchase-order PDF into a reviewable Markdown document, then use the
Codex CLI to extract a validated Pydantic `PurchaseOrder`. The CLI saves the object
as JSON; the Python API returns the actual Pydantic object.

## Setup

Requires Python 3.12–3.14, Poetry 2, and an authenticated Codex CLI for extraction.

```bash
poetry install

# If Codex is not already installed (requires Node.js/npm):
npm install -g @openai/codex
codex login
```

The PDF conversion runs locally. Extraction sends the Markdown to Codex using
your existing CLI authentication and model configuration. No Python OpenAI SDK
or separate API key is required when using an authenticated Codex account.

## Usage

Replace `path/to/order.pdf` with the path to your purchase-order PDF.

```bash
poetry run orderscribe run path/to/order.pdf
```

Creates:

- `output/order.md`: page headings and formatted source text.
- `output/order.json`: the validated purchase order, including line items.

Run the stages separately to review or edit the Markdown before extraction:

```bash
# Local conversion; does not require Codex or a network connection.
poetry run orderscribe convert path/to/order.pdf

# Interpret an existing Markdown file.
poetry run orderscribe extract output/order.md
```

Options:

- `--output-dir PATH`: destination folder (default: `output`).
- `--force`: replace existing output files.
- `--model MODEL`: override the configured Codex model (`run` and `extract`).
- `--timeout SECONDS`: limit the Codex call (default: 180 seconds).

Existing outputs are preserved unless `--force` is supplied. If Codex fails,
the Markdown remains available, and no new JSON result is saved. If an older JSON
file already exists and a forced rerun fails, that older file remains unchanged.
Errors return exit code 1 and are written to stderr.

## Python API

```python
from pathlib import Path

from orderscribe import CodexExtractor, PurchaseOrder, pdf_to_markdown

markdown = pdf_to_markdown("path/to/order.pdf")
Path("order.md").write_text(markdown, encoding="utf-8")

order: PurchaseOrder = CodexExtractor(timeout=180).extract(markdown)
print(order.order_number)
print(order.items[0].supplier_part_number)
print(order.items[0].unit_price)  # Decimal, not float

Path("order.json").write_text(order.model_dump_json(indent=2), encoding="utf-8")

# Reload with the same validation and Python types.
saved = PurchaseOrder.model_validate_json(Path("order.json").read_text(encoding="utf-8"))
```

## Data and validation

The schema is in `src/orderscribe/models.py`. It covers buyer, supplier, ship-to
address, references, payment/delivery terms, currency, total, and line items with
both buyer and supplier part numbers. Ordered/remaining quantities and
requested/confirmed delivery dates are separate fields.

Amounts and quantities use `Decimal` and are serialized as strings, preserving
values such as `"1.3920"`. Dates become `datetime.date` values. Missing values are
explicit `null` values; missing lists are empty. A valid order must contain at
least one line item. Unknown fields, invalid dates, nonfinite amounts, and invalid
currency-code shapes are rejected. The prompt requests ambiguities in `warnings`
and document instructions in `notes`; missing totals are not calculated.

The Pydantic serialization schema is passed to `codex exec --output-schema`, and
the resulting JSON is validated locally. Codex runs in a temporary working
directory with a read-only command sandbox and an ephemeral session. The prompt
treats document content as data and requests extraction without tool use.
Your Codex CLI still needs access to its own state directory and authentication.

## Conversion scope

PyMuPDF4LLM preserves page boundaries and text formatting. Vector graphics are
ignored because the supplied order form's surrounding lines otherwise cause
the converter to omit its line items. This setting also disables automatic table
detection: rows remain formatted text in source order, with semantic fields
assigned by Codex in the second stage.

This version handles text-based PDFs. Image-only pages fail with an instruction
to run OCR first; password-protected PDFs are not supported. Mixed pages with
text and images only contribute their text layer. Complex layouts and unfamiliar
order templates should be checked against the source PDF. Pydantic validates
structure and types, not the factual accuracy or completeness of model extraction.

## Development

```bash
poetry run pytest
poetry run ruff check .
poetry run ruff format --check .
poetry build
```

Tests exercise the supplied PDF, multiple pages, invalid/textless PDFs, precision,
schema validation, subprocess errors/timeouts, and CLI output handling. Codex calls
are mocked in the test suite, so tests do not consume model usage.

Integration references: [Codex non-interactive mode and structured output](https://developers.openai.com/codex/noninteractive/)
and [PyMuPDF4LLM API](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html).
