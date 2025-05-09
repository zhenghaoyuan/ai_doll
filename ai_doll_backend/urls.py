from django.urls import path
from . import views

urlpatterns = [
    path("", views.heartbeat, name="aws_health"),
    path("api/auth/oauth/", views.oauth_user, name="oauth_user"),
    path("api/auth/register/", views.register, name="register"),
    path("api/auth/login/", views.login, name="login"),
    path("api/user/get_user_profile/", views.get_user_profile, name="get_user_profile"),
    path("api/user/get_user_credits/", views.get_user_credits, name="get_user_credits"),
    path(
        "api/payment/create_checkout_session/",
        views.create_checkout_session,
        name="create_checkout_session",
    ),
    path("api/payment/webhook_handler/", views.webhook_handler, name="webhook_handler"),
]