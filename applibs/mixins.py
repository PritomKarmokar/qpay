from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from applibs.response import  error_response

class IdempotencyMixin:
    @staticmethod
    def get_idempotency_key(request: Request) -> tuple[None, Response] | tuple[str, None]:
        idempotency_key = (request.headers.get("Idempotency-Key") or "").strip()

        if not idempotency_key:
            return None, error_response(
                code="IDEMPOTENCY_KEY_REQUIRED",
                message="Idempotency-Key header is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return idempotency_key, None