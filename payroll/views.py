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



# def generate_presigned_url(s3_key, expiration=3600):
#     """
#     Generate a presigned URL for accessing a private S3 file.
#     """
#     s3 = boto3.client(
#         's3',
#         aws_access_key_id=AWS_ACCESS_KEY_ID,
#         aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
#     )
#     try:
#         url = s3.generate_presigned_url(
#             'get_object',
#             Params={'Bucket':AWS_STORAGE_BUCKET_NAME, 'Key': s3_key},
#             ExpiresIn=expiration,
#         )
#         return url
#     except Exception as e:
#         raise Exception(f"Error generating presigned URL: {str(e)}")

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

        # Validate and save the serializer
        serializer = PayrollOrgSerializer(data=data)
        if serializer.is_valid():
            payroll_org = serializer.save()  # Save the instance directly
            return Response(
                PayrollOrgSerializer(payroll_org).data,
                status=status.HTTP_201_CREATED
            )

        # Handle validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PayrollOrgDetail(APIView):
    """
    Retrieve, update or delete a payroll organization instance.
    """
    def get(self, request, pk):
        try:
            payroll_org = PayrollOrg.objects.get(pk=pk)
        except PayrollOrg.DoesNotExist:
            return Response({"error": "PayrollOrg not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PayrollOrgSerializer(payroll_org)
        return Response(serializer.data)

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

# List all WorkLocations
@api_view(['GET'])
def work_location_list(request):
    payroll_id = request.query_params.get('payroll_id')  # Get payroll_id from query parameters

    if payroll_id:
        # Filter work locations by payroll_id
        work_locations = WorkLocations.objects.filter(payroll_id=payroll_id)
    else:
        # Retrieve all work locations if no payroll_id is provided
        work_locations = WorkLocations.objects.all()

    serializer = WorkLocationSerializer(work_locations, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


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
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        work_location.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# List and create departments
@api_view(['GET', 'POST'])
def department_list(request):
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')  # Get payroll_id from query parameters

        if payroll_id:
            # Filter departments by payroll_id
            departments = Departments.objects.filter(payroll_id=payroll_id)
        else:
            # Retrieve all departments if no payroll_id is provided
            departments = Departments.objects.all()

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
            designations = Designation.objects.filter(payroll_id=payroll_id)
        else:
            # Retrieve all designations if no payroll_id is provided
            designations = Departments.objects.all()
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
                epf_details = EPF.objects.get(payroll_id=payroll_id)  # Fetch EPF details for the specific payroll
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
def pf_list(request):
    """
    List PF records or create a new one, based on payroll_id.
    """
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')  # Get payroll_id from query parameters

        if payroll_id:
            # Since PF is a OneToOneField, there will be at most one PF record for a given payroll_id
            try:
                pf_instance = PF.objects.get(payroll_id=payroll_id)  # Fetch PF details for the specific payroll
                serializer = PFSerializer(pf_instance)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except PF.DoesNotExist:
                return Response({"error": "PF details not found for the given payroll ID."}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Retrieve all PF details if no payroll_id is provided
            pf_instances = PF.objects.all()
            serializer = PFSerializer(pf_instances, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = PFSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Ensure there is no existing PF record for the given payroll_id
                payroll_id = serializer.validated_data.get('payroll').id
                if PF.objects.filter(payroll_id=payroll_id).exists():
                    return Response({"error": "PF details already exist for this payroll ID."}, status=status.HTTP_400_BAD_REQUEST)

                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def pf_detail(request, pk):
    """
    Retrieve, update or delete a PF record.
    """
    try:
        pf_instance = PF.objects.get(pk=pk)
    except PF.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PFSerializer(pf_instance)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = PFSerializer(pf_instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        pf_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def earnings_list(request):
    """
    List all Earnings records, or create a new one.
    """
    if request.method == 'GET':
        payroll_id = request.query_params.get('payroll_id')  # Get payroll_id from query parameters

        if payroll_id:
            # Filter earnings by payroll_id
            earnings = Earnings.objects.filter(payroll_id=payroll_id)
        else:
            # Retrieve all earnings if no payroll_id is provided
            earnings = Earnings.objects.all()
        serializer = EarningsSerializer(earnings, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = EarningsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
