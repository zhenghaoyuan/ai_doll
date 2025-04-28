from django.db import models
from django.contrib.auth.models import AbstractUser, AnonymousUser
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import UserManager
from django.conf import settings
import datetime
import os
import uuid
import logging

logger = logging.getLogger(__name__)
from .storage_backends import get_media_storage


def get_timestamp() -> int:
    return int(datetime.datetime.now().timestamp())


class CustomUserManager(UserManager["AwemeCustomUser"]):
    def create_user(
        self, username=None, email=None, password=None, **extra_fields
    ) -> "AwemeCustomUser":
        if not email:
            raise ValueError("The Email field must be set")
        if not username:
            username = email
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, username=None, email=None, password=None, **extra_fields
    ) -> "AwemeCustomUser":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not email:
            raise ValueError("The Email field must be set")
        if not username:
            username = email
        return self.create_user(username, email, password, **extra_fields)


class AwemeCustomUser(AbstractUser):
    def user_avatar_upload_to(self, filename):
        # Use 'instance' to access model fields
        _, ext = os.path.splitext(filename)
        filename = f"{self.user_name or 'anonymous'}-{uuid.uuid4()}{ext}"
        logger.debug("user_avatar_upload_to: %s", filename)
        # Return the whole path to the file
        return os.path.join("user/avatar/", filename)

    email = models.EmailField(unique=True)
    user_name = models.CharField(max_length=255, unique=True, blank=True, null=True)
    birth_year = models.IntegerField(blank=True, null=True)
    gender = models.IntegerField(blank=True, null=True)
    nick_name = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.ImageField(
        storage=get_media_storage(),
        upload_to=user_avatar_upload_to,
        blank=True,
        null=True,
    )
    create_at = models.IntegerField(default=get_timestamp)
    update_at = models.IntegerField(default=get_timestamp)
    history = HistoricalRecords(cascade_delete_history=True)  # Track all the changes
    provider = models.CharField(max_length=255, blank=True, null=True)
    provider_id = models.CharField(max_length=255, blank=True, null=True)
    provider_avatar_url = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()  # type: ignore

    def __str__(self):
        return self.email
