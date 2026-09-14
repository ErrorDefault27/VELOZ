from datetime import datetime

from django.db.models.functions import Lower
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .formatters import format_decimal_plain, format_decimal_pt_br
from .models import IngredientPeriod
from .serializers import IngredientPeriodSerializer
from .services import calculate_replenishment


def ordered_ingredients():
    return IngredientPeriod.objects.order_by(Lower("name"), "name", "pk")


class IngredientPeriodViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientPeriodSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return ordered_ingredients()

    def get_object(self):
        try:
            ingredient = self.get_queryset().get(pk=self.kwargs["pk"])
        except (IngredientPeriod.DoesNotExist, TypeError, ValueError) as exc:
            raise NotFound("Ingrediente não encontrado.") from exc

        self.check_object_permissions(self.request, ingredient)
        return ingredient


class PurchaseListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        raw_reference_date = request.query_params.get("data_referencia")

        if raw_reference_date is None:
            reference_date = timezone.localdate()
        else:
            try:
                reference_date = datetime.strptime(
                    raw_reference_date, "%Y-%m-%d"
                ).date()
                if reference_date.isoformat() != raw_reference_date:
                    raise ValueError
            except (TypeError, ValueError):
                return Response(
                    {
                        "data_referencia": [
                            "Use uma data válida no formato YYYY-MM-DD."
                        ]
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        purchases = []
        for ingredient in ordered_ingredients():
            result = calculate_replenishment(
                ingredient,
                reference_date=reference_date,
            )
            if result.purchase_quantity <= 0:
                continue

            unit_label = ingredient.get_unit_display()
            quantity = format_decimal_plain(result.purchase_quantity)
            display_quantity = format_decimal_pt_br(result.purchase_quantity)
            purchases.append(
                {
                    "id": ingredient.pk,
                    "nome": ingredient.name,
                    "unidade": unit_label,
                    "quantidade": quantity,
                    "motivo": result.reason.value,
                    "texto": (
                        f"Comprar: {display_quantity} {unit_label} "
                        f"de {ingredient.name}"
                    ),
                }
            )

        return Response(
            {
                "data_referencia": reference_date.isoformat(),
                "compras": purchases,
            }
        )
