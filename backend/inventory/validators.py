from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import DecimalValidator, MaxValueValidator, MinValueValidator

from .choices import Unit

QUANTITY_MAX_DIGITS = 12
QUANTITY_DECIMAL_PLACES = 3
MAX_QUANTITY = Decimal("999999999.999")

QUANTITY_RANGE_VALIDATORS = (
    MinValueValidator(Decimal("0"), message="A quantidade não pode ser negativa."),
    MaxValueValidator(
        MAX_QUANTITY,
        message=f"A quantidade não pode ser maior que {MAX_QUANTITY}.",
    ),
)

QUANTITY_VALIDATORS = (
    *QUANTITY_RANGE_VALIDATORS,
    DecimalValidator(QUANTITY_MAX_DIGITS, QUANTITY_DECIMAL_PLACES),
)


def _validate_quantity(
    field_name: str,
    value: object,
    errors: dict[str, list[str]],
) -> bool:
    if not isinstance(value, Decimal) or not value.is_finite():
        errors.setdefault(field_name, []).append("Informe uma quantidade decimal válida.")
        return False

    is_valid = True
    for validator in QUANTITY_VALIDATORS:
        try:
            validator(value)
        except ValidationError as exc:
            errors.setdefault(field_name, []).extend(exc.messages)
            is_valid = False

    return is_valid


def validate_inventory_snapshot(
    *,
    unit: str,
    target_stock: object,
    initial_quantity: object,
    period_consumption: object,
    ran_out_before_month_end: bool,
) -> None:
    """Validate a period snapshot without mutating it.

    This function is the shared business-validation entry point for the model,
    API serializers and other programmatic callers.
    """

    errors: dict[str, list[str]] = {}
    valid_quantities = {
        "target_stock": _validate_quantity("target_stock", target_stock, errors),
        "initial_quantity": _validate_quantity(
            "initial_quantity", initial_quantity, errors
        ),
        "period_consumption": _validate_quantity(
            "period_consumption", period_consumption, errors
        ),
    }

    if unit not in Unit.values:
        errors.setdefault("unit", []).append("Selecione uma unidade válida.")

    if unit == Unit.ITEM:
        quantities = {
            "target_stock": target_stock,
            "initial_quantity": initial_quantity,
            "period_consumption": period_consumption,
        }
        for field_name, value in quantities.items():
            if valid_quantities[field_name] and value != value.to_integral_value():
                errors.setdefault(field_name, []).append(
                    "Quantidades medidas em un devem ser inteiras."
                )

    if valid_quantities["initial_quantity"] and valid_quantities["period_consumption"]:
        if period_consumption > initial_quantity:
            errors.setdefault("period_consumption", []).append(
                "O consumo não pode superar a quantidade inicial do período."
            )

        current_stock = initial_quantity - period_consumption
        if ran_out_before_month_end and not (
            current_stock == Decimal("0") and period_consumption > Decimal("0")
        ):
            errors.setdefault("ran_out_before_month_end", []).append(
                "A falta antecipada exige estoque atual zero e consumo maior que zero."
            )

    if errors:
        raise ValidationError(errors)
