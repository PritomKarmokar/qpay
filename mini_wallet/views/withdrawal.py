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

from mini_wallet.models import UserWallet, Transaction, IdempotencyRecord, ATM
from mini_wallet.serializers import (
    WithdrawalSerializer
)

logger = get_logger(__name__)

class WithDrawlView(APIView):
    serializer_class = WithdrawalSerializer

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="INVALID_DATA",
                message=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        data = serializer.validated_data
        try:
            with transaction.atomic():
                wallet = UserWallet.objects.select_for_update().get(id=data.get("wallet_id"), is_active=True)
                if wallet.balance < data.get("amount"):
                    return error_response(
                        "INSUFFICIENT_BALANCE",
                        "Insufficient balance.",
                        status.HTTP_400_BAD_REQUEST
                    )

                try:
                    atm = ATM.objects.get(terminal_id=data.get("terminal_id"), is_active=True)
                except ATM.DoesNotExist:
                    return error_response(
                        "INVALID_ATM",
                        "INVALID_ATM.",
                        status.HTTP_404_NOT_FOUND
                    )

                if atm.total_available_cash <= data.get("amount"):
                    return error_response(
                        "ATM_NOT_AVAILABLE",
                        "ATM_NOT_AVAILABLE",
                        status.HTTP_400_BAD_REQUEST
                    )

                atm.total_available_cash -= data.get("amount")
                wallet.balance -= data.get("amount")

                atm.save(update_fields=["total_available_cash"])
                wallet.save(update_fields=["balance"])

                txn = Transaction.objects.create(
                    wallet=wallet,
                    type=TransactionType.WITHDRAWAL,
                    amount=data.get("amount"),
                    balance_after=wallet.balance,
                    counterparty_wallet=atm,
                )

                data = {
                    "message": "success",
                    "txn_id": txn.id,
                }
                return success_response(data=data)

        except UserWallet.DoesNotExist:
            return error_response(
                "WALLET_NOT_FOUND",
                "Wallet does not exist.",
                status.HTTP_404_NOT_FOUND
            )