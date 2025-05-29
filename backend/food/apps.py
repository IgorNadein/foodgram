from django.apps import AppConfig


class FoodConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'food'

    def ready(self):
        from django.contrib import admin
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            admin.site.unregister(User)
        except admin.sites.NotRegistered:
            pass
