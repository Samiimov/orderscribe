from unittest.mock import patch

from orderscribe.cli import main
from orderscribe.codex import CodexExtractionError
from orderscribe.models import PurchaseOrder


def test_pipeline_saves_both_outputs(sample_pdf, tmp_path, order_data):
    with patch("orderscribe.cli.CodexExtractor.extract", return_value=PurchaseOrder(**order_data)):
        assert main(["run", str(sample_pdf), "--output-dir", str(tmp_path)]) == 0
    assert "PO39793" in (tmp_path / "PO39793-01.md").read_text()
    order = PurchaseOrder.model_validate_json((tmp_path / "PO39793-01.json").read_text())
    assert order.order_number == "PO39793"


def test_markdown_survives_codex_failure(sample_pdf, tmp_path):
    with patch(
        "orderscribe.cli.CodexExtractor.extract", side_effect=CodexExtractionError("offline")
    ):
        assert main(["run", str(sample_pdf), "--output-dir", str(tmp_path)]) == 1
    assert (tmp_path / "PO39793-01.md").is_file()
    assert not (tmp_path / "PO39793-01.json").exists()


def test_refuses_overwriting_output(sample_pdf, tmp_path):
    destination = tmp_path / "PO39793-01.md"
    destination.write_text("existing")
    assert main(["convert", str(sample_pdf), "--output-dir", str(tmp_path)]) == 1
    assert destination.read_text() == "existing"


def test_extract_existing_markdown(tmp_path, order_data):
    source = tmp_path / "order.md"
    source.write_text("# An order")
    with patch(
        "orderscribe.cli.CodexExtractor.extract", return_value=PurchaseOrder(**order_data)
    ) as run:
        assert main(["extract", str(source), "--output-dir", str(tmp_path)]) == 0
    run.assert_called_once_with("# An order")
    assert (tmp_path / "order.json").is_file()
