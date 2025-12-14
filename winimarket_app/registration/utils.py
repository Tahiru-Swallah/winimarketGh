import secrets
from django.utils import timezone

TOKEN_EXPIRY_HOURS = 24

def generate_verification_token():
    return secrets.token_urlsafe(48)

def regenerate_verification_token(verification):
    verification.token = generate_verification_token()
    verification.expires_at = timezone.now() + timezone.timedelta(hours=TOKEN_EXPIRY_HOURS)
    verification.save(updated_fields=['token', 'expires_at'])
    return verification