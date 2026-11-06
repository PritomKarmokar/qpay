from django.contrib import admin

from mini_wallet.models import UserWallet

@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    show_full_result_count = False
    list_per_page = 25
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    list_display = (
        "id",
        "user_id",
        "phone",
        "currency",
        "balance",
        "is_active",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "currency",
        "created_at",
    )

    search_fields = (
        "=id",
        "=user_id",
        "=phone",
    )

    readonly_fields = (
        "id",
        "user_id",
        "phone",
        "currency",
        "created_at",
        "updated_at",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only restrict columns on the changelist; the edit/detail view needs all fields.
        if request.resolver_match and request.resolver_match.url_name.endswith("_changelist"):
            return qs.only(*self.list_display)
        return qs


    fieldsets = (
        (
            "Wallet Details",
            {
                "fields": (
                    "id",
                    "user_id",
                    "phone",
                    "currency",
                )
            },
        ),
        (
            "Balance & Status",
            {
                "fields": (
                    "balance",
                    "is_active",
                )
            },
        ),
        (
            "Timestamps Information",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                    "deleted_at",
                ),
            },
        ),
    )

