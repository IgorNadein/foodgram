# api/routers.py
from rest_framework.routers import DefaultRouter
from api.views import TagViewSet, IngredientViewSet, RecipeViewSet
from users.views import UserViewSet


router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'users', UserViewSet)
router.register(r'recipes', RecipeViewSet)

urlpatterns = router.urls
