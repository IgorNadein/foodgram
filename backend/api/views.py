from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny
)
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework import status

from food.models import (
    Recipe,
    Tag,
    Ingredient,
    IngredientRecipe,
    ShoppingCart
)
from .serializers import (
    RecipeSerializer,
    RecipeCreateSerializer,
    TagSerializer,
    RecipeShortLinkSerializer,
    IngredientSerializer
)
from .permissions import IsAuthorOrReadOnly


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]

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
    serializer_class = RecipeSerializer

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

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        read_serializer = RecipeSerializer(instance)
        return Response(read_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        ingredients = serializer.validated_data.pop(
            'ingredients', None)
        tags = serializer.validated_data.pop('tags', None)
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
    recipe = get_object_or_404(Recipe, pk=pk)
    short_link = request.build_absolute_uri(
        reverse('recipe-redirect', args=[recipe.short_link]))  # Correct implementation
    serializer = RecipeShortLinkSerializer({'short_link': short_link})
    return Response(serializer.data, status=status.HTTP_200_OK)


def recipe_redirect(request, short_link):
    recipe = get_object_or_404(Recipe, short_link=short_link)
    detail_url = reverse("api:recipe-list") + str(recipe.pk) + "/"
    return redirect(detail_url)


@api_view(['POST', 'DELETE'])  # Allow both POST and DELETE
@permission_classes([IsAuthenticated])
def manage_shopping_cart(request, pk):
    """
    Adds or removes a recipe from the user's shopping cart.
    POST: Adds the recipe.
    DELETE: Removes the recipe.
    """
    recipe = get_object_or_404(Recipe, pk=pk)
    user = request.user

    if request.method == 'POST':
        # Add the recipe to the shopping cart
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response({'error': 'Recipe already in shopping cart.'}, status=status.HTTP_400_BAD_REQUEST)

        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = RecipeSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    elif request.method == 'DELETE':
        # Remove the recipe from the shopping cart
        try:
            shopping_cart_item = ShoppingCart.objects.get(user=user, recipe=recipe)
            shopping_cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)  # Successful deletion
        except ShoppingCart.DoesNotExist:
            return Response({'error': 'Recipe not in shopping cart.'}, status=status.HTTP_404_NOT_FOUND)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED) 

# @api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticatedOrReadOnly])
# def recipe_list_create(request):
#     if request.method == 'GET':
#         recipes = Recipe.objects.all()
#         serializer = RecipeSerializer(recipes, many=True)  # Use RecipeReadSerializer for GET
#         return Response(serializer.data)

#     elif request.method == 'POST':
#         serializer = RecipeCreateSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             recipe = serializer.save(author=request.user)  # Save the recipe
#             read_serializer = RecipeSerializer(recipe)  # Serialize using RecipeReadSerializer
#             return Response(read_serializer.data, status=status.HTTP_201_CREATED)  # Return serialized data
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
