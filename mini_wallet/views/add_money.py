from django.db.models import F
from django.db import transaction, IntegrityError

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from applibs.logger import get_logger
from applibs.decorator import measure_execution_time
from applibs.response import success_response, error_response

from mini_wallet.models import UserWallet, Transaction
from mini_wallet.serializers import (
    AddMoneySerializer
)

logger = get_logger(__name__)

class AddMoneyView(APIView):
    serializer_class = AddMoneySerializer

    @staticmethod
    def add_money(
            wallet: UserWallet,
            amount: int,
            gateway_ref: str,
    ) -> Transaction | None:

        try:
            with transaction.atomic():

                # Check duplicate gateway reference.
                if Transaction.objects.filter(
                        gateway_ref=gateway_ref,
                ).exists():
                    return None

                # Fetch the latest wallet state with a row lock.
                wallet = UserWallet.objects.select_for_update().get(
                    id=wallet.id,
                    is_active=True,
                )

                # Calculate new balance.
                new_balance = wallet.balance + amount

                # Update wallet balance.
                wallet.balance = new_balance
                wallet.save(update_fields=["balance"])

                # Create transaction record.
                return Transaction.objects.create(
                    wallet=wallet,
                    type="ADD_MONEY",
                    amount=amount,
                    balance_after=new_balance,
                    gateway_ref=gateway_ref,
                )

        except IntegrityError:
            logger.error({"message": "Payment already processed."})
            return None

    @measure_execution_time(step="add_money")
    def post(self, request: Request, wallet_id: str) -> Response:
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = dict(serializer.validated_data)

        wallet = UserWallet.objects.fetch_active_wallet_on_wallet_id(
            wallet_id=wallet_id,
        )

        if not wallet:
            return error_response(
                code="WALLET_NOT_FOUND", message="Wallet does not exist.", status_code=status.HTTP_404_NOT_FOUND
            )

        wallet_transaction = self.add_money(
            wallet=wallet,
            amount=validated_data["amount"],
            gateway_ref=validated_data["gateway_ref"],
        )
        if wallet_transaction is None:
            return error_response(
                code="DUPLICATE_PAYMENT", message="Payment already processed.", status_code=status.HTTP_409_CONFLICT
            )

        response_payload = {
            "transaction_id": wallet_transaction.id,
            "balance_after": wallet_transaction.balance_after,
            "gateway_ref": wallet_transaction.gateway_ref,
        }
        return Response(
            data=response_payload,
            status=status.HTTP_201_CREATED,
        )