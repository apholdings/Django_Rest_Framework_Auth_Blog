from io import BytesIO
from datetime import timedelta

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework import permissions
from rest_framework_api.views import StandardAPIView
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.utils.timezone import now
from django.core.mail import send_mail
from django.contrib.sites.models import Site
import pyotp
import qrcode

from core.permissions import HasValidAPIKey
from utils.ip_utils import get_client_ip
from utils.string_utils import sanitize_string, sanitize_username


User = get_user_model()


class UpdateUserInformationView(StandardAPIView):
    permission_classes = [permissions.IsAuthenticated, HasValidAPIKey]

    def put(self, request):
        user = request.user

        username = request.data.get("username", None)
        first_name = request.data.get("first_name", None)
        last_name = request.data.get("last_name", None)

        if username:
            user.username = sanitize_username(username)
        if first_name:
            user.first_name = sanitize_string(first_name)
        if last_name:
            user.last_name = sanitize_string(last_name)

        user.save()

        return self.response("User information updated successfully")
    

class GenerateQRCodeView(StandardAPIView):
    permission_classes = [permissions.IsAuthenticated, HasValidAPIKey]

    def get(self,request):
        user = request.user
        email = user.email

        otp_base32 = pyotp.random_base32()

        otp_auth_url = pyotp.totp.TOTP(otp_base32).provisioning_uri(
            name=email.lower(), issuer_name="Uridium"
        )

        stream = BytesIO()
        image = qrcode.make(f"{otp_auth_url}")
        image.save(stream)

        user.otp_base32 = otp_base32
        user.qr_code = ContentFile(
            stream.getvalue(), name=f"qr{get_random_string(10)}.png"
        )

        user.save()
        qr_code = user.qr_code
        return self.response(qr_code.url)


class OTPLoginResetView(StandardAPIView):
    permission_classes = [permissions.IsAuthenticated, HasValidAPIKey]

    def post(self, request):
        user = request.user

        new_ip = get_client_ip(request)

        if user.login_ip and user.login_ip != new_ip:
            print(f"New login IP for user: {user.email}")
            # TODO: Send user email

        user.login_ip = new_ip

        if user.qr_code is None or user.otp_base32 is None:
            return self.error("QR Code or OTP Base32 not found for user")
        
        try:
            totp = pyotp.TOTP(user.otp_base32).now()
        except Exception as e:
            return self.error(f"Error generating TOPT: {str(e)}")
        
        user.login_otp = make_password(totp)
        user.otp_created_at = timezone.now()
        user.login_otp_used = False

        user.save()

        return self.response("OTP Reset Successfully for user")
    

class VerifyOTPView(StandardAPIView):
    permission_classes = [permissions.IsAuthenticated, HasValidAPIKey]

    def post(self,request):
        user = request.user

        if user.qr_code is None or user.otp_base32 is None:
            return self.error("QR Code or OTP Base32 not found for user")

        # Get TOTP
        totp = pyotp.TOTP(user.otp_base32)
        otp = request.data.get("otp")
        verified = totp.verify(otp)

        if verified:
            user.login_otp_used = True
            user.save()
            return self.response("OTP Verified")
        else:
            return self.error("Error Verifying One Time Password")
        

class DisableOTPView(StandardAPIView):
    permission_classes = [permissions.IsAuthenticated, HasValidAPIKey]

    def post(self,request):
        user = request.user

        if user.qr_code is None or user.otp_base32 is None:
            return self.error("QR Code or OTP Base32 not found for user")
        
        # Get TOTP
        totp = pyotp.TOTP(user.otp_base32)
        otp = request.data.get("otp")
        verified = totp.verify(otp)

        if verified:
            user.two_factor_enabled = False
            user.otpauth_url = None
            user.otp_base32 = None
            user.qr_code = None
            user.login_otp = None
            user.login_otp_used = False
            user.otp_created_at = None
            user.save()

            return self.response("Two Factor Authentication Disabled")
        else:
            return self.error("Error Verifying One Time Password")
        

class Set2FAView(StandardAPIView):
    permission_classes = [permissions.IsAuthenticated, HasValidAPIKey]

    def post(self, request, *args, **kwargs):
        user = request.user

        if user.qr_code is None:
            return self.error(
                "QR Code not found for the user."
            )

        boolean = bool(request.data.get("bool"))

        if boolean:
            user.two_factor_enabled = True
            user.save()
            return self.response("2FA Activated")
        else:
            user.two_factor_enabled = False
            user.save()
            return self.response("2FA Disabled")
        

class OTPLoginView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp')

        if not email or not otp_code:
            return self.error("Both email and OTP code are required.")
        
        try:
            user = User.objects.get(email=email)
            
            # Verificar que el OTP es válido
            totp = pyotp.TOTP(user.otp_base32)
            if not totp.verify(otp_code):
                return self.error("Invalid OTP code.")
            
            # Actualizar el estado del OTP
            user.login_otp_used = True
            user.save()

            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            return self.response({
                "access": str(refresh.access_token), 
                "refresh": str(refresh)
            })

        except User.DoesNotExist:
            return self.response("User does not exist.", status=status.HTTP_404_NOT_FOUND)
        

class SendOTPLoginView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def post(self, request):
        email = request.data.get('email')

        # Verificar que existe un suario con ese email y que eestaa activo
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return self.error("User does not exist or is not active.")
        
        # Generar OTP
        secret = pyotp.random_base32()
        user.otp_secret = secret
        user.save()

        totp = pyotp.TOTP(secret)
        otp = totp.now()

        # Enviar correo con OTP
        # Obtener el dominio del sitio configurado
        site = Site.objects.get_current()
        domain = site.domain

        send_mail(
            'Your OTP Code',
            f'Your OTP code is {otp}',
            f'noreply@{domain}',
            [email],
            fail_silently=False,
        )

        return self.response("OTP sent successfully.")


class VerifyOTPLoginView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp')

        if not email or not otp_code:
            return self.error("Both email and OTP code are required.")

        # Verificar que existe un suario con ese email y que eestaa activo
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return self.error("User does not exist or is not active.")
        
        # Generar OTP
        totp = pyotp.TOTP(user.otp_secret)

        if totp.verify(otp_code):
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            return self.response({
                "access": str(refresh.access_token), 
                "refresh": str(refresh)
            })

        return self.error("Error verifying OTP code.")