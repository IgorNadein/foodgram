from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscription, User


class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email',
                    'first_name', 'last_name', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined')
    ordering = ('id',)


admin.site.register(User, CustomUserAdmin)


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'subscriber', 'author')
    list_filter = ('subscriber', 'author')
    search_fields = ('subscriber__username', 'author__username')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Customize the ForeignKey fields to filter only active users.
        """
        if db_field.name in ("author", "subscriber"):
            kwargs["queryset"] = User.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Subscription, SubscriptionAdmin)
