from django.db import models

class CurrencyType(models.TextChoices):
    USD = "USD", "USD"
    BDT = "BDT", "BDT"