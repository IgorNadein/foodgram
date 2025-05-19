# api/routers.py
from rest_framework.routers import DefaultRouter
from api.views import TagViewSet, IngredientViewSet, RecipeViewSet  # Исправленный импорт
from users.views import UserViewSet

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'users', UserViewSet)

urlpatterns = router.urls
