from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class JWTCookieAuthentication(JWTAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get('access_token')

        if not token:
            return None

        try:
            validated_token = self.get_validated_token(token)
        except Exception as e:
            raise AuthenticationFailed('Token is invalid or expired')

        user = self.get_user(validated_token)

        return user, validated_token