from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .serializers import *
import json

# 1. Entrepreneur Details Views
@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def entrepreneur_details_list(request):
    if request.method == 'GET':
        entrepreneurs = EntrepreneurDetails.objects.all()
        serializer = EntrepreneurDetailsSerializerRetrival(entrepreneurs, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data.copy()
        if 'address_of_entrepreneur' in data:
            address_data = data.get('address_of_entrepreneur')
            if isinstance(address_data, str):
                try:
                    address_data = json.loads(address_data)  # Convert string to dict
                    data['address_of_entrepreneur'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for address"},
                                    status=status.HTTP_400_BAD_REQUEST)
        try:
            entrepreneurs = EntrepreneurDetails.objects.get(user_id=data['user'])
            serializer = EntrepreneurDetailsSerializer(entrepreneurs,data=data,partial=True)
        except:
            serializer = EntrepreneurDetailsSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def entrepreneur_details_detail(request, pk):
    try:
        entrepreneur = EntrepreneurDetails.objects.get(pk=pk)
    except EntrepreneurDetails.DoesNotExist:
        return Response({"error": "Entrepreneur not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EntrepreneurDetailsSerializerRetrival(entrepreneur)
        return Response(serializer.data)

    elif request.method == 'PUT':
        data = request.data.copy()
        if 'address_of_entrepreneur' in data:
            address_data = data.get('address_of_entrepreneur')
            if isinstance(address_data, str):
                try:
                    address_data = json.loads(address_data)  # Convert string to dict
                    data['address_of_entrepreneur'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for address"},
                                    status=status.HTTP_400_BAD_REQUEST)
        serializer = EntrepreneurDetailsSerializer(entrepreneur, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        entrepreneur.delete()
        return Response({"message": "Entrepreneur deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

# 2. Establishment Details Views
@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def establishment_details_list(request):
    if request.method == 'GET':
        establishments = establishment_details.objects.all()
        serializer = EstablishmentDetailsSerializerRetrival(establishments, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data.copy()
        if 'address_of_establishment' in data:
            address_data = data.get('address_of_establishment')
            if isinstance(address_data, str):
                try:
                    address_data = json.loads(address_data)
                    data['address_of_establishment'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for address"},
                                    status=status.HTTP_400_BAD_REQUEST)
        try:
            establishments = establishment_details.objects.get(license_id=data['license'])
            serializer = EstablishmentDetailsSerializer(establishments,data=data,partial=True)
        except:
            serializer = EstablishmentDetailsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def establishment_details_detail(request, pk):
    try:
        establishment = establishment_details.objects.get(  license_id=pk)
    except establishment_details.DoesNotExist:
        return Response({"error": "Establishment not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EstablishmentDetailsSerializerRetrival(establishment)
        return Response(serializer.data)

    elif request.method == 'PUT':
        establishment = establishment_details.objects.get(license_id=pk)
        data = request.data.copy()
        if 'address_of_establishment' in data:
            address_data = data.get('address_of_establishment')
            if isinstance(address_data, str):
                try:
                    address_data = json.loads(address_data)
                    data['address_of_establishment'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for address"},
                                    status=status.HTTP_400_BAD_REQUEST)

        serializer = EstablishmentDetailsSerializer(establishment, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        establishment.delete()
        return Response({"message": "Establishment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def work_location_list(request):
    if request.method == 'GET':
        worklocation = Work_Location.objects.all()
        serializer = WorkLocationSerializerRetrival(worklocation, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data.copy()
        if 'work_location' in data:
            address_data = data.get('work_location')
            if isinstance(address_data, str):
                try:
                    address_data = json.loads(address_data)  # Convert string to dict
                    data['work_location'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for address"},
                                    status=status.HTTP_400_BAD_REQUEST)
        serializer = WorkLocationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def work_location_detail(request, pk):
    try:
        worklocation = Work_Location.objects.filter(license_id=pk)
    except Work_Location.DoesNotExist:
        return Response({"error": "Work Location not found"}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        serializer = WorkLocationSerializerRetrival(worklocation,many=True)
        return Response(serializer.data)
    elif request.method == 'PUT':
        worklocation = Work_Location.objects.get(license_id=pk)
        serializer = WorkLocationSerializer(worklocation, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        worklocation.delete()
        return Response({"message": "Work Location deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    else:
        return Response({"error": "Invalid request method"}, status=status.HTTP_400_BAD_REQUEST)

# 3. Employer Details Views
@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def employer_details_list(request):
    if request.method == 'GET':
        employers = EmployerDetails.objects.all()
        serializer = EmployerDetailsSerializerRetrival(employers, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data

        if 'address_of_employer' in data and isinstance(data.get('address_of_employer'), str):
            try:
                data['address_of_employer'] = json.loads(data['address_of_employer'])
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format for address"}, status=status.HTTP_400_BAD_REQUEST)

        if 'total_employees' in data and isinstance(data.get('total_employees'), str):
            try:
                data['total_employees'] = json.loads(data['total_employees'])
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format for total_employees"},
                                status=status.HTTP_400_BAD_REQUEST)
        try:
            employers = EmployerDetails.objects.get(license_id=data['license'])
            serializer = EmployerDetailsSerializer(employers,data=data,partial=True)
        except:
            serializer = EmployerDetailsSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def employer_details_detail(request, pk):
    try:
        employer = EmployerDetails.objects.get(license_id=pk)
    except EmployerDetails.DoesNotExist:
        return Response({"error": "Employer not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EmployerDetailsSerializerRetrival(employer)
        return Response(serializer.data)
    elif request.method == 'PUT':
        data = request.data.copy()
        if 'address_of_employer' in data:
            address_data = data.get('address_of_employer')
            if isinstance(address_data, str):
                try:
                    address_data = json.loads(address_data)  # Convert string to dict
                    data['address_of_employer'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for address"},
                                    status=status.HTTP_400_BAD_REQUEST)
        if 'total_employees' in data:
            address_data = data.get('total_employees')
            if isinstance(address_data, str):
                try:
                    address_data = json.loads(address_data)  # Convert string to dict
                    data['total_employees'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for address"},
                                    status=status.HTTP_400_BAD_REQUEST)
        serializer = EmployerDetailsSerializer(employer, data=data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        employer.delete()
        return Response({"message": "Employer deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def files_list(request):
    if request.method == 'GET':
        file = files.objects.all()
        serializer = filesSerializer(file, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data = request.data
        try:
            file = files.objects.get(license_id=data['license'])
            serializer = filesSerializer(file,data=data,partial=True)
        except:
            serializer = filesSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def files_detail(request, pk):
    try:
        file = files.objects.get(license_id=pk)
    except files.DoesNotExist:
        return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        serializer = filesSerializer(file)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = filesSerializer(file, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        file.delete()
        return Response({"message": "File deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    else:
        return Response({"error": "Invalid request method"}, status=status.HTTP_400_BAD_REQUEST)

