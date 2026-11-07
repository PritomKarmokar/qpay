from django.contrib import admin

from mini_wallet.models import IdempotencyRecord

@admin.register(IdempotencyRecord)
class IdempotencyRecordAdmin(admin.ModelAdmin):
    show_full_result_count = False
    list_per_page = 25
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    list_display = (
        "id",
        "key",
        "operation",
        "response_status",
        "created_at",
    )

    list_filter = (
        "operation",
        "response_status",
        "created_at",
    )

    search_fields = (
        "=id",
        "key",
        "=request_hash",
    )

    readonly_fields = (
        "id",
        "key",
        "operation",
        "request_hash",
        "response_status",
        "response_body",
        "created_at",
        "updated_at",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Restrict columns on the changelist for performance, keep all fields for detail views
        if request.resolver_match and request.resolver_match.url_name.endswith("_changelist"):
            return qs.only(
                "id",
                "key",
                "operation",
                "response_status",
                "created_at",
            )
        return qs

    fieldsets = (
        (
            "Idempotency Details",
            {
                "fields": (
                    "id",
                    "key",
                    "operation",
                    "response_status",
                )
            },
        ),
        (
            "Payload & Security",
            {
                "fields": (
                    "request_hash",
                    "response_body",
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
                ),
            },
        ),
    )