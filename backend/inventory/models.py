from decimal import Decimal

from django.db import models
from django.db.models import F, Q

from .choices import Unit
from .validators import (
    QUANTITY_DECIMAL_PLACES,
    QUANTITY_MAX_DIGITS,
    QUANTITY_RANGE_VALIDATORS,
    validate_inventory_snapshot,
)


def quantity_field(verbose_name: str) -> models.DecimalField:
    return models.DecimalField(
        verbose_name,
        max_digits=QUANTITY_MAX_DIGITS,
        decimal_places=QUANTITY_DECIMAL_PLACES,
        # DecimalField already adds its own DecimalValidator for precision.
        validators=list(QUANTITY_RANGE_VALIDATORS),
    )


class IngredientPeriod(models.Model):
    """A single ingredient snapshot for one evaluated period.

    This simplified version assumes there are no stock entries during the period.
    Current stock is therefore always initial quantity minus period consumption.
    """

    name = models.CharField("ingrediente", max_length=120)
    unit = models.CharField("unidade", max_length=2, choices=Unit.choices)
    target_stock = quantity_field("meta de estoque")
    initial_quantity = quantity_field("quantidade inicial")
    period_consumption = quantity_field("consumo do período")
    expiration_date = models.DateField("data de validade")
    ran_out_before_month_end = models.BooleanField(
        "acabou antes do fim do mês",
        default=False,
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "fotografia de ingrediente"
        verbose_name_plural = "fotografias de ingredientes"
        constraints = [
            models.CheckConstraint(
                condition=Q(target_stock__gte=Decimal("0")),
                name="inventory_target_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(initial_quantity__gte=Decimal("0")),
                name="inventory_initial_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(period_consumption__gte=Decimal("0")),
                name="inventory_consumption_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(period_consumption__lte=F("initial_quantity")),
                name="inventory_consumption_lte_initial",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def current_stock(self) -> Decimal:
        return self.initial_quantity - self.period_consumption

    def clean(self) -> None:
        super().clean()
        validate_inventory_snapshot(
            unit=self.unit,
            target_stock=self.target_stock,
            initial_quantity=self.initial_quantity,
            period_consumption=self.period_consumption,
            ran_out_before_month_end=self.ran_out_before_month_end,
        )

    def save(self, *args, **kwargs) -> None:
        # Django does not call full_clean() from save() by default. Doing it here
        # keeps normal ORM writes aligned with Admin and future API validation.
        self.full_clean()
        return super().save(*args, **kwargs)
