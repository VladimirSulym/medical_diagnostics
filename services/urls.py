from django.urls import path
from . import views

from .apps import ServicesConfig

app_name = ServicesConfig.name

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    # path("1/", views.ReviewView.as_view(), name="feedback"),
    # path("sales/", views.SalesView.as_view(), name="sales"),
    # path("payments/", views.PaymentsView.as_view(), name="payments"),
    # path("hw/", views.HWView.as_view(), name="hw"),
    # path("debt/", views.DebtView.as_view(), name="debt"),
    # path("transaction_deal/", views.transaction_deal, name="transaction-deal"),
    # path("expected_payment/", views.ExpectedPaymentView.as_view(), name="expected-payment"),
    # path("update_user//<int:pk>/", views.UpdateUserView.as_view(), name="update_user"),
]
