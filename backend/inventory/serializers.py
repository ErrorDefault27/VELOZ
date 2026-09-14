from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .choices import Unit
from .models import IngredientPeriod
from .validators import (
    MAX_QUANTITY,
    QUANTITY_DECIMAL_PLACES,
    QUANTITY_MAX_DIGITS,
    validate_inventory_snapshot,
)

MODEL_TO_API_FIELDS = {
    "unit": "unidade",
    "target_stock": "meta_estoque",
    "initial_quantity": "quantidade_inicial",
    "period_consumption": "consumo_periodo",
    "ran_out_before_month_end": "acabou_antes_fim_mes",
}

QUANTITY_ERROR_MESSAGES = {
    "required": "Este campo é obrigatório.",
    "invalid": "Informe uma quantidade decimal válida.",
    "max_value": f"A quantidade não pode ser maior que {MAX_QUANTITY}.",
    "min_value": "A quantidade não pode ser negativa.",
    "max_digits": f"Use no máximo {QUANTITY_MAX_DIGITS} dígitos no total.",
    "max_decimal_places": (
        f"Use no máximo {QUANTITY_DECIMAL_PLACES} casas decimais."
    ),
    "max_whole_digits": "A parte inteira da quantidade é muito grande.",
}


def quantity_field(*, source: str, read_only: bool = False):
    return serializers.DecimalField(
        source=source,
        max_digits=QUANTITY_MAX_DIGITS,
        decimal_places=QUANTITY_DECIMAL_PLACES,
        min_value=Decimal("0"),
        max_value=MAX_QUANTITY,
        coerce_to_string=True,
        read_only=read_only,
        error_messages=QUANTITY_ERROR_MESSAGES,
    )


class IngredientPeriodSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(
        source="name",
        max_length=120,
        error_messages={
            "required": "Este campo é obrigatório.",
            "blank": "O nome do ingrediente não pode ficar em branco.",
            "max_length": "O nome do ingrediente pode ter no máximo 120 caracteres.",
        },
    )
    unidade = serializers.ChoiceField(
        source="unit",
        choices=Unit.choices,
        error_messages={
            "required": "Este campo é obrigatório.",
            "invalid_choice": "Unidade inválida. Use kg, l ou un.",
        },
    )
    meta_estoque = quantity_field(source="target_stock")
    quantidade_inicial = quantity_field(source="initial_quantity")
    consumo_periodo = quantity_field(source="period_consumption")
    data_validade = serializers.DateField(
        source="expiration_date",
        error_messages={
            "required": "Este campo é obrigatório.",
            "invalid": "Use uma data válida no formato YYYY-MM-DD.",
        },
    )
    acabou_antes_fim_mes = serializers.BooleanField(
        source="ran_out_before_month_end",
        required=False,
        error_messages={"invalid": "Informe verdadeiro ou falso."},
    )
    estoque_atual = quantity_field(source="current_stock", read_only=True)

    class Meta:
        model = IngredientPeriod
        fields = (
            "id",
            "nome",
            "unidade",
            "meta_estoque",
            "quantidade_inicial",
            "consumo_periodo",
            "estoque_atual",
            "data_validade",
            "acabou_antes_fim_mes",
        )
        read_only_fields = ("id", "estoque_atual")

    def validate(self, attrs):
        instance = self.instance

        def combined_value(field_name: str, default=None):
            if field_name in attrs:
                return attrs[field_name]
            if instance is not None:
                return getattr(instance, field_name)
            return default

        try:
            validate_inventory_snapshot(
                unit=combined_value("unit"),
                target_stock=combined_value("target_stock"),
                initial_quantity=combined_value("initial_quantity"),
                period_consumption=combined_value("period_consumption"),
                ran_out_before_month_end=combined_value(
                    "ran_out_before_month_end", False
                ),
            )
        except DjangoValidationError as exc:
            api_errors = {
                MODEL_TO_API_FIELDS.get(field_name, field_name): messages
                for field_name, messages in exc.message_dict.items()
            }
            raise serializers.ValidationError(api_errors) from exc

        return attrs

