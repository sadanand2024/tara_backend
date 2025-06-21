from rest_framework import serializers
from .models import *

class ProposedCompanyDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposedCompanyDetails
        fields = '__all__'

class RegisteredOfficeAddressDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisteredOfficeAddressDetails
        fields = '__all__'


class AuthorizedPaidUpShareCapitalSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuthorizedPaidUpShareCapital
        fields = '__all__'


class DirectorsDetailsSerializer(serializers.ModelSerializer):
    no_of_shares = serializers.IntegerField(min_value=0, allow_null= True, required = False)
    shareholding_percentage = serializers.FloatField(allow_null= True, required = False)
    paid_up_capital = serializers.IntegerField(allow_null= True, required = False)

    class Meta:
        model = DirectorsDetails
        fields = '__all__'



class DirectorsSerializer(serializers.ModelSerializer):
    directors = DirectorsDetailsSerializer(many=True, read_only=True)

    class Meta:
        model = Directors
        fields = '__all__'

class ShareholdersDetailsSerializer(serializers.ModelSerializer):
    shareholding_percentage = serializers.FloatField(allow_null=True)

    class Meta:
        model = ShareholdersDetails
        fields = '__all__'


class ShareholdersSerializer(serializers.ModelSerializer):
    shareholders = ShareholdersDetailsSerializer(many=True, read_only=True)
    class Meta:
        model = Shareholders
        fields = '__all__'


class ReviewFilingCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewFilingCertificate
        fields = '__all__'