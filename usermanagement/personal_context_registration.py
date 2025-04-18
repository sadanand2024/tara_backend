from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import logging

from models import (
    Users, Context, Role, UserContextRole, Module,
    ModuleFeature, UserFeaturePermission, SubscriptionPlan, ModuleSubscription, Business, UserKYC
)


# Configure logging
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_personal_context(request):
    """
    Create a new personal context with KYC information.

    Expected request data:
    {
        "user_id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "name": "John Doe",
        "pan_number": "ABCDE1234F",
        "aadhaar_number": "123456789012",
        "date": "1990-01-01",
        "icai_number": "ICAI123456",
        "have_firm": true,
        "address": {
            "address_line1": "123 Main St",
            "address_line2": "Apt 4B",
            "state": "New York",
            "city": "New York City",
            "country": "USA",
            "pincode": "10001"
        }
    }
    """
    # Extract data from request
    user_id = request.data.get('user_id')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')

    # Extract KYC data
    name = request.data.get('name')
    pan_number = request.data.get('pan_number')
    aadhaar_number = request.data.get('aadhaar_number')
    date = request.data.get('date')
    icai_number = request.data.get('icai_number')
    have_firm = request.data.get('have_firm', False)
    address = request.data.get('address')

    # Validate required fields
    if not all([user_id, first_name, last_name, name, pan_number, aadhaar_number, date]):
        return Response(
                {"error": "Missing required fields. Please provide user_id, first_name, last_name, name, pan_number, aadhaar_number, and date."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate address if provided
    if address:
        required_address_fields = ['address_line1', 'state', 'city', 'country']
        missing_fields = [field for field in required_address_fields if not address.get(field)]
        if missing_fields:
            return Response(
                {"error": f"Missing required address fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    try:
        with transaction.atomic():
            # Get user
            try:
                user = Users.objects.get(id=user_id)
            except Users.DoesNotExist:
                return Response(
                    {"error": "User not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if user is active
            if user.is_active != 'yes':
                return Response(
                    {"error": "User account is not active. Please activate your account first."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check if user already has a KYC record
            try:
                existing_kyc = UserKYC.objects.get(user=user)
                return Response(
                    {"error": "User already has a KYC record."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except UserKYC.DoesNotExist:
                pass

            # Update user details
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            # Create user KYC record first
            user_kyc = UserKYC.objects.create(
                user=user,
                name=name,
                pan_number=pan_number,
                aadhaar_number=aadhaar_number,
                date=date,
                icai_number=icai_number if have_firm else None,
                have_firm=have_firm,
                address=address
            )

            # Create personal context
            context = Context.objects.create(
                name=f"{first_name}'s Personal Context",
                context_type='personal',
                owner_user=user,
                status='active',
                profile_status='complete',
                metadata={
                    'kyc_id': user_kyc.id,
                    'kyc_completed': user_kyc.is_completed
                }
            )

            # Create owner role for the personal context
            owner_role = Role.objects.get(
                context=context,
                role_type='owner'
            )

            # Assign user to context with owner role
            user_context_role = UserContextRole.objects.create(
                user=user,
                context=context,
                role=owner_role,
                status='active',
                added_by=user
            )

            return Response({
                "message": "Personal context created successfully",
                "context_id": context.id,
                "kyc_id": user_kyc.id,
                "kyc_completed": user_kyc.is_completed,
                "context_type": "personal"
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating personal context: {str(e)}")
        return Response(
            {"error": f"An error occurred while creating the personal context: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )