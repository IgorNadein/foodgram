from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from food.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                         ShoppingCart, Tag)
from food.serializers import Base64ImageField
from users.serializers import UserSerializer

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели Tag."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели Ingredient."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор модели IngredientRecipe."""
    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('ingredient', 'amount')


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор модели Favorite."""
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


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe."""
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.URLField(source='image.url', read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = [
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
        ]

    def get_ingredients(self, obj):
        ingredients = IngredientRecipe.objects.filter(
            recipe=obj).select_related('ingredient')
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
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для содания рецепта."""
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    image = Base64ImageField(required=True)
    ingredients = serializers.ListField(required=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=True
    )

    class Meta:
        model = Recipe
        fields = [
            'author',
            'cooking_time',
            'image',
            'ingredients',
            'name',
            'tags',
            'text',
        ]

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                "Список тегов не может быть пустым."
            )

        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError("Теги не должны повторяться.")

        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Список ингридиентов не может быть пустым."
            )

        ingredient_ids = []  # To track seen ingredient IDs
        validated_ingredients = []

        for ingredient_data in value:
            if not isinstance(ingredient_data, dict):
                raise serializers.ValidationError(
                    "Выберите из списка ингридиентов."
                )
            if 'id' not in ingredient_data or 'amount' not in ingredient_data:
                raise serializers.ValidationError(
                    "Каждый ингридиент должна содержать 'id' и 'amount'."
                )
            try:
                ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    f"Ингридиент с id '{ingredient_data['id']}' не существует."
                )

            if ingredient.id in ingredient_ids:
                raise serializers.ValidationError(
                    f"Ингредиент с id '{ingredient_data['id']}' дублируется.")
            ingredient_ids.append(ingredient.id)

            if not isinstance(ingredient_data['amount'], int):
                raise serializers.ValidationError(
                    "'amount' должен быть целым числом."
                )

            if ingredient_data['amount'] <= 0:
                raise serializers.ValidationError(
                    "'amount' должно быть положительным числом."
                )

            validated_ingredients.append({
                'ingredient': ingredient,
                'amount': ingredient_data['amount']
            })

        return validated_ingredients

    def create(self, validated_data):
        ingredients = validated_data.pop(
            'ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        IngredientRecipe.objects.bulk_create([
            IngredientRecipe(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            )
            for item in ingredients
        ])
        return recipe


class RecipeShortLinkSerializer(serializers.Serializer):
    """Сериализатор для создания коротких ссылок."""
    short_link = serializers.CharField()

    def to_representation(self, instance):
        return {'short-link': instance.get('short_link')}


class ShoppingCartFavoriteSerializer(RecipeSerializer):

    class Meta(RecipeSerializer.Meta):
        model = Recipe
        fields = [
            'id',
            'name',
            'image',
            'cooking_time'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        return {
            'id': representation['id'],
            'name': representation['name'],
            'image': representation['image'],
            'cooking_time': representation['cooking_time']
        }
