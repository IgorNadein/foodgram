from django.urls import include, path

from users import views as users_views
from . import views
from .routers import router

urlpatterns = [
    path('auth/token/login/',
         users_views.AuthTokenView.as_view(),
         name='auth-token'),
    path('auth/token/logout/',
         users_views.LogoutView.as_view(),
         name='auth-token-logout'),
    path('users/me/avatar/',
         users_views.UserAvatarUpdateOrDeleteView.as_view(),
         name='user-avatar-update'),
    path('users/subscriptions/',
         users_views.SubscriptionsListView.as_view(),
         name='user-subscriptions'),
    path('recipes/<int:pk>/get-link/',
         views.get_recipe_short_link,
         name='get-recipe-short-link'),
    path('recipes/<int:pk>/shopping_cart/',
         views.manage_shopping_cart,
         name='add-to-shopping-cart'),
    path('recipes/<int:pk>/favorite/',
         views.manage_favorite,
         name='add-to-shopping-cart'),
    path('recipes/download_shopping_cart/',
         views.download_shopping_cart,
         name='download-shopping-cart'),
    path('', include(router.urls)),
]
