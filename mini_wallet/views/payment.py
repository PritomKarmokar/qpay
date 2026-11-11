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

class WithDrawlView(APIView):
    serializer_class = AddMoneySerializer

    def post(self, request: Request) -> Response:
        return success_response(data={"message": "success"})
