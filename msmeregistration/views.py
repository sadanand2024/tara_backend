from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework import status
from .serializers import *
import json

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def msme_list(request):
    if request.method == 'GET':
        msme_details = MSMEDetails.objects.all()
        serializer = MSMEDetailsSerializerRetrieval(msme_details, many=True)
        return Response(serializer.data)  # DRF Response ensures proper JSON formatting

    elif request.method == 'POST':
        data = request.data.copy()
        try:
            msme_details = MSMEDetails.objects.get(user_id=data['user'])
            serializer = MSMEDetailsSerializer(msme_details,data=data,partial=True)
        except:
            serializer = MSMEDetailsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)  # Return created record
        return Response(serializer.errors, status=400)


@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser,JSONParser])
def msme_detail(request, pk):
    try:
        msme = MSMEDetails.objects.get(pk=pk)
    except MSMEDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    if request.method == 'GET':
        serializer = MSMEDetailsSerializerRetrieval(msme)
        return Response(serializer.data)

    elif request.method == 'PUT':
        data = request.data.copy()
        json_fields = ['official_address_of_enterprise', 'location_of_plant_or_unit', 'bank_details','status',
                       'no_of_persons_employed','nic_code']
        for field in json_fields:
            if field in data:
                field_data = data.get(field)
                if isinstance(field_data, str):
                    try:
                        field_data = json.loads(field_data)  # Convert string to dict
                        data[field] = field_data
                    except json.JSONDecodeError:
                        return Response({f"error": f"Invalid JSON format for {field}"},
                                        status=status.HTTP_400_BAD_REQUEST)
        serializer = MSMEDetailsSerializer(msme, data=data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        msme.delete()
        return Response({"message": "Deleted successfully"}, status=204)
