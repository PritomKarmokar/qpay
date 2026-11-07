from django.db import transaction, IntegrityError

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from applibs.logger import get_logger
from applibs.choices import StatusType, TransactionType
from applibs.mixins import IdempotencyMixin
from applibs.helpers import generate_request_hash
from applibs.decorator import measure_execution_time
from applibs.response import success_response, error_response

from mini_wallet.models import UserWallet, Transaction, IdempotencyRecord
from mini_wallet.serializers import (
    AddMoneySerializer
)

logger = get_logger(__name__)

class AddMoneyView(IdempotencyMixin, APIView):
    serializer_class = AddMoneySerializer

    @staticmethod
    def _error(code: str, message: str, status_code: int) -> tuple[dict, int]:
        return {"code": code, "message": message}, status_code

    @staticmethod
    def complete_idempotency(record, response_body, response_status) -> None:
        record.status = StatusType.COMPLETED
        record.response_body = response_body
        record.response_status = response_status
        record.save(update_fields=["status", "response_body", "response_status", "updated_at"])

    def _begin_idempotency(self, key, request_hash):
        """
        Returns (record, early_result).
        early_result is (body, status) if we should stop here, else None.
        """
        record, created = IdempotencyRecord.objects.get_or_create(
            operation=TransactionType.ADD_MONEY,
            key=key,
            defaults={"request_hash": request_hash},
        )

        if not created:
            if record.request_hash != request_hash:
                return record, self._error(
                    "IDEMPOTENCY_KEY_REUSED",
                    "Idempotency key already used with different request.",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            if record.status == StatusType.COMPLETED:
                return record, (record.response_body, record.response_status)

            return record, self._error(
                "REQUEST_IN_PROGRESS",
                "Request is already being processed.",
                status.HTTP_409_CONFLICT,
            )

        return record, None


    def _apply_add_money(self, wallet_id, amount, gateway_ref) -> tuple[dict, int]:
        wallet = UserWallet.objects.select_for_update().get(id=wallet_id, is_active=True)

        if Transaction.objects.filter(gateway_ref=gateway_ref).exists():
            return self._error(
                "DUPLICATE_GATEWAY_REF",
                "Duplicate gateway reference.",
                status.HTTP_409_CONFLICT,
            )

        wallet.balance += amount
        wallet.save(update_fields=["balance"])

        txn = Transaction.objects.create(
            wallet=wallet,
            type=TransactionType.ADD_MONEY,
            amount=amount,
            balance_after=wallet.balance,
            gateway_ref=gateway_ref,
        )

        return {
            "transaction_id": str(txn.id),
            "balance_after": txn.balance_after,
            "gateway_ref": txn.gateway_ref,
        }, status.HTTP_201_CREATED


    def add_money(self, wallet_id, amount, gateway_ref, request_hash, idempotency_key):
        try:
            with transaction.atomic():
                record, early = self._begin_idempotency(idempotency_key, request_hash)
                if early:
                    return early

                body, code = self._apply_add_money(wallet_id, amount, gateway_ref)
                self.complete_idempotency(record, body, code)
                return body, code

        except UserWallet.DoesNotExist:
            return self._error(
                "WALLET_NOT_FOUND",
                "Wallet does not exist.",
                status.HTTP_404_NOT_FOUND
            )

        except IntegrityError as e:
            logger.error("Integrity error in add money err: ", str(e), extra={"gateway_ref": gateway_ref})
            return self._error(
                "PAYMENT_PROCESSING_FAILED",
                "Unable to process payment.",
                status.HTTP_409_CONFLICT
            )

        except Exception as e:
            logger.error("Unexpected error in add money. err: ", str(e), extra={"gateway_ref": gateway_ref})
            return self._error(
                "INTERNAL_SERVER_ERROR",
                "Unable to process payment.",
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @measure_execution_time(step="add_money")
    def post(self, request: Request, wallet_id: str) -> Response:
        idempotency_key, error = self.get_idempotency_key(request)
        if error:
            return error

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="INVALID_DATA",
                message=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        data = serializer.validated_data

        request_hash = generate_request_hash({
            "wallet_id": str(wallet_id),
            "amount": data["amount"],
            "gateway_ref": data["gateway_ref"],
        })

        body, code = self.add_money(
            wallet_id=wallet_id,
            amount=data["amount"],
            gateway_ref=data["gateway_ref"],
            request_hash=request_hash,
            idempotency_key=idempotency_key,
        )

        if code >= 400:
            return error_response(
                code=body["code"],
                message=body["message"],
                status_code=code
            )

        return success_response(data=body, status_code=code)
