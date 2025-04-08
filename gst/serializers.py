from rest_framework import serializers
from .models import *
import json

class BasicDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = basic_Details
        fields = '__all__'

class BusinessDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = business_Details
        fields = '__all__'

    def create(self, validated_data):
        gst_details_data = validated_data.get('gst_details', {})
        if isinstance(gst_details_data, str):
            validated_data['gst_details'] = json.loads(gst_details_data)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        gst_details_data = validated_data.get('gst_details', instance.gst_details)
        if isinstance(gst_details_data, str):
            validated_data['gst_details'] = json.loads(gst_details_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance

class BusinessDetailsSerializerRetrieval(serializers.ModelSerializer):
    gst_details = serializers.JSONField()
    class Meta:
        model = business_Details
        fields = '__all__'

class BusinessDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessDocuments
        fields = '__all__'

        def update(self, instance, validated_data):
            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()

            return instance

class PartnerSerializer(serializers.ModelSerializer):
    address = serializers.JSONField()
    class Meta:
        model = partner
        fields = '__all__'

    def create(self, validated_data):
        address_data = validated_data.get('address', {})
        if isinstance(address_data, str):
            validated_data['address'] = json.loads(address_data)  # Convert string to JSON object

        return super().create(validated_data)
    def update(self, instance, validated_data):

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance

class PrincipalPlaceDetailSerializer(serializers.ModelSerializer):
    address = serializers.JSONField()
    class Meta:
        model = principal_Place_Detail
        fields = '__all__'


    def create(self, validated_data):
        address_data = validated_data.get('address', {})
        if isinstance(address_data, str):
            validated_data['address'] = json.loads(address_data)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        address_data = validated_data.get('address', instance.address)
        if isinstance(address_data, str):
            validated_data['address'] = json.loads(address_data)

        # Update all fields from validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Save the instance (this is likely where your error is)
        instance.save()  # Make sure you're calling save() on the instance, not the model class

        return instance