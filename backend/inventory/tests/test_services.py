from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from inventory.choices import Unit
from inventory.models import IngredientPeriod
from inventory.services import ReplenishmentReason, calculate_replenishment

REFERENCE_DATE = date(2026, 9, 13)


def make_snapshot(**overrides) -> IngredientPeriod:
    values = {
        "name": "Arroz",
        "unit": Unit.KILOGRAM,
        "target_stock": Decimal("10.000"),
        "initial_quantity": Decimal("8.000"),
        "period_consumption": Decimal("3.000"),
        "expiration_date": REFERENCE_DATE + timedelta(days=10),
        "ran_out_before_month_end": False,
    }
    values.update(overrides)
    return IngredientPeriod(**values)


class ReplenishmentServiceTests(TestCase):
    def test_normal_replenishment_uses_target_difference(self):
        result = calculate_replenishment(
            make_snapshot(), reference_date=REFERENCE_DATE
        )

        self.assertEqual(result.current_stock, Decimal("5.000"))
        self.assertEqual(result.usable_stock, Decimal("5.000"))
        self.assertEqual(result.purchase_quantity, Decimal("5.00"))
        self.assertEqual(result.reason, ReplenishmentReason.NORMAL)

    def test_expired_stock_is_unusable_and_target_is_purchased(self):
        result = calculate_replenishment(
            make_snapshot(expiration_date=REFERENCE_DATE - timedelta(days=1)),
            reference_date=REFERENCE_DATE,
        )

        self.assertEqual(result.current_stock, Decimal("5.000"))
        self.assertEqual(result.usable_stock, Decimal("0"))
        self.assertEqual(result.purchase_quantity, Decimal("10.00"))
        self.assertEqual(result.reason, ReplenishmentReason.EXPIRED)

    def test_early_depletion_purchases_consumption_plus_twenty_percent(self):
        result = calculate_replenishment(
            make_snapshot(
                initial_quantity=Decimal("7.500"),
                period_consumption=Decimal("7.500"),
                ran_out_before_month_end=True,
            ),
            reference_date=REFERENCE_DATE,
        )

        self.assertEqual(result.current_stock, Decimal("0.000"))
        self.assertEqual(result.usable_stock, Decimal("0.000"))
        self.assertEqual(result.purchase_quantity, Decimal("9.00"))
        self.assertEqual(result.reason, ReplenishmentReason.EARLY_DEPLETION)

    def test_sufficient_stock_results_in_zero_purchase(self):
        result = calculate_replenishment(
            make_snapshot(
                target_stock=Decimal("10.000"),
                initial_quantity=Decimal("12.000"),
                period_consumption=Decimal("1.000"),
            ),
            reference_date=REFERENCE_DATE,
        )

        self.assertEqual(result.current_stock, Decimal("11.000"))
        self.assertEqual(result.purchase_quantity, Decimal("0.00"))
        self.assertEqual(result.reason, ReplenishmentReason.STOCK_SUFFICIENT)

    def test_expiration_has_priority_over_early_depletion(self):
        result = calculate_replenishment(
            make_snapshot(
                target_stock=Decimal("5.000"),
                initial_quantity=Decimal("10.000"),
                period_consumption=Decimal("10.000"),
                expiration_date=REFERENCE_DATE - timedelta(days=1),
                ran_out_before_month_end=True,
            ),
            reference_date=REFERENCE_DATE,
        )

        self.assertEqual(result.purchase_quantity, Decimal("5.00"))
        self.assertEqual(result.reason, ReplenishmentReason.EXPIRED)

    def test_expiration_boundary_uses_fixed_reference_date(self):
        expected = {
            REFERENCE_DATE - timedelta(days=1): (
                ReplenishmentReason.EXPIRED,
                Decimal("10.00"),
            ),
            REFERENCE_DATE: (ReplenishmentReason.NORMAL, Decimal("5.00")),
            REFERENCE_DATE + timedelta(days=1): (
                ReplenishmentReason.NORMAL,
                Decimal("5.00"),
            ),
        }

        for expiration_date, (reason, purchase_quantity) in expected.items():
            with self.subTest(expiration_date=expiration_date):
                result = calculate_replenishment(
                    make_snapshot(expiration_date=expiration_date),
                    reference_date=REFERENCE_DATE,
                )
                self.assertEqual(result.reason, reason)
                self.assertEqual(result.purchase_quantity, purchase_quantity)

    def test_item_purchase_is_rounded_up_to_whole_unit(self):
        result = calculate_replenishment(
            make_snapshot(
                unit=Unit.ITEM,
                target_stock=Decimal("3"),
                initial_quantity=Decimal("3"),
                period_consumption=Decimal("3"),
                ran_out_before_month_end=True,
            ),
            reference_date=REFERENCE_DATE,
        )

        self.assertEqual(result.purchase_quantity, Decimal("4"))

    def test_kg_and_liter_purchases_are_rounded_up_to_two_places(self):
        for unit in (Unit.KILOGRAM, Unit.LITER):
            with self.subTest(unit=unit):
                result = calculate_replenishment(
                    make_snapshot(
                        unit=unit,
                        target_stock=Decimal("1.001"),
                        initial_quantity=Decimal("0"),
                        period_consumption=Decimal("0"),
                    ),
                    reference_date=REFERENCE_DATE,
                )
                self.assertEqual(result.purchase_quantity, Decimal("1.01"))

    def test_calculation_does_not_change_or_persist_snapshot_data(self):
        snapshot = make_snapshot()
        snapshot.save()
        original_values = {
            "target_stock": snapshot.target_stock,
            "initial_quantity": snapshot.initial_quantity,
            "period_consumption": snapshot.period_consumption,
            "expiration_date": snapshot.expiration_date,
            "ran_out_before_month_end": snapshot.ran_out_before_month_end,
        }

        with self.assertNumQueries(0):
            calculate_replenishment(snapshot, reference_date=REFERENCE_DATE)

        snapshot.refresh_from_db()
        persisted_values = {
            "target_stock": snapshot.target_stock,
            "initial_quantity": snapshot.initial_quantity,
            "period_consumption": snapshot.period_consumption,
            "expiration_date": snapshot.expiration_date,
            "ran_out_before_month_end": snapshot.ran_out_before_month_end,
        }
        self.assertEqual(persisted_values, original_values)
