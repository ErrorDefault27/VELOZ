from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from inventory.choices import Unit
from inventory.models import IngredientPeriod

REFERENCE_DATE = date(2026, 9, 13)


def ingredient_values(**overrides):
    values = {
        "name": "Farinha",
        "unit": Unit.KILOGRAM,
        "target_stock": Decimal("10.000"),
        "initial_quantity": Decimal("8.000"),
        "period_consumption": Decimal("3.000"),
        "expiration_date": REFERENCE_DATE + timedelta(days=10),
        "ran_out_before_month_end": False,
    }
    values.update(overrides)
    return values


def api_payload(**overrides):
    values = {
        "nome": "Farinha",
        "unidade": "kg",
        "meta_estoque": "10.000",
        "quantidade_inicial": "8.000",
        "consumo_periodo": "3.000",
        "data_validade": "2026-09-23",
        "acabou_antes_fim_mes": False,
    }
    values.update(overrides)
    return values


class IngredientApiTests(APITestCase):
    def test_crud_and_read_only_current_stock(self):
        create_response = self.client.post(
            reverse("ingredient-list"),
            api_payload(estoque_atual="999.000"),
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["meta_estoque"], "10.000")
        self.assertEqual(create_response.data["estoque_atual"], "5.000")
        ingredient_id = create_response.data["id"]

        list_response = self.client.get(reverse("ingredient-list"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)

        detail_url = reverse("ingredient-detail", args=[ingredient_id])
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["nome"], "Farinha")

        patch_response = self.client.patch(
            detail_url,
            {"consumo_periodo": "5.000", "estoque_atual": "999.000"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["estoque_atual"], "3.000")

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(IngredientPeriod.objects.exists())

    def test_patch_validates_changes_together_with_existing_values(self):
        ingredient = IngredientPeriod.objects.create(
            **ingredient_values(
                target_stock=Decimal("10.500"),
                initial_quantity=Decimal("8.500"),
                period_consumption=Decimal("3.500"),
            )
        )

        response = self.client.patch(
            reverse("ingredient-detail", args=[ingredient.pk]),
            {"unidade": "un"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("meta_estoque", response.data)
        self.assertIn("quantidade_inicial", response.data)
        self.assertIn("consumo_periodo", response.data)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.unit, Unit.KILOGRAM)

    def test_patch_rejects_consumption_above_existing_initial_quantity(self):
        ingredient = IngredientPeriod.objects.create(**ingredient_values())

        response = self.client.patch(
            reverse("ingredient-detail", args=[ingredient.pk]),
            {"consumo_periodo": "8.001"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("consumo_periodo", response.data)
        self.assertIn("não pode superar", str(response.data["consumo_periodo"][0]))

    def test_patch_rejects_inconsistent_early_depletion_flag(self):
        ingredient = IngredientPeriod.objects.create(**ingredient_values())

        response = self.client.patch(
            reverse("ingredient-detail", args=[ingredient.pk]),
            {"acabou_antes_fim_mes": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("acabou_antes_fim_mes", response.data)

    def test_post_returns_field_errors_in_portuguese(self):
        response = self.client.post(
            reverse("ingredient-list"),
            api_payload(quantidade_inicial="2.000", consumo_periodo="2.001"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("consumo_periodo", response.data)
        self.assertIn("não pode superar", str(response.data["consumo_periodo"][0]))

    def test_post_rejects_negative_and_fractional_item_quantities(self):
        invalid_payloads = (
            (api_payload(meta_estoque="-0.001"), "meta_estoque"),
            (
                api_payload(
                    unidade="un",
                    meta_estoque="3.500",
                    quantidade_inicial="3",
                    consumo_periodo="1",
                ),
                "meta_estoque",
            ),
        )

        for payload, expected_field in invalid_payloads:
            with self.subTest(expected_field=expected_field):
                response = self.client.post(
                    reverse("ingredient-list"), payload, format="json"
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(expected_field, response.data)

    def test_post_rejects_early_depletion_with_stock_or_zero_consumption(self):
        invalid_payloads = (
            api_payload(acabou_antes_fim_mes=True),
            api_payload(
                meta_estoque="1.000",
                quantidade_inicial="0",
                consumo_periodo="0",
                acabou_antes_fim_mes=True,
            ),
        )

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post(
                    reverse("ingredient-list"), payload, format="json"
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("acabou_antes_fim_mes", response.data)

    def test_list_order_is_stable_and_predictable(self):
        second = IngredientPeriod.objects.create(**ingredient_values(name="zimbro"))
        first = IngredientPeriod.objects.create(**ingredient_values(name="Açúcar"))
        third = IngredientPeriod.objects.create(**ingredient_values(name="Zimbro"))

        response = self.client.get(reverse("ingredient-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["id"] for item in response.data],
            [first.pk, third.pk, second.pk],
        )

    def test_missing_ingredient_returns_portuguese_not_found_error(self):
        response = self.client.get(reverse("ingredient-detail", args=[999999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"detail": "Ingrediente não encontrado."})


class PurchaseApiTests(APITestCase):
    def test_purchase_list_filters_zero_and_formats_output(self):
        normal = IngredientPeriod.objects.create(
            **ingredient_values(
                name="Farinha especial",
                target_stock=Decimal("2.000"),
                initial_quantity=Decimal("1.234"),
                period_consumption=Decimal("0"),
            )
        )
        enough = IngredientPeriod.objects.create(
            **ingredient_values(
                name="Açúcar",
                target_stock=Decimal("5.000"),
                initial_quantity=Decimal("7.000"),
                period_consumption=Decimal("1.000"),
            )
        )
        items = IngredientPeriod.objects.create(
            **ingredient_values(
                name="Ovos caipiras",
                unit=Unit.ITEM,
                target_stock=Decimal("3"),
                initial_quantity=Decimal("3"),
                period_consumption=Decimal("3"),
                ran_out_before_month_end=True,
            )
        )

        response = self.client.get(
            reverse("purchase-list"),
            {"data_referencia": REFERENCE_DATE.isoformat()},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data_referencia"], "2026-09-13")
        self.assertEqual(
            [purchase["id"] for purchase in response.data["compras"]],
            [normal.pk, items.pk],
        )
        self.assertNotIn(enough.pk, [item["id"] for item in response.data["compras"]])
        self.assertEqual(
            response.data["compras"][0],
            {
                "id": normal.pk,
                "nome": "Farinha especial",
                "unidade": "Kg",
                "quantidade": "0.77",
                "motivo": "reposicao_normal",
                "texto": "Comprar: 0,77 Kg de Farinha especial",
            },
        )
        self.assertEqual(response.data["compras"][1]["quantidade"], "4")
        self.assertEqual(
            response.data["compras"][1]["texto"],
            "Comprar: 4 un de Ovos caipiras",
        )

    def test_invalid_reference_date_returns_field_error(self):
        invalid_dates = ("13-09-2026", "2026-02-30", "", "2026-9-1")

        for invalid_date in invalid_dates:
            with self.subTest(invalid_date=invalid_date):
                response = self.client.get(
                    reverse("purchase-list"),
                    {"data_referencia": invalid_date},
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("data_referencia", response.data)

    @patch("inventory.views.timezone.localdate", return_value=REFERENCE_DATE)
    def test_missing_reference_date_uses_backend_local_date(self, localdate_mock):
        IngredientPeriod.objects.create(
            **ingredient_values(expiration_date=REFERENCE_DATE)
        )

        response = self.client.get(reverse("purchase-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data_referencia"], "2026-09-13")
        self.assertEqual(response.data["compras"][0]["motivo"], "reposicao_normal")
        localdate_mock.assert_called_once_with()

    def test_purchase_get_has_no_persistent_side_effects(self):
        ingredient = IngredientPeriod.objects.create(**ingredient_values())
        original = {
            "target_stock": ingredient.target_stock,
            "initial_quantity": ingredient.initial_quantity,
            "period_consumption": ingredient.period_consumption,
            "expiration_date": ingredient.expiration_date,
            "ran_out_before_month_end": ingredient.ran_out_before_month_end,
        }

        first_response = self.client.get(
            reverse("purchase-list"),
            {"data_referencia": REFERENCE_DATE.isoformat()},
        )
        second_response = self.client.get(
            reverse("purchase-list"),
            {"data_referencia": REFERENCE_DATE.isoformat()},
        )

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(first_response.data, second_response.data)
        ingredient.refresh_from_db()
        persisted = {
            "target_stock": ingredient.target_stock,
            "initial_quantity": ingredient.initial_quantity,
            "period_consumption": ingredient.period_consumption,
            "expiration_date": ingredient.expiration_date,
            "ran_out_before_month_end": ingredient.ran_out_before_month_end,
        }
        self.assertEqual(persisted, original)
        self.assertEqual(IngredientPeriod.objects.count(), 1)
