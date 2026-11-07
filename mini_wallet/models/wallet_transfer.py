from django.db import models
from django.db.models import F, Q

from applibs.logger import get_logger
from applibs.choices import StatusType
from applibs.helpers import generate_ulid

from mini_wallet.models import UserWallet

logger = get_logger(__name__)


class WalletTransfer(models.Model):
    id = models.CharField(
        max_length=26,
        primary_key=True,
        default=generate_ulid,
        editable=False,
    )
    from_wallet = models.ForeignKey(
        UserWallet, on_delete=models.PROTECT, related_name="transfers_out"
    )
    to_wallet = models.ForeignKey(
        UserWallet, on_delete=models.PROTECT, related_name="transfers_in"
    )
    amount = models.PositiveBigIntegerField()
    note = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=StatusType.choices,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Wallet Transfer"
        verbose_name_plural = "Wallet Transfers"
        db_table = "wallet_transfer"

        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="transfer_amount_positive"
            ),
            models.CheckConstraint(
                condition=~Q(from_wallet=F("to_wallet")),
                name="transfer_sender_receiver_differ",
            ),
        ]
        indexes = [
            models.Index(fields=["from_wallet", "-created_at"], name="transfer_from_idx"),
            models.Index(fields=["to_wallet", "-created_at"], name="transfer_to_idx"),
        ]

    def __str__(self) -> str:
        return (
            f"Amount: {self.amount} | "
            f"from_wallet: {self.from_wallet} | "
            f"to_wallet: {self.to_wallet}"
        )

