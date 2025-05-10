from rest_framework.decorators import api_view
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response
from rest_framework import status
from dataclasses import asdict
import stripe
from django.http import (
    HttpResponse,
    StreamingHttpResponse,
    JsonResponse,
    QueryDict,
    Http404,
)
from .models import AwemeCustomUser, AwemeUserCredits
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import timezone as dt_timezone
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.shortcuts import get_object_or_404
from .utils import (
    generate_success_generic_response,
    generate_fail_generic_response,
    aweme_login_required,
    generate_success_list_response,
)
from rest_framework_simplejwt.tokens import RefreshToken
from .interfaces import IUserProfile, IStripeSession, IUserCredits
from .constants import PLAN_ID, PLAN_ID_2_CREDITS
import logging
from typing import cast
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


def get_access_token_for_user(user: AwemeCustomUser) -> str:
    # Generate a refresh token instance to get the access token
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


def heartbeat(request):
    return HttpResponse("heartbeat...")


@api_view(["POST"])
def oauth_user(request: DRFRequest):
    logger.debug(request.data)
    provider = request.data.get("provider")
    provider_id = request.data.get("provider_id")
    email = request.data.get("email")
    nick_name = request.data.get("nick_name")
    avatar_url = request.data.get("avatar_url")

    logger.debug(f"{provider=}, {provider_id=}, {email=}, {nick_name=}, {avatar_url=}")

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
            provider_avatar_url=avatar_url,
        )
        AwemeUserCredits.objects.create(user=user)

        # Ensure create_user or subsequent saves handle all fields.

    # Generate JWT access token
    access_token = get_access_token_for_user(user)
    user_profile = IUserProfile(
        email=user.email,
        nick_name=user.nick_name,
        provider_avatar_url=user.provider_avatar_url,
    )
    response_data = asdict(user_profile)
    response_data["access_token"] = access_token

    return generate_success_generic_response(
        message="User logged in successfully", data=response_data
    )


@api_view(["POST"])
def register(request: DRFRequest):
    email = request.data.get("email")
    password = request.data.get("password")
    if password is None or not isinstance(password, str):
        return generate_fail_generic_response(
            message="Password is required", user=request.user
        )
    password = password.strip()

    if not email or not password:
        return generate_fail_generic_response(
            message="Email and password are required", user=request.user
        )

    if AwemeCustomUser.objects.filter(email=email).exists():
        return generate_fail_generic_response(
            message="User already exists", user=request.user
        )

    user = AwemeCustomUser.objects.create_user(email=email, password=password)
    AwemeUserCredits.objects.create(user=user)

    user_profile = IUserProfile(
        email=user.email,
        nick_name=user.nick_name,
    )

    return generate_success_generic_response(
        message="User registered successfully", data=asdict(user_profile)
    )


@api_view(["POST"])
def login(request: DRFRequest):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return generate_fail_generic_response(
            message="Email and password are required", user=request.user
        )

    try:
        user = AwemeCustomUser.objects.get(email=email)
    except AwemeCustomUser.DoesNotExist:
        return generate_fail_generic_response(
            message="User does not exist", user=request.user
        )

    if not user.check_password(password):
        return generate_fail_generic_response(
            message="Incorrect password", user=request.user
        )

    access_token = get_access_token_for_user(user)
    user_profile = IUserProfile(
        email=user.email,
        nick_name=user.nick_name,
    )
    response_data = asdict(user_profile)
    response_data["access_token"] = access_token

    return generate_success_generic_response(
        message="User logged in successfully", data=response_data
    )


@api_view(["POST"])
@aweme_login_required
def get_user_profile(request: DRFRequest):
    assert isinstance(request.user, AwemeCustomUser), "User must be authenticated"
    user = request.user

    user_profile = IUserProfile(
        email=user.email,
        nick_name=user.nick_name,
        provider_avatar_url=user.provider_avatar_url,
    )
    return generate_success_generic_response(
        message="User profile fetched successfully", data=asdict(user_profile)
    )


@api_view(["POST"])
@aweme_login_required
def get_user_credits(request: DRFRequest):
    assert isinstance(request.user, AwemeCustomUser), "User must be authenticated"
    user = request.user
    user_credits = AwemeUserCredits.objects.filter(user=user).first()
    if user_credits is None:
        user_credits = AwemeUserCredits.objects.create(
            user=user,
        )
        user_credits.save()
    user_credits_rsp = IUserCredits(
        credits=user_credits.credits,
        has_subscription=user_credits.has_subscription,
        cancel_at_end_time=user_credits.cancel_at_end_time,
        plan_type=user_credits.plan_type,
        subscription_start_time=(
            user_credits.subscription_start_time.strftime("%Y-%m-%d")
            if user_credits.subscription_start_time
            else None
        ),
        subscription_end_time=(
            user_credits.subscription_end_time.strftime("%Y-%m-%d")
            if user_credits.subscription_end_time
            else None
        ),
    )

    if (
        user_credits.subscription_end_time is not None
        and user_credits.subscription_end_time < timezone.now()
    ):
        user_credits_rsp.has_subscription = False

    return generate_success_generic_response(
        message="User credits fetched successfully", data=asdict(user_credits_rsp)
    )


@api_view(["POST"])
@aweme_login_required
def create_checkout_session(request: DRFRequest):
    logger.info(f"user={request.user.id}, request.data={request.data}")
    assert isinstance(request.user, AwemeCustomUser), "User must be authenticated"
    plan_type_str = request.data.get("plan_type")
    if plan_type_str is None:
        return generate_fail_generic_response(
            message="Plan type is required",
            user=request.user,
        )
    line_items = []
    try:
        plan_enum_member = PLAN_ID[plan_type_str]
        plan_id = plan_enum_member.value
    except KeyError:
        logger.warning(
            f"Invalid plan_type '{plan_type_str}' received from user {request.user.id if request.user else 'Unknown'}"
        )
        return generate_fail_generic_response(
            message=f"Invalid plan type: {plan_type_str}",
            user=request.user,
        )
    line_item = {"price": plan_id, "quantity": 1}
    line_items.append(line_item)

    checkout_session_params = {
        "line_items": line_items,
        "mode": "subscription",
        "success_url": f"{settings.WEBSITE_DOMAIN}",
        "cancel_url": f"{settings.WEBSITE_DOMAIN}",
    }

    user_credits = AwemeUserCredits.objects.filter(user=request.user).first()
    if user_credits is None:
        user_credits = AwemeUserCredits.objects.create(
            user=request.user,
        )

    if user_credits.stripe_customer_id is None:
        ## create a new user in stripe
        customer = stripe.Customer.create(
            email=request.user.email,
        )
        user_credits.stripe_customer_id = customer.id
        user_credits.save()
        checkout_session_params["customer"] = customer.id
    else:
        checkout_session_params["customer"] = user_credits.stripe_customer_id

    session = stripe.checkout.Session.create(**checkout_session_params)  # type: ignore

    stripeRsp = IStripeSession(url=session.url)
    return generate_success_generic_response(
        message="Success", data=asdict(stripeRsp), user=request.user
    )


@csrf_exempt
@api_view(("POST",))
def webhook_handler(request: DRFRequest):
    event = request.data
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        if session is None:
            return generate_fail_generic_response(message="Invalid event")
        customer_id = session.get("customer")
        user_credits = AwemeUserCredits.objects.filter(
            stripe_customer_id=customer_id
        ).first()
        if user_credits is None:
            return generate_fail_generic_response(
                message="Invalid user, no user email in the database"
            )
        user = user_credits.user
        with transaction.atomic():
            if session.get("mode") == "subscription":
                subscription_id = session.get("subscription")
                if subscription_id:
                    # Retrieve the subscription object
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    # Retrieve subscription start and end time
                    start_time_dt = datetime.now(dt_timezone.utc)
                    end_time_dt = start_time_dt + relativedelta(months=1)

                    user_credits.has_subscription = True
                    user_credits.subscription_start_time = start_time_dt
                    user_credits.subscription_end_time = end_time_dt

                    line_items = stripe.checkout.Session.list_line_items(session["id"])  # type: ignore
                    if len(line_items.data) < 1:
                        return generate_fail_generic_response(
                            message="Stripe error happen: no line items", user=user
                        )
                    line_item = line_items.data[0]
                    if line_item.price is None:
                        return generate_fail_generic_response(
                            message="Stripe error happen: no price", user=user
                        )
                    plan_id_str = line_item.price.id
                    try:
                        plan_id = PLAN_ID(line_item.price.id)
                    except Exception:
                        return generate_fail_generic_response(
                            message="Invalid plan id", user=user
                        )
                    credits_num = PLAN_ID_2_CREDITS[plan_id]

                    plan_name = PLAN_ID.get_name_from_price_Id(plan_id)
                    if plan_name:
                        user_credits.plan_type = plan_name[:-7]
                    user_credits.credits += credits_num
                    user_credits.acc_credits += credits_num
                    user_credits.cancel_at_end_time = False
                    user_credits.save()
                    return generate_success_generic_response(message="Success")
            else:
                return generate_success_generic_response(
                    message="Skip payment mode for now"
                )
    elif event["type"] == "invoice.payment_succeeded":
        session = event["data"]["object"]
        invoice = event["data"]["object"]

        ## only update when automatically renewal happen. Other taken care by the checkout.session.completed
        if invoice["billing_reason"] == "subscription_cycle":
            subscription_id = invoice["subscription"]
            customer_id = invoice["customer"]

            with transaction.atomic():
                user_credits = AwemeUserCredits.objects.filter(
                    stripe_customer_id=customer_id
                ).first()
                if user_credits is None:
                    return generate_fail_generic_response(message="Invalid user")
                subscription_id = invoice["subscription"]
                if subscription_id:
                    # Retrieve the subscription object
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    # Retrieve subscription start and end time
                    start_time = subscription.get("current_period_start")
                    end_time = subscription.get("current_period_end")
                    if start_time is None or end_time is None:
                        return generate_fail_generic_response(
                            message="Invalid subscription start time end time",
                        )
                    try:
                        start_time = float(start_time)
                        end_time = float(end_time)
                    except ValueError:
                        return generate_fail_generic_response(
                            message="Invalid subscription start time end time",
                        )
                    start_time_dt = datetime.utcfromtimestamp(start_time)
                    end_time_dt = datetime.utcfromtimestamp(end_time)
                    user_credits.has_subscription = True
                    user_credits.subscription_start_time = timezone.make_aware(
                        start_time_dt, dt_timezone.utc
                    )
                    user_credits.subscription_end_time = timezone.make_aware(
                        end_time_dt, dt_timezone.utc
                    )

                    line_items = invoice["lines"]
                    if len(line_items.data) < 1:
                        return generate_fail_generic_response(
                            message="Stripe error happen"
                        )
                    line_item = line_items.data[0]
                    if line_item.price is None:
                        return generate_fail_generic_response(
                            message="Stripe error happen"
                        )
                    plan_id_str = line_item.price.id
                    try:
                        plan_id = PLAN_ID(plan_id_str)
                    except Exception:
                        return generate_fail_generic_response(message="Invalid plan id")
                    credits_num = PLAN_ID_2_CREDITS[plan_id]
                    user_credits.credits += credits_num
                    user_credits.acc_credits += credits_num
                    user_credits.save()
                    return generate_success_generic_response(message="Success")
        else:
            return generate_success_generic_response(message="invoice payment ack")
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        with transaction.atomic():
            user_credits = AwemeUserCredits.objects.filter(
                stripe_customer_id=customer_id
            ).first()
            if user_credits is None:
                return generate_fail_generic_response(message="Invalid user")
            user_credits.has_subscription = False
            user_credits.save()
        return generate_success_generic_response(message="subscrption has been removed")
    elif event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        if subscription.get("cancel_at_period_end"):
            with transaction.atomic():
                user_credits = AwemeUserCredits.objects.filter(
                    stripe_customer_id=customer_id
                ).first()
                if user_credits is None:
                    return generate_fail_generic_response(message="Invalid user")
                user_credits.cancel_at_end_time = True
                user_credits.save()
            return generate_success_generic_response(
                message="get end cancel subsciption at end period"
            )
        return generate_success_generic_response(
            message="get other subscription update event"
        )
    return generate_success_generic_response(message="unhandled event ack ")