from django.urls import path
from . import views

urlpatterns = [
    path("api/auth/oauth-user/", views.oauth_user, name="oauth_user"),
]
