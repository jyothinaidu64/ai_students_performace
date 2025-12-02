from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path("my-fees/", views.my_fees_view, name="my_fees"),
    path("receipt/<int:payment_id>/", views.receipt_detail_view, name="receipt_detail"),
    path("overview/", views.finance_overview, name="overview"),
    path("class/<int:class_id>/", views.finance_class_detail, name="class_detail"),  # 👈 new
]
