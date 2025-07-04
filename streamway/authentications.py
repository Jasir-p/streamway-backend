from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get("access_token")
        if not token:
            return None  # No token, let IsAuthenticated fail later

        try:
            validated_token = self.get_validated_token(token)
        except Exception:
            raise AuthenticationFailed("Invalid or expired access token")

        return self.get_user(validated_token), validated_token

