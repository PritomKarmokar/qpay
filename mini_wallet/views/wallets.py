from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from applibs.logger import get_logger
from applibs.decorator import measure_execution_time

from mini_wallet.models import UserWallet
from mini_wallet.serializers import (
    CreateWalletSerializer,
    RetrieveWalletSerializer
)

logger = get_logger(__name__)

class CreateWalletView(APIView):
    serializer_class = CreateWalletSerializer

    def __init__(self):
        super().__init__()
        self.lang = "en"

    @staticmethod
    def create_success_response_payload(wallet: UserWallet) -> dict:
        return {
            "wallet_id": wallet.id,
            "user_id": wallet.user_id,
            "currency": wallet.currency,
            "balance": wallet.balance,
            "created_at": wallet.created_at,
        }

    @measure_execution_time(step="Create Wallet")
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.error({
                "Invalid serializer data Provided. Errors : {}".format(serializer.errors)
            })
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = dict(serializer.validated_data)

        existing_wallet = UserWallet.objects.get_active_wallet_by_phone(phone=validated_data.get("phone"))
        if existing_wallet:
            logger.error({"message": "Wallet already exists"})
            return Response(data={
                "error": {
                    "code": "DUPLICATE_WALLET",
                    "message": "Wallet already exists with this phone number."
                }
            }, status=status.HTTP_409_CONFLICT)

        new_wallet = UserWallet.objects.create_wallet(
            user_id=validated_data.get("user_id"),
            phone=validated_data.get("phone"),
        )
        if new_wallet is None:
            logger.error({
                "Failed to create new wallet"
            })
            return Response(data= {
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Due to internal server error, we are unable to create new wallet."
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_payload = self.create_success_response_payload(new_wallet)
        return Response(
            data=response_payload,
            status=status.HTTP_201_CREATED
        )

class RetrieveWalletView(APIView):
    @staticmethod
    def create_success_response_payload(wallet: UserWallet) -> dict:
        return {
            "wallet_id": wallet.id,
            "phone": wallet.phone,
            "currency": wallet.currency,
            "balance": wallet.balance, # todo: need to send balance omitting decimal field
        }

    @measure_execution_time(step="Retrieve Wallet")
    def get(self, request: Request, wallet_id: str) -> Response:
        existing_wallet = UserWallet.objects.fetch_active_wallet_on_wallet_id(wallet_id=wallet_id)
        if not existing_wallet:
            logger.error({"message": "Wallet doesn't exists"})
            return Response(data={
                "error": {
                    "code": "WALLET_NOT_FOUND",
                    "message": "Wallet does not exists with this wallet id."
                }
            }, status=status.HTTP_409_CONFLICT)

        response_payload = self.create_success_response_payload(existing_wallet)

        return Response(
            data=response_payload,
            status=status.HTTP_200_OK,
        )