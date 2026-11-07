from rest_framework import serializers

from applibs.validators import is_phone_valid
from applibs.helpers import clean_phone_number


class CreateWalletSerializer(serializers.Serializer):
    user_id = serializers.CharField(min_length=3, max_length=55)
    phone = serializers.CharField(min_length=11, max_length=15)

    @staticmethod
    def _check_phone(value: str) -> str:
        if not is_phone_valid(value):
            raise serializers.ValidationError(code="invalid_phone")

        value = clean_phone_number(value)
        return value

    def validate(self, attrs: dict) -> dict:
        attrs["phone"] = self._check_phone(attrs["phone"])
        return attrs