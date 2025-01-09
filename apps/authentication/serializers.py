from rest_framework import serializers
from djoser.serializers import UserCreateSerializer
from django.contrib.auth import get_user_model

from apps.media.serializers import MediaSerializer
from apps.user_profile.models import UserProfile


User = get_user_model()


class UserCreateSerializer(UserCreateSerializer):
    qr_code = serializers.URLField(source="get_qr_code")
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    qr_code = serializers.URLField(source="get_qr_code")
    profile_picture = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "role",
            "verified",
            "updated_at",
            "two_factor_enabled",
            "otpauth_url",
            "login_otp",
            "login_otp_used",
            "otp_created_at",
            "qr_code",
            "profile_picture",
        ]
    def get_profile_picture(self, obj):
        user_profile = UserProfile.objects.get(user=obj)
        if user_profile and user_profile.profile_picture:
            return MediaSerializer(user_profile.profile_picture).data
        return None

class UserPublicSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "updated_at",
            "role",
            "verified",
            "profile_picture",
        ]

    def get_profile_picture(self, obj):
        user_profile = UserProfile.objects.get(user=obj)
        if user_profile and user_profile.profile_picture:
            return MediaSerializer(user_profile.profile_picture).data
        return None