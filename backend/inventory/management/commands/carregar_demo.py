from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from inventory.choices import Unit
from inventory.models import IngredientPeriod


class Command(BaseCommand):
    help = "Carrega fotografias demonstrativas sem apagar ou sobrescrever dados."

    def handle(self, *args, **options):
        today = timezone.localdate()
        demonstrations = (
            {
                "name": "Arroz integral (demo)",
                "unit": Unit.KILOGRAM,
                "target_stock": Decimal("10.000"),
                "initial_quantity": Decimal("8.000"),
                "period_consumption": Decimal("3.000"),
                "expiration_date": today + timedelta(days=30),
                "ran_out_before_month_end": False,
            },
            {
                "name": "Leite integral (demo)",
                "unit": Unit.LITER,
                "target_stock": Decimal("15.000"),
                "initial_quantity": Decimal("12.000"),
                "period_consumption": Decimal("2.000"),
                "expiration_date": today - timedelta(days=1),
                "ran_out_before_month_end": False,
            },
            {
                "name": "Feijão preto (demo)",
                "unit": Unit.KILOGRAM,
                "target_stock": Decimal("8.000"),
                "initial_quantity": Decimal("6.000"),
                "period_consumption": Decimal("6.000"),
                "expiration_date": today + timedelta(days=30),
                "ran_out_before_month_end": True,
            },
            {
                "name": "Sal refinado (demo)",
                "unit": Unit.KILOGRAM,
                "target_stock": Decimal("5.000"),
                "initial_quantity": Decimal("8.000"),
                "period_consumption": Decimal("1.000"),
                "expiration_date": today + timedelta(days=90),
                "ran_out_before_month_end": False,
            },
            {
                "name": "Ovos (demo)",
                "unit": Unit.ITEM,
                "target_stock": Decimal("3"),
                "initial_quantity": Decimal("3"),
                "period_consumption": Decimal("3"),
                "expiration_date": today + timedelta(days=15),
                "ran_out_before_month_end": True,
            },
        )

        created = 0
        skipped = 0
        for values in demonstrations:
            if IngredientPeriod.objects.filter(name=values["name"]).exists():
                skipped += 1
                continue

            IngredientPeriod.objects.create(**values)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Carga concluída: {created} criado(s), {skipped} preservado(s)."
            )
        )
