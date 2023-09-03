from django.contrib import admin

from .models import Subscription, User


class UserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'username', 'email', 'role')
    search_fields = ('username', 'email')
    empty_value_display = 'N/A'
    list_editable = ('role',)


class SubAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    search_fields = ('user', 'author')
    empty_value_display = 'N/A'


admin.site.register(User, UserAdmin)
admin.site.register(Subscription, SubAdmin)
