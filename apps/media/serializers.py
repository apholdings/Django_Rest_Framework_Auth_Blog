import datetime

from rest_framework import serializers
from botocore.signers import CloudFrontSigner
from django.conf import settings
from django.utils import timezone

from utils.s3_utils import rsa_signer
from .models import Media


class MediaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = "__all__"

    def get_url(self, obj):
        if not obj.key:
            return None
        
        key_id = str(settings.AWS_CLOUDFRONT_KEY_ID)
        obj_url = f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/{obj.key}"

        cloudfront_signer = CloudFrontSigner(key_id, rsa_signer)
        expire_date = timezone.now() + datetime.timedelta(seconds=60)
        signed_url = cloudfront_signer.generate_presigned_url(obj_url, date_less_than=expire_date)
        return signed_url