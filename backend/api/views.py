from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, serializers, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from food.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                         ShoppingCart, Tag)
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, RecipeShortLinkSerializer,
                          ShoppingCartFavoriteSerializer, TagSerializer)


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = RecipeSerializer(
            serializer.instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED, headers=headers
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        ingredients = serializer.validated_data.pop(
            'ingredients', None)
        tags = serializer.validated_data.pop('tags', None)
        if 'ingredients' not in request.data:
            raise serializers.ValidationError(
                {'ingredients': 'Обязательное поле'}
            )
        if 'tags' not in request.data:
            raise serializers.ValidationError(
                {'tags': 'Обязательное поле'}
            )
        serializer.save()

        if ingredients is not None:
            IngredientRecipe.objects.filter(recipe=instance).delete()
            IngredientRecipe.objects.bulk_create([
                IngredientRecipe(
                    recipe=instance,
                    ingredient=item['ingredient'],
                    amount=item['amount'])
                for item in ingredients
            ])
        if tags is not None:
            instance.tags.set(tags)

        read_serializer = RecipeSerializer(instance)
        return Response(read_serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_recipe_short_link(request, pk):
    """Создание короткой ссылки."""
    recipe = get_object_or_404(Recipe, pk=pk)
    short_link_value = request.build_absolute_uri(
        reverse('recipe-redirect', args=[recipe.short_link]))

    data = {'short_link': short_link_value}
    serializer = RecipeShortLinkSerializer(data=data)

    if serializer.is_valid():
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def recipe_redirect(request, short_link):
    """Переход по короткой ссылке."""
    recipe = get_object_or_404(Recipe, short_link=short_link)
    detail_url = reverse("api:recipe-list") + str(recipe.pk) + "/"
    return redirect(detail_url)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_shopping_cart(request):
    """
    Загружает текстовый файл, содержащий список покупок пользователя.
    """
    user = request.user
    shopping_cart_items = ShoppingCart.objects.filter(
        user=user).select_related('recipe')

    if not shopping_cart_items.exists():
        return HttpResponse(
            "Ваш список покупок пуст.",
            content_type='text/plain; charset=utf-8'
        )

    shopping_list_content = "Список покупок:\n\n"
    ingredients = {}

    for item in shopping_cart_items:
        recipe = item.recipe
        for ingredient_recipe in recipe.ingredient_recipes.all():
            ingredient = ingredient_recipe.ingredient
            amount = ingredient_recipe.amount
            if ingredient in ingredients:
                ingredients[ingredient] += amount
            else:
                ingredients[ingredient] = amount

    for ingredient, total_amount in ingredients.items():
        shopping_list_content += f"""
        - {ingredient.name} ({ingredient.measurement_unit}) - {total_amount}\n
        """

    response = HttpResponse(shopping_list_content,
                            content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_list.txt"'
    )
    return response


def manage_relation(request, pk, model, error_message, serializer=None):
    """
    Универсальная функция для добавления/удаления рецепта из связанной модели
    (например, Избранное, корзина покупок).

    Аргументы:
        request: Объект HTTP-запроса.
        pk: Первичный ключ объекта Recipe.
        model: модель для управления (например, Избранное, корзина покупок).
        error_message: Сообщение об ошибке, которое возвращается, если рецепт
        уже включен в отношение.
        serializer (optional): Сериализатор, который используется для запросов
        POST. По умолчанию установлено значение "Нет".

    Returns:
        Объект ответа.
    """
    recipe = get_object_or_404(Recipe, pk=pk)
    user = request.user

    if request.method == 'POST':
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'error': error_message}, status=status.HTTP_400_BAD_REQUEST
            )

        model.objects.create(user=user, recipe=recipe)
        if serializer:
            serializer = serializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_201_CREATED)

    elif request.method == 'DELETE':
        try:
            item = model.objects.get(user=user, recipe=recipe)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except model.DoesNotExist:
            return Response(
                {'error': 'Рецепт не найден в списке.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_shopping_cart(request, pk):
    """
    Управляет добавлением / удалением рецептов из корзины покупок пользователя.
    """
    return manage_relation(
        request, pk, ShoppingCart,
        'Рецепт уже в корзине покупок.', ShoppingCartFavoriteSerializer
    )


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_favorite(request, pk):
    """
    Управляет добавлением / удалением рецептов из избранного пользователя.
    """
    return manage_relation(
        request, pk, Favorite,
        'Рецепт уже в избранном.', ShoppingCartFavoriteSerializer
    )
