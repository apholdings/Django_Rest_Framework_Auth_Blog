from rest_framework import serializers

from .models import UserProfile
from apps.media.serializers import MediaSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = MediaSerializer()
    banner_picture = MediaSerializer()
    class Meta:
        model = UserProfile
        fields = [
            'profile_picture',
            'banner_picture',
            'biography',
            'birthday',
            'website',
            'instagram',
            'facebook',
            'threads',
            'linkedin',
            'youtube',
            'tiktok',
            'github',
            'gitlab',
        ]