from Tara.settings.default import *
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from djongo.models import ArrayField, EmbeddedField, JSONField
from .helpers import *
from usermanagement.models import *
from django.db import models
from servicetasks.models import ServiceTask


class BasicBusinessInfo(models.Model):
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, related_name='basic_business_info')
    service_type = models.CharField(max_length=20, default="GST", editable=False)
    service_task = models.OneToOneField(ServiceTask, on_delete=models.CASCADE,
                                     related_name='service_task_basic_business_info')

    legal_name_of_business = models.CharField(max_length=255, blank=True)
    trade_name_of_business = models.CharField(max_length=255, blank=True)

    business_pan = models.FileField(upload_to=upload_business_pan, blank=True, null=True)
    constitution_of_business = models.CharField(max_length=255, blank=True, null=True)

    certificate_of_incorporation = models.FileField(upload_to=upload_certificate_of_incorporation, blank=True,
                                                    null=True)
    MOA_AOA = models.FileField(upload_to=upload_moa_aoa, blank=True, null=True)

    business_commencement_date = models.DateField()
    nature_of_business = models.TextField(blank=True, null=True)
    email_address = models.EmailField(blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ('in progress', 'In Progress'),
            ('completed', 'Completed'),
            ('sent for approval', 'Sent for Approval'),
            ('revoked', 'Revoked')
        ],
        default='in progress',
        null=False,
        blank=False
    )

    assignee = models.ForeignKey(
        Users, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_basic_business_info'
    )
    reviewer = models.ForeignKey(
        Users, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_basic_business_info'
    )

    def save(self, *args, **kwargs):
        # Default to service_task's values if not set
        if not self.assignee and self.service_task.assignee:
            self.assignee = self.service_task.assignee
        if not self.reviewer and self.service_task.reviewer:
            self.reviewer = self.service_task.reviewer
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.legal_name_of_business} - {self.trade_name_of_business or 'N/A'}"


class RegistrationInfo(models.Model):
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, related_name='registration_info')
    service_type = models.CharField(max_length=20, default="GST", editable=False)
    service_task = models.OneToOneField(ServiceTask, on_delete=models.CASCADE,
                                     related_name='service_task_registration_info')
    YES_NO_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]

    is_this_voluntary_registration = models.CharField(
        max_length=3,
        choices=YES_NO_CHOICES,
        default='No'
    )
    applying_for_casual_taxable_person = models.CharField(
        max_length=3,
        choices=YES_NO_CHOICES,
        default='No'
    )
    opting_for_composition_scheme = models.CharField(
        max_length=3,
        choices=YES_NO_CHOICES,
        default='No'
    )
    any_existing_registration = models.CharField(
        max_length=3,
        choices=YES_NO_CHOICES,
        default='No'
    )
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    date_of_registration = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('in progress', 'In Progress'), ('completed', 'Completed'),
                                                      ('sent for approval', 'Sent for Approval'),
                                                      ('revoked', 'Revoked')],default='in progress', null=False, blank=False)
    assignee = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='assigned_registration_info')
    reviewer = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='reviewed_registration_info')

    def save(self, *args, **kwargs):
        # Default to service_request values if not set
        if not self.assignee and self.service_task.assignee:
            self.assignee = self.service_task.assignee
        if not self.reviewer and self.service_task.reviewer:
            self.reviewer = self.service_task.reviewer
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Registration Info - {self.registration_number or 'N/A'}"


class PrincipalPlaceDetails(models.Model):
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, related_name='principal_place_details')
    service_type = models.CharField(max_length=20, default="GST", editable=False)
    service_task = models.OneToOneField(ServiceTask, on_delete=models.CASCADE,
                                     related_name='service_task_principal_place_details')
    ADDRESS_DOCUMENT_CHOICES = [
        ('Electricity Bill', 'Electricity Bill'),
        ('Lease deed/Rental agreement', 'Lease Deed/Rental Agreement'),
        ('Property tax receipt', 'Property Tax Receipt'),
    ]
    OWNERSHIP_TYPE_CHOICES = [
        ('own', 'Own'),
        ('rented', 'Rented'),
        ('lease', 'Lease'),
    ]
    principal_place = JSONField(default=dict, blank=True, null=True)
    nature_of_possession_of_premise = models.CharField(max_length=255,choices=OWNERSHIP_TYPE_CHOICES, blank=True, null=True)
    address_proof = models.CharField(max_length=255, choices=ADDRESS_DOCUMENT_CHOICES,blank=True, null=True)
    address_proof_file = models.FileField(upload_to=upload_address_proof_file, blank=True, null=True)
    rental_agreement_or_noc = models.FileField(upload_to=upload_rental_agreement, blank=True, null=True)
    bank_statement_or_cancelled_cheque = models.FileField(upload_to=upload_bank_statement, blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('in progress', 'In Progress'), ('completed', 'Completed'),
                                                      ('sent for approval', 'Sent for Approval'),
                                                      ('revoked', 'Revoked')], default='in progress',null=False, blank=False)
    assignee = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='assigned_principal_place_details')
    reviewer = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='reviewed_principal_place_details')

    def save(self, *args, **kwargs):
        # Default to service_request values if not set
        if not self.assignee and self.service_task.assignee:
            self.assignee = self.service_task.assignee
        if not self.reviewer and self.service_task.reviewer:
            self.reviewer = self.service_task.reviewer
        super().save(*args, **kwargs)

    def __str__(self):
        address_line = city = 'N/A'
        if isinstance(self.principal_place, dict):
            address_line = self.principal_place.get('address_line_1') or 'N/A'
            city = self.principal_place.get('city') or 'N/A'
        return f"Principal Place - {address_line} - {city}"

class PromoterSignatoryDetails(models.Model):
    service_request = models.OneToOneField(ServiceRequest,on_delete=models.CASCADE,
                            related_name='promoter_signatory_details')
    service_type = models.CharField(max_length=20, default="GST", editable=False)
    service_task = models.OneToOneField(
        ServiceTask,
        on_delete=models.CASCADE,
        related_name='service_task_promoter_signatory_details'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('in progress', 'In Progress'),
            ('completed', 'Completed'),
            ('sent for approval', 'Sent for Approval'),
            ('revoked', 'Revoked')
        ],
        default='in progress'
    )
    assignee = models.ForeignKey(Users, on_delete=models.SET_NULL,null=True, blank=True,
                                related_name='assigned_promoter_signatory_details')
    reviewer = models.ForeignKey(Users, on_delete=models.SET_NULL,null=True, blank=True,
                                 related_name='reviewed_promoter_signatory_details')

    def save(self, *args, **kwargs):
        if not self.assignee and self.service_task.assignee:
            self.assignee = self.service_task.assignee
        if not self.reviewer and self.service_task.reviewer:
            self.reviewer = self.service_task.reviewer
        super().save(*args, **kwargs)

    def __str__(self):
        return f"PromoterSignatoryDetails - {self.service_request.id}"

class PromoterSignatoryInfo(models.Model):
    promoter_detail = models.ForeignKey(
        PromoterSignatoryDetails,
        on_delete=models.CASCADE,
        related_name='info_list'
    )
    name = models.CharField(max_length=255)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True
    )
    mobile = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    pan = models.FileField(upload_to=upload_promoter_pan, blank=True, null=True)
    aadhaar = models.FileField(upload_to=upload_promoter_aadhaar, blank=True, null=True)
    photo = models.FileField(upload_to=upload_promoter_photo, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    residential_same_as_aadhaar_address = models.CharField(
        max_length=3,
        choices=[('Yes', 'Yes'), ('No', 'No')],
        default='No'
    )
    residential_address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.designation or 'N/A'}"


class GSTReviewFilingCertificate(models.Model):
    service_type = models.CharField(max_length=20, default="GST", editable=False)
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE,
                                            related_name='GST_review_filing_certificate')
    service_task = models.OneToOneField(ServiceTask, on_delete=models.CASCADE, related_name='ServiceTask_GST_review_filing_certificate')

    FILING_STATUS_CHOICES = [
        ('in progress', 'In Progress'),
        ('filed', 'Filed'),
        ('resubmitted', 'Resubmitted'),
        ]
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('resubmission', 'Resubmission'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved'),
    ]
    review_certificate = models.FileField(upload_to=review_filing_certificate, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('in progress', 'In Progress'), ('completed', 'Completed'),
                                        ('sent for approval', 'Sent for Approval'),('revoked', 'Revoked')],
                                         default='in progress', null=False,blank=False)

    filing_status = models.CharField(
        max_length=20,
        choices=FILING_STATUS_CHOICES,
        null=True,
        blank=True,
        default=None
    )
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        null=True,
        blank=True,
        default=None
    )
    assignee = models.ForeignKey(
        Users, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_gst_review_filing_certificate'
    )
    reviewer = models.ForeignKey(
        Users, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_gst_review_filing_certificate'
    )

    def save(self, *args, **kwargs):
        # Default to service_request values if not set
        if not self.assignee and self.service_task.assignee:
            self.assignee = self.service_task.assignee
        if not self.reviewer and self.service_task.reviewer:
            self.reviewer = self.service_task.reviewer
        super().save(*args, **kwargs)

    def __str__(self):
        return self.review_certificate_status or "No Review Status"


def calculate_completion_percentage(instance, exclude_fields=None):
    exclude_fields = exclude_fields or ['id', 'created_at', 'updated_at', 'service_request', 'service_task']
    total_fields = 0
    filled_fields = 0

    for field in instance._meta.fields:
        if field.name in exclude_fields:
            continue
        total_fields += 1
        value = getattr(instance, field.name)
        if value not in [None, '', []]:
            filled_fields += 1

    if total_fields == 0:
        return 0
    return round((filled_fields / total_fields) * 100)

@receiver(post_save, sender=BasicBusinessInfo)
def sync_service_task_status(sender, instance, **kwargs):
    task = instance.service_task

    # Sync status
    if task.status != instance.status:
        task.status = instance.status

    # Sync completion %
    task.completion_percentage = calculate_completion_percentage(instance)

    task.save()


@receiver(post_save, sender=RegistrationInfo)
def sync_service_task_status(sender, instance, **kwargs):
    task = instance.service_task

    # Sync status
    if task.status != instance.status:
        task.status = instance.status

    # Sync completion %
    task.completion_percentage = calculate_completion_percentage(instance)

    task.save()


@receiver(post_save, sender=PrincipalPlaceDetails)
def sync_service_task_status(sender, instance, **kwargs):
    task = instance.service_task

    # Sync status
    if task.status != instance.status:
        task.status = instance.status

    # Sync completion %
    task.completion_percentage = calculate_completion_percentage(instance)

    task.save()


@receiver(post_save, sender=PromoterSignatoryDetails)
def sync_service_task_status(sender, instance, **kwargs):
    task = instance.service_task

    # Sync status
    if task.status != instance.status:
        task.status = instance.status

    # Sync completion %
    task.completion_percentage = calculate_completion_percentage(instance)

    task.save()


@receiver(post_save, sender=GSTReviewFilingCertificate)
def sync_service_task_status(sender, instance, **kwargs):
    task = instance.service_task

    # Sync status
    if task.status != instance.status:
        task.status = instance.status

    # Sync completion %
    task.completion_percentage = calculate_completion_percentage(instance)

    task.save()