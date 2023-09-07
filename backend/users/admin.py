from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import Subscription

User = get_user_model()


class UserAdmin(UserAdmin):
    list_display = ('pk', 'username', 'email')
    search_fields = ('username', 'email')
    empty_value_display = 'N/A'


class SubAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    search_fields = ('user', 'author')
    empty_value_display = 'N/A'


admin.site.register(User, UserAdmin)
admin.site.register(Subscription, SubAdmin)
admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
