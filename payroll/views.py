from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from .serializers import *
from rest_framework.decorators import api_view
import boto3
from Tara.settings.default import *
from botocore.exceptions import ClientError
import csv
import pandas as pd
from io import TextIOWrapper
from django.shortcuts import get_object_or_404
from user_management.serializers import *
from django.db import transaction, DatabaseError
from django.core.exceptions import ObjectDoesNotExist
import json
from .helpers import *
import calendar
from django.db.models import Q
from django.db.models.functions import ExtractMonth
from num2words import num2words
from django.template.loader import render_to_string
from django.http import HttpResponse
import pdfkit
from django.http import JsonResponse
from django.db.models import OuterRef, Subquery, Q

def upload_to_s3(pdf_data, bucket_name, object_key):
    try:
        # Save the PDF to an S3 bucket
        s3 = boto3.client('s3', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        response = s3.put_object(Bucket=bucket_name, Key=object_key, Body=pdf_data)
        s3_path = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"
        return s3_path
    except Exception as e:
        return Response({'error_message': str(e), 'status_cd': 1},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def generate_presigned_url(s3_key, expiration=3600):
    """
    Generate a presigned URL for accessing a private S3 file.
    """
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket':AWS_STORAGE_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=expiration,
        )
        return url
    except Exception as e:
        raise Exception(f"Error generating presigned URL: {str(e)}")


class PayrollOrgList(APIView):
    """
    List all PayrollOrg instances or create a new PayrollOrg.
    """
    def get(self, request):
        payroll_orgs = PayrollOrg.objects.all()
        serializer = PayrollOrgSerializer(payroll_orgs, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        file = request.FILES.get('logo')  # Handle uploaded file (logo)
        bucket_name = S3_BUCKET_NAME
        business_id = data.get('business')
        business_data = data.pop('business_details', None)

        # Fetch business instance
        try:
            business = Business.objects.get(pk=business_id)
        except ObjectDoesNotExist:
            return Response({"error": "Business not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update business details if provided
        if business_data:
            if isinstance(business_data, list):  # Ensure we are working with a list
                business_data = business_data[0]  # Extract the first element (string)
            try:
                business_data = json.loads(business_data)  # Convert JSON string to dictionary
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format in business_details"},
                                status=status.HTTP_400_BAD_REQUEST)
            business_serializer = BusinessSerializer(business, data=business_data, partial=True)
            if business_serializer.is_valid():
                business_serializer.save()
            else:
                return Response(business_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Handle file upload
        if file:
            sanitized_file_name = file.name.replace(" ", "_")
            object_key = f'{business.nameOfBusiness}/business_logo/{sanitized_file_name}'

            try:
                data['logo'] = upload_to_s3(file.read(), bucket_name, object_key)
            except Exception as e:
                return Response({"error": f"File upload failed: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Fetch or create PayrollOrg
        try:
            payroll_org = PayrollOrg.objects.get(business_id=business_id)
            serializer = PayrollOrgSerializer(payroll_org, data=data, partial=True)
        except PayrollOrg.DoesNotExist:
            serializer = PayrollOrgSerializer(data=data)

        # Validate and save PayrollOrg
        if serializer.is_valid():
            payroll_org = serializer.save()
            return Response(PayrollOrgSerializer(payroll_org).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_payroll_details(request, payroll_id):
    payroll = get_object_or_404(PayrollOrg, id=payroll_id)
    serializer = PayrollEPFESISerializer(payroll)  # Fetch EPF & ESI details
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def business_payroll_check(request):
    """
    API to retrieve a business by client ID.
    """
    try:

        client_id = request.query_params.get('user_id')
        business_id = request.query_params.get('business_id')
        if client_id:

            try:
                business = Business.objects.get(client=client_id)  # Using get() instead of filter()
            except Business.DoesNotExist:
                return Response({'error': 'No business found for this client.'}, status=status.HTTP_404_NOT_FOUND)

        if business_id:
            try:
                business = Business.objects.get(id=business_id)  # Using get() instead of filter()
            except Business.DoesNotExist:
                return Response({'error': 'No business found for this client.'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize business data
        serializer = BusinessSerializer(business)
        response_data = serializer.data

        # Check if PayrollOrg exists for this business
        organisation_details = PayrollOrg.objects.filter(business=business).exists()

        if organisation_details:
            payroll_org = PayrollOrg.objects.get(business=business.id)
            response_data['payroll_id'] = payroll_org.id
            # payroll_data = PayrollOrgSerializer(payroll_org).data  # Serialize PayrollOrg
            # payroll_data["organisation_address"] = dict(payroll_data.get("organisation_address", {}))

            # Check if all necessary components exist
            all_components = all([
                WorkLocations.objects.filter(payroll=payroll_org.id).exists() or payroll_org.work_location,
                Departments.objects.filter(payroll=payroll_org.id).exists() or payroll_org.department,
                Designation.objects.filter(payroll=payroll_org.id).exists() or payroll_org.designation,
                payroll_org.statutory_component or all([
                    EPF.objects.filter(payroll=payroll_org.id).exists(),
                    ESI.objects.filter(payroll=payroll_org.id).exists(),
                    PT.objects.filter(payroll=payroll_org.id).exists()
                ]),
                payroll_org.salary_component or all([
                    Earnings.objects.filter(payroll=payroll_org.id).exists(),
                    # Benefits.objects.filter(payroll=payroll_org.id).exists(),
                    # Deduction.objects.filter(payroll=payroll_org.id).exists(),
                    # Reimbursement.objects.filter(payroll=payroll_org.id).exists()
                ]),
                payroll_org.salary_template or SalaryTemplate.objects.filter(payroll=payroll_org.id).exists(),
                payroll_org.pay_schedule or PaySchedule.objects.filter(payroll=payroll_org.id).exists(),
                payroll_org.leave_management or LeaveManagement.objects.filter(payroll=payroll_org.id).exists() ,
                payroll_org.holiday_management or HolidayManagement.objects.filter(payroll=payroll_org.id).exists(),
                payroll_org.employee_master or EmployeeManagement.objects.filter(payroll=payroll_org.id).exists(),
            ])
        else:
            all_components = False  # If PayrollOrg does not exist, setup is incomplete

        # Add payroll setup status to the response
        response_data["payroll_setup"] = all_components

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'An unexpected error occurred: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PayrollOrgDetail(APIView):
    """
    Retrieve, update or delete a payroll organization instance.
    """

    def get(self, request, pk):
        try:
            # Fetch PayrollOrg or return 404
            payroll_org = get_object_or_404(PayrollOrg, pk=pk)

            # Fetch associated Business
            business = payroll_org.business

            # Serialize PayrollOrg
            payroll_serializer = PayrollOrgSerializer(payroll_org)

            # Serialize Business
            business_serializer = BusinessSerializer(business)  # Serialize full business data

            # Construct response with full business details
            response_data = payroll_serializer.data  # Get serialized PayrollOrg data
            response_data["business_details"] = business_serializer.data  # Add full Business details

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            payroll_org = PayrollOrg.objects.get(pk=pk)
        except PayrollOrg.DoesNotExist:
            return Response({"error": "PayrollOrg not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        file = request.FILES.get('logo')  # Handle uploaded file (logo)
        bucket_name = S3_BUCKET_NAME

        if file:
            # Replace spaces with underscores in the file name
            sanitized_file_name = file.name.replace(" ", "_")
            business_name = request.data.get('org_name', 'default_org').replace(" ",
                                                                                "_")  # Ensure no spaces in org_name
            object_key = f'{business_name}/business_logo/{sanitized_file_name}'

            try:
                # Upload file to S3 as private
                url = upload_to_s3(file.read(), bucket_name, object_key)  # Read file content for upload
                # Store the S3 URL in the `logo` field
                data['logo'] = url
            except Exception as e:
                return Response(
                    {"error": f"File upload failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Validate and update the serializer
        serializer = PayrollOrgSerializer(payroll_org, data=data, partial=True)
        if serializer.is_valid():
            payroll_org = serializer.save()  # Update the instance directly
            return Response(
                PayrollOrgSerializer(payroll_org).data,
                status=status.HTTP_200_OK
            )

        # Handle validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            payroll_org = PayrollOrg.objects.get(pk=pk)
            payroll_org.delete()
            return Response({"message": "PayrollOrg deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except PayrollOrg.DoesNotExist:
            return Response({"error": "PayrollOrg not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
def update_payroll_org(request, business_id):
    try:
        business = Business.objects.get(pk=business_id)
    except Business.DoesNotExist:
        return Response({"error": "Business not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        payroll_org = PayrollOrg.objects.get(business_id=business_id)
    except PayrollOrg.DoesNotExist:
        return Response({"error": "PayrollOrg not found for this business"}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()
    file = request.FILES.get('logo')  # Handle uploaded file (logo)
    bucket_name = S3_BUCKET_NAME

    if file:
        # Sanitize file name
        sanitized_file_name = file.name.replace(" ", "_")
        business_name = request.data.get('org_name', 'default_org').replace(" ", "_")
        object_key = f'{business_name}/business_logo/{sanitized_file_name}'

        try:
            # Upload file to S3
            url = upload_to_s3(file.read(), bucket_name, object_key)
            data['logo'] = url
        except Exception as e:
            return Response({"error": f"File upload failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Get fields dynamically from serializers
    payroll_org_fields = set(PayrollOrgSerializer().get_fields().keys())
    business_fields = set(BusinessSerializer().get_fields().keys())

    payroll_org_data = {key: value for key, value in data.items() if key in payroll_org_fields}
    business_data = {key: value for key, value in data.items() if key in business_fields}

    # Use a transaction to ensure atomicity
    with transaction.atomic():
        if payroll_org_data:
            payroll_serializer = PayrollOrgSerializer(payroll_org, data=payroll_org_data, partial=True)
            if payroll_serializer.is_valid():
                payroll_serializer.save()
            else:
                return Response(payroll_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if business_data:
            business_serializer = BusinessSerializer(business, data=business_data, partial=True)
            if business_serializer.is_valid():
                business_serializer.save()
            else:
                return Response(business_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": "Successfully updated"}, status=status.HTTP_200_OK)


class PayrollOrgBusinessDetail(APIView):
    """
    Retrieve a payroll organization instance by its business ID.
    """

    def get(self, request, business_id):
        try:
            payroll_org = PayrollOrg.objects.get(business_id=business_id)
            serializer = PayrollOrgSerializer(payroll_org)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PayrollOrg.DoesNotExist:
            return Response(
                {"error": "Payroll organization not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PayrollOrgBusinessDetailView(APIView):
    def get(self, request, business_id):
        try:
            business = get_object_or_404(Business, id=business_id)
            # Check if PayrollOrg exists
            payroll_org = PayrollOrg.objects.filter(business=business_id).first()
            organisation_details = bool(payroll_org)

            response_data = {
                "business": business.id,
                "organisation_name": business.nameOfBusiness,
                "organisation_address": business.headOffice,
                # Checking existence of related objects
                "organisation_details": organisation_details,
                "payroll_id": payroll_org.id if organisation_details else None,
                "work_locations": WorkLocations.objects.filter(
                    payroll=payroll_org.id).exists() or payroll_org.work_location if organisation_details else False,
                "departments": Departments.objects.filter(payroll=payroll_org.id).exists() or payroll_org.department
                if organisation_details else False,
                "designations": Designation.objects.filter(payroll=payroll_org.id).exists() or payroll_org.designation
                if organisation_details else False,

                # Checking statutory components
                "statutory_component": (
                    payroll_org.statutory_component
                    if payroll_org.statutory_component is True
                    else (
                            EPF.objects.filter(payroll=payroll_org.id).exists()
                            and ESI.objects.filter(payroll=payroll_org.id).exists()
                            and PT.objects.filter(payroll=payroll_org.id).exists()
                    )
                ) if organisation_details else False,

                "salary_component": (
                    payroll_org.salary_component
                    if payroll_org.salary_component is True
                    else (
                            Earnings.objects.filter(payroll=payroll_org.id).exists()
                            # and Benefits.objects.filter(payroll=payroll_org.id).exists()
                            # and Deduction.objects.filter(payroll=payroll_org.id).exists()
                            # and Reimbursement.objects.filter(payroll=payroll_org.id).exists()
                    )
                ) if organisation_details else False,
                "pay_schedule": payroll_org.pay_schedule or PaySchedule.objects.filter(payroll=payroll_org.id).exists()
                if organisation_details else False,
                "leave_and_attendance": (LeaveManagement.objects.filter(payroll=payroll_org.id).exists()) and (
                            HolidayManagement.objects.filter(payroll=payroll_org.id).exists()) if organisation_details
                else False,
                "employee_master": (payroll_org.employee_master or
                                    EmployeeManagement.objects.filter(payroll=payroll_org.id).exists())
                if organisation_details else False,
                "salary_template": payroll_org.salary_template or
                                   SalaryTemplate.objects.filter(payroll=payroll_org.id).exists()
                if organisation_details else False
                }

            return Response(response_data,  status=status.HTTP_200_OK)

        except Business.DoesNotExist:
            return Response({"error": "Business does not exists, Please set up the Business"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# List all WorkLocations
@api_view(['GET'])
def work_location_list(request):
    business_id = request.query_params.get('business_id')
    payroll_id = request.query_params.get('payroll_id')
    try:
        if payroll_id:
            # Retrieve Work Locations for given payroll
            payroll_org = PayrollOrg.objects.get(id=payroll_id)
            business = payroll_org.business  # Fetch business linked to PayrollOrg

            work_locations = WorkLocations.objects.filter(payroll=payroll_org)
            work_location_data = WorkLocationSerializer(work_locations, many=True).data
            return Response(work_location_data, status=status.HTTP_200_OK)

        return Response({"error": "Either business_id or payroll_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    except Business.DoesNotExist:
        return Response({"error": "Invalid Business ID"}, status=status.HTTP_404_NOT_FOUND)

    except PayrollOrg.DoesNotExist:
        return Response({"error": "Invalid Payroll ID"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Create a new WorkLocation
@api_view(['POST'])
def work_location_create(request):
    if request.method == 'POST':
        serializer = WorkLocationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def bulk_work_location_upload(request):
    # Get payroll_id from form data
    payroll_id = request.data.get('payroll_id')
    if not payroll_id:
        return Response({"error": "Payroll ID is required in the form data."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Fetch PayrollOrg based on payroll_id
        payroll_org = PayrollOrg.objects.get(id=payroll_id)
    except PayrollOrg.DoesNotExist:
        return Response({"error": "PayrollOrg not found."}, status=status.HTTP_404_NOT_FOUND)

    # Check if file is provided
    file = request.FILES.get('file')
    if not file:
        return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

    # Check file format (CSV or Excel)
    if file.name.endswith('.csv'):
        try:
            data = csv.DictReader(TextIOWrapper(file, encoding='utf-8'))
            records = list(data)
        except Exception as e:
            return Response({"error": f"CSV file reading failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    elif file.name.endswith('.xlsx'):
        try:
            df = pd.read_excel(file)
            records = df.to_dict(orient='records')
        except Exception as e:
            return Response({"error": f"Excel file reading failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error": "Unsupported file format. Please upload CSV or Excel."},
                        status=status.HTTP_400_BAD_REQUEST)

    # Validate and Save Records
    errors = []
    for record in records:
        record['payroll'] = payroll_org  # Add payroll to each record manually
        serializer = WorkLocationSerializer(data=record)
        if serializer.is_valid():
            serializer.save()
        else:
            errors.append({"record": record, "errors": serializer.errors})

    if errors:
        return Response({"message": "Partial success", "errors": errors}, status=status.HTTP_207_MULTI_STATUS)

    return Response({"message": "All locations uploaded successfully."}, status=status.HTTP_201_CREATED)


# Retrieve a specific WorkLocation by ID
@api_view(['GET'])
def work_location_detail(request, pk):
    try:
        work_location = WorkLocations.objects.get(pk=pk)
    except WorkLocations.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = WorkLocationSerializer(work_location)
        return Response(serializer.data)


# Update a specific WorkLocation by ID
@api_view(['PUT'])
def work_location_update(request, pk):
    try:
        work_location = WorkLocations.objects.get(pk=pk)
    except WorkLocations.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = WorkLocationSerializer(work_location, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Delete a specific WorkLocation by ID
@api_view(['DELETE'])
def work_location_delete(request, pk):
    try:
        work_location = WorkLocations.objects.get(pk=pk)
    except WorkLocations.DoesNotExist:
        return Response({"error": "Work location not found"}, status=status.HTTP_404_NOT_FOUND)

    work_location.delete()
    return Response({"message": "Work location deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# List and create departments
@api_view(['GET', 'POST'])
def department_list(request):
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')  # Get payroll_id from query parameters

        if payroll_id:
            # Filter departments by payroll_id
            departments = Departments.objects.filter(payroll_id=payroll_id).order_by('-id')
        else:
            # Retrieve all departments if no payroll_id is provided
            departments = Departments.objects.all().order_by('-id')

        serializer = DepartmentsSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = DepartmentsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def parse_file(file):
    """
    Parse the uploaded file into a list of records.
    Supports CSV and Excel file formats.
    """
    if file.name.endswith('.csv'):
        try:
            data = csv.DictReader(TextIOWrapper(file, encoding='utf-8'))
            return list(data), None
        except Exception as e:
            return None, f"CSV file reading failed: {str(e)}"

    elif file.name.endswith('.xlsx'):
        try:
            df = pd.read_excel(file)
            return df.to_dict(orient='records'), None
        except Exception as e:
            return None, f"Excel file reading failed: {str(e)}"

    return None, "Unsupported file format. Please upload CSV or Excel."


@api_view(['POST'])
def bulk_department_upload(request):
    # Validate payroll_id
    payroll_id = request.data.get('payroll_id')
    if not payroll_id:
        return Response({"error": "Payroll ID is required in the form data."}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch PayrollOrg
    try:
        payroll_org = PayrollOrg.objects.get(id=payroll_id)
    except PayrollOrg.DoesNotExist:
        return Response({"error": "PayrollOrg not found."}, status=status.HTTP_404_NOT_FOUND)

    # Check for file in request
    file = request.FILES.get('file')
    if not file:
        return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

    # Parse file based on format (CSV or Excel)
    records, parse_error = parse_file(file)
    if parse_error:
        return Response({"error": parse_error}, status=status.HTTP_400_BAD_REQUEST)

    # Validate and save each record
    errors = []
    for record in records:
        record['payroll'] = payroll_org  # Assign payroll org to each record
        serializer = DepartmentsSerializer(data=record)
        if serializer.is_valid():
            serializer.save()
        else:
            errors.append({"record": record, "errors": serializer.errors})

    if errors:
        return Response({"message": "Partial success", "errors": errors}, status=status.HTTP_207_MULTI_STATUS)

    return Response({"message": "All departments uploaded successfully."}, status=status.HTTP_201_CREATED)


# Retrieve, update or delete a specific department
@api_view(['GET', 'PUT', 'DELETE'])
def department_detail(request, pk):
    try:
        department = Departments.objects.get(pk=pk)
    except Departments.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = DepartmentsSerializer(department)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = DepartmentsSerializer(department, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        department.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# List and create Designations
@api_view(['GET', 'POST'])
def designation_list(request):
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')  # Get payroll_id from query parameters

        if payroll_id:
            # Filter designations by payroll_id
            designations = Designation.objects.filter(payroll_id=payroll_id).order_by('-id')
        else:
            # Retrieve all designations if no payroll_id is provided
            designations = Designation.objects.all().order_by('-id')
        serializer = DesignationSerializer(designations, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = DesignationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Retrieve, update, or delete a specific Designation
@api_view(['GET', 'PUT', 'DELETE'])
def designation_detail(request, pk):
    try:
        designation = Designation.objects.get(pk=pk)
    except Designation.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = DesignationSerializer(designation)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = DesignationSerializer(designation, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        designation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def bulk_designation_upload(request):
    # Validate payroll_id
    payroll_id = request.data.get('payroll_id')
    if not payroll_id:
        return Response({"error": "Payroll ID is required in the form data."}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch PayrollOrg
    try:
        payroll_org = PayrollOrg.objects.get(id=payroll_id)
    except PayrollOrg.DoesNotExist:
        return Response({"error": "PayrollOrg not found."}, status=status.HTTP_404_NOT_FOUND)

    # Check for file in request
    file = request.FILES.get('file')
    if not file:
        return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

    # Parse file based on format (CSV or Excel)
    records, parse_error = parse_file(file)
    if parse_error:
        return Response({"error": parse_error}, status=status.HTTP_400_BAD_REQUEST)

    # Validate and save each record
    errors = []
    for record in records:
        record['payroll'] = payroll_org  # Assign payroll org to each record
        serializer = DesignationSerializer(data=record)
        if serializer.is_valid():
            serializer.save()
        else:
            errors.append({"record": record, "errors": serializer.errors})

    if errors:
        return Response({"message": "Partial success", "errors": errors}, status=status.HTTP_207_MULTI_STATUS)

    return Response({"message": "All departments uploaded successfully."}, status=status.HTTP_201_CREATED)


# List and create EPF details
@api_view(['GET', 'POST'])
def epf_list(request):
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')  # Get payroll_id from query parameters

        if payroll_id:
            # Since payroll is a OneToOneField, there will be at most one EPF record for a given payroll_id
            try:
                epf_details = EPF.objects.get(payroll=payroll_id)  # Fetch EPF details for the specific payroll
                serializer = EPFSerializer(epf_details)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except EPF.DoesNotExist:
                return Response({"error": "EPF details not found for the given payroll ID."}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Retrieve all EPF details if no payroll_id is provided
            epf_details = EPF.objects.all()
            serializer = EPFSerializer(epf_details, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = EPFSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Ensure there is no existing EPF record for the given payroll_id
                payroll_id = serializer.validated_data.get('payroll').id
                if EPF.objects.filter(payroll_id=payroll_id).exists():
                    return Response({"error": "EPF details already exist for this payroll ID."}, status=status.HTTP_400_BAD_REQUEST)

                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Retrieve, update, or delete specific EPF details
@api_view(['GET', 'PUT', 'DELETE'])
def epf_detail(request, pk):
    try:
        epf = EPF.objects.get(pk=pk)
    except EPF.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EPFSerializer(epf)
        return Response(serializer.data,  status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = EPFSerializer(epf, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        epf.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# List and create ESI details
@api_view(['GET', 'POST'])
def esi_list(request):
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')  # Get payroll_id from query parameters

        if payroll_id:
            # Since payroll is a OneToOneField, there will be at most one ESI record for a given payroll_id
            try:
                esi_details = ESI.objects.get(payroll_id=payroll_id)  # Fetch ESI details for the specific payroll
                serializer = ESISerializer(esi_details)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ESI.DoesNotExist:
                return Response({"error": "ESI details not found for the given payroll ID."}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Retrieve all ESI details if no payroll_id is provided
            esi_details = ESI.objects.all()
            serializer = ESISerializer(esi_details, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = ESISerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Ensure there is no existing ESI record for the given payroll_id
                payroll_id = serializer.validated_data.get('payroll').id
                if ESI.objects.filter(payroll_id=payroll_id).exists():
                    return Response({"error": "ESI details already exist for this payroll ID."}, status=status.HTTP_400_BAD_REQUEST)

                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Retrieve, update, or delete specific ESI details
@api_view(['GET', 'PUT', 'DELETE'])
def esi_detail(request, pk):
    try:
        esi = ESI.objects.get(pk=pk)
    except ESI.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ESISerializer(esi)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ESISerializer(esi, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        esi.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def pt_list(request):
    """
    List PF records or create a new one, based on payroll_id.
    """
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')

        if not payroll_id:
            return Response({"error": "payroll_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        pt_instances = PT.objects.filter(payroll_id=payroll_id)

        if not pt_instances.exists():
            # Fetch work locations linked to this payroll_id
            work_location_instances = WorkLocations.objects.filter(payroll_id=payroll_id)

            if not work_location_instances.exists():
                return Response({"error": "No PT records or work locations found for the given payroll ID."},
                                status=status.HTTP_404_NOT_FOUND)

            # Create PT objects dynamically
            pt_objects = []
            for wl in work_location_instances:
                pt = PT(payroll_id=payroll_id, work_location=wl)
                pt.save()  # Automatically assigns the slab in the model's `save()` method
                pt_objects.append(pt)

            # Fetch newly created PT objects
            pt_instances = PT.objects.filter(payroll_id=payroll_id)

        serializer = PTSerializerRetrieval(pt_instances, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = PTSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def pt_detail(request, pk):
    """
    Retrieve, update or delete a PF record.
    """
    try:
        pt_instance = PT.objects.get(pk=pk)
    except PT.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PTSerializerRetrieval(pt_instance)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = PTSerializer(pt_instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        pt_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def earnings_list(request):
    """
    List all Earnings records, or create a new one.
    """
    if request.method == 'GET':
        try:
            payroll_id = request.query_params.get('payroll_id')

            if not payroll_id:
                return Response({"error": "payroll_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                payroll_instance = PayrollOrg.objects.get(id=payroll_id)  # Fetch PayrollOrg instance
            except PayrollOrg.DoesNotExist:
                return Response({"error": "Invalid payroll_id"}, status=status.HTTP_400_BAD_REQUEST)

            # Filter earnings by payroll instance
            earnings = Earnings.objects.filter(payroll=payroll_instance)
            if not earnings.exists():
                created_earnings = []  # Track created earnings to manually delete on error
                try:
                    with transaction.atomic():  # Ensures all-or-nothing behavior
                        for earning_data in default_earnings:
                            earning_data['payroll'] = payroll_instance.id  # Assign ID

                            # Validate and save using serializer
                            serializer = EarningsSerializer(data=earning_data)
                            if serializer.is_valid(raise_exception=True):
                                created_earning = serializer.save()
                                created_earnings.append(created_earning)  # Track created object
                            else:
                                raise DatabaseError("Earning data is invalid, transaction will be rolled back.")
                except (ValidationError, DatabaseError) as e:
                    # Handle exceptions gracefully and rollback
                    # Manually delete created earnings if an error occurs
                    for earning in created_earnings:
                        earning.delete()
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    # Clean up if something unexpected happens
                    for earning in created_earnings:
                        earning.delete()
                    return Response({"error": f"Unexpected error occurred: {str(e)}"},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # If everything works, get the earnings
                earnings = Earnings.objects.filter(payroll=payroll_instance)

            serializer = EarningsSerializerRetrieval(earnings, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Unexpected error occurred: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        data = request.data.copy()
        payroll_id = data.get('payroll')
        if not payroll_id:
            return Response({"error": "payroll_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = EarningsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def earnings_in_payslip(request):
    """
    API to retrieve earnings where `is_included_in_payslip=True` for a specific payroll.
    """
    payroll_id = request.query_params.get('payroll_id')

    if not payroll_id:
        return Response({"error": "payroll_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    payroll_instance = get_object_or_404(PayrollOrg, id=payroll_id)

    # Filter only earnings included in payslip
    earnings = Earnings.objects.filter(payroll=payroll_instance, is_included_in_payslip=True)

    if not earnings.exists():
        return Response({"message": "No earnings found for the given payroll with is_included_in_payslip=True"},
                        status=status.HTTP_404_NOT_FOUND)

    serializer = EarningsSerializerRetrieval(earnings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'DELETE'])
def earnings_detail(request, pk):
    """
    Retrieve, update, or delete an Earnings record.
    """
    try:
        earnings = Earnings.objects.get(pk=pk)
    except Earnings.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EarningsSerializer(earnings)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = EarningsSerializer(earnings, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        earnings.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def benefits_list_create(request):
    """
    Handles GET (list) and POST (create) for Benefits.
    - GET: Returns a list of all Benefits, optionally filtered by `payroll` or `payslip_name`.
    - POST: Creates a new Benefit entry.
    """
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll')
        payslip_name = request.query_params.get('payslip_name')

        # Filter Benefits based on query parameters if provided
        benefits = Benefits.objects.all()
        if payroll_id:
            benefits = benefits.filter(payroll_id=payroll_id)
        if payslip_name:
            benefits = benefits.filter(payslip_name=payslip_name)

        serializer = BenefitsSerializer(benefits, many=True)
        return Response({"data": serializer.data, "message": "Benefits retrieved successfully."}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = BenefitsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Benefit created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def benefits_detail_update_delete(request, benefit_id):
    """
    Handles GET, PUT, and DELETE for a single Benefit based on its ID.
    - GET: Retrieves details of a specific Benefit.
    - PUT: Updates a specific Benefit.
    - DELETE: Deletes a specific Benefit.
    """
    try:
        benefit = Benefits.objects.get(id=benefit_id)
    except Benefits.DoesNotExist:
        return Response({"error": "Benefit not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = BenefitsSerializer(benefit)
        return Response({"data": serializer.data, "message": "Benefit retrieved successfully."},
                        status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = BenefitsSerializer(benefit, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Benefit updated successfully."},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        benefit.delete()
        return Response({"message": "Benefit deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def deduction_list_create(request):
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')  # Get payroll_id from query parameters

        if payroll_id:
            # Filter designations by payroll_id
            deductions = Deduction.objects.filter(payroll_id=payroll_id)
        else:
            # Retrieve all designations if no payroll_id is provided
            deductions = Deduction.objects.all()
        serializer = DeductionSerializer(deductions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'POST':
        serializer = DeductionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def deduction_detail(request, id):
    try:
        deduction = Deduction.objects.get(id=id)
    except Deduction.DoesNotExist:
        return Response({"error": "Deduction not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = DeductionSerializer(deduction)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'PUT':
        serializer = DeductionSerializer(deduction, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        deduction.delete()
        return Response({"message": "Deduction deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def reimbursement_list_create(request):
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')  # Get payroll_id from query parameters

        if payroll_id:
            # Filter reimbursements by payroll_id
            reimbursements = Reimbursement.objects.filter(payroll_id=payroll_id)
        else:
            # Retrieve all reimbursements if no payroll_id is provided
            reimbursements = Reimbursement.objects.all()
        serializer = ReimbursementSerializer(reimbursements, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'POST':
        serializer = ReimbursementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def reimbursement_detail(request, id):
    try:
        reimbursement = Reimbursement.objects.get(id=id)
    except Reimbursement.DoesNotExist:
        return Response({"error": "Reimbursement not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ReimbursementSerializer(reimbursement)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'PUT':
        serializer = ReimbursementSerializer(reimbursement, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        reimbursement.delete()
        return Response({"message": "Reimbursement deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def salary_template_list_create(request):
    """
    Handles GET (list) and POST (create) for Salary Templates.
    - GET: Returns a list of all Salary Templates, optionally filtered by `payroll` or `template_name`.
    - POST: Creates a new Salary Template entry.
    """
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')
        template_name = request.query_params.get('template_name')

        if payroll_id:
            salary_templates = SalaryTemplate.objects.filter(payroll_id=payroll_id)

        serializer = SalaryTemplateSerializer(salary_templates, many=True)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = SalaryTemplateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Salary Template created successfully."},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
def calculate_payroll(request):
    try:
        data = request.data
        annual_ctc = float(data["annual_ctc"])

        # Extract Earnings
        earnings = data["earnings"]
        basic_salary = next((item for item in earnings if item["component_name"] == "Basic"), None)

        if not basic_salary:
            return Response({"errorMessage": "Basic component is required"}, status=status.HTTP_400_BAD_REQUEST)

        basic_annual = basic_salary["annually"]
        basic_monthly = basic_annual / 12
        pf_restricted_wage = min(basic_annual, 180000)  # Max PF restricted wage = 15000 per month (180000 per year)

        # Compute Benefits
        benefits = {}

        # EPF (Always applicable)
        benefits["EPF"] = {
            "monthly": 0.12 * pf_restricted_wage / 12,
            "annually": 0.12 * pf_restricted_wage,
            "calculation_type": "Percentage (12%) of PF wage"
        }

        # EDLI & Admin Charges
        if basic_monthly <= 15000:
            benefits["EDLI"] = {
                "monthly": 0.005 * pf_restricted_wage / 12,
                "annually": 0.005 * pf_restricted_wage,
                "calculation_type": "Percentage (0.5%) of PF wage"
            }
            benefits["EPF admin charges"] = {
                "monthly": 0.005 * pf_restricted_wage / 12,
                "annually": 0.005 * pf_restricted_wage,
                "calculation_type": "Percentage (0.5%) of PF wage"
            }
        else:
            benefits["EDLI"] = {
                "monthly": 75,
                "annually": 900,
                "calculation_type": "Fixed Amount"
            }
            benefits["EPF admin charges"] = {
                "monthly": 75,
                "annually": 900,
                "calculation_type": "Fixed Amount"
            }

        # ESI (Only if PF wage is <= 21000)
        if basic_monthly <= 21000:
            benefits["ESI"] = {
                "monthly": 0.0325 * pf_restricted_wage / 12,
                "annually": 0.0325 * pf_restricted_wage,
                "calculation_type": "Percentage (3.25%) of PF wage"
            }
        else:
            benefits["ESI"] = {
                "monthly": 0,
                "annually": 0,
                "calculation_type": "Not Applicable"
            }

        total_benefits = sum(item["annually"] for item in benefits.values())

        # Adjust Fixed Allowance so that Gross Salary = Annual CTC - Benefits
        total_earnings = sum(item["annually"] for item in earnings if item["component_name"] != "Fixed Allowance")
        fixed_allowance = annual_ctc - total_benefits - total_earnings

        for earning in earnings:
            if earning["component_name"] == "Fixed Allowance":
                earning["annually"] = fixed_allowance
                earning["monthly"] = fixed_allowance / 12

        gross_salary = sum(item["annually"] for item in earnings)

        # Compute Deductions
        deductions = {
            "EPF Employee Contribution": {
                "monthly": 0.12 * pf_restricted_wage / 12,
                "annually": 0.12 * pf_restricted_wage,
                "calculation_type": "Percentage (12%) of PF wage"
            },
            "ESI Employee Contribution": {
                "monthly": (0.0075 * pf_restricted_wage / 12) if basic_monthly <= 21000 else 0,
                "annually": (0.0075 * pf_restricted_wage) if basic_monthly <= 21000 else 0,
                "calculation_type": "Percentage (0.75%) of PF wage" if basic_monthly <= 21000 else "Not Applicable"
            }
        }

        total_deductions = sum(item["annually"] for item in deductions.values())

        # Compute Net Salary
        net_salary = gross_salary - total_deductions

        # Compute Total CTC
        total_ctc = gross_salary + total_benefits

        # Prepare Response Data
        response_data = {
            "payroll": data.get('payroll', ''),
            "template_name": data["template_name"],
            "description": data["description"],
            "annual_ctc": annual_ctc,
            "earnings": earnings,
            "gross_salary": {"monthly": gross_salary / 12, "annually": gross_salary},
            "benefits": [
                {"component_name": key, **value} for key, value in benefits.items()
            ],
            "total_ctc": {"monthly": total_ctc / 12, "annually": total_ctc},
            "deductions": [
                {"component_name": key, **value} for key, value in deductions.items()
            ],
            "net_salary": {"monthly": net_salary / 12, "annually": net_salary},
            "errorMessage": ""
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"errorMessage": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def salary_template_detail_update_delete(request, template_id):
    """
    Handles GET, PUT, and DELETE for a single Salary Template based on its ID.
    - GET: Retrieves details of a specific Salary Template.
    - PUT: Updates a specific Salary Template.
    - DELETE: Deletes a specific Salary Template.
    """
    try:
        salary_template = SalaryTemplate.objects.get(id=template_id)
    except SalaryTemplate.DoesNotExist:
        return Response({"error": "Salary Template not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = SalaryTemplateSerializer(salary_template)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = SalaryTemplateSerializer(salary_template, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        salary_template.delete()
        return Response({"message": "Salary Template deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def pay_schedule_list_create(request):
    """
    Handles GET (list) and POST (create) for Pay Schedules.
    - GET: Returns a list of all Pay Schedules, optionally filtered by `payroll`.
    - POST: Creates a new Pay Schedule entry ensuring at least two days are selected.
    """
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')

        if payroll_id:
            try:
                pay_schedule = PaySchedule.objects.get(payroll_id=payroll_id)
                serializer = PayScheduleSerializer(pay_schedule)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ObjectDoesNotExist:
                return Response(
                    {"error": "No Pay Schedule found for the provided payroll_id."},
                    status=status.HTTP_404_NOT_FOUND
                )

        pay_schedules = PaySchedule.objects.all()
        serializer = PayScheduleSerializer(pay_schedules, many=True)
        return Response(
            {"data": serializer.data, "message": "Pay Schedules retrieved successfully."},
            status=status.HTTP_200_OK
        )

    elif request.method == 'POST':
        serializer = PayScheduleSerializer(data=request.data)
        if serializer.is_valid():
            days_selected = sum([
                serializer.validated_data.get(day, False) for day in [
                    'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'second_saturday',
                    'fourth_saturday'
                ]
            ])
            if days_selected < 2:
                return Response({"error": "At least two days must be selected."}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response({"data": serializer.data, "message": "Pay Schedule created successfully."},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def pay_schedule_detail_update_delete(request, schedule_id):
    """
    Handles GET, PUT, and DELETE for a single Pay Schedule based on its ID.
    - GET: Retrieves details of a specific Pay Schedule.
    - PUT: Updates a specific Pay Schedule ensuring at least two days are selected.
    - DELETE: Deletes a specific Pay Schedule.
    """
    try:
        pay_schedule = PaySchedule.objects.get(id=schedule_id)
    except PaySchedule.DoesNotExist:
        return Response({"error": "Pay Schedule not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PayScheduleSerializer(pay_schedule)
        return Response({"data": serializer.data, "message": "Pay Schedule retrieved successfully."},
                        status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = PayScheduleSerializer(pay_schedule, data=request.data)
        if serializer.is_valid():
            days_selected = sum([
                serializer.validated_data.get(day, False) for day in [
                    'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'second_saturday',
                    'fourth_saturday'
                ]
            ])
            if days_selected < 2:
                return Response({"error": "At least two days must be selected."}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response({"data": serializer.data, "message": "Pay Schedule updated successfully."},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        pay_schedule.delete()
        return Response({"message": "Pay Schedule deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def leave_management_list_create(request):
    """
    API for listing and creating Leave Management records.
    - GET: Retrieves all leave policies.
    - POST: Creates a new leave policy.
    """
    if request.method == 'GET':
        try:
            payroll_id = request.query_params.get('payroll_id')
            if not payroll_id:
                return Response({"error": "payroll_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                payroll_instance = PayrollOrg.objects.get(id=payroll_id)  # Fetch PayrollOrg instance
            except PayrollOrg.DoesNotExist:
                return Response({"error": "Invalid payroll_id"}, status=status.HTTP_400_BAD_REQUEST)
            leaves = LeaveManagement.objects.filter(payroll=payroll_id)
            if not leaves.exists():
                created_leaves = []  # Track created earnings to manually delete on error
                try:
                    with transaction.atomic():  # Ensures all-or-nothing behavior
                        for leaves_data in default_leave_management:
                            leaves_data['payroll'] = payroll_instance.id
                            # Validate and save using serializer
                            serializer = LeaveManagementSerializer(data=leaves_data)
                            if serializer.is_valid(raise_exception=True):
                                created_leave = serializer.save()
                                created_leaves.append(created_leave)  # Track created object
                            else:
                                raise DatabaseError("Earning data is invalid, transaction will be rolled back.")
                except (ValidationError, DatabaseError) as e:
                    # Handle exceptions gracefully and rollback
                    # Manually delete created earnings if an error occurs
                    for leaves in created_leaves:
                        leaves.delete()
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    # Clean up if something unexpected happens
                    for leaves in created_leaves:
                        leaves.delete()
                    return Response({"error": f"Unexpected error occurred: {str(e)}"},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                # If everything works, get the leaves
                leaves = LeaveManagement.objects.filter(payroll=payroll_id)
            serializer = LeaveManagementSerializer(leaves, many=True)
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Unexpected error occurred: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif request.method == 'POST':
        serializer = LeaveManagementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Leave Management record created successfully."},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def leave_management_detail_update_delete(request, leave_id):
    """
    API for retrieving, updating, and deleting a single Leave Management record.
    """
    try:
        leave = LeaveManagement.objects.get(id=leave_id)
    except LeaveManagement.DoesNotExist:
        return Response({"error": "Leave Management record not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = LeaveManagementSerializer(leave)
        return Response({"data": serializer.data, "message": "Leave Management record retrieved successfully."},
                        status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = LeaveManagementSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        leave.delete()
        return Response({"message": "Leave Management record deleted successfully."},
                        status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def holiday_management_list_create(request):
    """
    API for listing and creating Holiday Management records.
    - GET: Retrieves all holidays.
    - POST: Creates a new holiday entry.
    """
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')
        holidays = HolidayManagement.objects.all()
        if payroll_id:
            holidays = holidays.filter(payroll_id=payroll_id)

        serializer = HolidayManagementSerializer(holidays, many=True)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = HolidayManagementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def holiday_management_filtered_list(request):
    """
    API for retrieving Holiday Management records based on payroll_id, financial_year, and applicable_for.
    - GET: Retrieves holidays filtered by provided query parameters.
    """
    filters = {}

    payroll_id = request.query_params.get('payroll_id')
    financial_year = request.query_params.get('financial_year')
    applicable_for = request.query_params.get('applicable_for')

    if payroll_id:
        filters['payroll_id'] = payroll_id
    if financial_year:
        filters['financial_year'] = financial_year
    if applicable_for:
        filters['applicable_for'] = applicable_for

    holidays = HolidayManagement.objects.filter(**filters)  # Apply filters directly

    serializer = HolidayManagementSerializer(holidays, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'DELETE'])
def holiday_management_detail_update_delete(request, holiday_id):
    """
    API for retrieving, updating, and deleting a single Holiday Management record.
    """
    try:
        holiday = HolidayManagement.objects.get(id=holiday_id)
    except HolidayManagement.DoesNotExist:
        return Response({"error": "Holiday Management record not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = HolidayManagementSerializer(holiday)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = HolidayManagementSerializer(holiday, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        holiday.delete()
        return Response({"message": "Holiday Management record deleted successfully."},
                        status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def employee_list(request):
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')
        if payroll_id:
            employees = EmployeeManagement.objects.filter(payroll_id=payroll_id)
        else:
            employees = EmployeeManagement.objects.all()
        serializer = EmployeeDataSerializer(employees, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = EmployeeManagementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def employee_detail(request, pk):
    employee = get_object_or_404(EmployeeManagement, pk=pk)

    if request.method == 'GET':
        serializer = EmployeeDataSerializer(employee)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = EmployeeManagementSerializer(employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        employee.delete()
        return Response({"message": "Employee data Removed Successfully."},
                        status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def new_employees_list(request):
    try:
        payroll_id = request.query_params.get('payroll_id')
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        # Default to current date if month/year are not provided
        current_date = now().date()
        month = int(month) if month else current_date.month
        year = int(year) if year else current_date.year

        # Get the first day of the selected month
        start_of_month = datetime(year, month, 1).date()

        # Calculate the last day of the month dynamically
        next_month = start_of_month.replace(day=28) + timedelta(days=4)
        last_day_of_month = next_month - timedelta(days=next_month.day)

        filter_criteria = {
            "doj__gte": start_of_month,
            "doj__lte": last_day_of_month
        }

        if payroll_id:
            filter_criteria["payroll_id"] = payroll_id

        employees = EmployeeManagement.objects.filter(**filter_criteria)

        # If no employees found, return an empty list with a message
        if not employees.exists():
            return Response(
                {"message": "No employees found for the given criteria."},
                status=status.HTTP_200_OK
            )

        # Serialize and return data
        serializer = CurrentMonthEmployeeDataSerializer(employees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": "Something went wrong!", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Employee Salary Views
@api_view(['GET', 'POST'])
def employee_salary_list(request):
    if request.method == 'GET':
        employee_id = request.query_params.get('employee_id')
        if employee_id:
            salaries = EmployeeSalaryDetails.objects.filter(employee=employee_id)
        else:
            salaries = EmployeeSalaryDetails.objects.all()
        serializer = EmployeeSalaryDetailsSerializer(salaries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = EmployeeSalaryDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def employee_salary_detail(request, pk):
    """
    Handles GET, PUT, and DELETE for a single Employee Salary based on its ID.
    - GET: Retrieves details of a specific Employee Salary.
    - PUT: Updates a specific Employee Salary.
    - DELETE: Deletes a specific Employee Salary.
    """
    employee_salary_details = get_object_or_404(EmployeeSalaryDetails, pk=pk)

    if request.method == 'GET':
        serializer = EmployeeSalaryDetailsSerializer(employee_salary_details)
        return Response(
            {"data": serializer.data, "message": "Salary details retrieved successfully."},
            status=status.HTTP_200_OK
        )

    elif request.method == 'PUT':
        serializer = EmployeeSalaryDetailsSerializer(employee_salary_details, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"data": serializer.data, "message": "Salary details updated successfully."},
                status=status.HTTP_200_OK
            )
        return Response(
            {"errors": serializer.errors, "message": "Validation failed."},
            status=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == 'DELETE':
        employee_salary_details.delete()
        return Response(
            {"message": "Salary details deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

    return Response(
        {"error": "Invalid request method."},
        status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


# Employee Personal Details Views
@api_view(['GET', 'POST'])
def employee_personal_list(request):
    if request.method == 'GET':
        employee_id = request.query_params.get('employee_id')
        if employee_id:
            personal_details = EmployeePersonalDetails.objects.filter(employee=employee_id)
        else:
            personal_details = EmployeePersonalDetails.objects.all()
        serializer = EmployeePersonalDetailsSerializer(personal_details, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = EmployeePersonalDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def employee_personal_detail(request, pk):
    personal_detail = get_object_or_404(EmployeePersonalDetails, pk=pk)

    if request.method == 'GET':  # Retrieve personal details
        serializer = EmployeePersonalDetailsSerializer(personal_detail)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':  # Update personal details
        serializer = EmployeePersonalDetailsSerializer(personal_detail, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':  # Delete personal details
        personal_detail.delete()
        return Response({"message": "Employee Personal details deleted successfully."},
                        status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def employee_bank_list(request):
    """
    Handles listing a single employee's bank details or all entries and allows adding new entries.
    """
    if request.method == 'GET':
        employee_id = request.query_params.get('employee_id')

        if employee_id:
            bank_detail = get_object_or_404(EmployeeBankDetails, employee=employee_id)
            serializer = EmployeeBankDetailsSerializer(bank_detail)
            return Response(serializer.data,
                            status=status.HTTP_200_OK)

        bank_details = EmployeeBankDetails.objects.all()
        serializer = EmployeeBankDetailsSerializer(bank_details, many=True)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = EmployeeBankDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors, "message": "Invalid data provided."},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def employee_bank_detail(request, pk):
    """
    Handles retrieving, updating, and deleting an employee bank detail by ID.
    """
    bank_detail = get_object_or_404(EmployeeBankDetails, pk=pk)

    if request.method == 'GET':
        serializer = EmployeeBankDetailsSerializer(bank_detail)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = EmployeeBankDetailsSerializer(bank_detail, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        bank_detail.delete()
        return Response({"message": "Bank detail deleted successfully."},
                        status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def employee_exit_list(request):
    """
    Handles listing all employee exit records or a single employee's exit record.
    Allows adding new employee exit records.
    """
    if request.method == 'GET':
        employee_id = request.query_params.get('employee_id')

        if employee_id:
            exit_detail = get_object_or_404(EmployeeExit, employee=employee_id)
            serializer = EmployeeExitSerializer(exit_detail)
            return Response(serializer.data, status=status.HTTP_200_OK)

        exit_details = EmployeeExit.objects.all()
        serializer = EmployeeExitSerializer(exit_details, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = EmployeeExitSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"errors": serializer.errors, "message": "Invalid data provided."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def employee_exit_detail(request, pk):
    """
    Handles retrieving, updating, and deleting an employee exit record by ID.
    """
    exit_detail = get_object_or_404(EmployeeExit, pk=pk)

    if request.method == 'GET':
        serializer = EmployeeExitSerializer(exit_detail)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = EmployeeExitSerializer(exit_detail, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        exit_detail.delete()
        return Response({"message": "Employee exit record deleted successfully."},
                        status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def payroll_exit_settlement_details(request):
    """
    API to retrieve exit details for all employees under a specific payroll in the current month.
    Returns: Employee Name, Department, Designation, Exit Date, Total Days, Paid Days, Settlement Start Date, Annual CTC, Final Settlement Amount.
    """
    payroll_id = request.query_params.get('payroll_id')
    if not payroll_id:
        return Response({"error": "Payroll ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Get current month and year
    current_date = now()
    year, month = current_date.year, current_date.month
    _, total_days_in_month = monthrange(year, month)

    # Get Employees under Payroll
    employees = EmployeeManagement.objects.filter(payroll_id=payroll_id)
    if not employees.exists():
        return Response({"error": "No employees found for the given payroll ID."}, status=status.HTTP_404_NOT_FOUND)

    # Get Employees who exited this month
    exits = EmployeeExit.objects.filter(
        employee__payroll_id=payroll_id,
        doe__gte=datetime(year, month, 1).date(),
        doe__lte=datetime(year, month, total_days_in_month).date()
    )

    if not exits.exists():
        return Response([], status=status.HTTP_200_OK)

    response_data = []

    for exit_detail in exits:
        employee = exit_detail.employee

        # Fetch Salary Details (Latest Active Salary)
        salary_details = EmployeeSalaryDetails.objects.filter(employee=employee, valid_to__isnull=True).first()
        annual_ctc = salary_details.annual_ctc if salary_details else 0

        # Fetch Holidays for the Month
        holidays = set(HolidayManagement.objects.filter(
            payroll=employee.payroll,
            start_date__gte=datetime(year, month, 1).date(),
            start_date__lte=datetime(year, month, total_days_in_month).date()
        ).values_list('start_date', flat=True))

        # Fetch PaySchedule for Weekends & Off Days
        pay_schedule = PaySchedule.objects.filter(payroll=employee.payroll).first()
        off_days = set()
        for day in range(1, total_days_in_month + 1):
            date_obj = datetime(year, month, day).date()
            weekday = date_obj.weekday()  # 0 = Monday, 6 = Sunday

            if pay_schedule:
                if (weekday == 0 and pay_schedule.monday) or \
                   (weekday == 1 and pay_schedule.tuesday) or \
                   (weekday == 2 and pay_schedule.wednesday) or \
                   (weekday == 3 and pay_schedule.thursday) or \
                   (weekday == 4 and pay_schedule.friday) or \
                   (weekday == 5 and pay_schedule.saturday) or \
                   (weekday == 6 and pay_schedule.sunday):
                    off_days.add(date_obj)

                # Handle Second & Fourth Saturday
                if pay_schedule.second_saturday and (day >= 8 and day <= 14 and weekday == 5):
                    off_days.add(date_obj)
                if pay_schedule.fourth_saturday and (day >= 22 and day <= 28 and weekday == 5):
                    off_days.add(date_obj)

        # Calculate Paid Days (Excluding Holidays & Off Days)
        paid_days = total_days_in_month - len(holidays) - len(off_days)
        paid_days = max(0, paid_days)  # Ensure no negative values

        # Calculate Final Settlement (Assume F&F is Gross Salary / Total Days * Paid Days)
        gross_salary = salary_details.gross_salary.get('monthly', 0) if salary_details and salary_details.gross_salary else 0
        final_settlement = (gross_salary / total_days_in_month) * paid_days if gross_salary else 0

        # Append Data
        response_data.append({
            "employee_name": f"{employee.first_name} {employee.middle_name} {employee.last_name}".strip(),
            "id": exit_detail.id,
            "department": employee.department.dept_name,
            "designation": employee.designation.designation_name,
            "exit_date": exit_detail.doe,
            "total_days": total_days_in_month,
            "paid_days": paid_days,
            "settlement_sdate": exit_detail.doe,  # Assuming settlement starts on exit date
            "annual_ctc": annual_ctc,
            "final_settlement_amount": round(final_settlement, 2)
        })

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def advance_loan_list(request):
    """
    Handles listing all advance loans or retrieving a specific employee's advance loan.
    Allows creating new advance loan entries.
    """
    if request.method == 'GET':
        employee_id = request.query_params.get('employee_id')

        if employee_id:
            loan_detail = get_object_or_404(AdvanceLoan, employee_id=employee_id)
            serializer = AdvanceLoanSerializer(loan_detail)
            return Response(serializer.data, status=status.HTTP_200_OK)

        loans = AdvanceLoan.objects.all()
        serializer = AdvanceLoanSerializer(loans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = AdvanceLoanSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"errors": serializer.errors, "message": "Invalid data provided."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def advance_loan_detail(request, pk):
    """
    Handles retrieving, updating, and deleting an advance loan by ID.
    """
    loan_detail = get_object_or_404(AdvanceLoan, pk=pk)

    if request.method == 'GET':
        serializer = AdvanceLoanDetailSerializer(loan_detail)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = AdvanceLoanSerializer(loan_detail, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        loan_detail.delete()
        return Response({"message": "Advance loan record deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def payroll_advance_loans(request):
    """
    API to retrieve advance loans for employees under a specific payroll for the given month/year.
    If no month/year is provided, defaults to the current month.
    """
    try:
        payroll_id = request.query_params.get('payroll_id')
        if not payroll_id:
            return Response({"error": "Payroll ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Use current date if no month/year is provided
        current_date = now().date()
        year = int(request.query_params.get('year', current_date.year))
        month = int(request.query_params.get('month', current_date.month))

        # Construct the first day of the selected month
        selected_month = date(year, month, 1)

        # Get Employees under Payroll
        employees = EmployeeManagement.objects.filter(payroll_id=payroll_id)
        if not employees.exists():
            return Response({"error": "No employees found for the given payroll ID."}, status=status.HTTP_404_NOT_FOUND)

        # Get Active Loans for Employees in This Payroll
        loans = AdvanceLoan.objects.filter(
            employee__payroll=payroll_id,
            start_month__lte=selected_month,  # Loan must have started before or in the selected month
            end_month__gte=selected_month     # Loan must end after or in the selected month
        )

        if not loans.exists():
            return Response([], status=status.HTTP_200_OK)

        # Serialize the data
        serializer = AdvanceLoanSummarySerializer(loans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def employee_attendance_list(request):
    """
    Handles listing all employee attendance records or filtering by employee_id.
    Allows adding new employee attendance records.
    """
    if request.method == 'GET':
        employee_id = request.query_params.get('employee_id')

        if employee_id:
            attendance_records = EmployeeAttendance.objects.filter(employee=employee_id)
            serializer = EmployeeAttendanceSerializer(attendance_records, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        attendance_records = EmployeeAttendance.objects.all()
        serializer = EmployeeAttendanceSerializer(attendance_records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = EmployeeAttendanceSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"errors": serializer.errors, "message": "Invalid data provided."},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def employee_attendance_detail(request, pk):
    """
    Handles retrieving, updating, and deleting an employee attendance record by ID.
    """
    attendance_record = get_object_or_404(EmployeeAttendance, pk=pk)

    if request.method == 'GET':
        serializer = EmployeeAttendanceSerializer(attendance_record)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = EmployeeAttendanceSerializer(attendance_record, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        attendance_record.delete()
        return Response({"message": "Employee attendance record deleted successfully."},
                        status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def employee_attendance_filtered(request):
    """
    Retrieves employee attendance records based on payroll_id, financial_year, and month.
    """
    payroll_id = request.query_params.get('payroll_id')
    financial_year = request.query_params.get('financial_year')
    month = request.query_params.get('month')

    # Validate required parameters
    if not payroll_id or not financial_year or not month:
        return Response({"error": "payroll_id, financial_year, and month are required."}, status=status.HTTP_400_BAD_REQUEST)

    # Filter records
    attendance_records = EmployeeAttendance.objects.filter(
        employee__payroll_id=payroll_id, financial_year=financial_year, month=month
    )

    if not attendance_records.exists():
        return Response({"message": "No records found for the given criteria."}, status=status.HTTP_404_NOT_FOUND)

    data = []
    for record in attendance_records:
        # Calculate values
        working_days = record.total_days_of_month - record.holidays - record.week_offs
        present_days = working_days - record.loss_of_pay
        payable_days = record.total_days_of_month - record.loss_of_pay

        data.append({
            "id": record.id,
            "employee_name": record.employee.first_name + ' ' + record.employee.last_name,
            "loss_of_pay": record.loss_of_pay,
            "earned_leaves": record.earned_leaves,
            "week_offs": record.week_offs,
            "holidays": record.holidays,
            "total_days_of_month": record.total_days_of_month,
            "present_days": present_days,
            "payable_days": payable_days
        })

    return Response(data, status=status.HTTP_200_OK)


def calculate_holidays_and_week_offs(payroll_id, year, month):
    """
    Calculates total holidays and week-offs for a given month using HolidayManagement and PaySchedule.
    """
    # Get the financial year in format "YYYY-YYYY"
    financial_year = f"{year}-{year + 1}" if month >= 4 else f"{year - 1}-{year}"
    financial_year_start = int(financial_year.split("-")[0])

    # Get total days in the month
    total_days = calendar.monthrange(year, month)[1]

    # Get Payroll's Holiday Management
    first_day = date(year, month, 1)
    last_day = date(year, month, total_days)

    holidays = HolidayManagement.objects.filter(
        payroll_id=payroll_id,
        financial_year=financial_year,
        start_date__gte=first_day,
        start_date__lte=last_day
    )

    holiday_days = set()
    for holiday in holidays:
        current_date = holiday.start_date
        while current_date <= holiday.end_date:
            if current_date.month == month:
                holiday_days.add(current_date)
            current_date += timedelta(days=1)

    # Get Payroll's PaySchedule
    try:
        pay_schedule = PaySchedule.objects.get(payroll_id=payroll_id)
    except PaySchedule.DoesNotExist:
        return {"error": "PaySchedule not found for given payroll ID."}

    week_off_days = set()
    for day in range(1, total_days + 1):
        current_date = date(year, month, day)
        weekday = current_date.strftime('%A').lower()

        if getattr(pay_schedule, weekday, False):
            week_off_days.add(current_date)

        if current_date.strftime('%A') == 'Saturday':
            if (day > 7 and day <= 14) and pay_schedule.second_saturday:
                week_off_days.add(current_date)
            if (day > 21 and day <= 28) and pay_schedule.fourth_saturday:
                week_off_days.add(current_date)

    return {
        "total_days": total_days,
        "holiday_count": len(holiday_days),
        "week_off_count": len(week_off_days),
        "total_holidays": list(holiday_days),
        "total_week_offs": list(week_off_days)
    }


@api_view(['POST'])
def generate_next_month_attendance(request):
    """
    Automatically creates attendance records for all employees under a given payroll_id for the next month,
    excluding employees who have left the organization.
    """
    payroll_id = request.query_params.get("payroll_id")

    if not payroll_id:
        return Response({"error": "Payroll ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    today = date.today()
    next_month = today.month + 1 if today.month < 12 else 1
    next_year = today.year if today.month < 12 else today.year + 1
    first_day_next_month = date(next_year, next_month, 1)

    # Exclude employees who have exited before the next month's start date
    active_employees = EmployeeManagement.objects.filter(
        payroll=payroll_id
    ).exclude(
        Q(employee_exit_details__doe__lt=first_day_next_month)  # Employees who exited before next month
    )

    if not active_employees.exists():
        return Response({"error": "No active employees found for the given payroll ID."},
                        status=status.HTTP_404_NOT_FOUND)

    # Fetch holiday and week-off details
    holiday_data = calculate_holidays_and_week_offs(payroll_id, next_year, next_month)

    if "error" in holiday_data:
        return Response({"error": holiday_data["error"]}, status=status.HTTP_400_BAD_REQUEST)

    total_days = holiday_data["total_days"]
    holidays = holiday_data["holiday_count"]
    week_offs = holiday_data["week_off_count"]

    created_records = 0
    for employee in active_employees:
        # Determine financial year
        financial_year = f"{next_year}-{next_year + 1}" if next_month >= 4 else f"{next_year - 1}-{next_year}"

        # Calculate present and balance days
        present_days = 0
        balance_days = 0

        EmployeeAttendance.objects.create(
            employee=employee,
            financial_year=financial_year,
            month=next_month,
            total_days_of_month=total_days,
            holidays=holidays,
            week_offs=week_offs,
            present_days=present_days,
            balance_days=balance_days,
            casual_leaves=0,
            sick_leaves=0,
            earned_leaves=0,
            loss_of_pay =0
        )

        created_records += 1

    return Response({
        "message": f"Attendance records for {date(next_year, next_month, 1).strftime('%B %Y')} created successfully.",
        "created_records": created_records
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def generate_current_month_attendance(request):
    """
    Automatically creates attendance records for all employees under a given payroll_id for the current month,
    excluding employees who have left the organization. If records already exist, it skips them.
    """
    payroll_id = request.query_params.get("payroll_id")
    if not payroll_id:
        return Response({"error": "Payroll ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    today = date.today()
    current_month = today.month
    current_year = today.year
    first_day_current_month = date(current_year, current_month, 1)

    # Fetch all employees under the given payroll_id
    all_employees = EmployeeManagement.objects.filter(payroll=payroll_id)

    if not all_employees.exists():
        return Response({"error": "No employees found for the given payroll ID."}, status=status.HTTP_404_NOT_FOUND)

    # Fetch exited employees
    exited_employees = set(
        EmployeeExit.objects.filter(doe__lt=first_day_current_month)
        .values_list("employee_id", flat=True)
    )

    # Exclude exited employees manually
    active_employees = [emp for emp in all_employees if emp.id not in exited_employees]

    if not active_employees:
        return Response({"error": "No active employees found for the given payroll ID."}, status=status.HTTP_404_NOT_FOUND)

    # Fetch holiday and week-off details
    holiday_data = calculate_holidays_and_week_offs(payroll_id, current_year, current_month)

    if "error" in holiday_data:
        return Response({"error": holiday_data["error"]}, status=status.HTTP_400_BAD_REQUEST)

    total_days = holiday_data["total_days"]
    holidays = holiday_data["holiday_count"]
    week_offs = holiday_data["week_off_count"]

    created_records = 0
    skipped_records = 0

    for employee in active_employees:
        financial_year = f"{current_year}-{current_year + 1}" if current_month >= 4 else f"{current_year - 1}-{current_year}"

        # Check if an attendance record already exists
        if EmployeeAttendance.objects.filter(
            employee=employee, financial_year=financial_year, month=current_month
        ).exists():
            skipped_records += 1
            continue  # Skip this employee

        EmployeeAttendance.objects.create(
            employee=employee,
            financial_year=financial_year,
            month=current_month,
            total_days_of_month=total_days,
            holidays=holidays,
            week_offs=week_offs,
            present_days=0,
            balance_days=0,
            casual_leaves=0,
            sick_leaves=0,
            earned_leaves=0,
            loss_of_pay=0
        )
        created_records += 1

    return Response({
        "message": f"Attendance records for {date(current_year, current_month, 1).strftime('%B %Y')} processed successfully.",
        "created_records": created_records,
        "skipped_records": skipped_records
    }, status=status.HTTP_201_CREATED)



"""
    Calculate the Monthly salary for the employees
"""


@api_view(['GET'])
def calculate_employee_monthly_salary(request):
    today = date.today()
    current_day = today.day
    month = int(request.query_params.get("month", today.month))
    financial_year = request.query_params.get("financial_year", None)
    payroll_id = request.query_params.get("payroll_id")

    if not financial_year:
        return Response({"error": "Financial year is required."}, status=status.HTTP_400_BAD_REQUEST)

    if not payroll_id:
        return Response({"error": "Payroll ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    if current_day < 26 and month == today.month:
        return Response({"message": "Salary processing will be initiated between the 26th and 30th of the month."},
                        status=status.HTTP_200_OK)

    salary_records = EmployeeSalaryDetails.objects.filter(employee__payroll_id=payroll_id)
    if not salary_records.exists():
        return Response({"message": "No salary records found for this payroll ID"}, status=status.HTTP_200_OK)

    salaries = []
    for salary_record in salary_records:
        employee = salary_record.employee

        # Exclude employees who have exited
        if EmployeeExit.objects.filter(employee=employee).exists():
            continue

        try:
            attendance = EmployeeAttendance.objects.get(employee=employee, financial_year=financial_year,
                                                        month=month)
        except EmployeeAttendance.DoesNotExist:
            continue

        total_working_days = attendance.total_days_of_month - attendance.loss_of_pay
        gross_salary = salary_record.gross_salary.get("monthly", 0)
        per_day_salary = gross_salary / attendance.total_days_of_month
        earned_salary = per_day_salary * total_working_days
        lop_amount = per_day_salary * attendance.loss_of_pay

        # **Benefits Total**
        benefits_total = sum(
            benefit["monthly"] for benefit in salary_record.benefits) if salary_record.benefits else 0

        # **Taxes**
        taxes = sum(ded["monthly"] for ded in salary_record.deductions if "Tax" in ded["component_name"])

        # **Advance Loan EMI Deduction (Filtered for Financial Year & Month)**
        advance_loan = getattr(employee, "employee_advance_loan", None)
        emi_deduction = 0  # Default if no loan

        if advance_loan:
            active_loan = advance_loan.filter(
                start_month__lte=date(today.year, month, 1),
                end_month__gte=date(today.year, month, 1)
            ).first()

            if active_loan:
                emi_deduction = active_loan.emi_amount

        # **Employee-Specific Deductions**
        employee_deductions = sum(
            ded["monthly"] for ded in salary_record.deductions if
            "component_name" in ded and "Tax" not in ded["component_name"]
        )

        total_deductions = taxes + emi_deduction + employee_deductions
        net_salary = earned_salary - total_deductions

        salaries.append({
            "employee_id": employee.id,
            "employee_name": attendance.employee.first_name + ' ' + attendance.employee.last_name,
            "month": attendance.month,
            "financial_year": financial_year,
            "paid_days": total_working_days,
            "gross_salary": gross_salary,
            "earned_salary": round(earned_salary, 2),
            "benefits_total": round(benefits_total, 2),
            "deductions": {
                "Employee Deductions": round(employee_deductions, 2),
                "Taxes": round(taxes, 2),
                "Loan EMI": round(emi_deduction, 2),
                "Total": round(total_deductions, 2)
            },
            "net_salary": round(net_salary, 2)
        })

    return Response(salaries, status=status.HTTP_200_OK)


@api_view(['GET'])
def detail_employee_monthly_salary(request):
    try:
        today = date.today()
        current_day = today.day
        month = int(request.query_params.get("month", today.month))
        financial_year = request.query_params.get("financial_year", None)
        payroll_id = request.query_params.get("payroll_id")

        fy_start = int(financial_year.split('-')[0])
        year = fy_start if month >= 4 else fy_start + 1

        if not financial_year:
            return Response({"error": "Financial year is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not payroll_id:
            return Response({"error": "Payroll ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        if current_day < 26 and month == today.month:
            return Response({"message": "Salary processing will be initiated between the 26th and 30th of the month."},
                            status=status.HTTP_200_OK)

        salary_records = EmployeeSalaryDetails.objects.filter(employee__payroll_id=payroll_id)
        if not salary_records.exists():
            return Response({"message": "No salary records found for this payroll ID"}, status=status.HTTP_200_OK)

        salaries = []

        for salary_record in salary_records:
            employee = salary_record.employee
            salary_history = EmployeeSalaryHistory.objects.filter(
                employee=employee,
                payroll=payroll_id,
                month=month,
                financial_year=financial_year
            ).first()
            if not salary_history:
                # Exclude exited employees
                exit_obj = EmployeeExit.objects.filter(employee=employee).last()
                if exit_obj:
                    emp_exit_year = exit_obj.exit_year
                    emp_exit_month = exit_obj.exit_month

                    if emp_exit_year < year or (emp_exit_year == year and emp_exit_month < month):
                        continue

                try:
                    attendance = EmployeeAttendance.objects.get(employee=employee, financial_year=financial_year, month=month)
                except EmployeeAttendance.DoesNotExist:
                    continue

                total_working_days = attendance.total_days_of_month - attendance.loss_of_pay
                gross_salary = salary_record.gross_salary.get("monthly", 0)
                per_day_salary = gross_salary / attendance.total_days_of_month
                earned_salary = per_day_salary * total_working_days
                lop_amount = per_day_salary * attendance.loss_of_pay
                # EPF Calculation
                epf_earnings = [
                    e for e in Earnings.objects.filter(payroll_id=payroll_id)
                    if e.includes_epf_contribution is True
                ]
                epf_eligible_total = 0
                salary_earnings = salary_record.earnings
                # Convert to a dictionary for easier lookup
                component_amount_map = {
                    item["component_name"].lower().replace(" ", "_"): item.get("monthly", 0)
                    for item in salary_earnings
                }

                if epf_earnings:
                    for earning in epf_earnings:
                        component_name = earning.component_name.lower().replace(" ", "_")
                        component_amount = component_amount_map.get(component_name, 0)
                        prorated_component = (component_amount * total_working_days) / attendance.total_days_of_month
                        epf_eligible_total += prorated_component
                epf_base = min(epf_eligible_total, 15000)
                pf = round(epf_base * 0.12, 2)

                # ESI Calculation
                esi = round(earned_salary * 0.0075, 2) if gross_salary <= 21000 else 0

                # PT Calculation
                pt_amount = 0
                pt_obj = PT.objects.filter(payroll=payroll_id, work_location=employee.work_location).first()
                if pt_obj:
                    for slab in pt_obj.slab:
                        salary_range = slab.get("Monthly Salary (₹)")
                        pt_value = slab.get("Professional Tax (₹ per month)", "0").replace("₹", "").replace(",", "").strip()

                        try:
                            if "to" in salary_range:
                                parts = salary_range.split("to")
                                lower = int(parts[0].strip().replace("Up to", "").replace(",", ""))
                                upper = int(parts[1].strip().replace(",", ""))
                                if lower < gross_salary <= upper:
                                    pt_amount = int(pt_value) if pt_value.isdigit() else 0
                                    break

                            elif "and above" in salary_range:
                                threshold = int(salary_range.split("and")[0].strip().replace(",", ""))
                                if gross_salary > threshold:
                                    pt_amount = int(pt_value) if pt_value.isdigit() else 0
                                    break

                            elif "Up to" in salary_range:
                                upper = int(salary_range.replace("Up to", "").strip().replace(",", ""))
                                if gross_salary <= upper:
                                    pt_amount = int(pt_value) if pt_value.isdigit() else 0
                                    break

                        except (ValueError, IndexError):
                            continue  # Skip this slab if parsing fails

                # Benefits
                benefits_total = sum(b.get("monthly", 0) for b in salary_record.benefits or [])

                # Taxes
                taxes = sum(d.get("monthly", 0) for d in salary_record.deductions if "Tax" in d.get("component_name", ""))

                # Advance Loan EMI
                advance_loan = getattr(employee, "employee_advance_loan", None)
                emi_deduction = 0
                if advance_loan:
                    active_loan = advance_loan.filter(
                        start_month__lte=date(today.year, month, 1),
                        end_month__gte=date(today.year, month, 1)
                    ).first()
                    if active_loan:
                        emi_deduction = active_loan.emi_amount

                exclude_earnings = {"basic", "hra", "special_allowance", "bonus"}
                exclude_deductions = {"pf", "esi", "pt", "tds", "loan_emi"}

                def prorate(value):
                    return (value * total_working_days) / attendance.total_days_of_month if value else 0

                other_earnings = 0
                if salary_record.earnings:
                    for earning in salary_record.earnings:
                        name = earning.get("component_name", "").lower().replace(" ", "_")
                        if name not in exclude_earnings:
                            other_earnings += prorate(earning.get("monthly", 0))

                other_deductions = 0
                employee_deductions = 0
                if salary_record.deductions:
                    for deduction in salary_record.deductions:
                        name = deduction.get("component_name", "").lower().replace(" ", "_")
                        value = deduction.get("monthly", 0)
                        if "tax" not in name:
                            employee_deductions += value
                        if all(ex not in name for ex in exclude_deductions):
                            other_deductions += prorate(value)

                total_deductions = taxes + emi_deduction + employee_deductions + other_deductions + pt_amount
                net_salary = earned_salary - total_deductions

                def get_component_amount(earnings_data, component_name):
                    for item in earnings_data:
                        if item["component_name"].lower() == component_name.lower().replace("_", " "):
                            return item.get("monthly", 0)
                    return 0

                # Prorated fixed components
                prorated_basic = prorate(get_component_amount(salary_record.earnings, "basic"))
                prorated_hra = prorate(get_component_amount(salary_record.earnings, "hra"))
                prorated_bonus = prorate(get_component_amount(salary_record.earnings, "bonus"))
                prorated_special_allowance = prorate(get_component_amount(salary_record.earnings,
                                                                          "special allowance"))
                # Create or update EmployeeSalaryHistory

                EmployeeSalaryHistory.objects.create(
                    employee=employee,
                    payroll=employee.payroll,
                    month=month,
                    financial_year=financial_year,
                    total_days_of_month=attendance.total_days_of_month,
                    lop=attendance.loss_of_pay,
                    paid_days=total_working_days,
                    ctc=salary_record.annual_ctc,
                    gross_salary=int(gross_salary),
                    earned_salary=int(round(earned_salary, 2)),
                    basic_salary=int(round(prorated_basic, 2)),
                    hra=int(round(prorated_hra, 2)),
                    special_allowance=int(round(prorated_special_allowance, 2)),
                    bonus=int(round(prorated_bonus, 2)),
                    other_earnings=int(round(other_earnings, 2)),
                    benefits_total=int(
                        round(prorated_basic + prorated_hra + prorated_bonus + prorated_special_allowance + other_earnings,
                              2)),
                    epf=pf,
                    esi=esi,
                    pt=pt_amount,
                    tds=0,
                    loan_emi=round(emi_deduction, 2),
                    other_deductions=round(other_deductions, 2),
                    total_deductions=round(total_deductions, 2),
                    net_salary=int(round(net_salary, 2)),
                    is_active=True,
                    notes="Salary processed from API"
                )
        salary_records = EmployeeSalaryHistory.objects.filter(
            payroll=payroll_id,
            month=month,
            financial_year=financial_year
        )

        serializer = EmployeeSalaryHistorySerializer(salary_records, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

from django.db.models import Sum, Q
from django.db.models.functions import ExtractMonth, ExtractYear
@api_view(['GET'])
def payroll_summary_view(request):
    financial_year = request.query_params.get('financial_year')
    payroll_id = request.query_params.get('payroll_id')
    month = request.query_params.get('month')



    if not (financial_year and payroll_id and month):
        return Response(
            {"error": "Please provide financial_year, payroll_id, and month as query parameters."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        month = int(month)
        fy_start = int(financial_year.split('-')[0])
        start_year = fy_start if month >= 4 else fy_start + 1
        start_of_month = datetime(start_year, month, 1)
        end_of_month = datetime(start_year, month, calendar.monthrange(start_year, month)[1], 23, 59, 59)
    except:
        return Response(
            {"error": "Invalid format for financial_year or month."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Filter salary history
    salary_qs = EmployeeSalaryHistory.objects.filter(
        financial_year=financial_year,
        payroll_id=payroll_id,
        month=month
    )

    # Base aggregations
    total_employees = salary_qs.count()
    total_ctc = salary_qs.aggregate(Sum('ctc'))['ctc__sum'] or 0
    gross = salary_qs.aggregate(Sum('gross_salary'))['gross_salary__sum'] or 0
    total_deductions = salary_qs.aggregate(Sum('total_deductions'))['total_deductions__sum'] or 0
    net_pay = salary_qs.aggregate(Sum('net_salary'))['net_salary__sum'] or 0
    epf_total = salary_qs.aggregate(Sum('epf'))['epf__sum'] or 0
    esi_total = salary_qs.aggregate(Sum('esi'))['esi__sum'] or 0
    pt_total = salary_qs.aggregate(Sum('pt'))['pt__sum'] or 0
    tds_total = salary_qs.aggregate(Sum('tds'))['tds__sum'] or 0

    # Get all employees for this payroll
    all_employees = EmployeeManagement.objects.filter(payroll_id=payroll_id)

    total_new_joinees = EmployeeManagement.objects.filter(
        payroll_id=payroll_id,
        doj__gte=start_of_month,
        doj__lte=end_of_month
    ).count()

    total_exits = EmployeeExit.objects.filter(
        employee__payroll_id=payroll_id,
        exit_month=month,
        exit_year=start_year
    ).count()

    return Response({
        "total_employees": total_employees,
        "total_ctc": total_ctc,
        "gross": gross,
        "total_deductions": total_deductions,
        "net_pay": net_pay,
        "epf_total": epf_total,
        "esi_total": esi_total,
        "pt_total": pt_total,
        "tds_total": tds_total,
        "total_new_joinees": total_new_joinees,
        "total_exits": total_exits,
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_financial_year_summary(request):
    payroll_id = request.GET.get('payroll_id')
    financial_year = request.GET.get('financial_year')  # format: "2024-2025"

    if not payroll_id or not financial_year:
        return JsonResponse({"error": "Missing payroll_id or financial_year"}, status=400)

    try:
        start_year, end_year = map(int, financial_year.split('-'))
    except:
        return JsonResponse({"error": "Invalid financial year format"}, status=400)

    current_date = datetime.now()
    current_month = current_date.month
    current_day = current_date.day

    # Map months April (4) to March (3) of next year
    months = list(range(4, 13)) + list(range(1, 4))

    summary = []
    for idx, month in enumerate(months):
        if month >= 4:
            year = start_year
        else:
            year = end_year

        # Get salary records
        salary = EmployeeSalaryHistory.objects.filter(
            payroll_id=payroll_id,
            financial_year=financial_year,
            month=month
        ).first()

        # Calculate status
        if not salary:
            if year == current_date.year and month == current_month:
                if current_day < 20:
                    status = "-"
                    action = "-"
                elif 20 <= current_day <= 26:
                    status = "draft"
                    action = "start_payroll"
                else:
                    status = "processed"
                    action = "view"
            else:
                status = ""
                action = ""
            ctc = ""
        else:
            ctc = salary.ctc
            # if record exists, infer it's processed
            status = "processed"
            action = "view"

        summary.append({
            "month": datetime(year, month, 1).strftime('%B'),
            "year": year,
            "ctc": ctc,
            "status": status,
            "action": action,
        })

    return JsonResponse({"financial_year_summary": summary}, status=200)


class DocumentGenerator:
    def __init__(self, request, invoicing_profile, context):
        self.request = request
        self.invoicing_profile = invoicing_profile
        self.context = context

    def generate_document(self, template_name):
        try:
            # Render the HTML template with the context data
            html_content = render_to_string(template_name, self.context)

            # Generate the PDF from the HTML content using pdfkit
            try:
                pdf = pdfkit.from_string(html_content, False)  # False to get the PDF as a byte string
                print("PDF generation successful.")
            except Exception as pdf_error:
                print(f"Error in generating PDF: {pdf_error}")
                raise

            # Return the generated PDF as an HTTP response
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="salary_template.pdf"'
            print(response)
            return response
        except Exception as e:
            print(f"Error generating document: {e}")
            raise


def format_with_commas(number):
    try:
        return "{:,.2f}".format(float(number)).replace(".00", "")
    except (ValueError, TypeError):
        return str(number)


@api_view(['GET'])
def employee_monthly_salary_template(request):
    try:
        today = date.today()
        current_day = today.day
        month = int(request.query_params.get("month", today.month))
        year_ = int(request.query_params.get("year", today.year))
        financial_year = request.query_params.get("financial_year", None)
        employee_id = request.query_params.get("employee_id")

        month_name = calendar.month_abbr[month]
        print(month_name)

        if not financial_year:
            return Response({"error": "Financial year is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not employee_id:
            return Response({"error": "Employee Id  is required."}, status=status.HTTP_400_BAD_REQUEST)

        if current_day < 26 and month == today.month:
            return Response({"message": "Salary processing will be initiated between the 26th and 30th of the month."},
                            status=status.HTTP_200_OK)

        salary_record = EmployeeSalaryDetails.objects.filter(employee=employee_id).last()

        if not salary_record:
            return Response({"message": "No salary records found for this payroll ID"}, status=status.HTTP_200_OK)

        try:
            attendance = EmployeeAttendance.objects.get(employee=employee_id, financial_year=financial_year, month=month)
        except EmployeeAttendance.DoesNotExist:
            return Response({"message": "No attendance record found"}, status=status.HTTP_200_OK)

        # Calculate working days and per-day salary
        total_working_days = attendance.total_days_of_month - attendance.loss_of_pay
        gross_salary = salary_record.gross_salary.get("monthly", 0)  # Parse JSON string
        per_day_salary = gross_salary / attendance.total_days_of_month if attendance.total_days_of_month else 0
        earned_salary = per_day_salary * total_working_days
        lop_amount = per_day_salary * attendance.loss_of_pay

        # Extract Earnings from JSON
        earnings = salary_record.earnings if isinstance(salary_record.earnings, list) else json.loads(
            salary_record.earnings)

        # Allowance Keys to Extract
        allowance_keys = [
            "Basic", "HRA", "Conveyance Allowance", "Travelling Allowance",
            "Medical Allowance", "Internet Allowance", "Special Allowance", "Miscellaneous Allowance"
        ]

        # Initialize Allowance Dictionary
        allowance_values = {key.lower().replace(" ", "_"): 0 for key in allowance_keys}

        # Extract Allowances
        for item in earnings:
            component_name = item["component_name"]
            if component_name in allowance_keys:
                key = component_name.lower().replace(" ", "_")
                allowance_values[key] = item["monthly"]

        # Calculate Per-Day and Earned Allowances
        earned_allowances = {
            f"earned_{key}": (allowance_values[key] / attendance.total_days_of_month * total_working_days)
            if attendance.total_days_of_month else 0
            for key in allowance_values
        }

        # Merge the earned allowances into allowance_values
        allowance_values.update(earned_allowances)

        # Extract Deductions from JSON
        deductions = salary_record.deductions if isinstance(salary_record.deductions, list) \
            else json.loads(salary_record.deductions)

        # Deduction Keys
        deduction_keys = ["EPF Employee Contribution", "Professional Tax", "Income Tax", "ESI Employee Contribution"]

        # Initialize Deduction Dictionary
        deduction_values = {key.lower().replace(" ", "_"): 0 for key in deduction_keys}

        # Extract Deductions
        for item in deductions:
            component_name = item["component_name"]
            if component_name in deduction_keys:
                key = component_name.lower().replace(" ", "_")
                deduction_values[key] = item["monthly"]

        # Calculate Total Deduction (Sum of Required Deductions)
        total_deduction = sum(deduction_values.values())
        net_pay = earned_salary - total_deduction
        total_in_words = num2words(net_pay)
        total_in_words = total_in_words.capitalize()
        total_in_words = total_in_words.replace("<br/>", ' ')
        total_in_words = total_in_words.title() + ' ' + 'Rupees Only'

        # Construct the Context Dictionary
        context = {
            "company_name": getattr(salary_record.employee.payroll.business, "nameOfBusiness", ""),
            "address": f"{getattr(salary_record.employee.payroll, 'filling_address_line1', '')}, "
                       f"{getattr(salary_record.employee.payroll, 'filling_address_state', '')}, "
                       f"{getattr(salary_record.employee.payroll, 'filling_address_city', '')}, "
                       f"{getattr(salary_record.employee.payroll, 'filling_address_pincode', '')}",
            "month": month,
            "year": year_,
            "employee_name": f"{getattr(salary_record.employee, 'first_name', '')} {getattr(salary_record.employee, 'last_name', '')}",
            "designation": getattr(salary_record.employee.designation, "designation_name", ""),
            "employee_id": getattr(salary_record.employee, "associate_id", ""),
            "doj": getattr(salary_record.employee, "doj", ""),
            "pay_period": f"{month_name} {year_}",
            "pay_date": "",
            "bank_account_number": "",
            "uan_number": "",

            # Earnings and Allowances
            "basic": format_with_commas(allowance_values.get("basic", 0)),
            "hra_allowance": format_with_commas(allowance_values.get("hra", 0)),
            "conveyance_allowance": format_with_commas(allowance_values.get("conveyance_allowance", 0)),
            "travelling_allowance": format_with_commas(allowance_values.get("travelling_allowance", 0)),
            "medical_allowance": format_with_commas(allowance_values.get("medical_allowance", 0)),
            "internet_allowance": format_with_commas(allowance_values.get("internet_allowance", 0)),
            "special_allowance": format_with_commas(allowance_values.get("special_allowance", 0)),
            "miscellaneous_allowance": format_with_commas(allowance_values.get("miscellaneous_allowance", 0)),

            # Gross and Net Salary
            "gross_earnings": format_with_commas(earned_salary),
            "salary_adjustments": 0,  # Placeholder if any adjustments apply

            # Individual Deductions
            "epf_contribution": format_with_commas(deduction_values.get("epf_employee_contribution", 0)),
            "professional_tax": format_with_commas(deduction_values.get("professional_tax", 0)),
            "income_tax": format_with_commas(deduction_values.get("income_tax", 0)),
            "esi_employee_contribution": format_with_commas(deduction_values.get("esi_employee_contribution", 0)),
            "total_deduction": format_with_commas(total_deduction),

            # Final Net Pay Calculation
            "net_pay": format_with_commas(earned_salary - total_deduction),
            "paid_days": total_working_days,
            "lop_days": attendance.loss_of_pay,
            "amount_in_words": total_in_words,  # Placeholder for number-to-words conversion
        }

        # Assuming you have a DocumentGenerator class that generates the PDF
        document_generator = DocumentGenerator(request, salary_record, context)

        # Assuming `template_name` is the path to your HTML template
        template_name = "salary_template.html"

        # Generate the PDF document
        pdf_response = document_generator.generate_document(template_name)

        # Return the PDF response
        return pdf_response
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET', 'POST'])
def bonus_incentive_list(request):
    """
    List all bonus incentives or filter by employee ID.
    Create a new bonus incentive.
    """
    if request.method == 'GET':
        employee_id = request.query_params.get('employee_id')

        if employee_id:
            bonuses = BonusIncentive.objects.filter(employee=employee_id)
        else:
            bonuses = BonusIncentive.objects.all()

        serializer = BonusIncentiveSerializer(bonuses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = BonusIncentiveSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def bonus_incentive_detail(request, pk):
    """
    Retrieve, update, or delete a bonus incentive by ID.
    """
    bonus = get_object_or_404(BonusIncentive, pk=pk)

    if request.method == 'GET':
        serializer = BonusIncentiveSerializer(bonus)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = BonusIncentiveSerializer(bonus, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        bonus.delete()
        return Response({"message": "Bonus incentive record deleted successfully."},
                        status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def bonus_by_payroll_month_year(request):
    """
    Returns all BonusIncentives for a given payroll_id, month, and year.
    """
    try:
        payroll_id = request.query_params.get('payroll_id')
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        if not payroll_id or not month or not year:
            return Response(
                {"error": "Both payroll_id, month and year are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert to integers to avoid type mismatch issues
        try:
            payroll_id = int(payroll_id)
            month = int(month)
            year = int(year)
        except ValueError:
            return Response({"error": "payroll_id, month and year must be integers."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Query the DB
        bonus_qs = BonusIncentive.objects.filter(
            employee__payroll=payroll_id,
            month=month,
            year=year
        )

        if not bonus_qs.exists():
            return Response(
                {"message": "No bonus incentive data found for the given criteria."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BonusIncentiveSerializer(bonus_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['GET'])
# def active_employee_salaries(request):
#     try:
#         payroll_id = request.query_params.get('payroll_id')
#         year = request.query_params.get('year')
#         month = request.query_params.get('month')
#
#         if not all([payroll_id, year, month]):
#             return Response(
#                 {"error": "Missing required query parameters: payroll_id, year, and month."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         try:
#             year = int(year)
#             month = int(month)
#             cutoff_date = date(year, month, 1)
#         except ValueError:
#             return Response(
#                 {"error": "Year and month must be valid integers."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # Step 1: Retrieve all salary details for the given payroll_id
#         salary_details = EmployeeSalaryDetails.objects.filter(
#             employee__payroll_id=payroll_id
#         ).select_related('employee')
#
#         # Step 2: Manually filter out salary details of employees who exited before the given date
#         active_salary_details = []
#         for salary_detail in salary_details:
#             exit_record = EmployeeExit.objects.filter(employee=salary_detail.employee).first()
#             if exit_record:
#                 if exit_record.exit_year < year or (exit_record.exit_year == year and exit_record.exit_month < month):
#                     continue  # Skip this salary detail as the employee exited before the given date
#             active_salary_details.append(salary_detail)
#
#         # Step 3: Further filter salary details based on valid_from date
#         final_salary_details = [
#             detail for detail in active_salary_details if detail.valid_from <= cutoff_date
#         ]
#
#         serializer = EmployeeSalaryDetailsSerializer(active_salary_details, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['GET'])
# def active_employee_salaries(request):
#     try:
#         payroll_id = request.query_params.get('payroll_id')
#         year = request.query_params.get('year')
#         month = request.query_params.get('month')
#
#         # Validate required parameters
#         if not all([payroll_id, year, month]):
#             return Response(
#                 {"error": "Missing required query parameters: payroll_id, year, and month."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # Validate and parse year/month
#         try:
#             year = int(year)
#             month = int(month)
#         except ValueError:
#             return Response(
#                 {"error": "Year and month must be valid integers."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # Get base queryset with all related data in one query
#         salary_details = EmployeeSalaryDetails.objects.filter(
#             employee__payroll_id=payroll_id
#         ).select_related('employee')
#
#         # Filter active employees using the correct related_name
#         active_salary_details = salary_details.filter(
#             Q(employee__employee_exit_details=None) |  # No exit record
#             Q(employee__employee_exit_details__exit_year__gt=year) |  # Exited after our year
#             Q(employee__employee_exit_details__exit_year=year,
#               employee__employee_exit_details__exit_month__gte=month)  # Exited same year but month >= our month
#         )
#
#         serializer = EmployeeSalaryDetailsSerializer(active_salary_details, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def active_employee_salaries(request):
    try:
        payroll_id = request.query_params.get('payroll_id')
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        # Validate required parameters
        if not all([payroll_id, year, month]):
            return Response(
                {"error": "Missing required query parameters: payroll_id, year, and month."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate and parse year/month
        try:
            year = int(year)
            month = int(month)
        except ValueError:
            return Response(
                {"error": "Year and month must be valid integers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get all salary details for the payroll_id with employee and exit details
        salary_details = EmployeeSalaryDetails.objects.filter(
            employee__payroll_id=payroll_id,
            created_year=year, created_month=month
        ).select_related(
            'employee',
            'employee__employee_exit_details'
        )

        # Filter active employees (same logic as before)
        active_salaries = salary_details.filter(
            Q(employee__employee_exit_details=None) |
            Q(employee__employee_exit_details__exit_year__gt=year) |
            Q(employee__employee_exit_details__exit_year=year,
              employee__employee_exit_details__exit_month__gte=month)
        )

        # Group by employee and get the latest record (by highest ID assuming it's auto-increment)
        from django.db.models import Max
        latest_ids = list(active_salaries.values('employee')
                          .annotate(latest_id=Max('id'))
                          .values_list('latest_id', flat=True))
        result = active_salaries.filter(id__in=latest_ids)

        serializer = SimplifiedEmployeeSalarySerializer(result, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)












