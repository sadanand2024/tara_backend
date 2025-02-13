from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from user_management.models import User  # Assuming your user model is in user_management app
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from user_management.models import CustomGroup, CustomPermission, UserAffiliatedRole, Business, UserAffiliationSummary
from rest_framework.fields import CharField
from django.contrib.auth.hashers import check_password


User = get_user_model()  # Fetch the custom user model

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email_or_user_name'
    user_type = CharField(required=True)

    def validate(self, attrs):
        # Get email or mobile from the input data
        email_or_user_name = attrs.get("email_or_user_name")
        password = attrs.get("password")
        user_type = attrs.get("user_type")

        # Ensure email_or_mobile and password are provided
        if not email_or_user_name or not password:
            raise AuthenticationFailed("Email/Mobile and password are required.")

        # Attempt to find the user by email or mobile
        if "@" in email_or_user_name:
            users = User.objects.filter(email__iexact=email_or_user_name)
            if not users.exists():
                raise AuthenticationFailed("No user found with the provided email.")
            users = users.filter(user_type=user_type)
            if not users.exists():
                raise AuthenticationFailed("No user found with the provided user type.")
        else:
            users = User.objects.filter(user_name__iexact=email_or_user_name)
            if not users.exists():
                raise AuthenticationFailed("No user found with the provided username.")
            users = users.filter(user_type=user_type)
            if not users.exists():
                raise AuthenticationFailed("No user found with the provided user type.")

            # Iterate over the users to check the password
        for user in users:
            if check_password(password, user.password):
                # If password matches, proceed
                break
        else:
            # If no valid password match is found, raise error
            raise AuthenticationFailed("Invalid password. Please try again.")

        if not user.is_active:
            raise AuthenticationFailed("User account is not active. Please verify your email or mobile.")

        # if not user.check_password(password):
        #     raise AuthenticationFailed("Invalid password. Please try again.")

        # Ensure the user is active
        if not user.is_active:
            raise AuthenticationFailed("User account is not active. Please verify your email or mobile.")

        # Generate the refresh and access token
        refresh = self.get_token(user)

        # Check if UserKYC is completed
        user_kyc = False
        user_name = None
        if hasattr(user, 'userkyc'):  # Assuming `UserKYC` has a one-to-one or foreign key to `User`
            user_kyc_instance = user.userkyc
            user_name = user_kyc_instance.name
            user_kyc = True

            # if user_kyc_instance.is_completed:  # Assuming `is_completed` indicates KYC completion
            #     user.user_kyc = True  # Update the `user_kyc` field in the User model
            #     user.save(update_fields=['user_kyc'])  # Save only the `user_kyc` field
            #     user_kyc = True

        # Extract the date from created_on
        created_on_date = user.date_joined.date()

        # Retrieve the user's group
        # try:
        #     user_group = UserAffiliatedRole.objects.get(user=user)  # Fetch a single UserGroup instance
        # except UserAffiliatedRole.DoesNotExist:
        #     user_group = None
        #
        # if user_group:
        #     # Retrieve the user's groups and associated permissions
        #     # group_names = [group.get('name') for group in user_group.group if 'name' in group]
        #     group_name = user_group.group.name
        #     associated_services = list(user_group.custom_permissions.values_list('name', flat=True).distinct())
        # else:
        #     group_name = None  # No groups assigned
        #     associated_services = []  # No permissions assigned

        try:
            user_affiliation_summary = UserAffiliationSummary.objects.get(user=user)  # Fetch a single UserGroup instance
        except UserAffiliationSummary.DoesNotExist:
            raise ValueError("Something Wrong with this User, Please Connect Admin Team To Solve the Issue")

        business_exits = False

        # Customize the response data
        data = {
            'id': user.id,
            'email': user.email,
            'mobile_number': user.mobile_number,
            'user_name': user_name,
            'name': user.first_name + ' ' + user.last_name,
            'created_on': created_on_date,
            'user_type': user.user_type,
            'user_kyc': user_kyc,
            'individual_affiliated': list(user_affiliation_summary.individual_affiliated),
            'ca_firm_affiliated': list(user_affiliation_summary.ca_firm_affiliated),
            'service_provider_affiliated': list(user_affiliation_summary.service_provider_affiliated),
            'business_affiliated':list(user_affiliation_summary.business_affiliated),
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        if user.user_type == "Business":
            business_exists = Business.objects.filter(client=user).exists()
            data['business_exists'] = business_exists
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]  # Ensure this view is publicly accessible

    def post(self, request, *args, **kwargs):
        # Serialize the incoming request data
        print(request.data)
        serializer = self.get_serializer(data=request.data)

        # Prevent schema generation errors with Swagger
        swagger_fake_view = getattr(request, "swagger_fake_view", False)

        if swagger_fake_view:  # Skip processing if it's a Swagger fake view
            return Response(status=status.HTTP_204_NO_CONTENT)

        try:
            # Validate the data
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed as e:
            # If validation fails, return an error response
            return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        # Return the validated data along with tokens
        return Response(serializer.validated_data, status=status.HTTP_200_OK)