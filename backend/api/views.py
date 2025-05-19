from rest_framework import viewsets
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Count
from food.models import Recipe, Tag, Ingredient
from .serializers import (
    RecipeSerializer,
    RecipeCreateSerializer,
    RecipeShortSerializer,
    TagSerializer,
    IngredientSerializer
)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Tag.objects.annotate(recipes_count=Count('recipe'))


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['GET'])
    def search(self, request):
        query = request.query_params.get('query', '')
        if query:
            queryset = Ingredient.objects.filter(name__icontains=query)
        else:
            queryset = Ingredient.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Recipe.objects.all()
        if self.action == 'list':
            queryset = queryset.annotate(
                favorites_count=Count('favorites'),
                shopping_list_count=Count('shopping_list')
            )
        return queryset

    @action(detail=True, methods=['POST', 'DELETE'])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            request.user.favorites.add(recipe)
            return Response({'status': 'Рецепт добавлен в избранное'}, status=201)
        else:
            request.user.favorites.remove(recipe)
            return Response({'status': 'Рецепт удален из избранного'}, status=204)

    @action(detail=True, methods=['POST', 'DELETE'])
    def shopping_list(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            request.user.shopping_list.add(recipe)
            return Response({'status': 'Рецепт добавлен в список покупок'}, status=201)
        else:
            request.user.shopping_list.remove(recipe)
            return Response({'status': 'Рецепт удален из списка покупок'}, status=204)
