from django.db import models
from Tara.settings.default import *
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from djongo.models import ArrayField, EmbeddedField, JSONField
from .helpers import *
from django.core.validators import RegexValidator
from user_management.models import *

class CompanyIncorporation(models.Model):
    COMPANY_TYPE_CHOICES = [
        ('private limited', 'Private Limited Company'),
        ('foreign company', 'Foreign Company'),
        ('llp', 'LLP'),
        ('public limited', 'Public Limited Company'),
        ('section8', 'Section 8 Company'),
        ('one person', 'One-Person Company'),
        ('government company', 'Government Company'),
        ('any other', 'Any Other'),
    ]

    OWNERSHIP_TYPE_CHOICES = [
        ('owned', 'Owned'),
        ('rented', 'Rented'),
        ('leased', 'Leased'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='user')
    company_type = models.CharField(max_length=40,choices=COMPANY_TYPE_CHOICES,null=True,blank=True)
    option1 = models.CharField(max_length=255,null=True,blank=True)
    option2 = models.CharField(max_length=255,null=True,blank=True)
    option3 = models.CharField(max_length=255,null=True,blank=True)
    business_objective = models.TextField(null=True,blank=True)
    business_activity = models.CharField(max_length=255,null=True,blank=True)
    nic_code = models.CharField(max_length=255,null=True,blank=True)
    address = JSONField(default=dict,blank=True,null=True)
    ownership_type = models.CharField(choices=OWNERSHIP_TYPE_CHOICES,max_length=255,null=True,blank=True)
    email = models.EmailField()
    mobile_number = models.BigIntegerField()
    utility_bill = models.FileField(upload_to=upload_to_basic_details,null=True,blank=True)
    noc = models.FileField(upload_to=upload_to_basic_details,null=True,blank=True)
    rental_agreement = models.FileField(upload_to=upload_to_basic_details,null=True,blank=True)
    property_tax = models.FileField(upload_to=upload_to_basic_details,null=True,blank=True)

    def __str__(self):
        return self.company_type
class Directors_details(models.Model):
    EDUCATION_LEVEL_CHOICES = [
        ('highSchool', 'High School'),
        ('bachelor', "Bachelor's Degree"),
        ('master', "Master's Degree"),
        ('doctorate', 'Doctorate'),
        ('professional', 'Professional Degree'),
    ]
    ADDRESS_PROOF_CHOICES = [
        ('proof of residence', 'Proof of Residence'),
        ('bank statement', 'Bank Statement'),
        ('passport', 'Passport'),
        ('driving license', 'Driving License'),
        ('utility bill', 'Utility Bill'),
    ]

    YES_NO_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]

    company = models.ForeignKey(CompanyIncorporation, on_delete=models.CASCADE, related_name="directors_details")
    first_name = models.CharField(max_length = 255)
    middle_name = models.CharField(max_length = 255,blank=True)
    last_name = models.CharField(max_length = 255)
    father_first_name = models.CharField(max_length=60)
    father_middle_name = models.CharField(max_length=60,blank=True)
    father_last_name = models.CharField(max_length=60)
    gender = models.CharField(max_length=30)
    dob = models.DateField()
    occupation = models.CharField(max_length = 30)
    area_occupation = models.CharField(max_length = 30)
    nationality = models.CharField(max_length=30)
    educational = models.CharField(max_length=30,choices=EDUCATION_LEVEL_CHOICES,null=True,blank=True)
    address = JSONField(default=dict)
    proof_address = models.CharField(max_length=30,choices=ADDRESS_PROOF_CHOICES)
    proof_address_file = models.FileField(upload_to=upload_to_directors)
    email = models.EmailField()
    phone_number = models.BigIntegerField()
    pan_number = models.CharField(max_length=30)
    pan_number_file = models.FileField(upload_to=upload_to_directors)
    aadhar_number = models.BigIntegerField()
    aadhar_file = models.FileField(upload_to=upload_to_directors)
    din = models.CharField(max_length=30,choices=YES_NO_CHOICES)
    din_number = models.CharField(max_length=30, blank=True,null=True)
    directorship = models.CharField(max_length=30,choices=YES_NO_CHOICES)
    passport_photo = models.FileField(upload_to=upload_to_directors)
    signatory_name = models.CharField(max_length = 50)
    dsc = models.CharField(max_length = 50,choices=YES_NO_CHOICES)
    category_of_directors = models.CharField(max_length = 50)
    shareholder = models.CharField(max_length=50,choices=YES_NO_CHOICES)
    shareholder_details = JSONField(default = dict)
    share_file = models.FileField(upload_to=upload_to_directors,blank=True,null = True)
    def __str__(self):
        return f"{self.first_name} - {self.last_name}"

class Details_of_Existing_Directorships(models.Model):
    director = models.ForeignKey(Directors_details, on_delete=models.CASCADE, related_name="existing_company")
    companyName = models.CharField(max_length = 255)
    cin = models.CharField(max_length=255)
    typeOfCompany = models.CharField(max_length=255)
    positionHeld = models.CharField(max_length=255)

    def __str__(self):
        return self.companyName



class Authorized_And_Paid_up_Capital(models.Model):
    company = models.ForeignKey(CompanyIncorporation, on_delete=models.CASCADE, related_name="authorized_capital")
    authorized_share_capital = models.DecimalField(max_digits=15, decimal_places=2)
    paid_up_share_capital = models.DecimalField(max_digits=15, decimal_places=2)
    face_value_per_share = models.DecimalField(max_digits=10, decimal_places=2)
    no_of_shares = models.PositiveIntegerField()
    bank_name = models.CharField(max_length=255)
    def __str__(self):
        return self.company

class Share_Holders_Information(models.Model):
    IDENTITY_PROOF_CHOICES = [
        ('Aadhaar', 'Aadhaar Card'),
        ('Passport', 'Passport'),
        ('Driving License', 'Driving License'),
        ('Voter ID', 'Voter ID'),
    ]


    company = models.ForeignKey(CompanyIncorporation, on_delete=models.CASCADE, related_name="share_holders")
    type_of_shareholder = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255,blank=True,null=True)
    last_name = models.CharField(max_length=255)
    address = JSONField(default=dict)
    email = models.EmailField()
    mobile = models.BigIntegerField()
    holding_percentage = models.DecimalField(max_digits=15, decimal_places=2)
    pan_number_file = models.FileField(upload_to=upload_to_shareholders_details)
    address_proof = models.CharField(max_length=50,choices=IDENTITY_PROOF_CHOICES)
    address_proof_file = models.FileField(upload_to=upload_to_shareholders_details)
    def __str__(self):
        return f"{self.first_name} - {self.last_name}"

