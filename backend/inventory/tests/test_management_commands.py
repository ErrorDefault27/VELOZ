from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from inventory.models import IngredientPeriod

TODAY = date(2026, 9, 13)


class LoadDemoCommandTests(TestCase):
    @patch(
        "inventory.management.commands.carregar_demo.timezone.localdate",
        return_value=TODAY,
    )
    def test_command_is_idempotent_and_uses_relative_dates(self, localdate_mock):
        first_output = StringIO()
        call_command("carregar_demo", stdout=first_output)

        self.assertEqual(IngredientPeriod.objects.count(), 5)
        self.assertEqual(
            IngredientPeriod.objects.get(name="Leite integral (demo)").expiration_date,
            TODAY - timedelta(days=1),
        )
        self.assertEqual(
            IngredientPeriod.objects.get(name="Arroz integral (demo)").expiration_date,
            TODAY + timedelta(days=30),
        )
        self.assertIn("5 criado(s), 0 preservado(s)", first_output.getvalue())

        IngredientPeriod.objects.filter(name="Arroz integral (demo)").update(
            target_stock=Decimal("77.000")
        )
        second_output = StringIO()
        call_command("carregar_demo", stdout=second_output)

        self.assertEqual(IngredientPeriod.objects.count(), 5)
        self.assertEqual(
            IngredientPeriod.objects.get(name="Arroz integral (demo)").target_stock,
            Decimal("77.000"),
        )
        self.assertIn("0 criado(s), 5 preservado(s)", second_output.getvalue())
        self.assertEqual(localdate_mock.call_count, 2)

