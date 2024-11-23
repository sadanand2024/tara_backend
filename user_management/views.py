from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import UserRegistrationSerializer, UserDetailsSerializer, UserActivationSerializer
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
from .models import User, UserDetails
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
import logging
import random
import requests
import json
from Tara.settings.default import *

# Create loggers for general and error logs
logger = logging.getLogger('django')
error_logger = logging.getLogger('error_logger')


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
                    activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"

                    send_mail(
                        subject="Activate your account",
                        message=f"Activate your account using the link: {activation_link}",
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[email],
                    )
                    logger.info(f"Activation email sent to: {email}")
                    return Response(
                        {"message": "User registered. Check your email for activation link."},
                        status=status.HTTP_201_CREATED,
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
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            error_logger.error(f"Integrity error during registration: {str(e)}")
            return Response({"error": "A user with this email or mobile number already exists."},
                            status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            error_logger.error(f"Database error during registration: {str(e)}")
            return Response({"error": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            error_logger.error(f"Unexpected error during registration: {str(e)}")
            return Response({"error": "An unexpected error occurred.", "details": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Activate User

class ActivateUserView(APIView):
    """
    View for activating user accounts using UID and token.
    """

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'uid', openapi.IN_PATH, description="User ID (Base64 encoded)", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'token', openapi.IN_PATH, description="Activation token", type=openapi.TYPE_STRING
            )
        ],
        responses={
            200: openapi.Response("Account activated successfully"),
            400: openapi.Response("Invalid or expired activation link"),
        },
        operation_description="Activate user account using UID and token."
    )
    def get(self, request, uid, token):
        """
        Handle user account activation.
        """
        try:
            uid = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid)
        except (ValueError, TypeError, User.DoesNotExist):
            return Response({"message": "Invalid activation link"}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({"message": "Account activated successfully"}, status=status.HTTP_200_OK)

        return Response({"message": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)


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
        Handle forgot password functionality.
        """
        email = request.data.get("email")
        if not email:
            raise ValidationError("Email is required.")
        try:
            user = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            return Response({"message": "If an account exists with this email, you will receive a reset link."},
                            status=status.HTTP_200_OK)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(str(user.pk).encode())
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

        send_mail(
            subject="Reset Your Password",
            message=f"Click on the following link to reset your password: {reset_link}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
        )

        return Response({"message": "If an account exists with this email, you will receive a reset link."},
                        status=status.HTTP_200_OK)


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
            raise ValidationError("Password is required.")
        try:
            uid = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"message": "Invalid reset link"}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.set_password(password)
            user.save()
            return Response({"message": "Password has been successfully reset."}, status=status.HTTP_200_OK)
        return Response({"message": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)


# Refresh Token
class RefreshTokenView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
            }
        ),
        responses={
            200: openapi.Response("New access token generated"),
            400: openapi.Response("Invalid refresh token"),
        },
        operation_description="Generate a new access token using a refresh token."
    )
    def post(self, request, *args, **kwargs):
        """
        Refresh the access token using the refresh token.
        """
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)
            return Response({"token": new_access_token}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)


class UserDetailsListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all user details.",
        responses={200: UserDetailsSerializer(many=True)}
    )
    def get(self, request):
        user_details = UserDetails.objects.all()
        serializer = UserDetailsSerializer(user_details, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Register user details.",
        request_body=UserDetailsSerializer,
        responses={201: "User details saved successfully.", 400: "Invalid data."}
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
            payload = {
                "@entity": "in.co.sandbox.kyc.pan_verification.request",
                "reason": "For onboarding customers",
                "pan": request_data['pan_number'],
                "name_as_per_pan": request_data['user_name'],
                "date_of_birth": request_data['dob']
            }
            pan_verification_request = requests.post(url, json=payload, headers=headers)
            pan_verification_data = pan_verification_request.json()
            category = None
            if pan_verification_data['code'] == 200 and pan_verification_data['data']['status'] == 'valid':
                serializer = UserDetailsSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save(user=request.user)
                    return Response({"detail": "User details saved successfully."}, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            elif pan_verification_data['code'] != 200:
                return Response({'error_message': 'Invalid pan details, Please cross check the DOB, Pan number or Name'},
                                status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(e, exc_info=1)
            return Response({'error_message': str(e), 'status_cd': 1},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailsDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve user details.",
        responses={200: UserDetailsSerializer, 404: "User details not found."}
    )
    def get(self, request):
        try:
            user_details = request.user.userdetails
            serializer = UserDetailsSerializer(user_details)
            return Response(serializer.data)
        except UserDetails.DoesNotExist:
            return Response({"detail": "User details not found."}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Update user details.",
        request_body=UserDetailsSerializer,
        responses={200: "User details updated successfully.", 400: "Invalid data.", 404: "User details not found."}
    )
    def put(self, request):
        try:
            user_details = request.user.userdetails
            serializer = UserDetailsSerializer(user_details, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"detail": "User details updated successfully."}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserDetails.DoesNotExist:
            return Response({"detail": "User details not found."}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Delete user details.",
        responses={204: "User details deleted successfully.", 404: "User details not found."}
    )
    def delete(self, request):
        try:
            user_details = request.user.userdetails
            user_details.delete()
            return Response({"detail": "User details deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except UserDetails.DoesNotExist:
            return Response({"detail": "User details not found."}, status=status.HTTP_404_NOT_FOUND)