from django.urls import path

from .views import (
    GenerateQRCodeView,
    OTPLoginResetView,
    VerifyOTPView,
    DisableOTPView,
    Set2FAView,
    OTPLoginView
)


urlpatterns = [
    path(
        "generate_qr_code/",
        GenerateQRCodeView.as_view(),
        name="generate-qr-code-view",
    ),
    path("otp_login_reset/", OTPLoginResetView.as_view(), name="otp-login-reset-view"),
    path("verify_otp/", VerifyOTPView.as_view()),
    path("disable_otp/", DisableOTPView.as_view()),
    path("confirm_2fa/", Set2FAView.as_view()),
    path("otp_login/", OTPLoginView.as_view()),
]