import os
from rest_framework.response import Response

def upload_business_pan(instance, filename):
    return os.path.join('GST', 'BusinessPAN', str(instance.service_request.id), filename)

def upload_certificate_of_incorporation(instance, filename):
    return os.path.join('GST', 'CertificateOfIncorporation', str(instance.service_request.id), filename)

def upload_moa_aoa(instance, filename):
    return os.path.join('GST', 'MOA_AOA', str(instance.service_request.id), filename)


def upload_address_proof_file(instance, filename):
    return f'principal_place/address_proof/{instance.service_request.id}/{filename}'


def upload_rental_agreement(instance, filename):
    return f'principal_place/rental_agreement/{instance.service_request.id}/{filename}'


def upload_bank_statement(instance, filename):
    return f'principal_place/bank_statement/{instance.service_request.id}/{filename}'


def upload_promoter_pan(instance, filename):
    return os.path.join('GST', 'PromoterPAN', str(instance.promoter_detail.service_request.id), filename)

def upload_promoter_aadhaar(instance, filename):
    return os.path.join('GST', 'PromoterAadhaar', str(instance.promoter_detail.service_request.id), filename)

def upload_promoter_photo(instance, filename):
    return os.path.join('GST', 'PromoterPhotos', str(instance.promoter_detail.service_request.id), filename)

def get_all_records(model, serializer_class):
    """
    Returns serialized data for all objects of a model.
    """
    queryset = model.objects.all()
    serializer = serializer_class(queryset, many=True)
    return Response(serializer.data)

def review_filing_certificate(instance, filename):
    service_request_id = str(instance.service_request.id)
    # Construct the upload path
    return os.path.join('service_requests',  'GST', service_request_id,
                        'review_filing_certificate', filename)
