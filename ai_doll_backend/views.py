from rest_framework.decorators import api_view
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response
from rest_framework import status
from django.http import (
    HttpResponse,
    StreamingHttpResponse,
    JsonResponse,
    QueryDict,
    Http404,
)
from .models import AwemeCustomUser
from django.shortcuts import get_object_or_404
from .utils import generate_success_generic_response, generate_fail_generic_response


@api_view(["POST"])
def oauth_user(request: DRFRequest):
    provider = request.data.get("provider")
    provider_id = request.data.get("provider_id")
    email = request.data.get("email")
    nick_name = request.data.get("nick_name")
    avatar = request.data.get("avatar")

    if not provider or not provider_id or not email:
        return generate_fail_generic_response(
            message="Provider and provider_id and email are required", data={}
        )

    user = AwemeCustomUser.objects.get(email=email)
    # create user if not exists
    if not user:
        user = AwemeCustomUser.objects.create_user(email=email, nick_name=nick_name)
        user.avatar = avatar
        user.provider = provider
        user.provider_id = provider_id
        user.save()

    return generate_success_generic_response(
        message="User created successfully",
        data={
            "user_id": user.id,
            "email": user.email,
            "nick_name": user.nick_name,
        },
    )
