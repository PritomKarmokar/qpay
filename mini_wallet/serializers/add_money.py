from rest_framework import serializers

class AddMoneySerializer(serializers.Serializer):
    amount = serializers.BigIntegerField(required=True)
    gateway_ref = serializers.CharField(required=True)