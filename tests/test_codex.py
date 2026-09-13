import json
import subprocess
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from orderscribe.codex import CodexExtractionError, CodexExtractor
from orderscribe.models import PurchaseOrder


def test_extract_uses_schema_stdin_and_validates(order_data):
    def run(command, **kwargs):
        assert command[-1] == "-"
        assert "document contents" in kwargs["input"]
        assert "document contents" not in command
        assert command[command.index("--sandbox") + 1] == "read-only"
        assert command[command.index("--model") + 1] == "test-model"
        schema = json.loads(Path(command[command.index("--output-schema") + 1]).read_text())
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])
        decimal_schema = schema["$defs"]["LineItem"]["properties"]["ordered_quantity"]["anyOf"][0]
        assert decimal_schema["type"] == "string"
        assert "(?" not in decimal_schema["pattern"]
        output = Path(command[command.index("--output-last-message") + 1])
        output.write_text(json.dumps(order_data))
        return subprocess.CompletedProcess(command, 0, stdout="log noise", stderr="")

    with patch("orderscribe.codex.shutil.which", return_value="/usr/bin/codex"):
        with patch("orderscribe.codex.subprocess.run", side_effect=run):
            order = CodexExtractor(model="test-model").extract("document contents")
    assert isinstance(order, PurchaseOrder)
    assert order.order_date == date(2026, 9, 10)
    assert order.items[0].unit_price == Decimal("1.3920")
    assert order.items[0].unit_price.as_tuple().exponent == -4
    assert order.items[0].confirmed_delivery_date is None


def test_missing_executable():
    with patch("orderscribe.codex.shutil.which", return_value=None):
        with pytest.raises(CodexExtractionError, match="CLI not found"):
            CodexExtractor().extract("order")


@pytest.mark.parametrize("failure", ["timeout", "nonzero", "missing", "invalid"])
def test_codex_failures(failure):
    def run(command, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 1)
        if failure == "invalid":
            Path(command[command.index("--output-last-message") + 1]).write_text('{"items": []}')
        return subprocess.CompletedProcess(command, 1 if failure == "nonzero" else 0, "", "failure")

    with patch("orderscribe.codex.shutil.which", return_value="/usr/bin/codex"):
        with patch("orderscribe.codex.subprocess.run", side_effect=run):
            with pytest.raises(CodexExtractionError):
                CodexExtractor(timeout=1).extract("order")


def test_empty_input():
    with pytest.raises(ValueError, match="empty"):
        CodexExtractor().extract("  ")


def test_schema_rejects_invalid_values(order_data):
    order_data["items"][0]["requested_delivery_date"] = "2026-02-30"
    with pytest.raises(ValidationError):
        PurchaseOrder.model_validate(order_data)


def test_schema_rejects_invented_fields(order_data):
    order_data["invented"] = "value"
    with pytest.raises(ValidationError):
        PurchaseOrder.model_validate(order_data)


def test_schema_rejects_nonfinite_amounts(order_data):
    order_data["total_amount"] = "NaN"
    with pytest.raises(ValidationError):
        PurchaseOrder.model_validate(order_data)
