from django.db import models

from applibs.logger import get_logger
from applibs.helpers import generate_ulid
from applibs.choices import OperationType, StatusType

logger = get_logger(__name__)

class ATM(models.Model):
    id = models.CharField(
        max_length=26,
        primary_key=True,
        default=generate_ulid,
        editable=False,
    )
    terminal_id = models.CharField(
        max_length=50,
        unique=True,
    )
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)

    transaction_ref = models.JSONField(null=True, blank=True)

    total_available_cash = models.BigIntegerField(default=50000)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)