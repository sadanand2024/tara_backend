from rest_framework import serializers
from .models import *

class MSMEDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MSMEDetails
        fields = '__all__'

        def update(self, instance, validated_data):
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance


class MSMEDetailsSerializerRetrieval(serializers.ModelSerializer):
    official_address_of_enterprise = serializers.JSONField(default={})
    location_of_plant_or_unit = serializers.JSONField(default={})
    status = serializers.JSONField(default={})
    bank_details = serializers.JSONField(default={})
    no_of_persons_employed = serializers.JSONField(default={})
    nic_code = serializers.JSONField(default={})
    class Meta:
        model = MSMEDetails
        fields = '__all__'

        def save(self, *args, **kwargs):
            # Any custom save logic here
            super().save(*args, **kwargs)