from django.db import models
from Tara.settings.default import *
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from djongo.models import ArrayField, EmbeddedField, JSONField
from .helpers import *
from django.core.validators import RegexValidator
from user_management.models import *

class Basic_Detail(models.Model):
    Genders = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]
    company = [
        ('author_signatory', 'Author Signatory'),
        ('partner', 'Partner'),
        ('director', 'Director'),
        ('proprietor', 'Proprietor')
    ]
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255)
    father_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, choices=Genders,blank=True, null=True)
    mobile_number = models.BigIntegerField()
    email = models.EmailField()
    age = models.IntegerField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    have_trade_license = models.CharField(max_length=10,choices=[('yes','Yes'),('no','No')],default='no')
    upload_photo = models.FileField(upload_to=trade_license_upload_trade_photo, blank=True, null=True)
    address = JSONField(default=dict, blank=True, null=True)
    relationship_with_applicant = models.CharField(max_length=255, choices=company,blank=True,null=True)

    def __str__(self):
        return self.first_name

class Trade_License_Exist_or_not(models.Model):
    license = models.ForeignKey(Basic_Detail, on_delete=models.CASCADE, related_name='trade_license')
    tin_number = models.CharField(max_length=255,blank=True,null=True)
    trade_license_file = models.FileField(upload_to=trade_license_upload_trade_license, blank=True, null=True)

    def __str__(self):
        return self.license.id

class Trade_Entity(models.Model):
    Trade_Premises = [
        ('commercial', 'Commercial Area'),
        ('residential', 'Residential')
    ]
    Ownership_Type = [
        ('rental', 'Rental'),
        ('leased', 'Leased'),
        ('own', 'Own')
    ]
    Type_Of_Constitution = [
        ('proprietorship', 'Proprietorship'),
        ('partnership', 'Partnership'),
        ('company', 'Company'),
        ('trust', 'Trust')
    ]
    license = models.ForeignKey(Basic_Detail, on_delete=models.CASCADE, related_name='trade_license_entity')
    name_of_entity = models.CharField(max_length=255)
    trade_premises = models.CharField(max_length=255, choices=Trade_Premises)
    trade_description = models.TextField()
    total_area = models.IntegerField()
    ownership_type = models.CharField(max_length=255, choices=Ownership_Type)
    address = JSONField(default=dict)
    license_validity = models.CharField(max_length=255,blank=True,null=True)
    type_of_constitution = models.CharField(max_length=255, choices=Type_Of_Constitution,blank=True,null=True)
    id_proof = models.FileField(upload_to=trade_license_upload_trade_entity,blank=True,null=True)
    photos_of_partnership = models.FileField(upload_to=trade_license_upload_trade_entity,blank=True,null=True)
    property_tax_receipt = models.FileField(upload_to=trade_license_upload_trade_entity,blank=True,null=True)
    rental_or_lease_deed = models.FileField(upload_to=trade_license_upload_trade_entity,blank=True,null=True)
    road_type = models.CharField(max_length=255,blank=True,null=True)

    def __str__(self):
        return self.name_of_entity

class Partner_Details(models.Model):
    license = models.ForeignKey(Basic_Detail, on_delete=models.CASCADE, related_name='trade_license_partner')
    partner_name = models.CharField(max_length=255)
    partner_address = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)

    def __str__(self):
        return self.partner_name