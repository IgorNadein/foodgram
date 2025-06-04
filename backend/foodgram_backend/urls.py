from django.urls import include, path

from .admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('api/', include(('api.urls', 'api'), namespace='api')),
    path('', include(('food.urls', 'food'), namespace='food')),
]
