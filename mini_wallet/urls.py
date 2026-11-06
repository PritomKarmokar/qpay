from django.urls import path

api_base_url = "api/v1"
app_base_url = "app/v1/api"
web_base_url = "web/v1/api"
internal_base_url = "internal/v1/api"

from mini_wallet.views import CreateWalletView

app_urls = [
    # path(
    #     f"{api_base_url}/wallets",
    #     CreateWalletView.as_view(),
    #     name="api_v1_wallets"
    # )
]

web_urls = [
    # path(
    #     f"{api_base_url}/wallets",
    #     CreateWalletView.as_view(),
    #     name="api_v1_wallets"
    # )
]

internal_urls = [
    # path(
    #     f"{api_base_url}/wallets",
    #     CreateWalletView.as_view(),
    #     name="api_v1_wallets"
    # )
]

api_urls = [
    path(
        f"{api_base_url}/wallets",
        CreateWalletView.as_view(),
        name="api_v1_wallets"
    )
]

urlpatterns = app_urls + web_urls + internal_urls + api_urls