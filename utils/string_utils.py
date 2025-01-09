import re
from urllib.parse import urlparse

from rest_framework import serializers
import bleach

ALLOWED_TAGS = [
    "p", "h1", "h2", "ul", "ol", "li", "sub", "sup", "blockquote",
    "pre", "a", "span", "strong", "em", "u", "s", "br"
]

ALLOWED_ATTRIBUTES = {"a": ["href", "title"]}
ALLOWED_SCHEMES = ['http', 'https']

def sanitize_string(string):
    if string is None:
        return ""
    
    # Sanitizar usando bleach para remover cualquier tag que no deseamos
    cleaned_string = bleach.clean(string, tags=[], strip=True)

    # Permittir solamente letras, numeros, espacios, apostrofes, comillas, comas y puntos
    pattern = re.compile(r"[^a-zA-Z0-9\s',:.?-ÁÉÍÓÚáéíóúÑñüÜ]")

    # Remover caracters indeseados
    sanitized_string = pattern.sub("", cleaned_string)

    return sanitized_string

def sanitize_html(content):
    if content is None:
        return ""
    
    return bleach.clean(
        content, 
        tags=ALLOWED_TAGS, 
        attributes=ALLOWED_ATTRIBUTES, 
        protocols=ALLOWED_SCHEMES, 
        strip=True
    )

def sanitize_username(username):
    """Sanitizes and validates a username to ensure it contains only safe characters."""
    if username is None:
        return ""

    # Strip all unwanted HTML or special characters
    cleaned_username = bleach.clean(username, tags=[], strip=True)

    # Define a regex pattern to allow only letters, numbers, underscores, and hyphens
    pattern = re.compile(r"[^a-zA-Z0-9_-]")

    # Remove any characters that don't match the pattern
    sanitized_username = pattern.sub("", cleaned_username)

    # Ensure the username is not too long (e.g., max 150 characters)
    if len(sanitized_username) > 150:
        raise serializers.ValidationError("Username may not be more than 150 characters.")

    # Ensure the username is not too short (e.g., min 3 characters)
    if len(sanitized_username) < 3:
        raise serializers.ValidationError("Username must be at least 3 characters long.")

    return sanitized_username

def sanitize_url(url):
    """
    Sanitizes and validates a URL to ensure it is safe and well-formed.
    Only allows specific schemes like 'http' and 'https'.
    """
    if url is None:
        return ""

    # Strip all unwanted HTML or special characters
    cleaned_url = bleach.clean(url, tags=[], strip=True)

    # Use urlparse to validate and check the scheme
    parsed_url = urlparse(cleaned_url)

    if not parsed_url.scheme or parsed_url.scheme not in ALLOWED_SCHEMES:
        raise serializers.ValidationError("Invalid URL scheme. Only 'http' and 'https' are allowed.")

    # Ensure the URL contains a valid hostname
    if not parsed_url.netloc:
        raise serializers.ValidationError("Invalid URL. Missing hostname.")

    # Allow only valid URL characters using regex (can be extended based on specific needs)
    url_pattern = re.compile(
        r'^(https?://)?([a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,6}))([:/?#].*)?$'
    )

    if not url_pattern.match(cleaned_url):
        raise serializers.ValidationError("Invalid URL format.")

    return cleaned_url