from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import (UserRegistrationSerializer, UsersKYCSerializer, UserActivationSerializer,
                          FirmKYCSerializer,CustomPermissionSerializer, CustomGroupSerializer)

from .serializers import *
from password_generator import PasswordGenerator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
import traceback
from django.db import DatabaseError, IntegrityError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import User, UserKYC, FirmKYC, CustomPermission, CustomGroup, UserGroup
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
import logging
import random
import requests
import json
from Tara.settings.default import *
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from datetime import datetime
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from django.contrib.auth.password_validation import validate_password
from django.http import Http404
from .permissions import GroupPermission, has_group_permission
from django.contrib.auth.decorators import permission_required



# Create loggers for general and error logs
logger = logging.getLogger(__name__)


class Constants:
    SMS_API_POST_URL = 'https://www.fast2sms.com/dev/bulkV2'

def Autogenerate_password():
    pwo = PasswordGenerator()
    return pwo.shuffle_password('abcdefghijklmnopqrstuvwxyz', 8)  # Generates an 8-character password


def generate_otp():
    return random.randint(100000, 999999)

def send_otp_helper(phone_number, otp):
    try:
        payload = f"variables_values={otp}&route=otp&numbers={phone_number}"
        headers = {
            'authorization': "8Vt5jZpbP2KwMDOLlIeSGN9g7qn6kBi4FHuy1dvhoYEaARJQfsHlpLvoyPKxfN2jIbSkrXG3CdhRVQ1E",
            'Content-Type': "application/x-www-form-urlencoded",
            'Cache-Control': "no-cache",
        }
        response = requests.request("POST", Constants.SMS_API_POST_URL, data=payload, headers=headers)
        returned_msg = json.loads(response.text)
        return returned_msg
    except Exception as e:
        logger.error(e, exc_info=1)
        raise ValueError(f'Request failed: {str(e)}')

def authenticate():
    url = "https://api.sandbox.co.in/authenticate"
    payload = {}
    headers = {
        'x-api-key': SANDBOX_API_KEY,
        'x-api-secret': SANDBOX_API_SECRET,
        'x-api-version': '3.4.0'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()['access_token']


@api_view(['GET', 'POST'])
def custom_permission_list_create(request):
    if request.method == 'GET':
        permissions = CustomPermission.objects.all()
        serializer = CustomPermissionSerializer(permissions, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CustomPermissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def custom_permission_retrieve_update_destroy(request, pk):
    try:
        permission = CustomPermission.objects.get(pk=pk)
    except CustomPermission.DoesNotExist:
        return Response({"error": "Permission not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CustomPermissionSerializer(permission)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = CustomPermissionSerializer(permission, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        permission.delete()
        return Response({"message": "Permission deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# CRUD for CustomGroup

@api_view(['GET', 'POST'])
def custom_group_list_create(request):
    if request.method == 'GET':
        groups = CustomGroup.objects.all()
        serializer = CustomGroupSerializer(groups, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CustomGroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def custom_group_retrieve_update_destroy(request, pk):
    try:
        group = CustomGroup.objects.get(pk=pk)
    except CustomGroup.DoesNotExist:
        return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CustomGroupSerializer(group)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = CustomGroupSerializer(group, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        group.delete()
        return Response({"message": "Group deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# User Registration
@swagger_auto_schema(
    method='post',
    request_body=UserRegistrationSerializer,
    responses={
        201: openapi.Response("User registered successfully"),
        400: openapi.Response("Bad Request"),
        500: openapi.Response("Internal Server Error"),
    },
    operation_description="Handle user registration with email or mobile number verification."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def user_registration(request):
    """
    Handle user registration with autogenerated password if not provided,
    and verify email or mobile number.
    """
    logger.info("Received a user registration request.")
    print("*********************")

    if request.method == 'POST':
        try:
            request_data = request.data
            email = request_data.get('email', '').lower()
            mobile_number = request_data.get('mobile_number', '')

            logger.debug(f"Request data: email={email}, mobile_number={mobile_number}")

            # Ensure at least one of email or mobile_number is provided
            if not email and not mobile_number:
                logger.warning("Registration failed: Missing both email and mobile number.")
                return Response(
                    {"error": "Either email or mobile number must be provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = UserRegistrationSerializer(data=request_data)
            if serializer.is_valid():
                user = serializer.save()
                logger.info(f"User created successfully: {user.pk}")

                # Handle Email Verification
                if email:
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(str(user.pk).encode())
                    activation_link = f"{FRONTEND_URL}activation?uid={uid}&token={token}"
                    ses_client = boto3.client(
                        'ses',
                        region_name=AWS_REGION,
                        aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                    )

                    subject = "Activate your account"
                    body_html = f"""
                                        <html>
                                        <body>
                                            <h1>Activate Your Account</h1>
                                            <p>Click the link below to activate your account:</p>
                                            <a href="{activation_link}">Activate Account</a>
                                        </body>
                                        </html>
                                        """

                    try:
                        response = ses_client.send_email(
                            Source=EMAIL_HOST_USER,
                            Destination={'ToAddresses': [email]},
                            Message={
                                'Subject': {'Data': subject},
                                'Body': {
                                    'Html': {'Data': body_html},
                                    'Text': {'Data': f"Activate your account using the link: {activation_link}"}
                                },
                            }
                        )
                        logger.info(f"Activation email sent to: {email}")
                        return Response(
                            {"message": "User registered. Check your email for activation link."},
                            status=status.HTTP_201_CREATED,
                        )
                    except ClientError as e:
                        logger.error(f"Failed to send email via SES: {e.response['Error']['Message']}")
                        return Response(
                            {"error": "Failed to send activation email. Please try again later."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                # Handle Mobile Number Verification
                if mobile_number:
                    otp = generate_otp()
                    response = send_otp_helper(mobile_number, otp)  # Changed function name to avoid conflict
                    if response['return']:
                        query = User.objects.filter(mobileNumber=mobile_number)
                        if query.exists():
                            obj = query.first()
                            obj.otp = int(otp)
                            obj.save()
                            logger.info(f"OTP sent to mobile number: {mobile_number}")
                            return Response(
                                {"message": "User registered. Check your mobile for activation code."},
                                status=status.HTTP_201_CREATED,
                            )

            logger.warning("Registration failed: Validation errors.")
            logger.debug(f"Validation errors: {serializer.errors}")
            print("************************************")
            print("########################")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            logger.error(f"Integrity error during registration: {str(e)}")
            return Response({"error": "A user with this email or mobile number already exists."},
                            status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            logger.error(f"Database error during registration: {str(e)}")
            return Response({"error": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            return Response({"error": "An unexpected error occurred.", "details": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Define the conditional schema
def get_conditional_schema(user_type):
    """
    Return the schema based on the user type.
    """
    if user_type == 'ServiceProvider_Admin':
        # Add visa-related fields for ServiceProvider_Admin
        return openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email Address'),
                'mobile_number': openapi.Schema(type=openapi.TYPE_STRING, description='Mobile Number'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                'created_by': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the admin who created the user'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First Name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last Name'),
                'passport_number': openapi.Schema(type=openapi.TYPE_STRING, description='Passport Number'),
                'purpose': openapi.Schema(type=openapi.TYPE_STRING, description='Purpose of the Visa'),
                'visa_type': openapi.Schema(type=openapi.TYPE_STRING, description='Visa Type'),
                'destination_country': openapi.Schema(type=openapi.TYPE_STRING, description='Destination Country'),
            },
            required=['email', 'mobile_number', 'password', 'created_by']
        )
    else:
        # Return default schema for non-ServiceProvider_Admin
        return openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email Address'),
                'mobile_number': openapi.Schema(type=openapi.TYPE_STRING, description='Mobile Number'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                'created_by': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the admin who created the user'),
            },
            required=['email', 'mobile_number', 'password', 'created_by']
        )


# Swagger schema dynamically based on user type
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description="User's email address"),
            'mobile_number': openapi.Schema(type=openapi.TYPE_STRING, description="User's mobile number"),
        },
        required=['email', 'mobile_number'],
    ),
    responses={
        201: openapi.Response("User registered successfully. Check your email or mobile for credentials."),
        400: openapi.Response("Bad Request. Missing required fields or validation error."),
        500: openapi.Response("Internal Server Error. Database or email sending failed."),
    },
    operation_description="Admin can register users, send autogenerated credentials, and trigger email or OTP verification. Provide only `email` or `mobile_number` in the payload.",
    manual_parameters=[
        openapi.Parameter(
            'Authorization',
            openapi.IN_HEADER,
            description="Bearer <JWT Token>",
            type=openapi.TYPE_STRING,
        ),
    ],
   tags=["User Management - UsersCreation"]
)
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def users_creation(request):
    """
    Handles normal user registration by admin with autogenerated password.
    Sends credentials via email or OTP based on availability.
    """
    if request.method != 'POST':
        return Response({"error": "Invalid HTTP method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    admin_roles = [
        'Business_Owner', 'CA_Admin', 'Business_Admin',
        'ServiceProvider_Owner', 'ServiceProvider_Admin',
        'Tara_SuperAdmin', 'Tara_Admin'
    ]

    if request.user.user_role not in admin_roles:
        return Response(
            {'error_message': 'Unauthorized Access. Only admins can create users.', 'status_cd': 1},
            status=status.HTTP_401_UNAUTHORIZED
        )

    email = request.data.get('email', '').lower()
    mobile_number = request.data.get('mobile_number', '')
    if not email and not mobile_number:
        return Response(
            {"error": "Either email or mobile number must be provided."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        request_data = {
            'email': email,
            'mobile_number': mobile_number,
            'password': Autogenerate_password(),
            'created_by': request.user.id,
            'user_type': request.data.get('user_type', ''),
            'user_role': request.data.get('user_role', '')
        }

        with transaction.atomic():
            serializer = UserRegistrationSerializer(data=request_data)
            if serializer.is_valid():
                user_data = serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Send email or OTP
        if email:
            send_user_email(email, request_data['password'])
        elif mobile_number:
            if not send_user_otp(mobile_number):
                raise Exception("Failed to send OTP to mobile number.")

        return Response(
            {"message": "User registered successfully. Credentials sent via email or mobile."},
            status=status.HTTP_201_CREATED,
        )
    except IntegrityError as e:
        logger.error(f"Integrity error: {str(e)}")
        return Response(
            {"error": "User with this email or mobile already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return Response(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name of the user'),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name of the user'),
            'passport_number': openapi.Schema(type=openapi.TYPE_STRING, description='Passport number of the user'),
            'purpose': openapi.Schema(type=openapi.TYPE_STRING, description='Purpose of travel'),
            'visa_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of visa'),
            'destination_country': openapi.Schema(type=openapi.TYPE_STRING, description='Destination country'),
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of the user'),
            'mobile_number': openapi.Schema(type=openapi.TYPE_STRING, description='Mobile number of the user'),
        },
        required=['first_name', 'last_name', 'passport_number', 'visa_type', 'destination_country'],
    ),
    responses={
        201: openapi.Response("Visa user registered successfully."),
        400: openapi.Response("Bad Request. Missing required fields or validation error."),
        500: openapi.Response("Internal Server Error. Database error occurred."),
    },
    operation_description="ServiceProviderAdmin can register visa users with additional details.",
    tags=["User Management - VisaUsersCreation"],
    manual_parameters=[
        openapi.Parameter(
            'Authorization',
            openapi.IN_HEADER,
            description="Bearer <JWT Token>",
            type=openapi.TYPE_STRING,
        ),
    ],
)
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def visa_users_creation(request):
    """
    Handles the creation of a visa user by ServiceProvider_Admin.
    Creates a user first and associates visa application details with them.
    """
    if request.method != 'POST':
        return Response({"error": "Invalid HTTP method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    service_provider_admin_roles = [
        'ServiceProvider_Owner', 'ServiceProvider_Admin',
        'Tara_SuperAdmin', 'Tara_Admin'
    ]

    if request.user.user_role not in service_provider_admin_roles:
        return Response(
            {'error_message': 'Unauthorized Access. Only ServiceProviderAdmin can create visa users.', 'status_cd': 1},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        # Step 1: Create the user
        email = request.data.get('email', '').lower()
        mobile_number = request.data.get('mobile_number', '')
        if not email and not mobile_number:
            return Response(
                {"error": "Either email or mobile number must be provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_data = {
            'email': email,
            'mobile_number': mobile_number,
            'password': Autogenerate_password(),
            'created_by': request.user.id,
            'user_type': 'ServiceProvider',
            'user_role': 'Individual_User',
            'first_name': request.data.get('first_name'),
            'last_name': request.data.get('last_name'),
        }

        with transaction.atomic():
            # Validate and save user
            user_serializer = UserRegistrationSerializer(data=user_data)
            if user_serializer.is_valid():
                user_instance = user_serializer.save()
            else:
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Step 2: Create visa application details
            visa_applications_data = {
                'passport_number': request.data.get('passport_number', ''),
                'purpose': request.data.get('purpose'),
                'visa_type': request.data.get('visa_type'),
                'destination_country': request.data.get('destination_country'),
                'user': user_instance.id,
            }

            visa_serializer = VisaApplicationsSerializer(data=visa_applications_data)
            if visa_serializer.is_valid():
                visa_serializer.save()
            else:
                return Response(visa_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Send email or OTP for the created user
            if email:
                send_user_email(email, user_data['password'])
            elif mobile_number:
                if not send_user_otp(mobile_number):
                    raise Exception("Failed to send OTP to mobile number.")

        return Response(
            {"message": "Visa user registered successfully."},
            status=status.HTTP_201_CREATED,
        )
    except IntegrityError as e:
        logger.error(f"Integrity error: {str(e)}")
        return Response(
            {"error": "User with this email or mobile already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return Response(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def send_user_email(email, password):
    """Sends autogenerated credentials to user's email."""
    ses_client = boto3.client(
        'ses',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    subject = "Welcome to TaraFirst! Your Account Has Been Created"
    body_html = f"""
        <html>
        <body>
            <h1>Welcome to TaraFirst!</h1>
            <p>Your account has been created.</p>
            <p><strong>Username:</strong> {email}</p>
            <p><strong>Password:</strong> {password}</p>
            <footer style="margin-top: 30px;">TaraFirst Team</footer>
        </body>
        </html>
    """
    ses_client.send_email(
        Source=EMAIL_HOST_USER,
        Destination={'ToAddresses': [email]},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Html': {'Data': body_html}},
        },
    )


def send_user_otp(mobile_number):
    """Generates and sends OTP to user's mobile number."""
    otp = generate_otp()
    response = send_otp_helper(mobile_number, otp)
    if response['return']:
        query = User.objects.filter(mobile_number=mobile_number)
        if query.exists():
            user = query.first()
            user.otp = otp
            user.save()
        return True
    return False


# Activate User

class ActivateUserView(APIView):
    """
    View for activating user accounts using UID and token.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('uid', openapi.IN_QUERY, description="User ID (Base64 encoded)", type=openapi.TYPE_STRING),
            openapi.Parameter('token', openapi.IN_QUERY, description="Activation token", type=openapi.TYPE_STRING)
        ],
        responses={
            200: openapi.Response("Account activated successfully"),
            400: openapi.Response("Invalid or expired activation link"),
        },
        operation_description="Activate user account using UID and token."
    )
    def get(self, request, *args, **kwargs):
        """
        Handle user account activation using query parameters (uid and token).
        """
        logger.info("Starting user account activation process.")

        # Get 'uid' and 'token' from query parameters
        uid = request.query_params.get('uid')
        token = request.query_params.get('token')

        if not uid or not token:
            raise Http404("UID or token is missing from the request.")

        try:
            uid = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid)
            logger.info(f"User with UID {uid} found.")
        except (ValueError, TypeError, User.DoesNotExist) as e:
            logger.error(f"Error during activation process: {e}")
            return Response({"message": "Invalid activation link"}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            logger.info(f"User account with UID {uid} successfully activated.")
            return Response({"message": "Account activated successfully"}, status=status.HTTP_200_OK)

        logger.warning(f"Activation token for user with UID {uid} is invalid or expired.")
        return Response({"message": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description="Current password"),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description="New password"),
            },
            required=['old_password', 'new_password']
        ),
        responses={
            200: openapi.Response("Password changed successfully"),
            400: openapi.Response("Invalid input or validation failed"),
            401: openapi.Response("Authentication required")
        },
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <JWT Token>",
                type=openapi.TYPE_STRING
            ),
        ],
        operation_description="Change the password for the authenticated user."
    )
    def put(self, request, *args, **kwargs):
        """
        Allow the authenticated user to change their password.
        """
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            raise ValidationError({"detail": "Both 'old_password' and 'new_password' are required."})

        # Check if the old password is correct
        if not user.check_password(old_password):
            raise ValidationError({"old_password": "Old password is incorrect."})

        # Validate the new password
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            # Catch the ValidationError and return a 400 Bad Request with the error message
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Set the new password
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


# Test Protected API

class TestProtectedAPIView(APIView):

    @swagger_auto_schema(
        operation_description="Test protected endpoint",
        responses={
            200: openapi.Response("Success", openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                "message": openapi.Schema(type=openapi.TYPE_STRING)
            })),
            403: openapi.Response("Forbidden")
        }
    )
    def get(self, request):
        """
        Protected endpoint for authenticated users.
        """
        return Response({
            'message': 'You have access to this protected view!',
            'user_id': request.user.id,
            'email': request.user.email
        })


# Forgot Password
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
            }
        ),
        responses={
            200: openapi.Response("Reset link sent if the email exists"),
            400: openapi.Response("Bad Request")
        },
        operation_description="Send a password reset link to the user's email."
    )
    def post(self, request, *args, **kwargs):
        """
        Handle forgot password functionality with Amazon SES.
        """
        email = request.data.get("email")
        if not email:
            logger.warning("Email not provided in the request.")
            print("**********************")
            raise ValidationError("Email is required.")

        try:
            user = User.objects.get(email=email.lower())
            logger.info(f"User found for email: {email}")
        except User.DoesNotExist:
            logger.info(f"Attempt to reset password for non-existent email: {email}")
            # Send a generic response even if the email does not exist
            return Response({"message": "If an account exists with this email, you will receive a reset link."},
                            status=status.HTTP_200_OK)

        # Generate reset token and link
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(str(user.pk).encode())
        reset_link = f"{Reference_link}/reset-password/{uid}/{token}/"

        # Send the email via Amazon SES
        try:
            ses_client = boto3.client(
                'ses',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )

            subject = "Reset Your Password"
            body = f"""
            Hello Sir/Madam,

            You requested to reset your password. Click the link below to reset it:
            {reset_link}

            If you did not request this, please ignore this email.

            Thanks,
            TaraFirst
            """

            response = ses_client.send_email(
                Source=settings.EMAIL_HOST_USER,
                Destination={'ToAddresses': [email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )
            logger.info(f"Password reset email sent to {email} successfully.")
            return Response({"message": "If an account exists with this email, you will receive a reset link."},
                            status=status.HTTP_200_OK)

        except (BotoCoreError, ClientError) as e:
            # Log SES-related errors
            logger.error(f"SES Error: {str(e)}")
            return Response({"message": "Unable to send reset email. Please try again later."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Reset Password
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='New password'),
            }
        ),
        manual_parameters=[
            openapi.Parameter('uid', openapi.IN_PATH, description="User ID", type=openapi.TYPE_STRING),
            openapi.Parameter('token', openapi.IN_PATH, description="Reset Token", type=openapi.TYPE_STRING)
        ],
        responses={
            200: openapi.Response("Password has been successfully reset"),
            400: openapi.Response("Invalid reset link or expired token"),
        },
        operation_description="Reset user's password using token and UID."
    )
    def post(self, request, uid, token, *args, **kwargs):
        """
        Reset user password.
        """
        password = request.data.get("password")
        if not password:
            logger.warning("Password not provided in the request.")
            raise ValidationError("Password is required.")

        try:
            uid = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid)
            logger.info(f"User found for UID: {uid}")
        except (User.DoesNotExist, ValueError, TypeError) as e:
            logger.error(f"Error decoding UID or finding user: {str(e)}")
            return Response({"message": "Invalid reset link"}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.set_password(password)
            user.save()
            logger.info(f"Password successfully reset for user: {user.email}")
            return Response({"message": "Password has been successfully reset."}, status=status.HTTP_200_OK)

        logger.warning(f"Invalid or expired token for user: {user.email}")
        return Response({"message": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)


# Refresh Token
class RefreshTokenView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Refresh token obtained during login'
                ),
            },
            required=['refresh'],  # Indicate that 'refresh' is required
        ),
        responses={
            200: openapi.Response(
                description="New access token generated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Newly generated access token'
                        ),
                    }
                )
            ),
            400: openapi.Response("Invalid or missing refresh token"),
        },
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <JWT Token>",
                type=openapi.TYPE_STRING
            ),
        ],
        operation_description="Generate a new access token using a valid refresh token."
    )
    def post(self, request, *args, **kwargs):
        """
        Refresh the access token using the provided refresh token.
        """
        refresh_token = request.data.get("refresh")

        # Ensure the refresh token is provided
        if not refresh_token:
            logger.warning("Refresh token is missing from the request.")
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Validate and create a new access token
            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)
            logger.info(f"New access token generated for refresh token: {refresh_token}")
            return Response(
                {"access": new_access_token},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            # Handle invalid or expired refresh tokens
            logger.error(f"Error generating new access token: {str(e)}. Refresh token: {refresh_token}")
            return Response(
                {"detail": "Invalid refresh token.", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UsersKYCListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all user details.",
        tags=["UsersKYC"],
        responses={200: UsersKYCSerializer(many=True)},  # Specify many=True for list
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <JWT Token>",
                type=openapi.TYPE_STRING
            ),
        ]
    )
    def get(self, request):
        user_details = UserKYC.objects.all()
        serializer = UsersKYCSerializer(user_details, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Register user details (PAN, Aadhaar, ICAI number, etc.) based on user type.",
        tags=["UsersKYC"],
        request_body=UsersKYCSerializer,
        responses={
            201: "User details saved successfully.",
            400: "Invalid data",
        },
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <JWT Token>",
                type=openapi.TYPE_STRING
            ),
        ]
    )
    def post(self, request):
        try:
            if hasattr(request.user, 'userdetails'):
                return Response({"detail": "User details already exist."}, status=status.HTTP_400_BAD_REQUEST)

            request_data = request.data
            # authorizing access token from the sandbox
            access_token = authenticate()
            url = f"{SANDBOX_API_URL}/kyc/pan/verify"
            headers = {
                'Authorization': access_token,
                'x-api-key': SANDBOX_API_KEY,
                'x-api-version': SANDBOX_API_VERSION
            }
            date_field = datetime.strptime(request_data['date'], "%Y-%m-%d")
            dob = date_field.strftime("%d/%m/%Y")
            payload = {
                "@entity": "in.co.sandbox.kyc.pan_verification.request",
                "reason": "For onboarding customers",
                "pan": request_data['pan_number'],
                "name_as_per_pan": request_data['name'],
                "date_of_birth": dob,
                "consent": "Y"
            }
            pan_verification_request = requests.post(url, json=payload, headers=headers)
            pan_verification_data = pan_verification_request.json()
            category = None
            if pan_verification_data['code'] == 200 and pan_verification_data['data']['status'] == 'valid':
                serializer = UsersKYCSerializer(data=request_data,
                                                context={'request': request})  # Pass request in the context
                if serializer.is_valid():
                    serializer.save(user=request.user)  # Ensure the user is passed when saving
                    return Response({"data":serializer.data, "detail": "User details saved successfully."}, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            elif pan_verification_data['code'] != 200:
                return Response({'error_message': 'Invalid pan details, Please cross check the DOB, Pan number or Name'},
                                status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(e, exc_info=1)
            return Response({'error_message': str(e), 'status_cd': 1},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UsersKYCDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve user details by ID.",
        tags=["UsersKYC"],
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <JWT Token>",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        responses={
            200: UsersKYCSerializer,
            404: openapi.Response(description="User details not found.")
        }
    )
    def get(self, request, pk=None):
        """
        Retrieve user details by ID.
        """
        try:
            user_details = UserKYC.objects.get(pk=pk, user=request.user)
            serializer = UsersKYCSerializer(user_details)
            return Response(serializer.data)
        except UserKYC.DoesNotExist:
            raise NotFound("User details not found.")

    @swagger_auto_schema(
        operation_description="Update user details by ID.",
        tags=["UsersKYC"],
        request_body=UsersKYCSerializer,
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <JWT Token>",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        responses={
            200: openapi.Response(description="User details updated successfully."),
            400: openapi.Response(description="Invalid data."),
            404: openapi.Response(description="User details not found.")
        }
    )
    def put(self, request, pk=None):
        """
        Update user details by ID.
        """
        try:
            user_details = UserKYC.objects.get(pk=pk, user=request.user)
            serializer = UsersKYCSerializer(user_details, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"detail": "User details updated successfully."}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserKYC.DoesNotExist:
            raise NotFound("User details not found.")

    @swagger_auto_schema(
        operation_description="Delete user details by ID.",
        tags=["UsersKYC"],
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <JWT Token>",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        responses={
            204: openapi.Response(description="User details deleted successfully."),
            404: openapi.Response(description="User details not found.")
        }
    )
    def delete(self, request, pk=None):
        """
        Delete user details by ID.
        """
        try:
            user_details = UserKYC.objects.get(pk=pk, user=request.user)
            user_details.delete()
            return Response({"detail": "User details deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except UserKYC.DoesNotExist:
            raise NotFound("User details not found.")


class FirmKYCView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve the FirmKYC details of the authenticated user.",
        tags=["FirmKYC"],
        responses={
            200: FirmKYCSerializer,
            404: "FirmKYC details not found."
        },
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <JWT Token>",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ]
    )
    def get(self, request):
        """
        Retrieve FirmKYC details for the authenticated user.
        """
        try:
            firm_kyc = request.user.firmkyc
            serializer = FirmKYCSerializer(firm_kyc)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except FirmKYC.DoesNotExist:
            return Response({"detail": "FirmKYC details not found."}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Create FirmKYC details for the authenticated user.",
        tags=["FirmKYC"],
        request_body=FirmKYCSerializer,
        responses={
            201: "FirmKYC details created successfully.",
            400: "Invalid data."
        },
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <JWT Token>",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ]
    )
    def post(self, request):
        """
        Create FirmKYC details for the authenticated user.
        """
        serializer = FirmKYCSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Update FirmKYC details for the authenticated user.",
        tags=["FirmKYC"],
        request_body=FirmKYCSerializer,
        responses={
            200: "FirmKYC details updated successfully.",
            400: "Invalid data.",
            404: "FirmKYC details not found."
        },
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <JWT Token>",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ]
    )
    def put(self, request):
        """
        Update FirmKYC details for the authenticated user.
        """
        try:
            firm_kyc = request.user.firmkyc
            serializer = FirmKYCSerializer(firm_kyc, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except FirmKYC.DoesNotExist:
            return Response({"detail": "FirmKYC details not found."}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Delete FirmKYC details for the authenticated user.",
        tags=["FirmKYC"],
        responses={
            204: "FirmKYC details deleted successfully.",
            404: "FirmKYC details not found."
        },
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <JWT Token>",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ]
    )
    def delete(self, request):
        """
        Delete FirmKYC details for the authenticated user.
        """
        try:
            firm_kyc = request.user.firmkyc
            firm_kyc.delete()
            return Response({"detail": "FirmKYC details deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except FirmKYC.DoesNotExist:
            return Response({"detail": "FirmKYC details not found."}, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='patch',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email_or_mobile': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Email or Mobile Number of the user (optional).'
            ),
            'email': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Email address of the user (optional).'
            ),
            'mobile_number': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Mobile number of the user (optional).'
            ),
            'user_type': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='User type to be updated. Choices are: "individual", "cafirm", "business_or_corporate", "superuser". (optional).'
            ),
        },
        required=[],  # No required fields because any field from the serializer can be passed.
    ),
    responses={
        200: openapi.Response(
            description="User updated successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Success message'
                    ),
                }
            ),
        ),
        400: openapi.Response("Invalid data provided."),
        404: openapi.Response("User not found."),
    },
    manual_parameters=[
        openapi.Parameter(
            'Authorization',
            openapi.IN_HEADER,
            description="Bearer <JWT Token>",
            type=openapi.TYPE_STRING,
            required=True  # Make Authorization header required
        ),
    ],
    operation_description="Updates the user fields like email, mobile number, or user type of the currently authenticated user. Only the fields provided will be updated."
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])  # Ensure only authenticated users can access this endpoint
def partial_update_user(request):
    """
    Handle partial update of user profile, allowing only specified fields to be updated.
    """
    try:
        user = request.user  # Get the currently authenticated user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()  # Save the updated user data
            return Response({
                "message": "User updated successfully.",
                "data": serializer.data  # Include the updated user data in the response
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error updating user info: {str(e)}")
        return Response({"error": "An unexpected error occurred while updating user info."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class PermissionListView(APIView):
#     permission_classes = [AllowAny]
#     def get(self, request):
#         """
#         List all available permissions.
#         """
#         permissions = Permission.objects.all()
#         serializer = PermissionSerializer(permissions, many=True)
#         return Response(serializer.data)
#
#
# class GroupListCreateView(APIView):
#     """
#     Create a new group or list all groups.
#     """
#
#     def get(self, request):
#         groups = Group.objects.all()
#         serializer = GroupSerializer(groups, many=True)
#         return Response(serializer.data)
#
#     def post(self, request):
#         """
#         Create a new group.
#         """
#         serializer = GroupSerializer(data=request.data)
#         if serializer.is_valid():
#             group = serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServicesMasterDataListAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Retrieve a list of all services.",
        tags=["ServicesMasterData"],
        responses={
            200: ServicesMasterDataSerializer(many=True),
            404: "No services found."
        }
    )
    def get(self, request):
        services = ServicesMasterData.objects.all()
        if not services.exists():
            return Response({"error": "No services found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ServicesMasterDataSerializer(services, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Bulk create or add multiple services.",
        tags=["ServicesMasterData"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "services": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="List of service names to add"
                )
            }
        ),
        responses={
            201: "Services created successfully.",
            400: "Invalid data."
        }
    )
    def post(self, request):
        services = request.data.get("services", [])
        if not services or not isinstance(services, list):
            return Response({"error": "Please provide a list of service names."}, status=status.HTTP_400_BAD_REQUEST)

        created_services = []
        for service_name in services:
            service, created = ServicesMasterData.objects.get_or_create(service_name=service_name)
            if created:
                created_services.append(service_name)

        return Response(
            {
                "message": "Services created successfully.",
                "created_services": created_services
            },
            status=status.HTTP_201_CREATED
        )


class ServicesMasterDataDetailAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Retrieve details of a specific service by ID.",
        tags=["ServicesMasterData"],
        responses={
            200: ServicesMasterDataSerializer,
            404: "Service not found."
        }
    )
    def get(self, request, pk):
        try:
            service = ServicesMasterData.objects.get(pk=pk)
            serializer = ServicesMasterDataSerializer(service)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ServicesMasterData.DoesNotExist:
            return Response({"error": "Service not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Update an existing service by ID.",
        tags=["ServicesMasterData"],
        request_body=ServicesMasterDataSerializer,
        responses={
            200: "Service updated successfully.",
            400: "Invalid data.",
            404: "Service not found."
        }
    )
    def put(self, request, pk):
        try:
            service = ServicesMasterData.objects.get(pk=pk)
        except ServicesMasterData.DoesNotExist:
            return Response({"error": "Service not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ServicesMasterDataSerializer(service, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a service by ID.",
        tags=["ServicesMasterData"],
        responses={
            204: "Service deleted successfully.",
            404: "Service not found."
        }
    )
    def delete(self, request, pk):
        try:
            service = ServicesMasterData.objects.get(pk=pk)
            service.delete()
            return Response({"message": "Service deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except ServicesMasterData.DoesNotExist:
            return Response({"error": "Service not found"}, status=status.HTTP_404_NOT_FOUND)


# class VisaApplicationsAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     @swagger_auto_schema(
#         operation_description="Retrieve a list of all visa applications.",
#         responses={
#             200: openapi.Response(description="List of visa applications retrieved successfully."),
#             403: openapi.Response(description="Unauthorized access. Only ServiceProviderAdmins can view this data."),
#         },
#         manual_parameters=[
#             openapi.Parameter(
#                 'Authorization',
#                 openapi.IN_HEADER,
#                 description="Bearer <JWT Token>",
#                 type=openapi.TYPE_STRING,
#                 required=True,
#             ),
#         ],
#     )
#     def get(self, request):
#         if request.user.user_type == "ServiceProviderAdmin":
#             # Retrieve the ID of the user who created the current user
#             created_by_id = request.user.id
#             print(created_by_id)
#
#             # Filter visa applications for the user created by the current user
#             visa_applications = VisaApplications.objects.filter(user_id=created_by_id)
#             serializer = VisaApplicationsSerializer(visa_applications, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             # If the user is not a ServiceProviderAdmin, return an unauthorized response
#             return Response(
#                 {"error": "Unauthorized access. Only ServiceProviderAdmins can view this data."},
#                 status=status.HTTP_403_FORBIDDEN
#             )


class VisaApplicationDetailAPIView(APIView):
    permission_classes = [GroupPermission]
    permission_required = "VS Task View"

    @swagger_auto_schema(
        operation_description="Retrieve details of a specific visa application by ID.",
        tags=["VisaApplication"],
        responses={
            200: "Visa application details retrieved successfully.",
            404: "Visa application not found."
        },
        manual_parameters=[
                    openapi.Parameter(
                        'Authorization',
                        openapi.IN_HEADER,
                        description="Bearer <JWT Token>",
                        type=openapi.TYPE_STRING,
                        required=True,
                    ),
                ]
    )
    def get(self, request, pk):
        try:
            # visa_application = VisaApplications.objects.get(user_id=pk)
            # serializer = VisaApplicationsGetSerializer(visa_application)
            visa_applications = VisaApplications.objects.filter(user_id=pk)
            serializer = VisaClientUserListSerializer(visa_applications, many=True)
            response_data = []
            user_data_map = {}

            for visa_app in serializer.data:  # Use serializer.data to get the serialized data
                user = visa_app['email']

                if user not in user_data_map:
                    # Add user data to the map if not already added
                    user_data_map[user] = {
                        "email": visa_app['email'],
                        "mobile_number": visa_app['mobile_number'],
                        "first_name": visa_app['first_name'],
                        "last_name": visa_app['last_name'],
                        "services": [],
                        "user": visa_app['user'],
                    }

                # Check if services list is empty
                services = visa_app['services']
                if len(services) > 0:
                    for service in services:
                        user_data_map[user]["services"].append({
                            "id": service['id'],
                            "service_type": service['service_type'],
                            "service_name": service['service_name'],
                            "date": service['date'],
                            "status": service['status'],
                            "comments": service['comments'],
                            "quantity": service['quantity'],
                            "visa_application": visa_app['id'],
                            "last_updated_date": service['last_updated_date'],
                            "passport_number": visa_app['passport_number'],
                            "purpose": visa_app['purpose'],
                            "visa_type": visa_app['visa_type'],
                            "destination_country": visa_app['destination_country'],
                            'user_id': visa_app['user']
                        })
                else:
                    # If no services, add specific fields directly to user data
                    user_data_map[user].update({
                        "passport_number": visa_app['passport_number'],
                        "purpose": visa_app['purpose'],
                        "visa_type": visa_app['visa_type'],
                        "destination_country": visa_app['destination_country'],
                        'user_id': visa_app['user']
                    })

            # Convert the user data map to a list
            response_data = user_data_map[user]

            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except VisaApplications.DoesNotExist:
            return Response({"error": "Visa application not found"}, status=status.HTTP_404_NOT_FOUND)

    permission_required = "VS Task Edit"
    @swagger_auto_schema(
        operation_description="Update an existing visa application by ID.",
        tags=["VisaApplication"],
        request_body=VisaApplicationsSerializer,
        responses={
            200: "Visa application updated successfully.",
            400: "Invalid data.",
            404: "Visa application not found."
        }
    )
    def put(self, request, pk):
        try:
            visa_application = VisaApplications.objects.get(pk=pk)
        except VisaApplications.DoesNotExist:
            return Response({"error": "Visa application not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = VisaApplicationsSerializer(visa_application, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # For DELETE
    permission_required = "VS Task Delete"  # Define the required permission for DELETE method
    @swagger_auto_schema(
        operation_description="Delete a visa application by ID.",
        tags=["VisaApplication"],
        responses={
            204: "Visa application deleted successfully.",
            404: "Visa application not found."
        }
    )
    def delete(self, request, pk):
        try:
            visa_application = VisaApplications.objects.get(pk=pk)
            visa_application.delete()
            return Response({"message": "Visa application deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except VisaApplications.DoesNotExist:
            return Response({"error": "Visa application not found"}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='post',
    operation_description="Create a new visa application or add multiple services to an existing visa application.",
    tags=["VisaApplication"],
    manual_parameters=[
        openapi.Parameter(
            'Authorization',
            openapi.IN_HEADER,
            description="Bearer <JWT Token>",
            type=openapi.TYPE_STRING,
            required=True,  # Mark as required
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="ID of the user creating the visa application (required for creating a new visa application)."
            ),
            'passport_number': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Passport number of the applicant (required for creating a new visa application)."
            ),
            'purpose': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Purpose of the visa application (required for creating a new visa application)."
            ),
            'visa_type': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Type of visa (required for creating a new visa application)."
            ),
            'destination_country': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Destination country for the visa application (required for creating a new visa application)."
            ),
            'services': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'service_type': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Type of the service (e.g., Visa Stamping, Processing)."
                        ),
                        'comments': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Comments or additional information about the service."
                        ),
                        'quantity': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Quantity of the service."
                        )
                    },
                    required=['service_type', 'quantity']  # Required properties for each service
                ),
                description="List of services to add to the visa application (optional)."
            )
        },
        required=['user_id', 'passport_number', 'purpose', 'visa_type', 'destination_country'],  # Mandatory fields for new visa application
    ),
    responses={
        201: openapi.Response(
            description="Successfully created a new visa application or added services.",
            examples={
                "application/json": {
                    "message": "Visa application and services added successfully."
                }
            }
        ),
        400: openapi.Response(
            description="Invalid data provided.",
            examples={
                "application/json": {
                    "error": "Missing required fields. Provide 'user_id', 'passport_number', 'purpose', 'visa_type', and 'destination_country'."
                }
            }
        ),
        401: openapi.Response(
            description="Unauthorized access.",
            examples={
                "application/json": {
                    "error_message": "Unauthorized Access. Only Service Providers with roles (ServiceProvider_Admin, Individual_User) can add visa users.",
                    "status_cd": 1
                }
            }
        ),
        500: openapi.Response(
            description="Internal server error.",
            examples={
                "application/json": {
                    "error": "An internal error occurred. Please try again later."
                }
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])  # Add 'GroupPermission' if necessary for handling role-based permission
@has_group_permission('VS Task Create')
def manage_visa_applications(request):
    try:
        # Authorization check
        if request.user.user_role not in ["ServiceProvider_Admin", "Individual_User"] or request.user.user_type != "ServiceProvider":
            return Response(
                {
                    'error_message': 'Unauthorized Access. Only Service Providers with roles '
                                     '(ServiceProvider_Admin, Individual_User) can add visa users.',
                    'status_cd': 1
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Extract required fields from request data
        user_id = request.data.get('user_id')
        passport_number = request.data.get('passport_number', '')
        purpose = request.data.get('purpose')
        visa_type = request.data.get('visa_type')
        destination_country = request.data.get('destination_country')


        # Validate required fields
        if not all([user_id, purpose, visa_type, destination_country]):
            return Response(
                {"error": "Missing required fields. Provide 'user_id', "
                          "'purpose', 'visa_type', and 'destination_country'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the visa application already exists
        visa_applications = VisaApplications.objects.filter(
            visa_type=visa_type, user_id=user_id, purpose=purpose, destination_country=destination_country
        )
        if visa_applications.exists():
            visa_application = visa_applications.first()
        else:
            # Create a new visa application
            visa_data = {
                'user': user_id,
                'passport_number': passport_number,
                'purpose': purpose,
                'visa_type': visa_type,
                'destination_country': destination_country
            }
            visa_serializer = VisaApplicationsSerializer(data=visa_data)
            if visa_serializer.is_valid():
                visa_serializer.save()
                visa_application = VisaApplications.objects.get(id=visa_serializer.data['id'])
            else:
                return Response(visa_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Process services data
        services_data = request.data.get('services', [])
        if services_data:
            for service in services_data:
                service['visa_application'] = visa_application.id
                service_serializer = ServiceDetailsSerializer(data=service)
                if service_serializer.is_valid():
                    service_serializer.save()
                else:
                    return Response(service_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Visa application and services added successfully."}, status=status.HTTP_201_CREATED)

        return Response(
            {"error": "No services provided. Provide 'services' data to add to the visa application."},
            status=status.HTTP_400_BAD_REQUEST
        )

    except Exception as e:
        logger.error(f"Error managing visa applications: {str(e)}", exc_info=True)
        return Response({"error": "An internal error occurred. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@swagger_auto_schema(
    methods=['get'],
    operation_description="Retrieve a list of all visa clients with their applications.",
    tags=["VisaApplicantsList"],
    responses={
        200: VisaClientUserListSerializer(many=True),
        403: "Unauthorized Access. Only Service Provider Admins can access this resource."
    },
    manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <JWT Token>",
                type=openapi.TYPE_STRING,
            ),
        ],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@has_group_permission('VS Task View')
def get_visa_clients_users_list(request):
    try:
        # Check if the user is a ServiceProvider_Admin with the correct type
        print("****************")
        if request.user.user_role == "ServiceProvider_Admin" and request.user.user_type == "ServiceProvider":
            # Get all users created by the current ServiceProviderAdmin
            created_by_id = request.user.id
            users = User.objects.filter(created_by=created_by_id)

            # Retrieve VisaApplications for these users
            visa_applications = VisaApplications.objects.filter(user__in=users)
            serializer = VisaClientUserListSerializer(visa_applications, many=True)

        elif request.user.user_role == "Individual_User" and request.user.user_type == "ServiceProvider":
            visa_applications = VisaApplications.objects.filter(user=request.user)
            serializer = VisaClientUserListSerializer(visa_applications, many=True)

        else:
            return Response({"error": "Unauthorized access."}, status=status.HTTP_403_FORBIDDEN)

        # Grouping visa applications and services by user
        response_data = []
        user_data_map = {}

        for visa_app in serializer.data:  # Use serializer.data to get the serialized data
            user = visa_app['email']

            if user not in user_data_map:
                # Add user data to the map if not already added
                user_data_map[user] = {
                    "email": visa_app['email'],
                    "mobile_number": visa_app['mobile_number'],
                    "first_name": visa_app['first_name'],
                    "last_name": visa_app['last_name'],
                    "services": [],
                    "user": visa_app['user'],
                }

            # Check if services list is empty
            services = visa_app['services']
            if len(services) > 0:
                for service in services:
                    user_data_map[user]["services"].append({
                        "id": service['id'],
                        "service_type": service['service_type'],
                        "service_name": service['service_name'],
                        "date": service['date'],
                        "status": service['status'],
                        "comments": service['comments'],
                        "quantity": service['quantity'],
                        "visa_application": visa_app['id'],
                        "last_updated_date": service['last_updated_date'],
                        "passport_number": visa_app['passport_number'],
                        "purpose": visa_app['purpose'],
                        "visa_type": visa_app['visa_type'],
                        "destination_country": visa_app['destination_country'],
                        'user_id': visa_app['user']
                    })
            else:
                # If no services, add specific fields directly to user data
                user_data_map[user].update({
                    "passport_number": visa_app['passport_number'],
                    "purpose": visa_app['purpose'],
                    "visa_type": visa_app['visa_type'],
                    "destination_country": visa_app['destination_country'],
                    'user_id': visa_app['user']
                })

        # Convert the user data map to a list
        response_data = list(user_data_map.values())

        return Response(response_data, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    except VisaApplications.DoesNotExist:
        return Response({"error": "No visa applications found."}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@swagger_auto_schema(
    methods=['get'],
    operation_description="Retrieve a list of all visa clients with their applications and "
                          "count the services based on status (progress, in progress, completed).",
    tags=["VisaApplicantsOverallStatus"],
    responses={
        200: openapi.Response(
            description="Counts of services based on status.",
            examples={
                "application/json": {
                    "progress": 1,
                    "in_progress": 0,
                    "completed": 0
                }
            }
        ),
        403: "Unauthorized Access. Only Service Provider Admins can access this resource."
    },
    manual_parameters=[
        openapi.Parameter(
            'Authorization',
            openapi.IN_HEADER,
            description="Bearer <JWT Token>",
            type=openapi.TYPE_STRING,
        ),
    ],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def service_status(request):
    try:
        # Check if the user has the appropriate role and type
        if request.user.user_role in ["ServiceProvider_Admin", "Individual_User"] and request.user.user_type == "ServiceProvider":
            # Determine the users and VisaApplications based on the role
            if request.user.user_role == "ServiceProvider_Admin":
                created_by_id = request.user.id
                users = User.objects.filter(created_by=created_by_id)
                visa_applications = VisaApplications.objects.filter(user__in=users)
            elif request.user.user_role == "Individual_User":
                visa_applications = VisaApplications.objects.filter(user=request.user)

            # Serialize the VisaApplications data
            serializer = VisaClientUserListSerializer(visa_applications, many=True)

            # Initialize counters and data containers
            counts = {
                'pending': 0,
                'pending_data': [],
                'in_progress': 0,
                'in_progress_data': [],
                'completed': 0,
                'completed_data': []
            }

            # Process each serialized item
            for item in serializer.data:
                for service in item['services']:
                    service_data = {
                        'service_id': service['id'],
                        'visa_applicant_name': item['first_name'] + ' ' + item['last_name'],
                        'service_type': service['service_type'],
                        'service_name': service['service_name'],
                        'comments': service.get('comments', ''),
                        'quantity': service.get('quantity', 0),
                        'date': service.get('date', ''),
                        'status': service['status'],
                        'passport_number': item.get('passport_number'),
                        'visa_type': item.get('visa_type'),
                        'destination_country': item.get('destination_country'),
                        'purpose': item.get('purpose'),
                        'user': item.get('user')
                    }

                    # Categorize based on the service status
                    if service['status'] == 'pending':
                        counts['pending'] += 1
                        counts['pending_data'].append(service_data)
                    elif service['status'] == 'in progress':
                        counts['in_progress'] += 1
                        counts['in_progress_data'].append(service_data)
                    elif service['status'] == 'completed':
                        counts['completed'] += 1
                        counts['completed_data'].append(service_data)

            return Response(counts, status=status.HTTP_200_OK)

        # If user is unauthorized
        return Response({"error": "Unauthorized access."}, status=status.HTTP_403_FORBIDDEN)

    except User.DoesNotExist:
        # Handle the case where the user is not found
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    except VisaApplications.DoesNotExist:
        # Handle the case where visa applications are not found
        return Response({"error": "No visa applications found."}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        # Handle other unexpected errors
        return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def parse_last_updated_date(last_updated):
    """
    Helper function to parse the last_updated field.
    """
    try:
        # Parse the string to a datetime object using strptime
        return datetime.strptime(last_updated, '%Y-%m-%dT%H:%M:%S.%fZ').date()
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing last_updated: {e}")
        # Return an empty string if the date parsing fails
        return ''


def collect_service_data(serializer_data, user_role):
    """
    Helper function to collect and format service data.
    """
    all_services = []
    for item in serializer_data:
        if user_role == 'Individual_User':
            if not item['services']:
                service_data = {
                    'email': item.get('email'),
                    'mobile_number': item.get('mobile_number'),
                    'passport_number': item.get('passport_number'),
                    'visa_type': item.get('visa_type'),
                    'destination_country': item.get('destination_country'),
                    'purpose': item.get('purpose'),
                    'first_name': item['first_name'],
                    'last_name': item['last_name'],
                    'user': item.get('user')
                }
                all_services = service_data

        for service in item['services']:
            try:
                last_updated_date = parse_last_updated_date(service.get('last_updated'))
                service_data = {
                    'email': item.get('email'),
                    'mobile_number': item.get('mobile_number'),
                    'passport_number': item.get('passport_number'),
                    'visa_type': item.get('visa_type'),
                    'destination_country': item.get('destination_country'),
                    'purpose': item.get('purpose'),
                    'id': service['id'],
                    'service_type': service['service_type'],
                    'service_name': service['service_name'],
                    'first_name': item['first_name'],
                    'last_name': item['last_name'],
                    'comments': service.get('comments', ''),
                    'quantity': service.get('quantity', 0),
                    'date': service.get('date', ''),
                    'last_updated': last_updated_date,
                    'status': service['status'],
                    'passport': item.get('passport_number'),
                    'user': item.get('user')
                }
                all_services.append(service_data)
            except KeyError as e:
                logger.error(f"Missing key in service data: {e}")
                return {"error": f"Missing key in service data: {e}"}, False
            except Exception as e:
                logger.error(f"Unexpected error while processing service data: {e}")
                return {"error": f"Unexpected error: {e}"}, False
    return all_services, True

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all service data irrespective of their statuses"
                          " (pending, in-progress, completed, etc.) for "
                          "Visa Applications under the logged-in ServiceProviderAdmin.",
    tags=["VisaApplicantsAllTasks"],
    responses={
        200: openapi.Response(
            description="A list of all services.",
            examples={
                "application/json": [
                    {
                        "service_id": 1,
                        "service_type": "Visa Renewal",
                        "service_name": "Renewal Service",
                        "visa_application_name": "John Doe",
                        "comments": "Urgent processing required",
                        "quantity": 1,
                        "date": "2024-12-11",
                        "status": "in_progress"
                    },
                    {
                        "service_id": 2,
                        "service_type": "New Visa",
                        "service_name": "New Application Service",
                        "visa_application_name": "Jane Smith",
                        "comments": "",
                        "quantity": 1,
                        "date": "2024-12-10",
                        "status": "completed"
                    }
                ]
            }
        ),
        403: openapi.Response("Unauthorized access."),
    },
    manual_parameters=[
        openapi.Parameter(
            'Authorization',
            openapi.IN_HEADER,
            description="Bearer <JWT Token>",
            type=openapi.TYPE_STRING,
            required=True
        )
    ]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_service_data(request):
    user_role = request.user.user_role

    try:
        if user_role == "ServiceProvider_Admin":
            # Get all VisaApplications for the current ServiceProviderAdmin
            created_by_id = request.user.id
            users = User.objects.filter(created_by=created_by_id)
            visa_applications = VisaApplications.objects.filter(user__in=users)

        elif user_role == "Individual_User":
            # Get all VisaApplications for the current Individual User
            user_id = request.user.id
            visa_applications = VisaApplications.objects.filter(user=user_id)

        else:
            return Response(
                {"error": "Unauthorized access."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Serialize the data
        serializer = VisaClientUserListSerializer(visa_applications, many=True)

        # Collect and format all services data
        all_services, success = collect_service_data(serializer.data, user_role)
        if not success:
            return Response(all_services, status=status.HTTP_400_BAD_REQUEST)

        return Response(all_services, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Unexpected error in all_service_data: {e}")
        return Response(
            {"error": f"An unexpected error occurred: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


auth_header = openapi.Parameter(
    'Authorization',
    in_=openapi.IN_HEADER,
    description="Bearer <JWT Token>",
    type=openapi.TYPE_STRING,
    required=True
)

class ServiceDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def has_permission(self, user):
        """
        Check if the user has the required role and type.
        """
        return (
                user.user_role in ['ServiceProvider_Admin', 'Individual_User'] and
                user.user_type == 'ServiceProvider'
        )

    @swagger_auto_schema(
        operation_description="Retrieve a specific ServiceDetails instance by ID.",
        tags=["VisaServiceTasks"],
        manual_parameters=[auth_header],
        responses={
            200: ServiceDetailsSerializer(),
            401: "Unauthorized - Missing or invalid token.",
            404: "Service not found.",
        },
    )
    def get(self, request, pk):
        """Retrieve a specific ServiceDetails instance by ID."""
        print("****")
        if not self.has_permission(request.user):
            return Response(
                {"error": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        service = get_object_or_404(ServiceDetails, pk=pk)
        serializer = ServiceDetailsSerializer(service)
        return Response(serializer.data, status=status.HTTP_200_OK)

    request_body = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'visa_application': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'passport_number': openapi.Schema(type=openapi.TYPE_STRING),
                    'purpose': openapi.Schema(type=openapi.TYPE_STRING),
                    'visa_type': openapi.Schema(type=openapi.TYPE_STRING),
                    'destination_country': openapi.Schema(type=openapi.TYPE_STRING)
                },
                required=['user', 'passport_number', 'purpose', 'visa_type', 'destination_country']
            ),
            'service': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'service_type_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'date': openapi.Schema(type=openapi.FORMAT_DATETIME),
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'comments': openapi.Schema(type=openapi.TYPE_STRING),
                    'quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'last_updated': openapi.Schema(type=openapi.FORMAT_DATETIME),
                },
                required=['id', 'service_type_id', 'date', 'status', 'comments', 'quantity', 'last_updated']
            ),
        },
        required=['visa_application', 'service']
    )

    @swagger_auto_schema(
        operation_description="Partially update a specific ServiceDetails instance (partial=True).",
        tags=["VisaServiceTasks"],
        manual_parameters=[auth_header],
        request_body=request_body,
        responses={
            200: ServiceDetailsSerializer(),
            400: "Validation error.",
            401: "Unauthorized - Missing or invalid token.",
            404: "Service not found.",
        },
    )
    def put(self, request, pk):
        """Partially update a specific ServiceDetails instance (partial=True)."""
        if not self.has_permission(request.user):
            return Response(
                {"error": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        # service = get_object_or_404(ServiceDetails, pk=pk)
        service = ServiceDetails.objects.get(id=pk)

        visa_data = request.data.get('visa_application', {})
        # Check if the VisaApplication exists
        user_id = visa_data.get('user')
        passport_number= visa_data.get('passport_number', '')
        purpose= visa_data.get('purpose')
        visa_type = visa_data.get('visa_type')
        destination_country = visa_data.get('destination_country')
        visa_application = VisaApplications.objects.filter(
            user_id=visa_data.get('user'),
            purpose=visa_data.get('purpose'),
            visa_type=visa_data.get('visa_type'),
            destination_country=visa_data.get('destination_country')
        ).first()
        if visa_application:
            # Update existing VisaApplication with provided data
            service_data = request.data.get('service', {})
            service_data['visa_application'] = visa_application.id  # Set the existing visa application ID
        else:
            visa_data['passport_number'] = passport_number
            visa_application_serializer = VisaApplicationsSerializer(data=visa_data)
            if visa_application_serializer.is_valid():
                visa_application_ = visa_application_serializer.save()
                service_data = request.data.get('service', {})
                service_data['visa_application'] = visa_application_.id
            else:
                return Response(visa_application_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                # Update the ServiceDetails instance
        service = get_object_or_404(ServiceDetails, id=request.data.get('service').get('id'))
        serializer = ServiceDetailsSerializer(service, data=service_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a specific ServiceDetails instance by ID.",
        tags=["VisaServiceTasks"],
        manual_parameters=[auth_header],
        responses={
            204: "Service deleted successfully.",
            401: "Unauthorized - Missing or invalid token.",
            404: "Service not found.",
        },
    )
    def delete(self, request, pk):
        """Delete a specific ServiceDetails instance."""
        if not self.has_permission(request.user):
            return Response(
                {"error": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        service = get_object_or_404(ServiceDetails, pk=pk)
        service.delete()
        return Response({"message": "Service deleted successfully."}, status=status.HTTP_204_NO_CONTENT)