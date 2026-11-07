from django.db.models import F
from django.db import transaction, IntegrityError

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from applibs.logger import get_logger
from applibs.choices import StatusType
from applibs.helpers import generate_request_hash
from applibs.decorator import measure_execution_time
from applibs.response import success_response, error_response

from mini_wallet.models import UserWallet, Transaction, IdempotencyRecord
from mini_wallet.serializers import (
    AddMoneySerializer
)

logger = get_logger(__name__)

class AddMoneyView(APIView):
    serializer_class = AddMoneySerializer

    @staticmethod
    def complete_idempotency(
            record: IdempotencyRecord,
            response_body: dict,
            response_status: int,
    ) -> None:
        record.status = StatusType.COMPLETED
        record.response_body = response_body
        record.response_status = response_status

        record.save(update_fields=[
            "status",
            "response_body",
            "response_status",
            "updated_at",
        ])

    def add_money(
            self,
            wallet: UserWallet,
            amount: int,
            gateway_ref: str,
            request_hash: str,
            idempotency_key: str,
    ) -> tuple[Transaction |IdempotencyRecord | None, dict | None]:

        try:
            with transaction.atomic():
                # 1. Register or retrieve idempotency record
                record, created = IdempotencyRecord.objects.get_or_create(
                    operation="ADD_MONEY",
                    key=idempotency_key,
                    defaults={"request_hash": request_hash},
                )
                # 2. Check request fingerprint
                if record.request_hash != request_hash:
                    return None, {
                        "code": "IDEMPOTENCY_KEY_REUSED",
                        "message": "Idempotency key already used with different request.",
                        "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    }

                # 3. Handle existing idempotency record
                if not created:
                    if record.status == StatusType.COMPLETED:
                        return record, None

                    return None, {
                        "code": "REQUEST_IN_PROGRESS",
                        "message": "Request is already being processed.",
                        "status_code": status.HTTP_409_CONFLICT,
                    }

                # 4. Lock wallet
                wallet = UserWallet.objects.select_for_update().get(
                    id=wallet.id,
                    is_active=True,
                )

                # 5. Check gateway reference
                if Transaction.objects.filter(
                        gateway_ref=gateway_ref,
                ).exists():
                    response_body = {
                        "code": "DUPLICATE_GATEWAY_REF",
                        "message": "Duplicate gateway reference.",
                    }
                    response_status = status.HTTP_409_CONFLICT

                    self.complete_idempotency(record, response_body, response_status)

                    return None, {
                        **response_body,
                        "status_code": response_status,
                    }

                # 6. Update wallet balance
                new_balance = wallet.balance + amount

                wallet.balance = new_balance
                wallet.save(update_fields=["balance"])

                # 7. Create transaction
                wallet_transaction = Transaction.objects.create(
                    wallet=wallet,
                    type="ADD_MONEY",
                    amount=amount,
                    balance_after=new_balance,
                    gateway_ref=gateway_ref,
                )

                # 8. Store successful response
                response_body = {
                    "transaction_id": str(wallet_transaction.id),
                    "balance_after": wallet_transaction.balance_after,
                    "gateway_ref": wallet_transaction.gateway_ref,
                }

                self.complete_idempotency(record, response_body, status.HTTP_201_CREATED)

                return wallet_transaction, None

        except IntegrityError as e:
            logger.error(
                "Integrity error while processing add money. error ", str(e),
                extra={"gateway_ref": gateway_ref},
            )

            return None, {
                "code": "PAYMENT_PROCESSING_FAILED",
                "message": "Unable to process payment.",
                "status_code": status.HTTP_409_CONFLICT,
            }

        except Exception as e:
            logger.error(
                "Unexpected error while processing add money. error ", str(e),
                extra={"gateway_ref": gateway_ref},
            )

            return None, {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Unable to process payment.",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }

    @measure_execution_time(step="add_money")
    def post(self, request: Request, wallet_id: str) -> Response:
        idempotency_key = (request.headers.get("Idempotency-Key") or "").strip()
        if not idempotency_key:
            return error_response(
                code="IDEMPOTENCY_KEY_REQUIRED",
                message="Idempotency-Key header is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return error_response(
                code="INVALID_DATA", message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
            )

        validated_data = dict(serializer.validated_data)

        wallet = UserWallet.objects.fetch_active_wallet_on_wallet_id(
            wallet_id=wallet_id,
        )

        if not wallet:
            return error_response(
                code="WALLET_NOT_FOUND", message="Wallet does not exist.", status_code=status.HTTP_404_NOT_FOUND
            )

        request_hash = generate_request_hash({
            "wallet_id": str(wallet_id),
            "amount": validated_data["amount"],
            "gateway_ref": validated_data["gateway_ref"],
        })

        result, error = self.add_money(
            wallet=wallet,
            amount=validated_data["amount"],
            gateway_ref=validated_data["gateway_ref"],
            request_hash=request_hash,
            idempotency_key=idempotency_key,
        )

        if error:
            return error_response(
                code=error["code"],
                message=error["message"],
                status_code=error["status_code"],
            )

        if isinstance(result, IdempotencyRecord):
            return Response(
                data=result.response_body,
                status=result.response_status,
            )

        return Response(
            data={
                "transaction_id": str(result.id),
                "balance_after": result.balance_after,
                "gateway_ref": result.gateway_ref,
            },
            status=status.HTTP_201_CREATED,
        )