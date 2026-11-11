from rest_framework import serializers

from applibs.choices import WithdrawalMethod

class P2PTransferSerializer(serializers.Serializer):
    amount = serializers.BigIntegerField(min_value=1, max_value=25000)
    from_wallet_id = serializers.CharField(required=True)
    to_wallet_id = serializers.CharField(required=True)
    note = serializers.CharField(required=True)

class WithdrawalSerializer(serializers.Serializer):
    wallet_id = serializers.CharField(required=True)
    amount = serializers.BigIntegerField(
        min_value=1,
        max_value=25000,
    )
    atm_terminal_id = serializers.CharField(
        required=True,
    )
    note = serializers.CharField(
        required=False,
        allow_blank=True,
    )