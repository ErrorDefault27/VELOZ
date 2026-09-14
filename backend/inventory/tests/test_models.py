from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from inventory.choices import Unit
from inventory.models import IngredientPeriod


def valid_snapshot(**overrides) -> IngredientPeriod:
    values = {
        "name": "Feijão",
        "unit": Unit.KILOGRAM,
        "target_stock": Decimal("10.000"),
        "initial_quantity": Decimal("8.000"),
        "period_consumption": Decimal("3.000"),
        "expiration_date": date(2026, 10, 1),
        "ran_out_before_month_end": False,
    }
    values.update(overrides)
    return IngredientPeriod(**values)


class IngredientPeriodValidationTests(TestCase):
    def test_current_stock_is_derived_from_initial_quantity_and_consumption(self):
        snapshot = valid_snapshot()

        self.assertEqual(snapshot.current_stock, Decimal("5.000"))

    def test_quantities_cannot_be_negative(self):
        for field_name in ("target_stock", "initial_quantity", "period_consumption"):
            with self.subTest(field_name=field_name):
                snapshot = valid_snapshot(**{field_name: Decimal("-0.001")})
                with self.assertRaises(ValidationError) as context:
                    snapshot.full_clean()
                self.assertIn(field_name, context.exception.message_dict)

    def test_consumption_cannot_exceed_initial_quantity(self):
        snapshot = valid_snapshot(
            initial_quantity=Decimal("2.000"),
            period_consumption=Decimal("2.001"),
        )

        with self.assertRaises(ValidationError) as context:
            snapshot.full_clean()

        self.assertIn("period_consumption", context.exception.message_dict)

    def test_early_depletion_requires_zero_current_stock(self):
        snapshot = valid_snapshot(ran_out_before_month_end=True)

        with self.assertRaises(ValidationError) as context:
            snapshot.full_clean()

        self.assertIn("ran_out_before_month_end", context.exception.message_dict)

    def test_early_depletion_requires_positive_consumption(self):
        snapshot = valid_snapshot(
            target_stock=Decimal("1.000"),
            initial_quantity=Decimal("0"),
            period_consumption=Decimal("0"),
            ran_out_before_month_end=True,
        )

        with self.assertRaises(ValidationError) as context:
            snapshot.full_clean()

        self.assertIn("ran_out_before_month_end", context.exception.message_dict)

    def test_item_quantities_must_be_integers(self):
        for field_name in ("target_stock", "initial_quantity", "period_consumption"):
            with self.subTest(field_name=field_name):
                values = {
                    "target_stock": Decimal("5"),
                    "initial_quantity": Decimal("5"),
                    "period_consumption": Decimal("1"),
                    field_name: Decimal("1.500"),
                }
                snapshot = valid_snapshot(unit=Unit.ITEM, **values)
                with self.assertRaises(ValidationError) as context:
                    snapshot.full_clean()
                self.assertIn(field_name, context.exception.message_dict)

    def test_quantity_precision_and_maximum_are_enforced(self):
        invalid_values = (Decimal("1.0001"), Decimal("1000000000.000"))

        for value in invalid_values:
            with self.subTest(value=value):
                snapshot = valid_snapshot(target_stock=value)
                with self.assertRaises(ValidationError) as context:
                    snapshot.full_clean()
                self.assertIn("target_stock", context.exception.message_dict)

    def test_save_runs_full_clean(self):
        snapshot = valid_snapshot(
            initial_quantity=Decimal("1.000"),
            period_consumption=Decimal("2.000"),
        )

        with self.assertRaises(ValidationError):
            snapshot.save()

        self.assertEqual(IngredientPeriod.objects.count(), 0)

