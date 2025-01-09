from django.urls import path

from .views import NewsletterSignupView

urlpatterns = [path("signup/", NewsletterSignupView.as_view())]