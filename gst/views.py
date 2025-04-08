from django.shortcuts import render
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import json
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from .models import partner

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def create_basic_details(request):
    if request.method == 'GET':
        details = basic_Details.objects.all()
        serializer = BasicDetailsSerializer(details,many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data = request.data
        try:
            details = basic_Details.objects.get(user_id=data['user'])
            serializer = BasicDetailsSerializer(details,data=data,partial=True)
        except:
            serializer = BasicDetailsSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','PUT','DELETE'])
@parser_classes([MultiPartParser,FormParser,JSONParser])
def basic_details_view(request, pk):
    basic_detail = basic_Details.objects.get(pk=pk)

    if request.method == 'GET':
        serializer = BasicDetailsSerializer(basic_detail)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = BasicDetailsSerializer(basic_detail, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        basic_detail.delete()
        return Response({"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def business_details_list(request):

    if request.method == 'GET':
        queryset = business_Details.objects.all()
        serializer = BusinessDetailsSerializerRetrieval(queryset, many=True)  # ✅ Fix: many=True for multiple objects
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        data = request.data.copy()
        if 'gst_details' in data:
            address_data = data.get('gst_details')
            if isinstance(address_data, str):
                try:
                    address_data = json.loads(address_data)  # Convert string to dict
                    data['gst_details'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for address"},
                                    status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = business_Details.objects.get(gst_id=data['gst'])
            serializer = BusinessDetailsSerializer(queryset,data=data,partial=True)
        except:
            serializer = BusinessDetailsSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def business_details_view(request, pk):
    business_detail = business_Details.objects.get(gst_id=pk)
    if request.method == 'GET':
        serializer = BusinessDetailsSerializerRetrieval(business_detail)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        data = request.data.copy()
        if 'gst_details' in data:
            gst_details_data = data.get('gst_details')
            if isinstance(gst_details_data, str):
                try:
                    address_data = json.loads(gst_details_data)  # Convert string to dict
                    data['gst_details'] = address_data
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for gst_details"},
                                    status=status.HTTP_400_BAD_REQUEST)
        serializer = BusinessDetailsSerializer(business_detail, data=data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        business_detail.delete()
        return Response({"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def business_document_list_create(request):
    if request.method == 'GET':
        documents = BusinessDocuments.objects.all()
        serializer = BusinessDocumentsSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        data = request.data
        try:
            documents = BusinessDocuments.objects.get(gst_id=data['gst'])
            serializer = BusinessDocumentsSerializer(documents,data=data,partial=True)
        except:
            serializer = BusinessDocumentsSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def business_document_detail(request, pk):
    document = BusinessDocuments.objects.get(gst_id=pk)

    if request.method == 'GET':
        serializer = BusinessDocumentsSerializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = BusinessDocumentsSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        document.delete()
        return Response({"message": "Document deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def partner_list(request):
    if request.method == 'GET':
        queryset = partner.objects.all()
        serializer = PartnerSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        data = request.data.copy()
        if 'gst' in data:
            existing_partners = partner.objects.filter(
                gst_id=data.get('gst'),
                first_name=data.get('first_name'),
                email=data.get('email'),
                mobile=data.get('mobile'),
                dob=data.get('dob'),
                pan_number=data.get('pan_number')
            )
            if existing_partners.exists():
                return Response(
                    {"error": "A partner with the same details already exists for this GST"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = PartnerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def partner_detail(request, pk):
    partner_instance = partner.objects.filter(gst_id=pk)

    if request.method == 'GET':
        serializer = PartnerSerializer(partner_instance,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        partner_instance = partner.objects.get(id=pk)
        serializer = PartnerSerializer(partner_instance, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        partner_instance.delete()
        return Response({"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def principal_place_list(request):
    if request.method == 'GET':
        queryset = principal_Place_Detail.objects.all()
        serializer = PrincipalPlaceDetailSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        data = request.data
        try:
            queryset = principal_Place_Detail.objects.get(gst_id=data['gst'])
            serializer = PrincipalPlaceDetailSerializer(queryset,data=data,partial=True)
        except:
            serializer = PrincipalPlaceDetailSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def principal_place_detail_view(request, pk):
    principal_place = principal_Place_Detail.objects.get(gst_id=pk)

    if request.method == 'GET':
        serializer = PrincipalPlaceDetailSerializer(principal_place)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        try:
            instance = principal_Place_Detail.objects.get(gst_id=pk)
        except principal_Place_Detail.DoesNotExist:
            return Response({"error": "Data not found"}, status=404)
        serializer = PrincipalPlaceDetailSerializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()  # Ensure instance is passed
            return Response(serializer.data, status=200)

        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        principal_place.delete()
        return Response({"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)