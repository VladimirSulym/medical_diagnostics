from django.urls import path
from . import views

from .apps import ServicesConfig

app_name = ServicesConfig.name

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("services/", views.ServiceView.as_view(), name="services"),
    path("services/<int:pk>/", views.ServiceDetailView.as_view(), name="services-detail"),
    path("appointment_create/", views.AppointmentCreateView.as_view(), name="appointment-create"),
    path("contacts/", views.ContactsView.as_view(), name="contacts"),
    # path("sales/", views.SalesView.as_view(), name="sales"),
    # path("payments/", views.PaymentsView.as_view(), name="payments"),
    # path("hw/", views.HWView.as_view(), name="hw"),
    # path("debt/", views.DebtView.as_view(), name="debt"),
    # path("transaction_deal/", views.transaction_deal, name="transaction-deal"),
    # path("expected_payment/", views.ExpectedPaymentView.as_view(), name="expected-payment"),
    # path("update_user//<int:pk>/", views.UpdateUserView.as_view(), name="update_user"),
]
