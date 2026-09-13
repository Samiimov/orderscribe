"""Purchase-order schema. Missing document values remain null, never guessed."""

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, WithJsonSchema

Number = Annotated[
    Decimal,
    Field(allow_inf_nan=False),
    # Pydantic's default decimal regex uses lookarounds, which Codex rejects.
    WithJsonSchema({"type": "string", "pattern": r"^-?[0-9]+(\.[0-9]+)?$"}, mode="serialization"),
]
Currency = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]


class OrderModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Party(OrderModel):
    name: str | None
    address_lines: list[str]
    country: str | None
    vat_number: str | None
    email: str | None
    phone: str | None


class LineItem(OrderModel):
    position: str | None
    buyer_part_number: str | None
    supplier_part_number: str | None
    description: str | None
    ordered_quantity: Number | None
    remaining_quantity: Number | None
    unit: str | None
    unit_price: Number | None
    currency: Currency | None
    requested_delivery_date: date | None
    confirmed_delivery_date: date | None
    line_total: Number | None = Field(
        description="Explicit printed line total only; do not compute"
    )


class PurchaseOrder(OrderModel):
    order_number: str | None
    order_date: date | None
    supplier_number: str | None
    buyer: Party | None
    supplier: Party | None
    ship_to: Party | None
    buyer_reference: str | None
    supplier_reference: str | None
    payment_terms: str | None
    delivery_terms: str | None
    forwarder_account: str | None
    mark: str | None
    currency: Currency | None
    total_amount: Number | None
    items: list[LineItem] = Field(min_length=1)
    notes: list[str]
    warnings: list[str] = Field(description="Ambiguities, unreadable values or inconsistencies")
