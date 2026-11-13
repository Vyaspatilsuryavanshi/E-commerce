from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("confirmation/<str:order_number>/", views.order_success, name="order_success"),
    path("payment/verify/<str:order_number>/", views.payment_verify, name="payment_verify"),
    path("payment/razorpay/webhook/", views.razorpay_webhook, name="razorpay_webhook"),
    path("detail/<str:order_number>/", views.order_detail, name="order_detail"),
    path("cancel/<str:order_number>/", views.cancel_order, name="cancel_order"),
    path("return/<str:order_number>/", views.request_return, name="request_return"),
    path("api/reverse-geocode/", views.api_reverse_geocode, name="api_reverse_geocode"),
]
