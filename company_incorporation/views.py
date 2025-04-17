from graphql.language.parser import expect
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import *
from .serializers import *
import json
# Create a new company incorporation entry testing

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def create_company(request):
    if request.method == 'POST':
        data = request.data

        if 'address' in data and isinstance(data.get('address'), str):
            try:
                data['address'] = json.loads(data['address'])
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format for address"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            company_detail = CompanyIncorporation.objects.get(user_id=data['user'])
            serializer = CompanyIncorporationSerializer(company_detail,data=data,partial=True)
        except:
            serializer = CompanyIncorporationSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def get_all_companies(request):
    companies = CompanyIncorporation.objects.all()
    serializer = CompanyIncorporationSerializerRetrieval(companies, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def company_detail(request, id):
    if request.method == 'GET':
        try:
            company = CompanyIncorporation.objects.get(user_id=id)
        except CompanyIncorporation.DoesNotExist:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanyIncorporationSerializerRetrieval(company)
        return Response(serializer.data)

    elif request.method == 'PUT':
        company = CompanyIncorporation.objects.get(id=id)
        data = request.data.copy()
        if 'address' in data:
            address_data = data.get('address')
            if isinstance(address_data, str):
                try:
                    address_data = json.loads(address_data)  # Convert string to dict
                    data['address'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for address"},
                                    status=status.HTTP_400_BAD_REQUEST)
        serializer = CompanyIncorporationSerializer(company, data=data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        company = CompanyIncorporation.objects.get(id=id)
        company.delete()
        return Response({'message': 'Company deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def directors_details(request):
    if request.method == 'POST':
        data = request.data.copy()
        if 'address' in data:
            address_data = data.get('address')
            if isinstance(address_data, str):
                try:
                    address_data = json.loads(address_data)  # Convert string to dict
                    data['address'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for address"},
                                    status=status.HTTP_400_BAD_REQUEST)
        if 'shareholder_details' in data:
            address_data = data.get('shareholder_details')
            if isinstance(address_data, str):
                try:
                    address_data = json.loads(address_data)  # Convert string to dict
                    data['shareholder_details'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for address"},
                                    status=status.HTTP_400_BAD_REQUEST)
        
        if 'company' in data:
            existing_directors = Directors_details.objects.filter(
                first_name=data.get('first_name'),
                email=data.get('email'),
                phone_number=data.get('phone_number'),
                aadhar_number=data.get('aadhar_number'),
                dob=data.get('dob'),
                company_id=data.get('company')
            )
            if existing_directors.exists():
                return Response(
                    {"error": "A director with the same details already exists for this company"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = DirectorsDetailsSerializer(data=data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'GET':
        companies = Directors_details.objects.all()
        serializer = DirectorsDetailsSerializerRetrieval(companies, many=True)
        if serializer.data:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Director not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def directors_details_update(request, pk):
    if request.method == 'GET':
        try:
            director = Directors_details.objects.filter(company_id=pk)
        except Directors_details.DoesNotExist:
            return Response({'error': 'Director not found'}, status=status.HTTP_404_NOT_FOUND)
        if not director.exists():
            return Response({"detail": "No directors found for this company."},status=status.HTTP_201_CREATED)

        serializer = DirectorsDetailsSerializerRetrieval(director, many=True)
        return Response(serializer.data)


    elif request.method == 'PUT':
        director = Directors_details.objects.get(pk=pk)
        data = request.data

        if 'address' in data and isinstance(data['address'], str):

            try:

                data['address'] = json.loads(data['address'])

            except json.JSONDecodeError:

                return Response({"error": "Invalid JSON format for address"}, status=status.HTTP_400_BAD_REQUEST)

        if 'shareholder_details' in data and isinstance(data['shareholder_details'], str):

            try:

                data['shareholder_details'] = json.loads(data['shareholder_details'])

            except json.JSONDecodeError:

                return Response({"error": "Invalid JSON format for Shareholders"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DirectorsDetailsSerializer(director, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        director = Directors_details.objects.get(pk=pk)
        director.delete()
        return Response({'message': 'Director deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def share_holders_list_create(request):
    if request.method == 'GET':
        share_holders = Share_Holders_Information.objects.all()
        serializer = ShareHoldersInformationSerializerRetrieval(share_holders, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data = request.data.copy()
        if 'address' in data:
            address_data = data.get('address')
            if isinstance(address_data, str):
                try:
                    address_data = json.loads(address_data)  # Convert string to dict
                    data['address'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for address"},
                                    status=status.HTTP_400_BAD_REQUEST)
        
        if 'company' in data:
            existing_shareholders = Share_Holders_Information.objects.filter(
                type_of_shareholder=data.get('type_of_shareholder'),
                first_name=data.get('first_name'),
                email=data.get('email'),
                mobile=data.get('mobile'),
                company_id=data.get('company')
            )
            if existing_shareholders.exists():
                return Response(
                    {"error": "A Shareholder with the same details already exists for this company"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = ShareHoldersInformationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error": "Invalid request method"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser])
def shareholder_detail(request, pk):
    try:
        shareholder = Share_Holders_Information.objects.filter(company_id=pk)
    except Share_Holders_Information.DoesNotExist:
        return Response({"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        shareholder = Share_Holders_Information.objects.filter(company_id=pk)
        serializer = ShareHoldersInformationSerializerRetrieval(shareholder,many=True)
        return Response(serializer.data)

    elif request.method == 'PUT':
        shareholder = Share_Holders_Information.objects.get(pk=pk)
        data = request.data.copy()
        if 'address' in data:
            address_data = data.get('address')
            if isinstance(address_data, str):
                try:
                    address_data = json.loads(address_data)  # Convert string to dict
                    data['address'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for address"},
                                    status=status.HTTP_400_BAD_REQUEST)
            serializer = ShareHoldersInformationSerializer(shareholder, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        shareholder = Share_Holders_Information.objects.get(company_id=pk)
        shareholder.delete()
        return Response({"message": "Record deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def authorized_capital_list_create(request):
    if request.method == 'GET':
        capital_entries = Authorized_And_Paid_up_Capital.objects.all()
        serializer = AuthorizedAndPaidUpCapitalSerializer(capital_entries, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data
        try:
            capital_entries = Authorized_And_Paid_up_Capital.objects.get(company_id=data['company'])
            serializer = AuthorizedAndPaidUpCapitalSerializer(capital_entries,data=data,partial=True)
        except:
            serializer = AuthorizedAndPaidUpCapitalSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser])
def authorized_capital_detail(request, pk):
    try:
        capital_entry = Authorized_And_Paid_up_Capital.objects.get(company_id=pk)
    except Authorized_And_Paid_up_Capital.DoesNotExist:
        return Response({"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AuthorizedAndPaidUpCapitalSerializer(capital_entry)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = AuthorizedAndPaidUpCapitalSerializer(capital_entry, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        capital_entry.delete()
        return Response({"message": "Record deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def existing_company(request):
    if request.method == 'GET':
        capital_entries = Details_of_Existing_Directorships.objects.all()
        serializer = DetailsOfExistingDirectorshipsSerializer(capital_entries, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data.copy()
        
        # Check for existing company with same director and details
        if 'director' in data:
            existing_companies = Details_of_Existing_Directorships.objects.filter(
                companyName=data.get('companyName'),
                cin=data.get('cin'),
                typeOfCompany=data.get('typeOfCompany'),
                positionHeld=data.get('positionHeld'),
                director_id=data.get('director')
            )
            if existing_companies.exists():
                return Response(
                    {"error": "A company with the same details already exists for this director"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = DetailsOfExistingDirectorshipsSerializer(data=data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def existing_company_detail(request, pk):
    if request.method == 'GET':
        capital_entry = Details_of_Existing_Directorships.objects.filter(director_id=pk)

        serializer = DetailsOfExistingDirectorshipsSerializer(capital_entry,many=True)
        return Response(serializer.data)

    elif request.method == 'PUT':
        capital_entry = Details_of_Existing_Directorships.objects.get(id=pk)

        serializer = DetailsOfExistingDirectorshipsSerializer(capital_entry, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            capital_entry = Details_of_Existing_Directorships.objects.get(pk=pk)
            capital_entry.delete()
            return Response(
                {"message": "Record deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )

        except Details_of_Existing_Directorships.DoesNotExist:
            return Response(
                {"error": f"Record with id {pk} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )




