from rest_framework import serializers
from .models import *

class BasicDetailsSerializer(serializers.ModelSerializer):
    trade_license_file = serializers.FileField(required=False)
    upload_photo = serializers.FileField(required=False)
    class Meta:
        model = Basic_Detail
        fields = '__all__'

class BasicDetailsSerializerRetrieval(serializers.ModelSerializer):
    address = serializers.JSONField()
    class Meta:
        model = Basic_Detail
        fields = '__all__'

class TradeLicenseExistOrNotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade_License_Exist_or_not
        fields = '__all__'

class TradeEntitySerializer(serializers.ModelSerializer):
    # address = serializers.JSONField()
    class Meta:
        model = Trade_Entity
        fields = '__all__'

class TradeEntitySerializerRetrieval(serializers.ModelSerializer):
    address = serializers.JSONField()
    class Meta:
        model = Trade_Entity
        fields = '__all__'

class PartnerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner_Details
        fields = '__all__'
