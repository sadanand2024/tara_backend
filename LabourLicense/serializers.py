from rest_framework import serializers
from .models import *

class EntrepreneurDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntrepreneurDetails
        fields = '__all__'

class EntrepreneurDetailsSerializerRetrival(serializers.ModelSerializer):
    address_of_entrepreneur = serializers.JSONField()
    class Meta:
        model = EntrepreneurDetails
        fields = '__all__'

class EstablishmentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = establishment_details
        fields = '__all__'

class EstablishmentDetailsSerializerRetrival(serializers.ModelSerializer):
    address_of_establishment = serializers.JSONField()
    class Meta:
        model = establishment_details
        fields = '__all__'

class WorkLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work_Location
        fields = '__all__'

class WorkLocationSerializerRetrival(serializers.ModelSerializer):
    work_location = serializers.JSONField()
    class Meta:
        model = Work_Location
        fields = '__all__'

class EmployerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployerDetails
        fields = '__all__'

class EmployerDetailsSerializerRetrival(serializers.ModelSerializer):
    address_of_employer = serializers.JSONField()
    total_employees = serializers.JSONField()
    class Meta:
        model = EmployerDetails
        fields = '__all__'

class filesSerializer(serializers.ModelSerializer):
    class Meta:
        model = files
        fields = '__all__'