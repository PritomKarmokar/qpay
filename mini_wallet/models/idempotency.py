from typing import Optional
from django.db import models

from applibs.logger import get_logger
from applibs.choices import OperationType
from applibs.helpers import generate_ulid

logger = get_logger(__name__)

class IdempotencyRecord(models.Model):

    id = models.CharField(
        max_length=26,
        primary_key=True,
        default=generate_ulid,
        editable=False,
    )
    key = models.CharField(max_length=255)
    operation = models.CharField(max_length=50, choices=OperationType.choices)

    # sha256 hex of: operation + path params + canonical JSON body
    request_hash = models.CharField(max_length=64)
    response_status = models.PositiveSmallIntegerField()
    response_body = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "idempotency_record"
        verbose_name = "Idempotency Record"
        verbose_name_plural = "Idempotency Records"

    def __str__(self):
        return (
            f"ID: {self.id}"
        )