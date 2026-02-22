from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.identity.serializers import LoginSerializer, RegisterSerializer, UserAuthSerializer
from apps.identity.services import error_response, find_user_by_identifier, success_response


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        return success_response(
            {
                "token_type": "Token",
                "access_token": token.key,
                "user": UserAuthSerializer(user).data,
            },
            status_code=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        identifier = serializer.validated_data["identifier"]
        password = serializer.validated_data["password"]

        user = find_user_by_identifier(identifier)
        if user is None or not user.check_password(password):
            return error_response(
                code="INVALID_CREDENTIALS",
                message="The provided credentials are invalid.",
                details={},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return error_response(
                code="ACCOUNT_DISABLED",
                message="This account is disabled.",
                details={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        return success_response(
            {
                "token_type": "Token",
                "access_token": token.key,
                "user": UserAuthSerializer(user).data,
            },
            status_code=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return success_response({"message": "Logged out successfully."}, status_code=status.HTTP_200_OK)


class CurrentUserAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(UserAuthSerializer(request.user).data, status_code=status.HTTP_200_OK)
