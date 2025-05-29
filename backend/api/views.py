from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from food.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .paginations import LimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          ReadRecipeSerializer, RecipePreviewSerializer,
                          RecipeWriteSerializer, SubscribedUserSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserSerializer)

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """Кастомный вьюсет пользователя с обработкой подписок."""
    serializer_class = UserSerializer
    pagination_class = LimitPagination

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        """Получение информации о текущем пользователе."""
        return super().me(request)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        serializer_class=AvatarSerializer,
        permission_classes=(IsAuthenticated,)
    )
    def avatar(self, request):
        """Обновление или удаление аватара пользователя."""
        user = request.user

        if request.method == 'PUT':
            serializer = self.get_serializer(
                user, data=request.data, partial=False
            )
            serializer.is_valid(raise_exception=True)
            if user.avatar:
                user.avatar.delete(save=False)
            instance = serializer.save()
            avatar_url = instance.avatar.url
            full_avatar_url = request.build_absolute_uri(avatar_url)

            return Response(
                {'avatar': full_avatar_url},
                status=status.HTTP_200_OK
            )

        else:
            if user.avatar:
                user.avatar.delete(save=True)
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        """Подписка/отписка от пользователя."""
        author = get_object_or_404(User, id=id)
        serializer = SubscriptionSerializer(
            data=request.data,
            context={
                'request': request,
                'author': author,
                'recipes_limit': request.query_params.get('recipes_limit')
            }
        )

        serializer.is_valid(raise_exception=True)
        if request.method == 'POST':
            serializer.create(serializer.validated_data)
            return Response(
                serializer.to_representation(author),
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            serializer.destroy()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise ValidationError

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Получение списка подписок пользователя."""
        subscribed_authors = User.objects.filter(
            authors__subscriber=request.user)
        page = self.paginate_queryset(subscribed_authors)
        serializer = SubscribedUserSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    pagination_class = LimitPagination
    queryset = Recipe.objects.all()
    serializer_class = ReadRecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ReadRecipeSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        url_path='get-link',
        permission_classes=(AllowAny,)
    )
    def get_link(self, request, pk=None):
        """Создание короткой ссылки."""
        return Response({'short-link': request.build_absolute_uri(
            f'/s/{pk}/')}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user

        recipes = user.shopping_cart_recipes.select_related(
            'recipe').all().distinct()

        ingredients_with_sum = recipes.values(
            'recipe__recipe_ingredients__ingredient__name',
            'recipe__recipe_ingredients__ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('recipe__recipe_ingredients__amount')
        ).order_by('recipe__recipe_ingredients__ingredient__name')

        content = render_to_string('shopping_list.txt', {
            'ingredients': ingredients_with_sum,
            'recipes': recipes,
            'date': timezone.now().date()
        })
        return FileResponse(
            content,
            as_attachment=True,
            filename='shopping_list.txt'
        )

    def manage_relation(self, request, pk, model):
        """
        Универсальная функция для добавления/удаления
        рецепта из связанной модели.

        Аргументы:
            request: Объект HTTP-запроса
            pk: Первичный ключ объекта Recipe
            model: Модель для управления (например, Favorite, ShoppingCart)
            error_message: Сообщение об ошибке при дублировании
            serializer: Сериализатор для ответа (опционально)

        Примеры:
            Добавление в избранное: POST /api/recipes/{id}/favorite/
            Удаление из корзины: DELETE /api/recipes/{id}/shopping_cart/
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            obj, created = model.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                return Response(
                    {'error': f'Рецепт уже в {model._meta.verbose_name}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                RecipePreviewSerializer(
                    recipe, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        elif request.method == 'DELETE':
            try:
                get_object_or_404(model, user=user, recipe=recipe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Http404:
                return Response(
                    {'error': 'Рецепт не найден в списке.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(
        detail=True,
        url_path='shopping_cart',
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        """
        Управляет добавлением / удалением
        рецептов из корзины покупок пользователя.
        """
        return self.manage_relation(
            request, pk, ShoppingCart,
        )

    @action(
        detail=True,
        url_path='favorite',
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """
        Управляет добавлением / удалением
        рецептов из избранного пользователя.
        """
        return self.manage_relation(
            request, pk, Favorite,
        )
