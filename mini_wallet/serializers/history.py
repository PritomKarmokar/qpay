from rest_framework import serializers

from applibs.choices import TransactionType

class WalletHistorySerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=TransactionType.choices,
        required=False,
    )
    from_date = serializers.DateTimeField(required=False)
    to_date = serializers.DateTimeField(required=False)

    def validate(self, attrs: dict) -> dict:
        from_date = attrs.get("from_date")
        to_date = attrs.get("to_date")

        if from_date and to_date and from_date > to_date:
            raise serializers.ValidationError({
                "to": "End date must be greater than or equal to start date."
            })

        return attrs