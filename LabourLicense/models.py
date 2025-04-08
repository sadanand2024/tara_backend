from django.db import models
from Tara.settings.default import *
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from djongo.models import ArrayField, EmbeddedField, JSONField
from .helpers import *
from django.core.validators import RegexValidator
from user_management.models import *

class EntrepreneurDetails(models.Model):
    Genders = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    gender = models.CharField(max_length=255,choices=Genders)
    mobile_number = models.BigIntegerField()
    address_of_entrepreneur = JSONField(default=dict)

    def __str__(self):
        return self.name

class establishment_details(models.Model):
    license = models.ForeignKey(EntrepreneurDetails, on_delete=models.CASCADE, related_name='establishment_details')
    classification = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    name_of_establishment = models.CharField(max_length=255)
    address_of_establishment = JSONField(default=dict)

    def __str__(self):
        return self.name_of_establishment

class Work_Location(models.Model):
    license = models.ForeignKey(EntrepreneurDetails, on_delete=models.CASCADE, related_name='work_location')
    work_location = JSONField(default=dict)

class EmployerDetails(models.Model):
    Genders = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]
    license = models.ForeignKey(EntrepreneurDetails, on_delete=models.CASCADE, related_name='employer_details')
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255,blank=True,null=True)
    last_name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)
    age = models.IntegerField()
    mobile_number = models.BigIntegerField()
    email = models.EmailField()
    pan_file = models.FileField(upload_to=labour_license_upload_employer_details)
    aadhar_card_file = models.FileField(upload_to=labour_license_upload_employer_details)
    photos_of_employer = models.FileField(upload_to=labour_license_upload_employer_details)
    address_of_employer = JSONField(default=dict)
    nature_of_business = models.CharField(max_length=255)
    date_of_commencement = models.DateField()
    total_employees = JSONField(default=dict)

    def __str__(self):
        return self.first_name

class files(models.Model):
    license = models.ForeignKey(EntrepreneurDetails, on_delete=models.CASCADE, related_name='files_uploaded')
    pan_entity_file = models.FileField(upload_to=labour_license_upload_file)
    address_proof_of_establishment = models.FileField(upload_to=labour_license_upload_file)
    name_board_file = models.FileField(upload_to=labour_license_upload_file)
    photo_file = models.FileField(upload_to=labour_license_upload_file)
    authorization_letter = models.FileField(upload_to=labour_license_upload_file, blank=True, null=True)
    partnership_deed = models.FileField(upload_to=labour_license_upload_file, blank=True, null=True)
    certificate_of_incorporation = models.FileField(upload_to=labour_license_upload_file, blank=True, null=True)
    memorandum_of_articles = models.FileField(upload_to=labour_license_upload_file, blank=True, null=True)


    def __str__(self):
        return self.license.name