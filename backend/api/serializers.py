import base64

from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.core.files.base import ContentFile
from food.models import Tag, Ingredient, Recipe, IngredientRecipe, Favorite, ShoppingCart
from rest_framework.validators import UniqueTogetherValidator

from users.serializers import UserSerializer
from food.serializers import Base64ImageField

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели Tag."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('ingredient', 'amount')


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['user', 'recipe']
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=['user', 'recipe']
            )
        ]


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    # Changed from Base64ImageField
    image = serializers.URLField(source='image.url', read_only=True)
    # Added read_only=True for output representation
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_ingredients(self, obj):
        # Efficiently retrieve ingredient information using prefetch_related
        ingredients = IngredientRecipe.objects.filter(
            recipe=obj).select_related('ingredient')  # Only one query now!
        return [
            {
                'id': item.ingredient.id,
                'name': item.ingredient.name,
                'measurement_unit': item.ingredient.measurement_unit,
                'amount': item.amount
            }
            for item in ingredients
        ]

    def get_is_favorited(self, obj):
        # You will need to pass in the request via the context
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        # You will need to pass in the request via the context
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    image = Base64ImageField(required=True)
    ingredients = serializers.ListField()  # Custom validation handles this
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = (
            'author',
            'cooking_time',
            'image',
            'ingredients',
            'name',
            'tags',
            'text',
        )

    def validate_ingredients(self, value):
        """
        Check that all ingredients are valid. Returns a list of dicts,
        each containing 'ingredient' and 'amount'.
        """
        validated_ingredients = []
        for ingredient_data in value:
            if not isinstance(ingredient_data, dict):
                raise serializers.ValidationError(
                    "Each ingredient entry must be a dictionary."
                )
            if 'id' not in ingredient_data or 'amount' not in ingredient_data:
                raise serializers.ValidationError(
                    "Each ingredient entry must have both 'id' and 'amount'."
                )
            try:
                ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    f"Ingredient with id '{ingredient_data['id']}' does not exist."
                )
            if not isinstance(ingredient_data['amount'], int):
                raise serializers.ValidationError(
                    "Ingredient 'amount' must be an integer."
                )

            if ingredient_data['amount'] <= 0:
                raise serializers.ValidationError(
                    "Ingredient 'amount' must be a positive integer."
                )

            validated_ingredients.append({
                'ingredient': ingredient,
                'amount': ingredient_data['amount']
            })

        return validated_ingredients  # Return validated data

    def create(self, validated_data):
        ingredients = validated_data.pop(
            'ingredients')  # Extract ingredients first
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)  # No need to pop tags

        # Create IngredientRecipe objects more efficiently
        IngredientRecipe.objects.bulk_create([
            IngredientRecipe(
                recipe=recipe, ingredient=item['ingredient'], amount=item['amount'])
            for item in ingredients
        ])
        return recipe


class RecipeShortLinkSerializer(serializers.Serializer):
    short_link = serializers.CharField(read_only=True)
