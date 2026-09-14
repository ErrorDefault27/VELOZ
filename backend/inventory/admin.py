from django.contrib import admin

from .models import IngredientPeriod


@admin.register(IngredientPeriod)
class IngredientPeriodAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "unit",
        "target_stock",
        "initial_quantity",
        "period_consumption",
        "current_stock_display",
        "expiration_date",
        "ran_out_before_month_end",
    )
    list_filter = ("unit", "ran_out_before_month_end", "expiration_date")
    search_fields = ("name",)
    readonly_fields = ("current_stock_display",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "unit",
                    "target_stock",
                    "initial_quantity",
                    "period_consumption",
                    "current_stock_display",
                    "expiration_date",
                    "ran_out_before_month_end",
                )
            },
        ),
    )

    @admin.display(description="estoque atual")
    def current_stock_display(self, obj: IngredientPeriod | None):
        return obj.current_stock if obj and obj.pk else "—"

