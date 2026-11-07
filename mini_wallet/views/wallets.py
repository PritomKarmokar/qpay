from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from applibs.logger import get_logger
from applibs.decorator import measure_execution_time
from applibs.response import success_response, error_response

from mini_wallet.models import UserWallet
from mini_wallet.serializers import CreateWalletSerializer

logger = get_logger(__name__)

class CreateWalletView(APIView):
    serializer_class = CreateWalletSerializer

    @measure_execution_time(step="create_wallet")
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            logger.error({"message": "Invalid serializer data", "errors": serializer.errors})
            return error_response(
                code="INVALID_DATA",
                message=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        validated_data = dict(serializer.validated_data)

        existing_wallet = UserWallet.objects.get_active_wallet_by_phone(
            phone=validated_data.get("phone")
        )
        if existing_wallet:
            logger.error({"message": "Wallet already exists"})
            return error_response(
                code="DUPLICATE_WALLET",
                message="Wallet already exists with this phone number.",
                status_code=status.HTTP_409_CONFLICT
            )

        new_wallet = UserWallet.objects.create_wallet(
            user_id=validated_data.get("user_id"),
            phone=validated_data.get("phone"),
        )
        if new_wallet is None:
            logger.error({"message": "Failed to create new wallet"})
            return error_response(
                code="INTERNAL_SERVER_ERROR",
                message="Due to technical issues, we are unable to create new wallet. Please try again later.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response_data = {
            "wallet_id": new_wallet.id,
            "user_id": new_wallet.user_id,
            "currency": new_wallet.currency,
            "balance": new_wallet.balance,
            "created_at": new_wallet.created_at,
        }
        return success_response(
            data=response_data,
            status_code=status.HTTP_201_CREATED
        )

class RetrieveWalletView(APIView):

    @measure_execution_time(step="retrieve_wallet")
    def get(self, request: Request, wallet_id: str) -> Response:
        wallet = UserWallet.objects.fetch_active_wallet_on_wallet_id(
            wallet_id=wallet_id
        )
        if not wallet:
            logger.error({"message": "Wallet doesn't exists"})
            return error_response(
                code="WALLET_NOT_FOUND",
                message="Wallet does not exists with this wallet id.",
                status_code=status.HTTP_409_CONFLICT,
            )

        response_data = {
            "wallet_id": wallet.id,
            "phone": wallet.phone,
            "currency": wallet.currency,
            "balance": wallet.balance,
        }
        return success_response(
            data=response_data,
            status_code=status.HTTP_200_OK
        )
