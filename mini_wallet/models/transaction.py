from typing import Optional
from django.db import models

from applibs.logger import get_logger
from applibs.choices import TransactionType
from applibs.helpers import generate_ulid

from mini_wallet.models import UserWallet, WalletTransfer

logger = get_logger(__name__)

class Transaction(models.Model):
    id = models.CharField(
        max_length=26,
        primary_key=True,
        default=generate_ulid,
        editable=False,
    )
    wallet = models.ForeignKey(
        UserWallet, on_delete=models.PROTECT, related_name="transactions"
    )
    type = models.CharField(max_length=30, choices=TransactionType.choices)

    amount = models.PositiveBigIntegerField()
    balance_after = models.BigIntegerField()

    counterparty_wallet = models.ForeignKey(
        UserWallet,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="counterparty_transactions",
    )
    transfer = models.ForeignKey(
        WalletTransfer,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    gateway_ref = models.CharField(
        max_length=100, null=True, blank=True, unique=True
    )
    # Transfer ID for transfers, gateway_ref for add-money. Shown in history.
    reference_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = "transaction"
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return (
            f"ID: {self.id}"
        )
