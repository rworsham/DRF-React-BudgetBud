from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from datetime import timedelta
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.utils.deprecation import MiddlewareMixin

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


class TokenRefreshMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.method in ['POST', 'GET']:
            access_token = request.COOKIES.get('access_token')
            refresh_token = request.COOKIES.get('refresh_token')
            print(f"auth token {access_token}")
            print(f"refresh token {refresh_token}")
            try:
                refresh = RefreshToken(refresh_token)

                new_access_token = str(refresh.access_token)
                response = JsonResponse({"message": "Access token refreshed successfully"})
                response.set_cookie(
                    'access_token', new_access_token,
                    httponly=True,
                    secure=True,
                    samesite='None',
                    max_age=timedelta(minutes=30),
                    path='/'
                )

                return response


            except Exception as e:
                raise AuthenticationFailed('Invalid or expired refresh token')

        return None