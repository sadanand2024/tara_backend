from rest_framework import serializers
from .models import (
    Users, Context, Module, Role, UserContextRole,
    UserFeaturePermission, SubscriptionPlan, ModuleSubscription,
)
from .models import *
from django.utils.timezone import now


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the Users model"""

    class Meta:
        model = Users
        fields = ['id', 'email', 'mobile_number', 'created_at', 'status', 'first_name', 'last_name',
                  'service_request', 'created_by', 'active_context',
                  'registration_flow', 'initial_selection', 'registration_completed']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """Override create method to properly handle password hashing"""
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class ContextSerializer(serializers.ModelSerializer):
    """Serializer for the Context model"""

    class Meta:
        model = Context
        fields = ['id', 'name', 'context_type', 'status', 'profile_status']


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for the Module model"""
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = Module
        fields = ['id', 'name', 'description', 'context_type', 'is_active']


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for the Role model"""

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'context_type', 'is_active']
        read_only_fields = ['id']


class UserContextRoleSerializer(serializers.ModelSerializer):
    """Serializer for the UserContextRole model"""

    class Meta:
        model = UserContextRole
        fields = ['id', 'user', 'context', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserFeaturePermissionSerializer(serializers.ModelSerializer):
    """Serializer for the UserModulePermission model"""

    class Meta:
        model = UserFeaturePermission
        fields = ['id', 'user_context_role', 'module', 'permissions']
        read_only_fields = ['id']


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for SubscriptionPlan model"""
    features_enabled = serializers.JSONField(default={})

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'module', 'suite', 'name', 'description', 'plan_type',
            'base_price',  'billing_cycle_days', 'is_active', 'features_enabled',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Custom validation for subscription plan data
        """
        # Validate plan type and pricing
        if data.get('plan_type') == 'trial':
            if data.get('base_price') != 0:
                raise serializers.ValidationError(
                    "Trial plans must have zero base price and price per unit"
                )

        # Validate billing cycle days is positive
        if data.get('billing_cycle_days', 0) <= 0:
            raise serializers.ValidationError(
                "Billing cycle days must be positive"
            )

        return data


class SubscriptionPlanDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for SubscriptionPlan with related data"""
    module_name = serializers.CharField(source='module.name', read_only=True)
    active_subscriptions_count = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'module', 'module_name', 'name', 'description', 'plan_type',
            'base_price', 'usage_unit', 'free_tier_limit',
            'price_per_unit', 'billing_cycle_days', 'is_active',
            'created_at', 'updated_at', 'active_subscriptions_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'active_subscriptions_count']

    def get_active_subscriptions_count(self, obj):
        """Get count of active subscriptions for this plan"""
        return obj.module_subscriptions.filter(
            status__in=['trial', 'active', 'pending_renewal']
        ).count()


class ModuleSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for ModuleSubscription model"""
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    context_name = serializers.CharField(source='context.name', read_only=True)
    module_name = serializers.CharField(source='module.name', read_only=True)

    class Meta:
        model = ModuleSubscription
        fields = [
            'id', 'context', 'context_name', 'module', 'module_name',
            'plan', 'plan_details', 'status', 'start_date', 'end_date',
            'auto_renew', 'current_usage', 'last_usage_update',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'plan_details',
            'context_name', 'module_name', 'last_usage_update'
        ]

    def validate(self, data):
        """
        Custom validation for module subscription data
        """
        # Check if context and module exist
        if 'context' in data and 'module' in data:
            # Check if this module is already subscribed in this context
            existing = ModuleSubscription.objects.filter(
                context=data['context'],
                module=data['module']
            )
            if self.instance:  # If updating existing subscription
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError(
                    "This module is already subscribed in this context"
                )

        # Validate end date is after start date
        if 'start_date' in data and 'end_date' in data:
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError(
                    "End date must be after start date"
                )

        return data


class ModuleSubscriptionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for ModuleSubscription with related data"""
    plan_details = SubscriptionPlanDetailSerializer(source='plan', read_only=True)
    context_details = serializers.SerializerMethodField()
    module_details = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    current_price = serializers.SerializerMethodField()

    class Meta:
        model = ModuleSubscription
        fields = [
            'id', 'context', 'context_details', 'module', 'module_details',
            'plan', 'plan_details', 'status', 'start_date', 'end_date',
            'auto_renew', 'current_usage', 'last_usage_update',
            'created_at', 'updated_at', 'days_remaining', 'current_price'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'plan_details',
            'context_details', 'module_details', 'last_usage_update',
            'days_remaining', 'current_price'
        ]

    def get_context_details(self, obj):
        """Get context details"""
        return {
            'id': obj.context.id,
            'name': obj.context.name,
            'context_type': obj.context.context_type
        }

    def get_module_details(self, obj):
        """Get module details"""
        return {
            'id': obj.module.id,
            'name': obj.module.name,
            'description': obj.module.description
        }

    def get_days_remaining(self, obj):
        """Get days remaining in subscription"""
        return obj.days_remaining()

    def get_current_price(self, obj):
        """Get current price based on usage"""
        return obj.calculate_current_price()


# Nested serializers for more detailed responses

class UserDetailSerializer(UserSerializer):
    """Detailed serializer for Users with nested relationships"""
    active_context = ContextSerializer(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['context_roles', 'module_permissions']

    def to_representation(self, instance):
        """Customize the representation to include nested data"""
        representation = super().to_representation(instance)

        # Add context roles
        context_roles = []
        for context_role in instance.context_roles.all():
            role_data = {
                'id': context_role.id,
                'context': context_role.context.name,
                'role': context_role.role.name,
                'created_at': context_role.created_at
            }
            context_roles.append(role_data)
        representation['context_roles'] = context_roles

        # Add module permissions
        module_permissions = []
        for context_role in instance.context_roles.all():
            for permission in context_role.module_permissions.all():
                permission_data = {
                    'id': permission.id,
                    'module': permission.module.name,
                    'permissions': permission.permissions
                }
                module_permissions.append(permission_data)
        representation['module_permissions'] = module_permissions

        return representation


class ContextDetailSerializer(ContextSerializer):
    """Detailed serializer for Context with nested relationships"""
    owner_user = UserSerializer(read_only=True)

    class Meta(ContextSerializer.Meta):
        fields = ContextSerializer.Meta.fields + ['users', 'subscriptions']

    def to_representation(self, instance):
        """Customize the representation to include nested data"""
        representation = super().to_representation(instance)

        # Add users
        users = []
        for user in instance.users.all():
            user_data = {
                'id': user.id,
                'email': user.email,
                'status': user.status
            }
            users.append(user_data)
        representation['users'] = users

        # Add subscriptions
        subscriptions = []
        for subscription in instance.subscriptions.all():
            subscription_data = {
                'id': subscription.id,
                'module': subscription.module.name,
                'plan': subscription.plan.name,
                'status': subscription.status,
                'start_date': subscription.start_date,
                'end_date': subscription.end_date
            }
            subscriptions.append(subscription_data)
        representation['subscriptions'] = subscriptions

        return representation


class AddressSerializer(serializers.Serializer):
    address_line1 = serializers.CharField(max_length=255, required=False)
    address_line2 = serializers.CharField(max_length=255, required=False)
    address_line3 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    pinCode = serializers.IntegerField(required=False, allow_null=True)
    state = serializers.CharField(max_length=20, required=False)
    city = serializers.CharField(max_length=20, required=False)
    country = serializers.CharField(max_length=20, required=False)


class ModuleDetailSerializer(ModuleSerializer):
    """Detailed serializer for Module with nested relationships"""

    class Meta(ModuleSerializer.Meta):
        fields = ModuleSerializer.Meta.fields + ['subscriptions', 'permissions']

    def to_representation(self, instance):
        """Customize the representation to include nested data"""
        representation = super().to_representation(instance)

        # Add subscriptions
        subscriptions = []
        for subscription in instance.subscriptions.all():
            subscription_data = {
                'id': subscription.id,
                'context': subscription.context.name,
                'plan': subscription.plan.name,
                'status': subscription.status,
                'start_date': subscription.start_date,
                'end_date': subscription.end_date
            }
            subscriptions.append(subscription_data)
        representation['subscriptions'] = subscriptions

        # Add permissions
        permissions = []
        for permission in instance.permissions.all():
            permission_data = {
                'id': permission.id,
                'user_context_role': {
                    'id': permission.user_context_role.id,
                    'user': permission.user_context_role.user.email,
                    'context': permission.user_context_role.context.name,
                    'role': permission.user_context_role.role.name
                },
                'permissions': permission.permissions
            }
            permissions.append(permission_data)
        representation['permissions'] = permissions

        return representation


class RoleDetailSerializer(RoleSerializer):
    """Detailed serializer for Role with nested relationships"""

    class Meta(RoleSerializer.Meta):
        fields = RoleSerializer.Meta.fields + ['user_context_roles']

    def to_representation(self, instance):
        """Customize the representation to include nested data"""
        representation = super().to_representation(instance)

        # Add user context roles
        user_context_roles = []
        for user_context_role in instance.user_context_roles.all():
            user_context_role_data = {
                'id': user_context_role.id,
                'user': user_context_role.user.email,
                'context': user_context_role.context.name,
                'created_at': user_context_role.created_at
            }
            user_context_roles.append(user_context_role_data)
        representation['user_context_roles'] = user_context_roles

        return representation


class ModuleFeatureSerializer(serializers.ModelSerializer):
    module_name = serializers.CharField(source='module.name', read_only=True)

    class Meta:
        model = ModuleFeature
        fields = ['id', 'module', 'module_name', 'service', 'action', 'label']
        read_only_fields = ['id']

    def validate(self, data):
        # Validate that the action is one of the allowed values
        allowed_actions = [
            'create', 'read', 'update', 'delete', 'approve',
            'send', 'print', 'export', 'cancel', 'void', 'reconcile', 'generate_report'
        ]
        if data['action'] not in allowed_actions:
            raise serializers.ValidationError({
                'action': f'Action must be one of: {", ".join(allowed_actions)}'
            })
        return data


class UserFeaturePermissionSerializer(serializers.ModelSerializer):
    user_context_role_name = serializers.CharField(source='user_context_role.role.name', read_only=True)
    module_name = serializers.CharField(source='module.name', read_only=True)

    class Meta:
        model = UserFeaturePermission
        fields = ['id', 'user_context_role', 'user_context_role_name', 'module', 'module_name',
                  'feature_code', 'actions']
        read_only_fields = ['id']

    def validate(self, data):
        # Validate that all actions are valid
        allowed_actions = ['create', 'read', 'update', 'delete', 'approve']
        invalid_actions = [action for action in data['actions'] if action not in allowed_actions]
        if invalid_actions:
            raise serializers.ValidationError({
                'actions': f'Actions must be one or more of: {", ".join(allowed_actions)}. Invalid actions: {", ".join(invalid_actions)}'
            })
        return data


class UserActivationSerializer(serializers.Serializer):
    token = serializers.CharField()


class BusinessSerializer(serializers.ModelSerializer):
    entityType = serializers.CharField(max_length=50, required=False)
    pan = serializers.CharField(max_length=15, required=False, default=None)
    headOffice = serializers.JSONField(default=dict)

    class Meta:
        model = Business
        fields = '__all__'

    def create(self, validated_data):
        """
        Create and return a new `Business` instance, given the validated data.
        """
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        """
        Update and return an existing `Business` instance, given the validated data.
        """
        [setattr(instance, k, v) for k, v in validated_data.items()]
        instance.save()
        return instance


class GSTDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = GSTDetails
        fields = '__all__'

    def create(self, validated_data):
        """
        Create and return a new `Business` instance, given the validated data.
        """
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        """
        Update and return an existing `Business` instance, given the validated data.
        """
        [setattr(instance, k, v) for k, v in validated_data.items()]
        instance.save()
        return instance


class BusinessUserSerializer(serializers.ModelSerializer):
    entityType = serializers.CharField(max_length=50, required=False)
    pan = serializers.CharField(max_length=15, required=True)
    headOffice = serializers.JSONField(default=dict)
    gst_details = GSTDetailsSerializer(many=True, read_only=True)

    class Meta:
        model = Business
        fields = '__all__'


class UserBusinessRetrieveSerializer(serializers.ModelSerializer):

    class Meta:
        model = Business
        fields = ['id', 'nameOfBusiness', 'entityType', 'client']


class BusinessWithGSTSerializer(serializers.ModelSerializer):
    gst_details = GSTDetailsSerializer(many=True, read_only=True)
    headOffice = serializers.JSONField(default=dict)

    class Meta:
        model = Business
        fields = ['id', 'nameOfBusiness', 'entityType', 'registrationNumber', 'pan', 'mobile_number', 'trade_name',
                  'email', 'dob_or_incorp_date', 'gst_details', 'headOffice', 'headOffice', 'business_nature']


class UserBusinessSerializer(serializers.ModelSerializer):
    date_joined = serializers.SerializerMethodField()
    business = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = [
            'id', 'user_name', 'email', 'mobile_number',
            'first_name', 'last_name', 'user_type',
            'is_active', 'date_joined', 'business'
        ]

    def get_date_joined(self, obj):
        return obj.date_joined.strftime('%d-%m-%Y')  # Format as dd-mm-yyyy

    def get_business(self, obj):
        # Fetch related Business objects
        businesses = obj.business_clients_id.all()
        return BusinessWithGSTSerializer(businesses, many=True).data



class UsersKYCSerializer(serializers.ModelSerializer):
    address = AddressSerializer(default={}, required=False)  # Nested serializer for address

    class Meta:
        model = UserKYC
        fields = [
            'id', 'user', 'pan_number', 'aadhaar_number', 'date', 'icai_number', 'address', 'name', 'have_firm'
        ]
        read_only_fields = ['user']  # Prevent modification of `user` field

    def validate(self, data):
        """
        Validate data based on the user type.
        """
        user = self.context['request'].user  # Accessing the user from the request context

        # Ensure user_type exists in the user model
        if not hasattr(user, 'user_type'):
            raise serializers.ValidationError("User type is missing.")

        user_type = user.user_type
        icai_number = data.get('icai_number')

        # Ensure `icai_number` is None for individuals
        if user_type == 'individual' and icai_number is not None:
            raise serializers.ValidationError({
                "icai_number": "ICAI Number must be None for individual user type."
            })

        # Ensure `icai_number` is provided for CA firms
        if user_type == 'cafirm' and not icai_number:
            raise serializers.ValidationError({
                "icai_number": "ICAI Number is required for Chartered Accountant Firm."
            })

        return data

    def create(self, validated_data):
        """
        Create a new `UserKYC` instance.
        """
        # Handle address field: if it's not provided, use default empty address
        address_data = validated_data.pop('address', None)
        if address_data is None:
            address_data = {
                "address_line1": None,
                "address_line2": None,
                "address_line3": None,
                "pinCode": None,
                "state": None,
                "city": None,
                "country": None
            }

        # Create the UserKYC instance
        user_details = UserKYC.objects.create(**validated_data, address=address_data)
        return user_details

    def update(self, instance, validated_data):
        """
        Update an existing `UserKYC` instance.
        """
        # Extract and handle address data
        address_data = validated_data.pop('address', None)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update the address field if it's provided
        if address_data:
            instance.address = address_data

        instance.save()
        return instance


class FirmKYCSerializer(serializers.ModelSerializer):
    address = AddressSerializer(required=False)

    class Meta:
        model = FirmKYC
        fields = [
            'user', 'firm_name', 'firm_registration_number', 'firm_email', 'firm_mobile_number',
            'number_of_firm_partners', 'address'
        ]
        read_only_fields = ['user']

    def create(self, validated_data):
        """
        Create a new `UserKYC` instance.
        """
        # Check if 'address' is present in validated_data
        if 'address' not in validated_data:
            # If not present, set default address values
            validated_data['address'] = {
                "address_line1": None,
                "address_line2": None,
                "address_line3": None,
                "pinCode": None,
                "state": None,
                "city": None,
                "country": None
            }

        # Create and save the UserKYC instance
        user_details = FirmKYC.objects.create(**validated_data)

        return user_details


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['user_name', 'email', 'mobile_number', 'user_type', 'first_name', 'last_name', 'is_active']
        # You can modify this list based on the fields you want to allow updating

    def update(self, instance, validated_data):
        # Perform the actual update for the instance
        return super().update(instance, validated_data)


class ServicesMasterDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicesMasterData
        fields = '__all__'


class ServiceDetailsSerializer(serializers.ModelSerializer):
    service_type = serializers.PrimaryKeyRelatedField(queryset=ServicesMasterData.objects.all())
    visa_application = serializers.PrimaryKeyRelatedField(queryset=VisaApplications.objects.all(), required=True)  # Include this line
    service_name = serializers.ReadOnlyField(source='service_type.service_name')
    last_updated_date = serializers.SerializerMethodField()

    class Meta:
        model = ServiceDetails
        fields = ['id', 'service_type', 'service_name', 'date', 'status', 'comments', 'quantity',
                  'visa_application', 'last_updated_date']  # Ensure service_name is included

    def get_last_updated_date(self, obj):
        if obj.last_updated:
            # Get only the date part from the datetime field
            return obj.last_updated.date()
        return None



class VisaApplicationsSerializer(serializers.ModelSerializer):
    # services = ServiceDetailsSerializer(many=True)

    class Meta:
        model = VisaApplications
        fields = "__all__"


class IndividualServiceDetailsSerializer(serializers.ModelSerializer):
    service_type = serializers.PrimaryKeyRelatedField(queryset=ServicesMasterData.objects.all())
    visa_application = serializers.PrimaryKeyRelatedField(queryset=VisaApplications.objects.all(), required=True)  # Include this line
    service_name = serializers.ReadOnlyField(source='service_type.service_name')
    last_updated_date = serializers.SerializerMethodField()

    class Meta:
        model = ServiceDetails
        fields = ['id', 'service_type', 'service_name', 'date', 'status', 'comments', 'quantity',
                  'visa_application', 'last_updated_date']  # Ensure service_name is included

    def get_last_updated_date(self, obj):
        if obj.last_updated:
            # Get only the date part from the datetime field
            return obj.last_updated.date()
        return None


class VisaApplicationsGetSerializer(serializers.ModelSerializer):
    services = IndividualServiceDetailsSerializer(many=True)
    email = serializers.SerializerMethodField()
    mobile_number = serializers.SerializerMethodField()

    class Meta:
        model = VisaApplications
        fields = "__all__"

    def get_email(self, obj):
        # Assuming the related User model has the email field
        return obj.user.email if obj.user else None

    def get_mobile_number(self, obj):
        # Assuming the related User model has the mobile_number field
        return obj.user.mobile_number if obj.user else None

class VisaClientUserListSerializer(serializers.ModelSerializer):
    services = ServiceDetailsSerializer(many=True)
    email = serializers.SerializerMethodField()
    mobile_number = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = VisaApplications
        fields = "__all__"  # Ensure this includes any fields from `VisaApplications` needed

    def get_email(self, obj):
        # Assuming the related User model has the email field
        return obj.user.email if obj.user else None

    def get_mobile_number(self, obj):
        # Assuming the related User model has the mobile_number field
        return obj.user.mobile_number if obj.user else None

    def get_first_name(self, obj):
        # Assuming the related User model has the email field
        return obj.user.first_name if obj.user else None

    def get_last_name(self, obj):
        # Assuming the related User model has the mobile_number field
        return obj.user.last_name if obj.user else None

    def get_user(self, obj):
        # Assuming the related User model has the mobile_number field
        return obj.user.id if obj.user else None


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"

    def validate_email(self, value):
        """ Ensure only one request per email per day """
        today = now().date()  # Get today's date
        if Contact.objects.filter(email=value, created_date=today).exists():
            raise serializers.ValidationError("You can only submit one request per day.")
        return value


class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = "__all__"

    def validate_time(self, value):
        """ Ensure time is stored in HH:MM format only (remove seconds) """
        return value.replace(second=0)

    def validate(self, data):
        """ Prevent duplicate bookings for the same date, time slot, and email """
        email = data.get("email")
        date = data.get("date")
        time = data.get("time")

        # Check if the same email has already booked this slot
        if Consultation.objects.filter(email=email, date=date, time=time).exists():
            raise serializers.ValidationError(
                {"time": "This time slot is already booked. Please select a different slot."}
            )

        return data