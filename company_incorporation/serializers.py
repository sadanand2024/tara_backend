from rest_framework import serializers
from .models import *


class CompanyIncorporationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyIncorporation
        fields = '__all__'

    def create(self, validated_data):
        return CompanyIncorporation.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CompanyIncorporationSerializerRetrieval(serializers.ModelSerializer):
    address = serializers.JSONField()

    class Meta:
        model = CompanyIncorporation
        fields = '__all__'


class DirectorsDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Directors_details
        fields = '__all__'

        def create(self, validated_data):
            return Share_Holders_Information.objects.create(**validated_data)

        def update(self, instance, validated_data):
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance



class DirectorsDetailsSerializerRetrieval(serializers.ModelSerializer):
    address = serializers.JSONField()
    shareholder_details = serializers.JSONField()

    class Meta:
        model = Directors_details
        fields = '__all__'


class AuthorizedAndPaidUpCapitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authorized_And_Paid_up_Capital
        fields = '__all__'

    def create(self, validated_data):
        return Authorized_And_Paid_up_Capital.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ShareHoldersInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Share_Holders_Information
        fields = '__all__'

    def create(self, validated_data):
        return Share_Holders_Information.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ShareHoldersInformationSerializerRetrieval(serializers.ModelSerializer):
    address = serializers.JSONField()

    class Meta:
        model = Share_Holders_Information
        fields = '__all__'


class DetailsOfExistingDirectorshipsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Details_of_Existing_Directorships
        fields = '__all__'

    def create(self, validated_data):
        return Details_of_Existing_Directorships.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance