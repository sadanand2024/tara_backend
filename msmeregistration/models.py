from django.db import models
from Tara.settings.default import *
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from djongo.models import ArrayField, EmbeddedField, JSONField
from .helpers import *
from django.core.validators import RegexValidator

from user_management.models import *

class MSMEDetails(models.Model):
    radios = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('exempted','Exempted')
    ]

    BUSINESS_ACTIVITY_CHOICES = [
        ('manufacturing', 'Manufacturing'),
        ('service', 'Service'),
    ]

    MSME_REGISTRATION_TYPE_CHOICES = [
        ('n/a', 'N/A'),
        ('EM-II', 'EM-II'),
        ('previous UAM', 'Previous UAM'),
    ]
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    aadhar_number = models.BigIntegerField(blank=True, null=True)
    name_of_entrepreneur = models.CharField(max_length=255,blank=True,null=True)
    type_of_organisation = models.CharField(max_length=255,blank=True,null=True)
    pan_number = models.CharField(max_length=255,blank=True,null=True)
    pan_number_holder_name = models.CharField(max_length=255,blank=True,null=True)
    dob = models.DateField(blank=True, null=True)
    itr_previous_year = models.CharField(max_length=8,choices=radios,blank=True,null=True)
    have_GSTIN = models.CharField(max_length=15,choices=radios,blank=True,null=True)
    mobile_number = models.BigIntegerField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    name_of_the_enterprise = models.CharField(max_length=255,blank=True,null=True)
    official_address_of_enterprise = JSONField(default=dict,blank=True,null=True)
    location_of_plant_or_unit = JSONField(default=dict,blank=True,null=True)
    uam_number = models.CharField(max_length=255,choices=MSME_REGISTRATION_TYPE_CHOICES,blank=True,null=True)
    status = JSONField(default=dict,blank=True,null=True)
    bank_details = JSONField(default=dict,blank=True,null=True)
    major_activity_of_unit = models.CharField(max_length=255,choices=BUSINESS_ACTIVITY_CHOICES,blank=True,null=True)
    nic_code = JSONField(default=dict,blank=True,null=True)
    no_of_persons_employed = JSONField(default=dict,blank=True,null=True)

    def __str__(self):
        return self.name_of_entrepreneur