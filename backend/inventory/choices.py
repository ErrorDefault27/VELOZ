from django.db import models


class Unit(models.TextChoices):
    KILOGRAM = "kg", "Kg"
    LITER = "l", "L"
    ITEM = "un", "un"

