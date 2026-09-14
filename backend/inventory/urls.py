from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import IngredientPeriodViewSet, PurchaseListView

router = SimpleRouter()
router.register("ingredientes", IngredientPeriodViewSet, basename="ingredient")

urlpatterns = [
    *router.urls,
    path("compras/", PurchaseListView.as_view(), name="purchase-list"),
]
