import os

def labour_license_upload_employer_details(instance, filename):
    return os.path.join('LabourLicense', 'EmployerDetails', str(instance.license.id), filename)

def labour_license_upload_file(instance,filename):
    return os.path.join('LabourLicense', 'files', str(instance.license.id), filename)
