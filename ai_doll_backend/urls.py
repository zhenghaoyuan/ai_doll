from django.urls import path
from . import views

urlpatterns = [
    path("", views.heartbeat, name="aws_health"),
    path("api/auth/oauth/", views.oauth_user, name="oauth_user"),
    path("api/user/get_user_profile/", views.get_user_profile, name="get_user_profile"),
]
