from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.db import transaction
from .models import OtherCapitalGains, OtherCapitalGainsDocument
from .serializers import OtherCapitalGainsSerializer, OtherCapitalGainsDocumentSerializer


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upsert_other_capital_gains_with_files(request):
    try:
        service_request = request.data.get('service_request')
        service_task = request.data.get('service_task')

        if not service_request or not service_task:
            return Response({"error": "Missing service_request or service_task"}, status=400)

        try:
            instance = OtherCapitalGains.objects.get(service_request=service_request)
            serializer = OtherCapitalGainsSerializer(instance, data=request.data, partial=True)
        except OtherCapitalGains.DoesNotExist:
            serializer = OtherCapitalGainsSerializer(data=request.data)

        with transaction.atomic():
            if serializer.is_valid(raise_exception=True):
                gain_instance = serializer.save()

                files = request.FILES.getlist('documents')
                for file in files:
                    OtherCapitalGainsDocument.objects.create(
                        other_capital_gains=gain_instance,
                        file=file
                    )

                return Response({
                    "message": "Other Capital Gains details saved",
                    "data": serializer.data,
                    "files_uploaded": len(files)
                }, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def get_other_capital_gains_details(request, service_request_id):
    try:
        gain = OtherCapitalGains.objects.get(service_request__id=service_request_id)
        serializer = OtherCapitalGainsSerializer(gain)

        return Response({
            "data": serializer.data
        })

    except OtherCapitalGains.DoesNotExist:
        return Response({"error": "Details not found"}, status=404)


@api_view(['DELETE'])
def delete_other_capital_gains(request, service_request_id):
    try:
        gain = OtherCapitalGains.objects.get(service_request__id=service_request_id)
        gain.delete()
        return Response({"message": "Deleted successfully"})

    except OtherCapitalGains.DoesNotExist:
        return Response({"error": "Record not found"}, status=404)


@api_view(['DELETE'])
def delete_other_capital_gains_file(request, file_id):
    try:
        doc = OtherCapitalGainsDocument.objects.get(id=file_id)
        doc.delete()
        return Response({"message": "File deleted"})

    except OtherCapitalGainsDocument.DoesNotExist:
        return Response({"error": "File not found"}, status=404)
