# Standard library imports
import datetime
from urllib.parse import urlparse

# Third-party imports
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

# Local application imports
from .email_otp_request_service import send_otp_email
from .helpers import generate_otp
from .models import (
    Module,
    PendingUserOTP,
    Role,
    SubscriptionPlan,
    UserFeaturePermission,
    Users,
    SubscriptionCycle,
    ModuleUsageCycle,
    ModuleSubscription,
    Context
)
from .serializers import (
    ModuleDetailSerializer,
    ModuleSerializer,
    RoleDetailSerializer,
    RoleSerializer,
    SubscriptionPlanSerializer,
    UserFeaturePermissionSerializer
)
import json

# Module Management APIs


@api_view(['POST'])
@permission_classes([AllowAny])
def request_otp(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user already exists
    if Users.objects.filter(email=email).exists():
        # Before
        return Response({'error': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    # Generate and store OTP
    otp_code = generate_otp()
    expires_at = timezone.now() + datetime.timedelta(minutes=10)

    pending_otp, created = PendingUserOTP.objects.update_or_create(
        email=email,
        defaults={'otp_code': otp_code, 'expires_at': expires_at}
    )

    special_emails = {'hr@finixco.in', 'cleoskinc@gmail.com', 'h.chahal@venturiq.com', 'accounts@ereena.co',
                      'Theholeinthewallcafehyd2@gmail.com', 'accounts@sashaclinics.com', 'admin@flexpilates.in',
                      'karshakinfratech@gmail.com', 'camanisai@gmail.com', 'udaykiran256303@gmail.com',
                      'info@svpandco.com', 'akhila.tadisina@gmail.com'}

    # Send OTP email
    if email in special_emails:
        send_otp_email("saikiranmekala@tarafirst.com", otp_code)
    else:
        send_otp_email(email, otp_code)

    return Response({'message': 'OTP sent to email'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def create_module(request):
    """Create a new module.

    Expected JSON payload:
    {
        "name": "Payroll",
        "description": "Payroll management system",
        "context_type": "business",
        "is_active": true
    }
    """
    serializer = ModuleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Module created successfully',
            'module': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'message': 'Invalid data',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_modules(request):
    """
    API endpoint for listing all modules
    Optional query parameters:
    - context_type: Filter by context type (personal/business)
    - is_active: Filter by active status (true/false)
    """
    try:
        context_type = request.query_params.get('context_type')
        is_active_param = request.query_params.get('is_active')
        category = request.query_params.get('category')

        filters = {}
        if context_type:
            filters['context_type'] = context_type

        if is_active_param is not None:
            filters['is_active'] = is_active_param
        if category:
            filters['category'] = category

        # Fetch modules with or without filters
        modules = Module.objects.filter(**filters)
        serializer = ModuleSerializer(modules, many=True)

        return Response({
            'success': True,
            'modules': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'error': 'An unexpected error occurred.',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
def update_module(request, module_id):
    """
    API endpoint for updating a module
    Expected JSON payload:
    {
        "name": "Updated Payroll",
        "description": "Updated description",
        "is_active": false
    }
    """
    try:
        module = Module.objects.get(id=module_id)
    except Module.DoesNotExist:
        return Response({
            'success': False,
            'message': f'Module with ID {module_id} does not exist'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ModuleDetailSerializer(module)
        return Response({
            'success': True,
            'module': serializer.data
        })

    serializer = ModuleSerializer(module, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Module updated successfully',
            'module': serializer.data
        })
    return Response({
        'success': False,
        'message': 'Invalid data',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_module(request, module_id):
    """
    API endpoint for deleting a module
    """
    try:
        module = Module.objects.get(id=module_id)
    except Module.DoesNotExist:
        return Response({
            'success': False,
            'message': f'Module with ID {module_id} does not exist'
        }, status=status.HTTP_404_NOT_FOUND)

    module.delete()
    return Response({
        'success': True,
        'message': 'Module deleted successfully'
    })


# Subscription Plan Management APIs


# Role Management APIs

@api_view(['POST'])
def create_role(request):
    """
    API endpoint for creating a new role
    Expected JSON payload:
    {
        "name": "Manager",
        "description": "Manager role with limited permissions",
        "context_type": "business",
        "is_active": true
    }
    """
    serializer = RoleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Role created successfully',
            'role': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'message': 'Invalid data',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def list_roles(request):
    """
    API endpoint for listing all roles
    Optional query parameters:
    - context_type: Filter by context type (personal/business)
    - is_active: Filter by active status (true/false)
    """
    context_type = request.query_params.get('context_type')
    is_active = request.query_params.get('is_active')

    # Build query
    query = {}
    if context_type:
        query['context_type'] = context_type
    if is_active is not None:
        query['is_active'] = is_active.lower() == 'true'

    # Get roles
    roles = Role.objects.filter(**query)
    serializer = RoleSerializer(roles, many=True)

    return Response({
        'success': True,
        'roles': serializer.data
    })


@api_view(['GET', 'PUT'])
def update_role(request, role_id):
    """
    API endpoint for updating a role
    Expected JSON payload:
    {
        "name": "Updated Manager",
        "description": "Updated description",
        "is_active": false
    }
    """
    try:
        role = Role.objects.get(id=role_id)
    except Role.DoesNotExist:
        return Response({
            'success': False,
            'message': f'Role with ID {role_id} does not exist'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = RoleDetailSerializer(role)
        return Response({
            'success': True,
            'role': serializer.data
        })

    serializer = RoleSerializer(role, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Role updated successfully',
            'role': serializer.data
        })
    return Response({
        'success': False,
        'message': 'Invalid data',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_role(request, role_id):
    """
    API endpoint for deleting a role
    """
    try:
        role = Role.objects.get(id=role_id)
    except Role.DoesNotExist:
        return Response({
            'success': False,
            'message': f'Role with ID {role_id} does not exist'
        }, status=status.HTTP_404_NOT_FOUND)

    role.delete()
    return Response({
        'success': True,
        'message': 'Role deleted successfully'
    })


# Module Permission Management APIs

@api_view(['POST'])
def create_module_permission(request):
    """
    API endpoint for creating module permissions for a role
    Expected JSON payload:
    {
        "role_id": 1,
        "module_id": 1,
        "permissions": ["create", "read", "update", "delete"]
    }
    """
    serializer = UserFeaturePermissionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Module permission created successfully',
            'permission': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'message': 'Invalid data',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def list_module_permissions(request):
    """
    API endpoint for listing module permissions
    Optional query parameters:
    - role_id: Filter by role ID
    - module_id: Filter by module ID
    """
    role_id = request.query_params.get('role_id')
    module_id = request.query_params.get('module_id')

    # Build query
    query = {}
    if role_id:
        query['role_id'] = role_id
    if module_id:
        query['module_id'] = module_id

    # Get permissions
    permissions = UserFeaturePermission.objects.filter(**query)
    serializer = UserFeaturePermissionSerializer(permissions, many=True)

    return Response({
        'success': True,
        'permissions': serializer.data
    })


@api_view(['GET', 'PUT'])
def update_module_permission(request, permission_id):
    """
    API endpoint for updating module permissions
    Expected JSON payload:
    {
        "permissions": ["read", "update"]
    }
    """
    try:
        permission = UserFeaturePermission.objects.get(id=permission_id)
    except UserFeaturePermission.DoesNotExist:
        return Response({
            'success': False,
            'message': f'Permission with ID {permission_id} does not exist'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UserFeaturePermissionSerializer(permission)
        return Response({
            'success': True,
            'permission': serializer.data
        })

    serializer = UserFeaturePermissionSerializer(permission, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Module permission updated successfully',
            'permission': serializer.data
        })
    return Response({
        'success': False,
        'message': 'Invalid data',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_module_permission(request, permission_id):
    """
    API endpoint for deleting module permissions
    """
    try:
        permission = UserFeaturePermission.objects.get(id=permission_id)
    except UserFeaturePermission.DoesNotExist:
        return Response({
            'success': False,
            'message': f'Permission with ID {permission_id} does not exist'
        }, status=status.HTTP_404_NOT_FOUND)

    permission.delete()
    return Response({
        'success': True,
        'message': 'Module permission deleted successfully'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def happy_coder(request):
    """Return a simple success message."""
    return Response({"message": "Happy Coder, My Job is to be Consistent and Discipline"},
                    status=status.HTTP_200_OK)


"""Views for user management functionality.

This module contains views for handling user-related operations including:
- OTP management
- Module management
- Role management
"""

@api_view(["GET"])
@permission_classes([AllowAny])
def get_usage_summary_by_context(request, context_id):
    """
    Retrieve all usage entries for a given context ID.
    Optional query param testing: module_id
    """
    try:
        module_id = request.query_params.get("module_id")

        # Filter subscriptions
        sub_filters = {
            "context_id": context_id,
            "status__in": ["active", "trial"]
        }
        if module_id:
            sub_filters["module_id"] = module_id

        subscriptions = ModuleSubscription.objects.filter(**sub_filters)

        if not subscriptions.exists():
            return Response(
                {"error": "No active/trial subscriptions found for the given context."},
                status=status.HTTP_404_NOT_FOUND
            )

        usage_summary = []

        for sub in subscriptions:
            cycle = SubscriptionCycle.objects.filter(subscription=sub).order_by("-start_date").first()
            if not cycle:
                continue

            usage_entries = ModuleUsageCycle.objects.filter(cycle=cycle)

            for entry in usage_entries:
                usage_summary.append({
                    "module_id": sub.module_id,
                    "feature_key": entry.feature_key,
                    "usage_count": entry.usage_count,
                    "actual_count": entry.actual_count,
                    "is_limited": str(entry.actual_count).lower() != "unlimited"
                })

        return Response({
            "success": True,
            "context_id": context_id,
            "data": usage_summary
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "success": False,
            "error": "Failed to fetch usage summary.",
            "details": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])  # This view only accepts DELETE requests
def context_delete_drf(request, context_id):
    """
    Deletes a specific Context object.
    """
    try:
        # 1. Get the object, ensuring it exists and the user has permission
        context = get_object_or_404(Context, id=context_id, owner_user=request.user)
        # The `owner_user=request.user` in the query is the permission check.

        # 2. (Optional) You can add more complex checks here
        # if context.status == 'active':
        #     return Response({"error": "Cannot delete an active context."}, status=status.HTTP_409_CONFLICT)

        # 3. Perform the deletion
        # This will call your custom model's delete() method
        context.delete()

        # 4. Return a success response
        return Response(
            {
                "success": True,
                "message": f"Context '{context.name}' was successfully deleted."
            },
            status=status.HTTP_200_OK # or status.HTTP_204_NO_CONTENT
        )

    except Exception as e:
        # Handle any unexpected errors
        return Response(
            {
                "success": False,
                "error": "Failed to delete context.",
                "details": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

