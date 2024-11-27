from rest_framework import permissions
from rest_framework_api.views import StandardAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model

from core.permissions import HasValidAPIKey
from .models import UserProfile
from .serializers import UserProfileSerializer

User = get_user_model()


class MyUserProfileView(StandardAPIView):
    permission_classes = [HasValidAPIKey, permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = User.objects.get(id=request.user.id)
        user_profile = UserProfile.objects.get(user=user)
        serialized_user_profile = UserProfileSerializer(user_profile).data
        return self.response(serialized_user_profile)
