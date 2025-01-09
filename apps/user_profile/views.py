from datetime import datetime, timedelta

from rest_framework import permissions, status
from rest_framework_api.views import StandardAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from botocore.signers import CloudFrontSigner

from core.permissions import HasValidAPIKey
from .models import UserProfile
from apps.media.models import Media
from apps.authentication.serializers import UserPublicSerializer
from .serializers import UserProfileSerializer
from utils.s3_utils import rsa_signer
from utils.string_utils import sanitize_string, sanitize_html, sanitize_url

User = get_user_model()


class MyUserProfileView(StandardAPIView):
    permission_classes = [HasValidAPIKey, permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        user_profile = UserProfile.objects.get(user=user)
        serialized_user_profile = UserProfileSerializer(user_profile).data
        return self.response(serialized_user_profile)


class DetailUserProfileView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def get(self, request):
        username = request.query_params.get("username", None)
        if not username:
            return self.error("A valid username must be provided")
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return self.response("User does not exist", status=status.HTTP_404_NOT_FOUND)

        serialized_user = UserPublicSerializer(user).data

        user_profile = UserProfile.objects.get(user=user)
        serialized_user_profile = UserProfileSerializer(user_profile).data

        return self.response({
            "user":serialized_user,
            "profile":serialized_user_profile
        })



class GetMyProfilePictureView(StandardAPIView):
    permission_classes = [HasValidAPIKey, permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        profile = UserProfile.objects.get(user=user)

        # Ensure user exists and has a profile picture
        if not profile.profile_picture:
            return self.response(
                "No profile picture found.", status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate a signed URL for secure access if necessary
        if hasattr(profile.profile_picture, "key"):
            key_id = settings.AWS_CLOUDFRONT_KEY_ID
            signer = CloudFrontSigner(key_id, rsa_signer)
            expire_date = timezone.now() + timedelta(seconds=60)
            obj_url = f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/{profile.profile_picture.key}"
            signed_url = signer.generate_presigned_url(
                obj_url, date_less_than=expire_date
            )
            return self.response(signed_url)
        return self.error('Error fetching image from aws')


class GetMyBannerPictureView(StandardAPIView):
    permission_classes = [HasValidAPIKey, permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        profile = UserProfile.objects.get(user=user)

        # Ensure user exists and has a banner picture
        if not profile.banner_picture:
            return self.response(
                "No banner picture found.", status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate a signed URL for secure access if necessary
        if hasattr(profile.banner_picture, "key"):
            key_id = settings.AWS_CLOUDFRONT_KEY_ID
            signer = CloudFrontSigner(key_id, rsa_signer)
            expire_date = timezone.now() + timedelta(seconds=60)
            obj_url = f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/{profile.banner_picture.key}"
            signed_url = signer.generate_presigned_url(
                obj_url, date_less_than=expire_date
            )
            return self.response(signed_url)
        return self.error('Error fetching image from aws')


class UploadProfilePictureView(StandardAPIView):
    permission_classes = [HasValidAPIKey, permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        user = request.user
        profile = UserProfile.objects.get(user=user)

        key = request.data.get("key")
        title = request.data.get("title")
        size = request.data.get("size")
        file_type = request.data.get("type")

        profile_picture = Media.objects.create(
            order=0,
            name=title,
            size=size,
            type=file_type,
            key=key,
            media_type='image',
        )

        profile.profile_picture = profile_picture
        profile.save()

        return self.response("Profile picture has been updated.")

class UploadBannerPictureView(StandardAPIView):
    permission_classes = [HasValidAPIKey, permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        user = request.user
        profile = UserProfile.objects.get(user=user)

        key = request.data.get("key")
        title = request.data.get("title")
        size = request.data.get("size")
        file_type = request.data.get("type")

        banner_picture = Media.objects.create(
            order=0,
            name=title,
            size=size,
            type=file_type,
            key=key,
            media_type='image',
        )

        profile.banner_picture = banner_picture
        profile.save()

        return self.response("Banner picture has been updated.")

class GetMyProfilePicture(StandardAPIView):
    permission_classes = [HasValidAPIKey, permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        profile = UserProfile.objects.get(user=user)


class UpdateUserProfileView(StandardAPIView):
    permission_classes = [HasValidAPIKey, permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def put(self, request):
        user = request.user
        profile = UserProfile.objects.get(user=user)
        
        biography = request.data.get("biography", None)
        birthday = request.data.get("birthday", None)
        website = request.data.get("website", None)
        instagram = request.data.get("instagram", None)
        facebook = request.data.get("facebook", None)
        threads = request.data.get("threads", None)
        linkedin = request.data.get("linkedin", None)
        youtube = request.data.get("youtube", None)
        tiktok = request.data.get("tiktok", None)
        github = request.data.get("github", None)
        gitlab = request.data.get("gitlab", None)

        try:
            if biography:
                profile.biography = sanitize_html(biography)
            if birthday:
                # Validar y transformar el formato de la fecha
                try:
                    formatted_birthday = datetime.strptime(birthday, "%Y-%m-%d").date()
                    profile.birthday = formatted_birthday
                except ValueError:
                    raise ValidationError("Invalid date format. Use YYYY-MM-DD.")
            if instagram:
                profile.instagram = sanitize_url(instagram)
            if facebook:
                profile.facebook = sanitize_url(facebook)
            if threads:
                profile.threads = sanitize_url(threads)
            if linkedin:
                profile.linkedin = sanitize_url(linkedin)
            if youtube:
                profile.youtube = sanitize_url(youtube)
            if tiktok:
                profile.tiktok = sanitize_url(tiktok)
            if github:
                profile.github = sanitize_url(github)
            if gitlab:
                profile.gitlab = sanitize_url(gitlab)
            if website:
                profile.website = sanitize_url(website)

            profile.save()

            return self.response("Profile has been updated successfully.")
        except ValidationError as e:
            return self.error(str(e))

