from rest_framework import serializers
from .models import *
import json

class BasicDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicDetails
        fields = '__all__'

class BusinessDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessDetails
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
        model = BusinessDetails
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
        model = Partner
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
        model = PrincipalPlaceDetails
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

class GSTServiceRequestSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer that combines all GST-related data for a service request
    """
    basic_details = BasicDetailsSerializer(read_only=True)
    business_details = BusinessDetailsSerializerRetrieval(source='BusinessDetails', read_only=True, many=True)
    business_documents = BusinessDocumentsSerializer(source='business_document', read_only=True, many=True)
    partners = PartnerSerializer(source='partner_details', read_only=True, many=True)
    principal_place_details = PrincipalPlaceDetailSerializer(source='principal_place', read_only=True, many=True)
    
    class Meta:
        model = BasicDetails
        fields = '__all__'