from rest_framework_api.views import StandardAPIView
from rest_framework import status
from rest_framework.exceptions import APIException

from core.permissions import HasValidAPIKey
from .models import NewsletterUser

class DuplicateEmailException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Duplicate email."  # Custom error message
    default_code = "duplicate_email"


class NewsletterSignupView(StandardAPIView):
    permission_classes = (HasValidAPIKey,)

    def post(self, request):
        email = request.data.get("email")

        if NewsletterUser.objects.filter(email=email).exists():
            # Raise the exception with the default detail "Duplicate email"
            raise DuplicateEmailException()

        newsletter_user = NewsletterUser(email=email)
        newsletter_user.save()
        return self.response("Successfully added user.")
