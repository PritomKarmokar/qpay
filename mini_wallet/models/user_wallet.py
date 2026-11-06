from django.db import models
from django.utils import timezone

from applibs.logger import get_logger
from applibs.choices import CurrencyType
from applibs.helpers import generate_ulid

logger = get_logger(__name__)

class UserWallet(models.Model):
    id = models.CharField(max_length=26, primary_key=True, default=generate_ulid, editable=False)
    user_id = models.CharField(max_length=55)
    phone = models.CharField(max_length=15, unique=True)
    currency = models.CharField(max_length=10, choices=CurrencyType.choices, default=CurrencyType.BDT)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "User Wallet"
        verbose_name_plural = "User Wallets"
        indexes = [
            models.Index(fields=["user_id"]),
        ]
        db_table = "user_wallet"

    def __str__(self):
        return f"Wallet ID: {self.id} | User ID: {self.user_id} | Status: {self.is_active}"
