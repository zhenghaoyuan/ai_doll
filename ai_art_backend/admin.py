from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import AwemeCustomUser

# Register your models here.

admin.site.register(AwemeCustomUser, SimpleHistoryAdmin)
