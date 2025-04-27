from rest_framework.decorators import api_view
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response
from rest_framework import status
from dataclasses import asdict
from django.http import (
    HttpResponse,
    StreamingHttpResponse,
    JsonResponse,
    QueryDict,
    Http404,
)
from .models import AwemeCustomUser
from django.shortcuts import get_object_or_404
from .utils import generate_success_generic_response, generate_fail_generic_response, aweme_login_required
from rest_framework_simplejwt.tokens import RefreshToken
from .interfaces import IUserProfile

def get_access_token_for_user(user):
    # Generate a refresh token instance to get the access token
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)

def heartbeat(request):
    return HttpResponse("heartbeat...")

@api_view(["POST"])
def oauth_user(request: DRFRequest):
    print(request.data)
    provider = request.data.get("provider")
    provider_id = request.data.get("provider_id")
    email = request.data.get("email")
    nick_name = request.data.get("nick_name")
    avatar_url = request.data.get("avatar_url")

    print(provider, provider_id, email, nick_name, avatar_url)


    if not provider or not provider_id or not email:
        return generate_fail_generic_response(
            message="Provider, provider_id, and email are required", data={}
        )

    try:
        user = AwemeCustomUser.objects.get(email=email)
    except AwemeCustomUser.DoesNotExist:
        # Create user if not exists
        user = AwemeCustomUser.objects.create_user(
            email=email,
            nick_name=nick_name,
            provider=provider,
            provider_id=provider_id,
            provider_avatar_url=avatar_url
            )
        # Ensure create_user or subsequent saves handle all fields.

    # Generate JWT access token
    access_token = get_access_token_for_user(user)
    user_profile = IUserProfile(
            email=user.email,
            nick_name=user.nick_name,
            provider_avatar_url=user.provider_avatar_url
        )
    response_data = asdict(user_profile)
    response_data['access_token'] = access_token

    return generate_success_generic_response(
        message="User logged in successfully",
        data=response_data
    )

@api_view(["POST"])
@aweme_login_required
def get_user_profile(request: DRFRequest):
    user = request.user
    user_profile = IUserProfile(
        email=user.email,
        nick_name=user.nick_name,
        provider_avatar_url=user.provider_avatar_url
    )
    return generate_success_generic_response(
        message="User profile fetched successfully",
        data=asdict(user_profile)
    )
