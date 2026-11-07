from django.db.models import F
from django.db import transaction, IntegrityError

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from applibs.logger import get_logger
from applibs.choices import StatusType, TransactionType
from applibs.helpers import generate_request_hash
from applibs.decorator import measure_execution_time
from applibs.response import success_response, error_response

from mini_wallet.models import UserWallet, Transaction, IdempotencyRecord
from mini_wallet.serializers import (
    P2PTransferSerializer
)

logger = get_logger(__name__)

class P2PTransferView(APIView):
    serializer_class = P2PTransferSerializer

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

    def transfer_money(
            self,
            from_wallet_id: str,
            to_wallet_id: str,
            amount: int,
            request_hash: str,
            idempotency_key: str,
    ) -> tuple[tuple[Transaction, Transaction] | IdempotencyRecord | None, dict | None]:

        try:
            with transaction.atomic():

                # 1. Register or retrieve idempotency record
                record, created = IdempotencyRecord.objects.get_or_create(
                    operation="P2P_TRANSFER",
                    key=idempotency_key,
                    defaults={
                        "request_hash": request_hash,
                    },
                )

                # 2. Validate request fingerprint
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

                # 4. Validate sender and receiver
                if from_wallet_id == to_wallet_id:
                    response_body = {
                        "code": "INVALID_TRANSFER",
                        "message": "Cannot transfer money to the same wallet.",
                    }

                    response_status = status.HTTP_400_BAD_REQUEST

                    self.complete_idempotency(
                        record,
                        response_body,
                        response_status,
                    )

                    return None, {
                        **response_body,
                        "status_code": response_status,
                    }

                # 5. Lock both wallets in consistent order
                wallets = list(
                    UserWallet.objects.select_for_update()
                    .filter(
                        id__in=[from_wallet_id, to_wallet_id],
                        is_active=True,
                    )
                    .order_by("id")
                )

                wallet_map = {
                    str(wallet.id): wallet
                    for wallet in wallets
                }

                # 6. Validate sender wallet
                from_wallet = wallet_map.get(str(from_wallet_id))

                if not from_wallet:
                    response_body = {
                        "code": "SENDER_WALLET_NOT_FOUND",
                        "message": "Sender wallet does not exist.",
                    }

                    response_status = status.HTTP_404_NOT_FOUND

                    self.complete_idempotency(
                        record,
                        response_body,
                        response_status,
                    )

                    return None, {
                        **response_body,
                        "status_code": response_status,
                    }

                # 7. Validate receiver wallet
                to_wallet = wallet_map.get(str(to_wallet_id))

                if not to_wallet:
                    response_body = {
                        "code": "RECEIVER_WALLET_NOT_FOUND",
                        "message": "Receiver wallet does not exist.",
                    }

                    response_status = status.HTTP_404_NOT_FOUND

                    self.complete_idempotency(
                        record,
                        response_body,
                        response_status,
                    )

                    return None, {
                        **response_body,
                        "status_code": response_status,
                    }

                # 8. Check sender balance
                if from_wallet.balance < amount:
                    response_body = {
                        "code": "INSUFFICIENT_BALANCE",
                        "message": "Insufficient balance in the wallet.",
                    }

                    response_status = status.HTTP_400_BAD_REQUEST

                    self.complete_idempotency(
                        record,
                        response_body,
                        response_status,
                    )

                    return None, {
                        **response_body,
                        "status_code": response_status,
                    }

                # 9. Calculate updated balances
                sender_balance = from_wallet.balance - amount
                receiver_balance = to_wallet.balance + amount

                # 10. Debit sender
                from_wallet.balance = sender_balance
                from_wallet.save(update_fields=["balance"])

                # 11. Credit receiver
                to_wallet.balance = receiver_balance
                to_wallet.save(update_fields=["balance"])

                # 12. Create debit transaction
                debit_transaction = Transaction.objects.create(
                    wallet=from_wallet,
                    type=TransactionType.TRANSFER_OUT,
                    amount=amount,
                    balance_after=sender_balance,
                    counterparty_wallet=to_wallet,
                )

                # 13. Create credit transaction
                credit_transaction = Transaction.objects.create(
                    wallet=to_wallet,
                    type=TransactionType.TRANSFER_IN,
                    amount=amount,
                    balance_after=receiver_balance,
                    counterparty_wallet=from_wallet,
                )

                # 14. Prepare response
                response_body = {
                    "debit_transaction_id": str(debit_transaction.id),
                    "credit_transaction_id": str(credit_transaction.id),
                    "from_wallet_id": str(from_wallet.id),
                    "to_wallet_id": str(to_wallet.id),
                    "amount": amount,
                    "sender_balance_after": sender_balance,
                    "receiver_balance_after": receiver_balance,
                }

                response_status = status.HTTP_201_CREATED

                # 15. Complete idempotency record
                self.complete_idempotency(
                    record,
                    response_body,
                    response_status,
                )

                return (
                    debit_transaction,
                    credit_transaction,
                ), None

        except IntegrityError as e:
            logger.exception(
                "Integrity error while processing P2P transfer. error ", str(e),
                extra={
                    "from_wallet_id": from_wallet_id,
                    "to_wallet_id": to_wallet_id,
                },
            )

            return None, {
                "code": "TRANSFER_PROCESSING_FAILED",
                "message": "Unable to process transfer.",
                "status_code": status.HTTP_409_CONFLICT,
            }

        except Exception as e:
            logger.error(
                "Unexpected error while processing P2P transfer. error ", str(e),
                extra={
                    "from_wallet_id": from_wallet_id,
                    "to_wallet_id": to_wallet_id,
                },
            )

            return None, {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Unable to process transfer.",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }

    @measure_execution_time(step="p2p_transfer")
    def post(self, request: Request) -> Response:
        # 1. Validate idempotency key
        idempotency_key = (
            request.headers.get("Idempotency-Key") or ""
        ).strip()

        if not idempotency_key:
            return error_response(
                code="IDEMPOTENCY_KEY_REQUIRED",
                message="Idempotency-Key header is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Validate request payload
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return error_response(
                code="INVALID_DATA",
                message=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data

        from_wallet_id = validated_data["from_wallet_id"]
        to_wallet_id = validated_data["to_wallet_id"]
        amount = validated_data["amount"]

        # 3. Generate request fingerprint
        request_hash = generate_request_hash({
            "from_wallet_id": from_wallet_id,
            "to_wallet_id": to_wallet_id,
            "amount": amount,
        })

        # 4. Execute transfer
        result, error = self.transfer_money(
            from_wallet_id=from_wallet_id,
            to_wallet_id=to_wallet_id,
            amount=amount,
            request_hash=request_hash,
            idempotency_key=idempotency_key,
        )

        # 5. Handle errors
        if error:
            return error_response(
                code=error["code"],
                message=error["message"],
                status_code=error["status_code"],
            )

        # 6. Handle idempotency replay
        if isinstance(result, IdempotencyRecord):
            return Response(
                data=result.response_body,
                status=result.response_status,
            )

        # 7. Return successful transfer
        debit_transaction, credit_transaction = result

        return Response(
            data={
                "transfer_id": str(credit_transaction.id),
                "from_wallet_id": str(debit_transaction.wallet_id),
                "to_wallet_id": str(credit_transaction.wallet_id),
                "amount": amount,
                "status": "COMPLETED",
                "created_at": debit_transaction.created_at,
            },
            status=status.HTTP_201_CREATED,
        )
