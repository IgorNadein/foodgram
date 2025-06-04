from django.contrib import admin
from rest_framework.authtoken.models import Token


class CustomAdminSite(admin.AdminSite):
    site_header = 'Администрирование сайта'
    site_title = 'Администрирование сайта'
    index_title = 'Администрирование сайта'


admin_site = CustomAdminSite(name='customadmin')


@admin.register(Token, site=admin_site)
class TokenAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'created')
    search_fields = ('key', 'user__username')
    readonly_fields = ('key', 'created')
