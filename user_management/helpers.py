import os


def gst_document_upload_path(instance, filename):
    # Get the name of the business, replace spaces with underscores
    business_name = instance.business.nameOfBusiness.replace(' ', '_')
    # Construct the upload path
    return os.path.join(business_name, 'gst_documents', filename)
