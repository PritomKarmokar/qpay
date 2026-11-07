from django.contrib import admin

from mini_wallet.models import WalletTransfer

@admin.register(WalletTransfer)
class WalletTransferAdmin(admin.ModelAdmin):
    show_full_result_count = False
    list_per_page = 25
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    list_display = (
        "id",
        "from_wallet_id",
        "to_wallet_id",
        "amount",
        "status",
        "created_at",
    )

    list_select_related = (
        "from_wallet",
        "to_wallet",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "=id",
        "=from_wallet__id",
        "=from_wallet__user_id",
        "=from_wallet__phone",
        "=to_wallet__id",
        "=to_wallet__user_id",
        "=to_wallet__phone",
        "note",
    )

    readonly_fields = (
        "id",
        "from_wallet",
        "to_wallet",
        "amount",
        "note",
        "status",
        "created_at",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Restrict columns on the changelist for performance, keep all fields for detail views
        if request.resolver_match and request.resolver_match.url_name.endswith("_changelist"):
            return qs.only(
                "id",
                "from_wallet_id",
                "to_wallet_id",
                "amount",
                "status",
                "created_at",
            )
        return qs

    fieldsets = (
        (
            "Transfer Overview",
            {
                "fields": (
                    "id",
                    "status",
                    "amount",
                )
            },
        ),
        (
            "Sender & Receiver",
            {
                "fields": (
                    "from_wallet",
                    "to_wallet",
                )
            },
        ),
        (
            "Additional Details",
            {
                "fields": (
                    "note",
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