import os
import requests
from flask import request

CLOUDFLARE_TURNSTILE_SECRET = os.environ.get('CLOUDFLARE_TURNSTILE_SECRET')

def verify_cloudflare_challenge(challenge_token):
    if CLOUDFLARE_TURNSTILE_SECRET:
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={'secret': CLOUDFLARE_TURNSTILE_SECRET, 'response': challenge_token}
        )

        if response and response.json():
            return response.json().get('success', False)
        
        return False
    
    # protection is off
    print('Turnstile is off, skipping...')
    return True

def get_real_ip():
    x_real_ip = request.headers.get('X-Real-IP') or request.headers.get('X-Real-Ip')
    return x_real_ip or request.remote_addr

def get_real_host():
    x_host = request.headers.get('X-Host')
    return x_host and f'https://{x_host}/' or request.host_url