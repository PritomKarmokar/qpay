from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from applibs.logger import get_logger
from applibs.decorator import measure_execution_time
from applibs.choices import StatusType, TransactionType
from applibs.response import success_response, error_response

from mini_wallet.models import UserWallet, Transaction
from mini_wallet.serializers import (
    WalletHistorySerializer
)

logger = get_logger(__name__)

class WalletTransactionHistoryView(APIView):
    serializer_class = WalletHistorySerializer

    @staticmethod
    def create_transaction_payload(transaction: Transaction) -> dict:
        counterparty = transaction.counterparty_wallet

        return {
            "transaction_id": transaction.id,
            "type": transaction.type,
            "amount": transaction.amount,
            "balance_after": transaction.balance_after,
            "counterparty": {
                "wallet_id": counterparty.id,
                "phone": counterparty.phone,
            } if counterparty else None,
            "reference_id": transaction.reference_id,
            "created_at": transaction.created_at,
        }

    @staticmethod
    def create_success_response_payload(
        transactions: list,
        count: int,
        page: int,
        page_size: int,
    ) -> dict:
        return {
            "count": count,
            "page": page,
            "page_size": page_size,
            "total_pages": (count + page_size - 1) // page_size,
            "results": [
                WalletTransactionHistoryView.create_transaction_payload(transaction)
                for transaction in transactions
            ],
        }

    @measure_execution_time(step="transaction_history")
    def get(self, request: Request, wallet_id: str) -> Response:
        # 1. Validate wallet
        existing_wallet = UserWallet.objects.fetch_active_wallet_on_wallet_id(
            wallet_id=wallet_id,
        )

        if not existing_wallet:
            logger.error({
                "step": "wallet_transaction_history",
                "message": "Wallet doesn't exist",
                "wallet_id": wallet_id,
            })

            return Response(
                data={
                    "error": {
                        "code": "WALLET_NOT_FOUND",
                        "message": "Wallet does not exist with this wallet id.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2. Read query parameters
        params = request.query_params
        serializer = self.serializer_class(data=params)
        if not serializer.is_valid():
            return error_response(
                code="INVALID_DATA",
                message=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        transaction_type = params.get("type")
        from_date = params.get("from")
        to_date = params.get("to")

        page = params.get("page", 1)
        page_size = params.get("page_size", 20)

        # 3. Validate pagination
        try:
            page = int(page)
            page_size = int(page_size)

            if page < 1 or page_size < 1 or page_size > 100:
                raise ValueError

        except (TypeError, ValueError):
            return Response(
                data={
                    "error": {
                        "code": "INVALID_PAGINATION",
                        "message": "Page must be positive and page_size must be between 1 and 100.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Build queryset
        queryset = Transaction.objects.filter(
            wallet=existing_wallet,
        ).select_related(
            "counterparty_wallet",
        )

        # 5. Apply transaction type filter
        if transaction_type:
            valid_types = TransactionType.values

            if transaction_type not in valid_types:
                return Response(
                    data={
                        "error": {
                            "code": "INVALID_TRANSACTION_TYPE",
                            "message": "Invalid transaction type.",
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            queryset = queryset.filter(
                type=transaction_type,
            )

        # 6. Apply date filters
        if from_date:
            queryset = queryset.filter(
                created_at__gte=from_date,
            )

        if to_date:
            queryset = queryset.filter(
                created_at__lte=to_date,
            )

        # 7. Sort newest first
        queryset = queryset.order_by(
            "-created_at",
            "-id",
        )

        # 8. Pagination
        total_count = queryset.count()

        total_pages = (total_count + page_size - 1) // page_size

        if page > max(total_pages, 1):
            return Response(
                data={
                    "error": {
                        "code": "INVALID_PAGE",
                        "message": "Requested page does not exist.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        offset = (page - 1) * page_size

        transactions = queryset[offset:offset + page_size]

        # 9. Build response
        response_payload = self.create_success_response_payload(
            transactions=transactions,
            count=total_count,
            page=page,
            page_size=page_size,
        )

        return Response(
            data=response_payload,
            status=status.HTTP_200_OK,
        )