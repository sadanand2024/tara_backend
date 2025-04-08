import os

def trade_license_upload_trade_entity(instance, filename):
    return os.path.join('trade_license', str(instance.name_of_entity), filename)

def trade_license_upload_trade_photo(instance, filename):
    return os.path.join('trade_license', str(instance.id),str(instance.first_name), filename)

def trade_license_upload_trade_license(instance, filename):
    return os.path.join('trade_license', str(instance.license.id),str(instance.tin_number), filename)