import os


def upload_to_basic_details(instance, filename):
    return os.path.join('Company Incorporation', instance.option1, filename)

def upload_to_shareholders_details(instance, filename):
    return os.path.join('Company Incorporation', str(instance.company.option1), str(instance.id), filename)

def upload_to_directors(instance, filename):
    return os.path.join('Company Incorporation', str(instance.company.option1), str(instance.id), filename)