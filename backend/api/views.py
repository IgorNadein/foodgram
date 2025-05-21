from rest_framework import viewsets
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny
)
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from food.models import Recipe, Tag, Ingredient, IngredientRecipe
from .serializers import (
    RecipeSerializer,
    RecipeCreateSerializer,
    TagSerializer,
    IngredientSerializer
)
from .permissions import IsAuthorOrReadOnly
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status


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


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:  # anyone can view
            permission_classes = [AllowAny]
        else:  # requires authentication and authorization
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
            serializer.instance)  # Updated reference
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=False)  # full update
        serializer.is_valid(raise_exception=True)
        serializer.save()
        read_serializer = RecipeSerializer(instance)  # Updated reference
        return Response(read_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        # getting the serializer of the Recipe
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        # If not valid, then raise an exception.
        serializer.is_valid(raise_exception=True)

        ingredients = serializer.validated_data.pop(
            'ingredients', None)  # Delete all ingredients
        tags = serializer.validated_data.pop('tags', None)  # Delete tags

        serializer.save()  # Save the recipe
        # Save tags and ingredients to the recipe

        if ingredients is not None:  # if there were ingredients
            # We have to delete everything that was there before
            IngredientRecipe.objects.filter(recipe=instance).delete()
            # If there were, add them
            IngredientRecipe.objects.bulk_create([
                IngredientRecipe(
                    recipe=instance, ingredient=item['ingredient'], amount=item['amount'])
                for item in ingredients
            ])
        if tags is not None:  # If there were tags, set them
            instance.tags.set(tags)  # Assign the new ones

        read_serializer = RecipeSerializer(instance)  # Updated reference
        return Response(read_serializer.data)  # Return the output
