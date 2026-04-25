from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from .serializers import (
    EmailTokenObtainSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    RegisterRequestSerializer,
    MessageResponseSerializer,
    UserInfoResponseSerializer,
    LogoutRequestSerializer,
    TokenResponseSerializer,
    TokenRefreshResponseSerializer,
)
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from drf_spectacular.utils import extend_schema

User = get_user_model()

@extend_schema(
    tags=["Auth"],
    summary="Register user",
    description="Creates a new user account using email and password.",
    request=RegisterRequestSerializer,
    responses={
        201: MessageResponseSerializer,
        400: MessageResponseSerializer,
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    email = request.data.get("email", "").lower()
    password = request.data.get("password")

    if not email or not password:
        return Response(
            {"message": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"message": "Email already in use."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_password(password)
    except ValidationError as e:
        return Response(
            {"message": " ".join(e.messages)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    User.objects.create_user(email=email, password=password)
    return Response(
        {"message": "User created successfully."},
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    tags=["Auth"],
    summary="Get current user",
    description="Returns basic information about the authenticated user.",
    responses={200: UserInfoResponseSerializer},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_info(request):
    return Response({
        "id": request.user.id,
        "email": request.user.email,
    })


@extend_schema(
    tags=["Auth"],
    summary="Logout user",
    description="Blacklists the provided refresh token and logs the user out.",
    request=LogoutRequestSerializer,
    responses={
        205: MessageResponseSerializer,
        400: MessageResponseSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh_token = request.data.get("refresh")

    if not refresh_token:
        return Response(
            {"message": "Refresh token is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(
            {"message": "Logged out successfully."},
            status=status.HTTP_205_RESET_CONTENT
        )
    except TokenError:
        return Response(
            {"message": "Invalid or expired refresh token."},
            status=status.HTTP_400_BAD_REQUEST
        )

@extend_schema(
    tags=["Auth"],
    summary="Request password reset",
    description="Sends a password reset link if an active account with the provided email exists.",
    request=PasswordResetRequestSerializer,
    responses={200: MessageResponseSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data["email"]

    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return Response(
            {"message": "If an account with that email exists, a reset link has been sent."},
            status=status.HTTP_200_OK
        )

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/reset-password/{uid}/{token}"

    send_mail(
        subject="Reset your password",
        message=(
            f"Hello,\n\n"
            f"Use the link below to reset your password:\n\n"
            f"{reset_link}\n\n"
            f"If you did not request this change, you can ignore this email."
        ),
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[user.email],
        fail_silently=False,
    )

    return Response(
        {"message": "If an account with that email exists, a reset link has been sent."},
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=["Auth"],
    summary="Confirm password reset",
    description="Resets the password using uid, token, and a new password.",
    request=PasswordResetConfirmSerializer,
    responses={
        200: MessageResponseSerializer,
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data["user"]
    password = serializer.validated_data["password"]

    user.set_password(password)
    user.save()

    return Response(
        {"message": "Password has been reset successfully."},
        status=status.HTTP_200_OK
    )

@extend_schema(
    tags=["Auth"],
    summary="Obtain JWT token pair",
    description="Authenticates the user with email and password and returns access and refresh tokens.",
    request=EmailTokenObtainSerializer,
    responses={200: TokenResponseSerializer},
)
class EmailTokenObtainView(TokenObtainPairView):
    serializer_class = EmailTokenObtainSerializer

@extend_schema(
    tags=["Auth"],
    summary="Refresh JWT access token",
    description="Returns a new access token using a valid refresh token.",
    request=TokenRefreshSerializer,
    responses={200: TokenRefreshResponseSerializer},
)
class CustomTokenRefreshView(TokenRefreshView):
    pass    