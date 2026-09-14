from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from inventory.choices import Unit
from inventory.models import IngredientPeriod

REFERENCE_DATE = date(2026, 9, 13)


def create_ingredient(name: str, **overrides) -> IngredientPeriod:
    values = {
        "name": name,
        "unit": Unit.KILOGRAM,
        "target_stock": Decimal("10.000"),
        "initial_quantity": Decimal("10.000"),
        "period_consumption": Decimal("0"),
        "expiration_date": REFERENCE_DATE + timedelta(days=1),
        "ran_out_before_month_end": False,
    }
    values.update(overrides)
    return IngredientPeriod.objects.create(**values)


class ControlledReferenceAcceptanceTests(APITestCase):
    def test_required_outcomes_cross_database_service_and_purchase_api(self):
        normal = create_ingredient(
            "01 Normal",
            target_stock=Decimal("20.000"),
            initial_quantity=Decimal("20.000"),
            period_consumption=Decimal("8.000"),
        )
        expired = create_ingredient(
            "02 Vencido com sobra",
            target_stock=Decimal("20.000"),
            initial_quantity=Decimal("30.000"),
            period_consumption=Decimal("5.000"),
            expiration_date=REFERENCE_DATE - timedelta(days=1),
        )
        early = create_ingredient(
            "03 Falta antecipada",
            target_stock=Decimal("20.000"),
            initial_quantity=Decimal("10.000"),
            period_consumption=Decimal("10.000"),
            ran_out_before_month_end=True,
        )
        depleted = create_ingredient(
            "04 Esgotado sem falta antecipada",
            target_stock=Decimal("10.000"),
            initial_quantity=Decimal("10.000"),
            period_consumption=Decimal("10.000"),
        )
        sufficient = create_ingredient(
            "05 Estoque suficiente",
            target_stock=Decimal("10.000"),
            initial_quantity=Decimal("15.000"),
            period_consumption=Decimal("5.000"),
        )
        priority = create_ingredient(
            "06 Prioridade do vencimento",
            target_stock=Decimal("7.000"),
            initial_quantity=Decimal("10.000"),
            period_consumption=Decimal("10.000"),
            expiration_date=REFERENCE_DATE - timedelta(days=1),
            ran_out_before_month_end=True,
        )
        items = create_ingredient(
            "07 Compra em unidades",
            unit=Unit.ITEM,
            target_stock=Decimal("3"),
            initial_quantity=Decimal("3"),
            period_consumption=Decimal("3"),
            ran_out_before_month_end=True,
        )
        kg_rounding = create_ingredient(
            "08 Arredondamento Kg",
            target_stock=Decimal("1.001"),
            initial_quantity=Decimal("0"),
        )
        liter_rounding = create_ingredient(
            "09 Arredondamento L",
            unit=Unit.LITER,
            target_stock=Decimal("1.000"),
            initial_quantity=Decimal("1.111"),
            period_consumption=Decimal("1.111"),
            ran_out_before_month_end=True,
        )

        response = self.client.get(
            reverse("purchase-list"),
            {"data_referencia": REFERENCE_DATE.isoformat()},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data_referencia"], "2026-09-13")
        purchases = {item["id"]: item for item in response.data["compras"]}

        expected = {
            normal.pk: ("8", "reposicao_normal", "Comprar: 8 Kg de 01 Normal"),
            expired.pk: (
                "20",
                "vencimento",
                "Comprar: 20 Kg de 02 Vencido com sobra",
            ),
            early.pk: (
                "12",
                "falta_antecipada",
                "Comprar: 12 Kg de 03 Falta antecipada",
            ),
            depleted.pk: (
                "10",
                "reposicao_normal",
                "Comprar: 10 Kg de 04 Esgotado sem falta antecipada",
            ),
            priority.pk: (
                "7",
                "vencimento",
                "Comprar: 7 Kg de 06 Prioridade do vencimento",
            ),
            items.pk: (
                "4",
                "falta_antecipada",
                "Comprar: 4 un de 07 Compra em unidades",
            ),
            kg_rounding.pk: (
                "1.01",
                "reposicao_normal",
                "Comprar: 1,01 Kg de 08 Arredondamento Kg",
            ),
            liter_rounding.pk: (
                "1.34",
                "falta_antecipada",
                "Comprar: 1,34 L de 09 Arredondamento L",
            ),
        }

        self.assertNotIn(sufficient.pk, purchases)
        self.assertEqual(list(purchases), list(expected))
        for ingredient_id, (quantity, reason, text) in expected.items():
            with self.subTest(ingredient_id=ingredient_id):
                self.assertEqual(purchases[ingredient_id]["quantidade"], quantity)
                self.assertEqual(purchases[ingredient_id]["motivo"], reason)
                self.assertEqual(purchases[ingredient_id]["texto"], text)

        self.assertTrue(
            all(
                Decimal(purchase["quantidade"]) > Decimal("0")
                for purchase in response.data["compras"]
            )
        )
