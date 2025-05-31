from django.urls import path

from . import views

urlpatterns = [
    path('s/<int:recipe_id>/', views.recipe_redirect),
]
