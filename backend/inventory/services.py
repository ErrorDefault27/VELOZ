from dataclasses import dataclass
from datetime import date
from decimal import ROUND_CEILING, Decimal
from enum import StrEnum

from django.core.exceptions import ValidationError

from .choices import Unit
from .models import IngredientPeriod
from .validators import validate_inventory_snapshot


class ReplenishmentReason(StrEnum):
    EXPIRED = "vencimento"
    EARLY_DEPLETION = "falta_antecipada"
    NORMAL = "reposicao_normal"
    STOCK_SUFFICIENT = "estoque_suficiente"


@dataclass(frozen=True, slots=True)
class ReplenishmentResult:
    current_stock: Decimal
    usable_stock: Decimal
    purchase_quantity: Decimal
    reason: ReplenishmentReason


def _round_purchase(quantity: Decimal, unit: str) -> Decimal:
    quantum = Decimal("1") if unit == Unit.ITEM else Decimal("0.01")
    return quantity.quantize(quantum, rounding=ROUND_CEILING)


def calculate_replenishment(
    snapshot: IngredientPeriod,
    *,
    reference_date: date,
) -> ReplenishmentResult:
    """Calculate replenishment for a snapshot without writing to the database."""

    if not isinstance(reference_date, date):
        raise TypeError("reference_date deve ser uma data explícita.")
    if not isinstance(snapshot.expiration_date, date):
        raise ValidationError({"expiration_date": "Informe uma data de validade válida."})

    validate_inventory_snapshot(
        unit=snapshot.unit,
        target_stock=snapshot.target_stock,
        initial_quantity=snapshot.initial_quantity,
        period_consumption=snapshot.period_consumption,
        ran_out_before_month_end=snapshot.ran_out_before_month_end,
    )

    current_stock = snapshot.current_stock

    if snapshot.expiration_date < reference_date:
        usable_stock = Decimal("0")
        raw_purchase = snapshot.target_stock
        reason = ReplenishmentReason.EXPIRED
    elif snapshot.ran_out_before_month_end:
        usable_stock = current_stock
        raw_purchase = snapshot.period_consumption * Decimal("1.20")
        reason = ReplenishmentReason.EARLY_DEPLETION
    else:
        usable_stock = current_stock
        raw_purchase = max(snapshot.target_stock - current_stock, Decimal("0"))
        reason = (
            ReplenishmentReason.NORMAL
            if raw_purchase > Decimal("0")
            else ReplenishmentReason.STOCK_SUFFICIENT
        )

    return ReplenishmentResult(
        current_stock=current_stock,
        usable_stock=usable_stock,
        purchase_quantity=_round_purchase(raw_purchase, snapshot.unit),
        reason=reason,
    )

