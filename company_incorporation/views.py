from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import *
from django.shortcuts import get_object_or_404
from .serializers import *
import json
from rest_framework import status
from .serializers import ProposedCompanyDetailsSerializer
import copy

@api_view(['POST', 'GET'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def create_proposed_company_details(request):
    try:
        if request.method == 'POST':
            serializer = ProposedCompanyDetailsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'GET':
            objs = ProposedCompanyDetails.objects.all()
            serializer = ProposedCompanyDetailsSerializer(objs,many=True)
            return Response(serializer.data)
        return Response({"error": "Invalid request method"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def proposed_company_details_by_service_request(request):
    try:
        service_request_id = request.query_params.get('service_request_id')
        if not service_request_id:
            return Response(
                {"error": "Provide 'service_request_id' as a query parameter."},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance = ProposedCompanyDetails.objects.get(service_request_id=service_request_id)
        serializer = ProposedCompanyDetailsSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except ProposedCompanyDetails.DoesNotExist:
        return Response({"error": "Proposed Company Details not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def proposed_company_detail(request, id):
    """
    Retrieve, update, or delete a single proposed company by ID.
    """
    try:
        instance = ProposedCompanyDetails.objects.get(id=id)
    except ProposedCompanyDetails.DoesNotExist:
        return Response({'error': 'Proposed company not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ProposedCompanyDetailsSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        data = request.data.copy()
        serializer = ProposedCompanyDetailsSerializer(instance, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        instance.delete()
        return Response({'message': 'Proposed company deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST', 'GET'])
def create_registered_office_address(request):
    try:
        if request.method == 'POST':
            serializer = RegisteredOfficeAddressDetailsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'GET':
            objs = RegisteredOfficeAddressDetails.objects.all()
            serializer = RegisteredOfficeAddressDetailsSerializer(objs,many=True)
            return Response(serializer.data)
        return Response({"error": "Invalid request method"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def registered_office_address_by_service_request(request):
    try:
        service_request_id = request.query_params.get('service_request_id')
        if not service_request_id:
            return Response(
                {"error": "Provide 'service_request_id' as a query parameter."},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance = RegisteredOfficeAddressDetails.objects.get(service_request_id=service_request_id)
        serializer = RegisteredOfficeAddressDetailsSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except RegisteredOfficeAddressDetails.DoesNotExist:
        return Response({"error": "Registered Office Address not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def registered_office_address_details(request, id):
    try:
        registered_office_address = RegisteredOfficeAddressDetails.objects.get(id=id)
    except RegisteredOfficeAddressDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        if request.method == 'GET':
            serializer = RegisteredOfficeAddressDetailsSerializer(registered_office_address)
            return Response(serializer.data)

        elif request.method == 'PUT':
            serializer = RegisteredOfficeAddressDetailsSerializer(registered_office_address,
                                                                  data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            file_to_delete = request.query_params.get('file')
            if file_to_delete: # If a specific file is requested for deletion
                if file_to_delete == 'address_proof_file' and registered_office_address.address_proof_file:
                    registered_office_address.address_proof_file.storage.delete(
                        registered_office_address.address_proof_file.name)
                    registered_office_address.address_proof_file = None
                elif (file_to_delete == 'utility_bill_file' and
                      registered_office_address.utility_bill_file):
                    registered_office_address.utility_bill_file.storage.delete(
                        registered_office_address.utility_bill_file.name)
                    registered_office_address.utility_bill_file = None
                elif file_to_delete == 'NOC_file' and registered_office_address.NOC_file:
                    registered_office_address.NOC_file.storage.delete(
                        registered_office_address.NOC_file.name)
                    registered_office_address.NOC_file = None
                elif file_to_delete == 'rent_agreement_file' and registered_office_address.rent_agreement_file:
                    registered_office_address.rent_agreement_file.storage.delete(
                        registered_office_address.rent_agreement_file.name)
                    registered_office_address.rent_agreement_file = None
                elif (file_to_delete == 'property_tax_receipt_file' and
                      registered_office_address.property_tax_receipt_file):
                    registered_office_address.property_tax_receipt_file.storage.delete(
                        registered_office_address.property_tax_receipt_file.name)
                    registered_office_address.property_tax_receipt_file = None
                else:
                    return Response({"error": "Invalid or missing file name"}, status=status.HTTP_400_BAD_REQUEST)
                registered_office_address.save()
                return Response({"message": f"{file_to_delete} deleted successfully"}, status=status.HTTP_200_OK)

            # delete entire object and its files
            if registered_office_address.address_proof_file:
                registered_office_address.address_proof_file.storage.delete(registered_office_address.address_proof_file.name)
            if registered_office_address.utility_bill_file:
                registered_office_address.utility_bill_file.storage.delete(
                    registered_office_address.utility_bill_file.name)
            if registered_office_address.NOC_file:
                registered_office_address.NOC_file.storage.delete(registered_office_address.NOC_file.name)
            if registered_office_address.rent_agreement_file:
                registered_office_address.rent_agreement_file.storage.delete(
                    registered_office_address.rent_agreement_file.name)
            if registered_office_address.property_tax_receipt_file:
                registered_office_address.property_tax_receipt_file.storage.delete(
                    registered_office_address.property_tax_receipt_file.name)

            registered_office_address.delete()
            return Response({"message": "Registered office address details deleted successfully"},
                            status=status.HTTP_204_NO_CONTENT)

        return Response({"error": "Invalid request method"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST', 'GET'])
def create_authorized_paid_up_capital(request):
    try:
        if request.method == 'POST':
            serializer = AuthorizedPaidUpShareCapitalSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'GET':
            objs = AuthorizedPaidUpShareCapital.objects.all()
            serializer = AuthorizedPaidUpShareCapitalSerializer(objs, many=True)
            return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def authorized_paid_up_capital_by_service_request(request):
    try:
        service_request_id = request.query_params.get('service_request_id')
        if not service_request_id:
            return Response({"error": "Provide 'service_request_id'"}, status=status.HTTP_400_BAD_REQUEST)
        instance = AuthorizedPaidUpShareCapital.objects.get(service_request_id=service_request_id)
        serializer = AuthorizedPaidUpShareCapitalSerializer(instance)
        return Response(serializer.data)
    except AuthorizedPaidUpShareCapital.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
def authorized_paid_up_capital_detail(request, id):
    try:
        instance = AuthorizedPaidUpShareCapital.objects.get(id=id)
    except AuthorizedPaidUpShareCapital.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AuthorizedPaidUpShareCapitalSerializer(instance)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = AuthorizedPaidUpShareCapitalSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        instance.delete()
        return Response({"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def directors_list(request):
    if request.method == 'GET':
        records = Directors.objects.all()
        serializer = DirectorsSerializer(records, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        if request.FILES:
           data =  request.data
        else:
            data = request.data.copy()
        service_request = data.get('service_request')

        try:
            instance = Directors.objects.get(service_request=service_request)
            serializer = DirectorsSerializer(instance, data=data, partial=True)
        except Directors.DoesNotExist:
            serializer = DirectorsSerializer(data=data)

        if serializer.is_valid():
            main_data = serializer.save()

            if data.get('director_first_name'):
                data['directors_ref'] = main_data.id
                serializer_info = DirectorsDetailsSerializer(data=data)
                if serializer_info.is_valid():
                    serializer_info.save()
                else:
                    return Response(serializer_info.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(DirectorsSerializer(main_data).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def get_directors_data(request):
    service_request_id = request.query_params.get('service_request_id')
    service_task_id = request.query_params.get('service_task')

    if not service_request_id and not service_task_id:
        return Response(
            {"error": "Provide either 'service_request_id' or 'service_task' as query parameter."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        if service_request_id:
            instance = Directors.objects.get(service_request_id=service_request_id)
        else:
            instance = Directors.objects.get(service_task_id=service_task_id)
    except Directors.DoesNotExist:
        return Response({"error": "No matching Directors data found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = DirectorsSerializer(instance)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def directors_detail(request, pk):
    try:
        record = DirectorsDetails.objects.get(pk=pk)
    except DirectorsDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = DirectorsDetailsSerializer(record)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = DirectorsDetailsSerializer(record, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            record = DirectorsDetails.objects.get(pk=pk)
            file_to_delete = request.query_params.get('file')
            if file_to_delete:
                if file_to_delete == 'pan_card_file' and record.pan_card_file:
                    record.pan_card_file.storage.delete(record.pan_card_file.name)
                    record.pan_card_file = None
                elif file_to_delete == 'aadhaar_card_file' and record.aadhaar_card_file:
                    record.aadhaar_card_file.storage.delete(record.aadhaar_card_file.name)
                    record.aadhaar_card_file = None
                elif file_to_delete == 'passport_photo_file' and record.passport_photo_file:
                    record.passport_photo_file.storage.delete(record.passport_photo_file.name)
                    record.passport_photo_file = None
                elif file_to_delete == 'residential_address_proof_file' and record.residential_address_proof_file:
                    record.residential_address_proof_file.storage.delete(record.residential_address_proof_file.name)
                    record.residential_address_proof_file = None
                elif file_to_delete == 'form_dir2' and record.form_dir2:
                    record.form_dir2.storage.delete(record.form_dir2.name)
                    record.form_dir2 = None
                elif file_to_delete == 'specimen_signature_of_director' and record.specimen_signature_of_director:
                    record.specimen_signature_of_director.storage.delete(record.specimen_signature_of_director.name)
                    record.specimen_signature_of_director = None
                else:
                    return Response({"error": "Invalid or missing file name"}, status=status.HTTP_400_BAD_REQUEST)
                record.save()
                return Response({"message": f"{file_to_delete} deleted successfully"}, status=status.HTTP_200_OK)
            # If no specific file is requested, delete the entire record and its files
            if record.pan_card_file:
                record.pan_card_file.storage.delete(record.pan_card_file.name)
            if record.aadhaar_card_file:
                record.aadhaar_card_file.storage.delete(record.aadhaar_card_file.name)
            if record.passport_photo_file:
                record.passport_photo_file.storage.delete(record.passport_photo_file.name)
            if record.residential_address_proof_file:
                record.residential_address_proof_file.storage.delete(record.residential_address_proof_file.name)
            if record.form_dir2:
                record.form_dir2.storage.delete(record.form_dir2.name)
            if record.specimen_signature_of_director:
                record.specimen_signature_of_director.storage.delete(record.specimen_signature_of_director.name)

            record.delete()
            return Response({"message": "All director details deleted successfully"},
                            status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def shareholders_list(request):
    if request.method == 'GET':
        records = Shareholders.objects.all()
        serializer = ShareholdersSerializer(records, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data.copy()
        service_request = data.get('service_request')
        try:
            instance = Shareholders.objects.get(service_request=service_request)
            serializer = ShareholdersSerializer(instance, data=data, partial=True)
        except Shareholders.DoesNotExist:
            serializer = ShareholdersSerializer(data=data)
        if serializer.is_valid():
            main_data = serializer.save()
            # Auto-create ShareholdersDetails if detail data is provided
            if data.get('shareholder_first_name'):
                data['shareholders_ref'] = main_data.id
                combined_data = data.copy()
                combined_data.update(request.FILES)
                serializer_info = ShareholdersDetailsSerializer(data=combined_data)
                if serializer_info.is_valid():
                    serializer_info.save()
                else:
                    return Response(serializer_info.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(ShareholdersSerializer(main_data).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def get_shareholders_data(request):
    service_request_id = request.query_params.get('service_request_id')
    service_task_id = request.query_params.get('service_task')

    if not service_request_id and not service_task_id:
        return Response(
            {"error": "Provide either 'service_request_id' or 'service_task' as query parameter."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        if service_request_id:
            instance = Shareholders.objects.get(service_request_id=service_request_id)
        else:
            instance = Shareholders.objects.get(service_task_id=service_task_id)

        serializer = ShareholdersSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Shareholders.DoesNotExist:
        return Response({"error": "No matching Shareholders data found."}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def shareholders_detail(request, pk):
    try:
        record = ShareholdersDetails.objects.get(pk=pk)
    except ShareholdersDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ShareholdersDetailsSerializer(record)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = ShareholdersDetailsSerializer(record, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            file_to_delete = request.query_params.get('file')
            if file_to_delete:
                if file_to_delete == 'pan_card_file' and record.pan_card_file:
                    record.pan_card_file.storage.delete(record.pan_card_file.name)
                    record.pan_card_file = None
                elif file_to_delete == 'aadhaar_card_file' and record.aadhaar_card_file:
                    record.aadhaar_card_file.storage.delete(record.aadhaar_card_file.name)
                    record.aadhaar_card_file = None
                elif file_to_delete == 'bank_statement_file' and record.bank_statement_file:
                    record.bank_statement_file.storage.delete(record.bank_statement_file.name)
                    record.bank_statement_file = None
                elif file_to_delete == 'residential_address_proof_file' and record.residential_address_proof_file:
                    record.residential_address_proof_file.storage.delete(record.residential_address_proof_file.name)
                    record.residential_address_proof_file = None
                else:
                    return Response({"error": "Invalid or missing file name"}, status=status.HTTP_400_BAD_REQUEST)
                record.save()
                return Response({"message": f"{file_to_delete} deleted successfully"}, status=status.HTTP_200_OK)

            if record.pan_card_file:
                record.pan_card_file.storage.delete(record.pan_card_file.name)
            if record.aadhaar_card_file:
                record.aadhaar_card_file.storage.delete(record.aadhaar_card_file.name)
            if record.bank_statement_file:
                record.bank_statement_file.storage.delete(record.bank_statement_file.name)
            if record.residential_address_proof_file:
                record.residential_address_proof_file.storage.delete(record.residential_address_proof_file.name)

            record.delete()
            return Response({"message": "All shareholder details deleted successfully"},
                            status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST', 'GET'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def create_review_filing_certificate(request):
    try:
        if request.method == 'POST':
            serializer = ReviewFilingCertificateSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'GET':
            objs = ReviewFilingCertificate.objects.all()
            serializer = ReviewFilingCertificateSerializer(objs, many=True)
            return Response(serializer.data)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def review_filing_certificate_by_service_request(request):
    try:
        service_request_id = request.query_params.get('service_request_id')
        if not service_request_id:
            return Response({"error": "Provide 'service_request_id'"}, status=status.HTTP_400_BAD_REQUEST)

        instance = ReviewFilingCertificate.objects.get(service_request_id=service_request_id)
        serializer = ReviewFilingCertificateSerializer(instance)
        return Response(serializer.data)

    except ReviewFilingCertificate.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def review_filing_certificate_detail(request, id):
    try:
        record = ReviewFilingCertificate.objects.get(id=id)
    except ReviewFilingCertificate.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ReviewFilingCertificateSerializer(record)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ReviewFilingCertificateSerializer(record, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response({"error": "Invalid request method"}, status=status.HTTP_400_BAD_REQUEST)


Task_Model_Serializer_Map = {
    'Proposed Company Details':(ProposedCompanyDetails, ProposedCompanyDetailsSerializer),
    'Registered Office Address':(RegisteredOfficeAddressDetails, RegisteredOfficeAddressDetailsSerializer),
    'Authorized PaidUp Share Capital':(AuthorizedPaidUpShareCapital, AuthorizedPaidUpShareCapitalSerializer),
    'Directors':(Directors, DirectorsSerializer),
    'Shareholders':(Shareholders, ShareholdersSerializer),
    'Review Filing Certificate':(ReviewFilingCertificate,ReviewFilingCertificateSerializer)
}
@api_view(['GET'])
def get_service_request_full_details(request, service_request_id):
    try:
        service_request = ServiceRequest.objects.get(id=service_request_id)
    except ServiceRequest.DoesNotExist:
        return Response({"error": "Service request not found"}, status=status.HTTP_404_NOT_FOUND)
    data = {}
    tasks = service_request.service_tasks.all()
    for task in tasks:
        category_name = task.category_name.strip()
        config = Task_Model_Serializer_Map.get(category_name)

        task_info = {
            "task_id": task.id,
            "category_name": category_name,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date,
            "assignee": task.assignee.id if task.assignee else None,
            "reviewer": task.reviewer.id if task.reviewer else None,
            "data": None
        }
        if config:
            model, serializer_class = config
            try:
                instance = model.objects.get(service_request_id=service_request_id)
                serializer = serializer_class(instance)
                task_info["data"] = serializer.data
            except model.DoesNotExist:
                task_info["data"] = None
        else:
            task_info["data"] = "No model/serializer mapping defined"
        data[category_name] = task_info
    return Response({
        "service_request_id": service_request.id,
        "client": service_request.user.id if service_request.user else None,
        "task_data": data
    }, status=status.HTTP_200_OK)

Category_Task_Map = {
    "proposed_company_details": ["Proposed Company Details","Registered Office Address",
                                 "Authorized PaidUp Share Capital"],
    "Directors": ["Directors"],
    "Shareholders": ["Shareholders"],
    "review_filing_certificate": ["Review Filing Certificate"]
}

@api_view(['GET'])
def get_service_request_tasks_by_category(request):
    """
    Retrieve tasks for a service request by category.
    """
    service_request_id = request.query_params.get('service_request_id')
    section_key = request.query_params.get('section')

    try:
        service_request = ServiceRequest.objects.get(id=service_request_id)
    except ServiceRequest.DoesNotExist:
        return Response({"error": "Service request not found"}, status=status.HTTP_404_NOT_FOUND)

    section_tasks = Category_Task_Map.get(section_key)

    if not section_tasks:
        return Response({"error": "Invalid section key"}, status=status.HTTP_400_BAD_REQUEST)

    tasks = service_request.service_tasks.filter(category_name__in=section_tasks)
    data = {}
    for task in tasks:
        category_name = task.category_name.strip()
        config = Task_Model_Serializer_Map.get(category_name)
        task_info = {
                "task_id": task.id,
                "status": task.status,
                "priority": task.priority,
                "due_date": task.due_date,
                "assignee": task.assignee.id if task.assignee else None,
                "reviewer": task.reviewer.id if task.reviewer else None,
                "data": None
            }
        if config:
            model, serializer_class = config
            try:
                instance = model.objects.get(service_task=task, service_request=service_request)
                serializer = serializer_class(instance)
                task_info["data"] = serializer.data
            except model.DoesNotExist:
                task_info["data"] = None
        else:
            task_info["data"] = "No model/serializer mapping defined"

        data[category_name] = task_info

    return Response({
        "service_request_id": service_request.id,
        "client": service_request.user.id if service_request.user else None,
        "task_data": data
    }, status=status.HTTP_200_OK)