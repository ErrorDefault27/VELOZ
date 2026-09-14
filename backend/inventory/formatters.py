from decimal import Decimal


def format_decimal_plain(value: Decimal) -> str:
    """Return a non-exponential decimal string without redundant zeroes."""

    formatted = format(value, "f")
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted or "0"


def format_decimal_pt_br(value: Decimal) -> str:
    """Format a Decimal for human-facing Brazilian Portuguese text."""

    plain = format_decimal_plain(value)
    integer_part, separator, decimal_part = plain.partition(".")
    grouped_integer = f"{int(integer_part):,}".replace(",", ".")
    return (
        f"{grouped_integer},{decimal_part}" if separator else grouped_integer
    )

