from rest_framework import serializers
from .models import (
    BasicBusinessInfo,
    RegistrationInfo,
    PrincipalPlaceDetails,
    PromoterSignatoryDetails,
    GSTReviewFilingCertificate,
    PromoterSignatoryInfo
)


class BasicBusinessInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicBusinessInfo
        fields = '__all__'


class RegistrationInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationInfo
        fields = '__all__'


class PrincipalPlaceDetailsSerializer(serializers.ModelSerializer):
    principal_place = serializers.JSONField(required=False, allow_null=True, default=dict)

    class Meta:
        model = PrincipalPlaceDetails
        fields = '__all__'


class PromoterSignatoryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoterSignatoryDetails
        fields = '__all__'


class PromoterSignatoryInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoterSignatoryInfo
        fields = '__all__'


class GSTReviewFilingCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GSTReviewFilingCertificate
        fields = '__all__'

