from typing import Optional
from django.db import models
from django.utils import timezone

from applibs.logger import get_logger
from applibs.choices import CurrencyType
from applibs.helpers import generate_ulid

logger = get_logger(__name__)

class UserWalletManager(models.Manager):

    def create_wallet(
            self,
            user_id: str,
            phone: str,
    ) -> Optional["UserWallet"]:
        try:
            return self.create(user_id=user_id, phone=phone)
        except Exception as e:
            logger.error({
                "step": "crete_wallet",
                "message": "Failed to new create Wallet",
                "error": repr(e)
            })
            return None

    def fetch_active_wallet(self, phone: str) -> Optional["UserWallet"]:
        try:
            return self.get(phone=phone, is_active=True)
        except Exception as e:
            logger.error({
                "step": "fetch_active_wallet",
                "message": "Failed to fetch active Wallet",
                "error": repr(e)
            })
            return None

    def get_active_wallet_by_phone(
            self,
            phone: str,
    ) -> Optional["UserWallet"]:
        return self.filter(
            phone=phone,
            is_active=True,
            deleted_at__isnull=True,
        ).first()

    def fetch_active_wallet_on_wallet_id(
            self,
            wallet_id: str
    ) -> Optional["UserWallet"]:
        return self.filter(
            id=wallet_id,
            is_active=True,
            deleted_at__isnull=True,
        ).first()

class UserWallet(models.Model):
    id = models.CharField(
        max_length=26,
        primary_key=True,
        default=generate_ulid,
        editable=False,
    )

    user_id = models.CharField(max_length=55)
    phone = models.CharField(max_length=15, unique=True)

    currency = models.CharField(
        max_length=10,
        choices=CurrencyType.choices,
        default=CurrencyType.BDT,
    )

    balance = models.BigIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UserWalletManager()

    class Meta:
        db_table = "user_wallet"
        verbose_name = "User Wallet"
        verbose_name_plural = "User Wallets"

        indexes = [
            models.Index(fields=["user_id"]),
        ]

    def __str__(self):
        return (
            f"Wallet ID: {self.id} | "
            f"User ID: {self.user_id} | "
            f"Status: {self.is_active}"
        )
