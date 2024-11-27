from django.urls import path

from .views import MyUserProfileView

urlpatterns = [
    path("my_profile/", MyUserProfileView.as_view(), name="my-profile-view")
]