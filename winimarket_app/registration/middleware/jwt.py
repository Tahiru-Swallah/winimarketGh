from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate user using JWT from either
    the Authorization header or access_token cookie.
    Sets request.user so Django views can use @login_required or check user.is_authenticated.
    """

    def process_request(self, request):
        jwt_authenticator = JWTAuthentication()

        raw_token = None

        # Try to get token from Authorization header
        header = jwt_authenticator.get_header(request)
        if header:
            raw_token = jwt_authenticator.get_raw_token(header)

        # If no token in header, try from cookies
        if raw_token is None:
            raw_token = request.COOKIES.get('access_token')

        if raw_token is None:
            return  # No token, user stays AnonymousUser

        try:
            validated_token = jwt_authenticator.get_validated_token(raw_token)
            user = jwt_authenticator.get_user(validated_token)
            request.user = user
            request._cached_user = user
        except AuthenticationFailed:
            pass  # Leave as AnonymousUser if token is invalid
