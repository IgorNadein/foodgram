from django.urls import path, include
from .routers import router
from users.views import AuthTokenView, LogoutView, UserAvatarUpdateView
from rest_framework.authtoken import views as auth_views
from . import views

urlpatterns = [
    path('auth/token/login/', AuthTokenView.as_view(), name='auth-token'),
    path('auth/token/logout/', LogoutView.as_view(), name='auth-token-logout'),
    path('users/me/avatar/', UserAvatarUpdateView.as_view(),
         name='user-avatar-update'),
    path('recipes/<int:pk>/get-link/', views.get_recipe_short_link,
         name='get-recipe-short-link'),
    path('recipes/<int:pk>/shopping_cart/',
         views.manage_shopping_cart, name='add-to-shopping-cart'),
    path('', include(router.urls)),
    # path('recipes/', views.recipe_list_create, name='recipe-create'),
]
