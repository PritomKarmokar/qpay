from django.contrib import admin

from mini_wallet.models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    show_full_result_count = False
    list_per_page = 25
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    list_display = (
        "id",
        "wallet_id",
        "type",
        "amount",
        "balance_after",
        "reference_id",
        "created_at",
    )

    list_filter = (
        "type",
        "created_at",
    )

    search_fields = (
        "=id",
        "=wallet__id",
        "=wallet__user_id",
        "=wallet__phone",
        "=reference_id",
        "=gateway_ref",
    )

    readonly_fields = (
        "id",
        "wallet",
        "type",
        "amount",
        "balance_after",
        "counterparty_wallet",
        "transfer",
        "gateway_ref",
        "reference_id",
        "created_at",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Restrict columns on the changelist for performance, keep all fields for detail views
        if request.resolver_match and request.resolver_match.url_name.endswith("_changelist"):
            return qs.only(
                "id",
                "wallet_id",
                "type",
                "amount",
                "balance_after",
                "reference_id",
                "created_at",
            )
        return qs

    fieldsets = (
        (
            "Transaction Overview",
            {
                "fields": (
                    "id",
                    "type",
                    "wallet",
                    "amount",
                    "balance_after",
                )
            },
        ),
        (
            "Relations & References",
            {
                "fields": (
                    "counterparty_wallet",
                    "transfer",
                    "reference_id",
                    "gateway_ref",
                )
            },
        ),
        (
            "Timestamps Information",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                ),
            },
        ),
    )