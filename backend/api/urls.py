from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                       UserViewSet)


router = DefaultRouter()

router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'users', UserViewSet, basename='user')
router.register(r'recipes', RecipeViewSet, basename='recipe')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
