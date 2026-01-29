import random
from secrets import token_urlsafe
from string import ascii_lowercase, digits
from web.utils.networking import get_real_host

def random_string(length=7):
    return ''.join(random.choices(ascii_lowercase + digits, k=length))

def api_key(length=60):
    return token_urlsafe(length)

def invite_key(length=20):
    return random_string(length)

def sxcu_config(api_key):
    return f"""{{
        "Version": "17.0.0",
        "Name": "{get_real_host()} - Uploader",
        "DestinationType": "ImageUploader, TextUploader, FileUploader",
        "RequestMethod": "POST",
        "RequestURL": "{get_real_host()}files/upload",
        "Headers": {{
            "X-Api-Key": "{api_key}"
        }},
        "Body": "MultipartFormData",
        "FileFormName": "file",
        "URL": "{{json:url}}",
        "DeletionURL": "{{json:deletion_url}}",
        "ErrorMessage": "{{json:error}}"
    }}"""