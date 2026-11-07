from django.urls import path

api_base_url = "api/v1"
app_base_url = "app/v1/api"
web_base_url = "web/v1/api"
internal_base_url = "internal/v1/api"

from mini_wallet.views import (
    AddMoneyView,
    P2PTransferView,
    CreateWalletView,
    RetrieveWalletView,
)

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
    ),
    path(
        "api/v1/wallets/<str:wallet_id>",
        RetrieveWalletView.as_view(),
        name="api_v1_retrieve_wallet",
    ),
    path(
        f"{api_base_url}/wallets/<str:wallet_id>/add-money",
            AddMoneyView.as_view(),
            name="api_v1_wallets"
    ),
    path(
        f"{api_base_url}/transfers",
            P2PTransferView.as_view(),
            name="api_v1_wallets"
    ),

]

urlpatterns = app_urls + web_urls + internal_urls + api_urls