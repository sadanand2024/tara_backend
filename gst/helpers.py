import os

def upload_document(instance, filename):
    return os.path.join('GST', 'BusinessDocuments', str(instance.gst.id),filename)

def upload_principal_document(instance,filename):
    return os.path.join('GST','principal Detail',str(instance.gst.id),filename)