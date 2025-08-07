import requests
from django.conf import settings


def validate_bin(bin_number):
    resp = requests.get(settings.GOV_API_URL, params={'bin': bin_number})
    return resp.ok and resp.json().get('valid', False)
