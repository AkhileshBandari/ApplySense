from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from .serializers import UserRegisterSerializer, UserSerializer

User = get_user_model()


def build_auth_response(user, access_token, refresh_token):
    return {
        "user": UserSerializer(user).data,
        "access": access_token,
        "refresh": refresh_token,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
    }


class LoginView(TokenObtainPairView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response(
            build_auth_response(user, access_token, refresh_token),
            status=status.HTTP_200_OK,
        )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response(
            build_auth_response(user, access_token, refresh_token),
            status=status.HTTP_201_CREATED,
        )


class RefreshTokenView(TokenRefreshView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        refresh_value = request.data.get("refresh") or request.data.get("refresh_token")
        if refresh_value:
            data = request.data.copy()
            data["refresh"] = refresh_value
            request._full_data = data

        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        refresh_value = request.data.get("refresh") or request.data.get("refresh_token")
        if refresh_value:
            try:
                token = RefreshToken(refresh_value)
                token.blacklist()
            except Exception:
                pass

        return Response({"detail": "Logged out successfully"}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
