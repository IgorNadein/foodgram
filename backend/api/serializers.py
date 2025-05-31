import base64
from collections import Counter

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from food.constants import COOKING_TIME_MIN_VALUE, INGREDIENT_AMOUNT_MIN_VALUE
from food.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                         ShoppingCart, Subscription, Tag)


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class BaseUserSerializerMixin(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta(DjoserUserSerializer.Meta):
        fields = (
            *DjoserUserSerializer.Meta.fields,
            'is_subscribed',
            'avatar'
        )
        read_only_fields = fields

    def get_is_subscribed(self, author):
        return (
            (request := self.context.get('request'))
            and request.user.is_authenticated
            and Subscription.objects.filter(
                subscriber=request.user,
                author=author
            ).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscribedUserSerializer(BaseUserSerializerMixin):
    """Сериализатор для subscriptions."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count')

    class Meta(BaseUserSerializerMixin.Meta):
        fields = (
            *BaseUserSerializerMixin.Meta.fields,
            'recipes',
            'recipes_count'
        )
        read_only_fields = fields

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        try:
            recipes_limit = int(recipes_limit) if recipes_limit else 10**10
        except ValueError:
            recipes_limit = 10**10

        recipes = obj.recipes.all()[:recipes_limit]
        return RecipeShortSerializer(
            recipes, many=True, context={'request': request}
        ).data


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


class ReadIngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='ingredient.id',
        read_only=True
    )
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe (для читающих запросов)."""
    ingredients = ReadIngredientRecipeSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = BaseUserSerializerMixin(read_only=True)

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

    def get_is_favorited(self, recipe):
        return self._check_user_relation(Favorite, recipe)

    def get_is_in_shopping_cart(self, recipe):
        return self._check_user_relation(ShoppingCart, recipe)

    def _check_user_relation(self, model, recipe):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and model.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists()
        )


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating IngredientRecipe."""
    id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        required=True,
        min_value=INGREDIENT_AMOUNT_MIN_VALUE
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи рецепта."""
    image = Base64ImageField(required=True)
    ingredients = RecipeIngredientWriteSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    cooking_time = serializers.IntegerField(
        required=True,
        min_value=COOKING_TIME_MIN_VALUE
    )

    class Meta:
        model = Recipe
        fields = [
            'cooking_time',
            'image',
            'ingredients',
            'name',
            'tags',
            'text',
        ]

    def validate_list_unique(self, data, field_name):
        """Проверяет, что список не пуст и содержит уникальные элементы."""
        if not data:
            raise serializers.ValidationError(
                f'Список "{field_name}" не может быть пустым.'
            )
        element_stats = Counter(data)
        duplicates = {element: count for element,
                      count in element_stats.items() if count > 1}

        if duplicates:
            raise serializers.ValidationError(
                f'{field_name} не должны повторяться: {duplicates}'
            )
        return data

    def validate_tags(self, tags):
        return self.validate_list_unique(tags, 'Tags')

    def validate_ingredients(self, ingredients):
        ingredient_ids = [ingredient_data['id']
                          for ingredient_data in ingredients]
        self.validate_list_unique(ingredient_ids, 'Ingredients')
        return ingredients

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.write_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, recipe, validated_data):
        IngredientRecipe.objects.filter(recipe=recipe).delete()
        ingredients_data = self.validate_ingredients(
            validated_data.pop('ingredients', [])
        )
        # if ingredients_data:
        self.write_ingredients(recipe, ingredients_data)
        tags_data = self.validate_tags(validated_data.pop('tags', []))
        # if tags_data:
        recipe.tags.set(tags_data)
        return super().update(recipe, validated_data)

    def write_ingredients(self, recipe, ingredients_data):
        IngredientRecipe.objects.bulk_create(
            IngredientRecipe(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            )
            for item in ingredients_data
        )

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context=self.context).data


class RecipePreviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        read_only_fields = fields
