# accounts/emails.py

from django.core.mail import send_mail
from django.conf import settings

def send_verification_email(user, token):
    verify_url = f"https://yourdomain.com/verify-email/{token}/"

    subject = "Verify your email address"
    message = f"""
        Hi {user.email},

        Welcome to UEW Marketplace.

        Please verify your email address by clicking the link below:

        {verify_url}

        This link will expire in 24 hours.

        If you didn’t create this account, please ignore this email.
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
