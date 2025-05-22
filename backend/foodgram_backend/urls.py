from django.contrib import admin
from django.urls import path, include
from api import views as api_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(('api.urls', 'api'), namespace='api')),
    path('s/<str:short_link>/', api_views.recipe_redirect, name='recipe-redirect'),
]
