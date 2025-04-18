from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
import boto3
from botocore.exceptions import ClientError
import logging
from Tara.settings.default import *

from .models import (
    Users, Context, Role, UserContextRole, Module,
    ModuleFeature, UserFeaturePermission, SubscriptionPlan, ModuleSubscription
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

# Configure logging
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_business(request):
    """
    Register a new business user with a module subscription and full feature permissions.

    Expected request data:
    {
        "email": "user@example.com",
        "password": "securepassword",
        "business_name": "My Business",
        "module_id": 1
    }
    """
    # Extract data from request
    email = request.data.get('email')
    password = request.data.get('password')
    business_name = request.data.get('business_name')
    module_id = request.data.get('module_id')

    # Validate required fields
    if not all([email, password, business_name, module_id]):
        return Response(
            {"error": "Missing required fields. Please provide email, password, business_name, and module_id."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Use transaction to ensure all operations succeed or fail together
        with transaction.atomic():
            # 1. Create user
            user = Users.objects.create_user(
                email=email,
                password=password,
                status='active',
                registration_flow='module',  # Set registration flow to 'module'
                registration_completed=False,
                is_active='no'  # Set is_active to 'yes'
            )

            # 2. Create business context
            context = Context.objects.create(
                name=business_name,
                context_type='business',
                owner_user=user,
                status='active',
                profile_status='complete'
            )

            # 3. Set active_context_id for the user
            user.active_context = context
            user.save()

            # 4. Get the module
            module = Module.objects.get(id=module_id)

            # 5. Set initial_selection to the module name
            user.initial_selection = module.name
            user.save()

            # 6. Get or create owner role for this context
            owner_role = Role.objects.get(
                context=context,
                role_type='owner'
            )

            # 7. Create user context role (owner)
            user_context_role = UserContextRole.objects.create(
                user=user,
                context=context,
                role=owner_role,
                status='active',
                added_by=user  # Self-registered
            )

            # 8. Get or create a trial subscription plan for this module
            trial_plan, created = SubscriptionPlan.objects.get_or_create(
                module=module,
                plan_type="trial",
                is_active="yes"

            )

            # 9. Create module subscription (trial)
            end_date = timezone.now() + relativedelta(days=30)
            module_subscription = ModuleSubscription.objects.create(
                context=context,
                module=module,
                plan=trial_plan,
                status='trial',
                start_date=timezone.now(),
                end_date=end_date,
                auto_renew='no'  # Don't auto-renew trial
            )

            # 10. Get all features for this module
            module_features = ModuleFeature.objects.filter(module=module)

            # 11. Create a single user feature permission with all actions
            # Collect all unique service.action combinations
            all_actions = []
            for feature in module_features:
                action = f"{feature.service}.{feature.action}"
                if action not in all_actions:
                    all_actions.append(action)

            # Create a single user feature permission with all actions
            UserFeaturePermission.objects.create(
                user_context_role=user_context_role,
                module=module,
                actions=all_actions,  # All service.action combinations
                is_active="yes",
                created_by=user  # Set the created_by field to the user being registered
            )

            # 12. Send activation email - This is a required step
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(str(user.pk).encode())
            activation_link = f"{FRONTEND_URL}activation?uid={uid}&token={token}"

            # Initialize SES client
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
                # Send the email
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

                # Return success response with activation information
                return Response(
                    {
                        "message": "Business registration successful. Check your email for activation link.",
                        "user_id": user.id,
                        "context_id": context.id,
                        "module_subscription_id": module_subscription.id,
                        "trial_end_date": end_date,
                        "active_context_id": user.active_context.id,
                        "initial_selection": user.initial_selection,
                        "registration_flow": user.registration_flow
                    },
                    status=status.HTTP_201_CREATED
                )
            except ClientError as e:
                # Log the error but don't fail the registration
                logger.error(f"Failed to send email via SES: {e.response['Error']['Message']}")

                # Return success response but note the email failure
                return Response(
                    {
                        "message": "Business registration successful, but failed to send activation email. "
                                   "Please contact support.",
                        "user_id": user.id,
                        "context_id": context.id,
                        "module_subscription_id": module_subscription.id,
                        "trial_end_date": end_date,
                        "activation_link": activation_link,  # Include the activation link in the response
                        "active_context_id": user.active_context.id,
                        "initial_selection": user.initial_selection,
                        "registration_flow": user.registration_flow
                    },
                    status=status.HTTP_201_CREATED
                )

    except Module.DoesNotExist:
        return Response(
            {"error": f"Module with ID {module_id} does not exist."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Registration failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_another_context(request):
    """
    Add another context to an existing user. The user will be the owner of the new context.

    Expected request data:
    {
        "business_name": "My New Business",
        "module_id": 1,
        "subscription_plan_id": 123,  # Optional: If not provided, a free trial will be created
        "user_id": 456  # Optional: If not provided, the authenticated user will be used
    }
    """
    # Extract data from request
    business_name = request.data.get('business_name')
    module_id = request.data.get('module_id')
    subscription_plan_id = request.data.get('subscription_plan_id')
    user_id = request.data.get('user_id')
    authenticated_user = request.user  # Get the authenticated user

    # Validate required fields
    if not all([business_name, module_id]):
        return Response(
            {"error": "Missing required fields. Please provide business_name and module_id."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Determine which user to use
        if user_id:
            # Check if the authenticated user has permission to add context for another user
            # This is a simple check - you might want to implement more sophisticated permission logic
            # if not authenticated_user.is_staff and not authenticated_user.is_superuser:
            #     return Response(
            #         {"error": "You don't have permission to add a context for another user."},
            #         status=status.HTTP_403_FORBIDDEN
            #     )

            # Get the specified user
            try:
                user = Users.objects.get(id=user_id)
            except Users.DoesNotExist:
                return Response(
                    {"error": f"User with ID {user_id} does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Use the authenticated user
            user = authenticated_user

        # Use transaction to ensure all operations succeed or fail together
        with transaction.atomic():
            # 1. Create business context
            context = Context.objects.create(
                name=business_name,
                context_type='business',
                owner_user=user,
                status='active',
                profile_status='complete'
            )

            # 2. Get or create owner role for this context
            owner_role = Role.objects.get(
                context=context,
                role_type='owner'
            )

            # 3. Create user context role (owner)
            user_context_role = UserContextRole.objects.create(
                user=user,
                context=context,
                role=owner_role,
                status='active',
                added_by=authenticated_user  # The user who is performing the action
            )

            # 4. Get the module
            module = Module.objects.get(id=module_id)

            # 5. Determine which subscription plan to use
            if subscription_plan_id:
                # User provided a subscription plan ID
                try:
                    subscription_plan = SubscriptionPlan.objects.get(id=subscription_plan_id)
                    subscription_type = 'paid'
                    auto_renew = request.data.get('auto_renew', False)
                except SubscriptionPlan.DoesNotExist:
                    return Response(
                        {"error": f"Subscription plan with ID {subscription_plan_id} does not exist."},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # No subscription plan provided, create a trial
                subscription_plan, created = SubscriptionPlan.objects.get_or_create(
                    module=module,
                    plan_type="trial",
                    is_active="yes"
                )
                subscription_type = 'trial'
                auto_renew = False

            # 6. Create module subscription
            if subscription_type == 'trial':
                end_date = timezone.now() + relativedelta(days=30)
                subscription_status = 'trial'
            else:
                # For paid subscriptions, use the plan's billing cycle
                end_date = timezone.now() + relativedelta(days=subscription_plan.billing_cycle_days)
                subscription_status = 'active'

            module_subscription = ModuleSubscription.objects.create(
                context=context,
                module=module,
                plan=subscription_plan,
                status=subscription_status,
                start_date=timezone.now(),
                end_date=end_date,
                auto_renew=auto_renew
            )

            # 7. Get all features for this module
            module_features = ModuleFeature.objects.filter(module=module)

            # 8. Create a single user feature permission with all actions
            # Collect all unique service.action combinations
            all_actions = []
            for feature in module_features:
                action = f"{feature.service}.{feature.action}"
                if action not in all_actions:
                    all_actions.append(action)

            # Create a single user feature permission with all actions
            UserFeaturePermission.objects.create(
                user_context_role=user_context_role,
                module=module,
                actions=all_actions,  # All service.action combinations
                is_active="yes",
                created_by=authenticated_user  # The user who is performing the action
            )

            # Return success response
            return Response(
                {
                    "message": f"New business context added successfully with {subscription_type} subscription.",
                    "user_id": user.id,
                    "context_id": context.id,
                    "module_subscription_id": module_subscription.id,
                    "subscription_type": subscription_type,
                    "subscription_plan_id": subscription_plan.id,
                    "subscription_plan_name": subscription_plan.name,
                    "end_date": end_date,
                    "auto_renew": auto_renew,
                    "active_context_id": user.active_context.id if user.active_context else None
                },
                status=status.HTTP_201_CREATED
            )

    except Module.DoesNotExist:
        return Response(
            {"error": f"Module with ID {module_id} does not exist."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to add new context: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



