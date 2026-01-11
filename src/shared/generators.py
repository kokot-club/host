import random
import qrcode
import base64
from flask import render_template_string
from io import BytesIO
from string import ascii_lowercase, digits
from .auth import get_user_settings, uid_to_username

def random_string(length):
    return ''.join(random.choices(ascii_lowercase + digits, k=length))

def qr_code(content):
    img = qrcode.make(content)
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

def file_page(file_url, file_type, filename, file_size_mb, file_date, uploader_id):
    user_settings = get_user_settings(uploader_id) or {}
    uploader_username = uid_to_username(uploader_id) or 'unknown'

    for embed_setting_name in user_settings.keys():
        new_value = user_settings.get(embed_setting_name)
        if new_value and embed_setting_name.startswith('embed') and not new_value.startswith('#') and not new_value.startswith('http'):
            new_value = new_value.replace(r'%date%', file_date)
            new_value = new_value.replace(r'%size%', str(file_size_mb))
            new_value = new_value.replace(r'%filename%', filename)
            new_value = new_value.replace(r'%owner%', uploader_username)
            user_settings[embed_setting_name] = new_value

    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File - {{ filename }}</title>

    <link rel="shortcut icon" href="/static/images/favicon.png" type="image/png">
    <link rel="stylesheet" href="/static/css/global.css">
    <script src="/static/js/index.js"></script>

    {% if file_type.startswith('image') %}
        <meta property="twitter:card" content="summary_large_image">
        <meta property="twitter:image" content="{{ file_url }}">
        <meta property="og:image" content="{{ file_url }}">
    {% endif %}
                                  
    {% if embed_color %}
        <meta name="theme-color" content="{{ embed_color }}">
    {% endif %}
                                  
    {% if embed_sitename %}
        <meta property="og:site_name" content="{{ embed_sitename }}">
    {% endif %}
                                  
    {% if embed_authorname %}
        
    {% endif %}
                                  
    {% if embed_description %}
        <meta property="og:description" content="{{ embed_description }}">
    {% endif %}
                                  
    {% if embed_title %}
        <meta property="og:title" content="{{ embed_title }}">
    {% endif %}
</head>
<body>
    <main>
        <section class="file-page">
            {% if file_type.startswith('image') %}
                <h1>{{ filename }}</h1>
                <img src="{{ file_url }}" class="file-page__media">
            {% elif file_type.startswith('video') %}
                <h1>{{ filename }}</h1>    
                <video class="file-page__media" controls>
                    <source src="{{ file_url }}">
                    Your browser does not support the video tag.
                </video>
            {% elif file_type.startswith('audio') %}
                <div class="file-page__jukebox">
                    <svg class="file-page__cd" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><!-- Icon from Lucide by Lucide Contributors - https://github.com/lucide-icons/lucide/blob/main/LICENSE --><g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M6 12c0-1.7.7-3.2 1.8-4.2"/><circle cx="12" cy="12" r="2"/><path d="M18 12c0 1.7-.7 3.2-1.8 4.2"/></g></svg>
                    <h1 class="jukebox__title" title="{{ filename }}">{{ filename }}</h1>
                    <audio class="jukebox__source" controls>
                        <source src="{{ file_url }}">
                        Your browser does not support the audio tag.
                    </audio>
                </div>
            {% elif file_type.startswith('text') %}
                <h1>{{ filename }}</h1>
                <textarea class="file-page__text" id="text-preview" readonly></textarea>
                <script>
                    const preview = document.querySelector('#text-preview')
                    fetch('{{ file_url }}').then(data => data.text()).then(resp => {
                        preview.textContent = resp
                    })
                </script>
            {% else %}
                <h1>{{ filename }}</h1>
                <p>Unable to generate preview</p>
            {% endif %}

            <p class="file-page__details">{{ file_date }} • @{{ uploader_username }}</p>
            <div class="buttons">
                <a href="{{ file_url }}">
                    <button>Download ({{ file_size_mb }}MB)</button>
                </a>
            </div>

            <small>Go back to <a class="link" href="/">the dashboard</a></small>
        </section>
    </main>
</body>
</html>
""", file_url=file_url, file_type=file_type, filename=filename, file_size_mb=file_size_mb, file_date=file_date, uploader_username=uploader_username, **user_settings)

def sxcu_file(host, api_key):
    return f"""{{
    "Version": "17.0.0",
    "Name": "{host} - Uploader",
    "DestinationType": "ImageUploader, FileUploader",
    "RequestMethod": "POST",
    "RequestURL": "{host}files/upload",
    "Headers": {{
        "X-Api-Key": "{api_key}"
    }},
    "Body": "MultipartFormData",
    "FileFormName": "file",
    "URL": "{{json:url}}",
    "DeletionURL": "{{json:deletion_url}}",
    "ErrorMessage": "{{json:error}}"
}}"""