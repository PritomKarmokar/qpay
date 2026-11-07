from rest_framework import serializers

class P2PTransferSerializer(serializers.Serializer):
    amount = serializers.BigIntegerField(min_value=1, max_value=25000)
    from_wallet_id = serializers.CharField(required=True)
    to_wallet_id = serializers.CharField(required=True)
    note = serializers.CharField(required=True)