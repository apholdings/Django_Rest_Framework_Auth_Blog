from django.urls import path

from .views import (
    MyUserProfileView, 
    UpdateUserProfileView, 
    GetMyProfilePictureView, 
    UploadProfilePictureView,
    GetMyBannerPictureView,
    UploadBannerPictureView,
    DetailUserProfileView
    )

urlpatterns = [
    path("my_profile/", MyUserProfileView.as_view(), name="my-profile-view"),
    path("update/", UpdateUserProfileView.as_view()),
    path("get/", DetailUserProfileView.as_view()),
    path("get_picture/", GetMyProfilePictureView.as_view()),
    path("get_banner_picture/", GetMyBannerPictureView.as_view()),
    path("upload_profile_picture/", UploadProfilePictureView.as_view()),
    path("upload_banner_picture/", UploadBannerPictureView.as_view())
]