import base64
from collections import Counter

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from food.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                         ShoppingCart, Subscription, Tag)
from rest_framework import serializers

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=True)

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + (
            'is_subscribed',
            'avatar',
            'last_name',
            'first_name'
        )

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            subscriber=request.user,
            author=author
        ).exists()


class UserRegistrationSerializer(UserCreateSerializer):
    """Регистрация."""
    class Meta(UserCreateSerializer.Meta):
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscribedUserSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения subscriptions."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            subscriber=request.user,
            author=obj
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                recipes_limit = None
        recipes = obj.recipes.all()[:recipes_limit]
        return RecipeShortSerializer(
            recipes, many=True, context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionSerializer(serializers.Serializer):
    """Сериализатор для добавления/удаления subscriptions."""
    recipes_limit = serializers.IntegerField(
        required=False,
        min_value=0,
        default=None,
        help_text='Лимит рецептов в ответе'
    )

    def validate(self, data):
        request = self.context['request']
        author = self.context['author']
        user = request.user

        if request.method == 'POST':
            if user == author:
                raise serializers.ValidationError("Нельзя подписаться на себя")
            if Subscription.objects.filter(
                subscriber=user, author=author
            ).exists():
                raise serializers.ValidationError(
                    f"Вы уже подписаны на {author.username}")
        else:
            if not Subscription.objects.filter(
                subscriber=user, author=author
            ).exists():
                raise serializers.ValidationError(
                    {"error": "Вы не подписаны на этого пользователя."}
                )
        return data

    def create(self, validated_data):
        author = self.context['author']
        Subscription.objects.create(
            subscriber=self.context['request'].user, author=author
        )
        return author

    def destroy(self):
        Subscription.objects.get(
            subscriber=self.context['request'].user,
            author=self.context['author']
        ).delete()

    def to_representation(self, instance):
        request = self.context['request']
        recipes_limit = self.context['recipes_limit']
        recipes = instance.recipes.all()
        if recipes_limit:
            recipes_limit = int(recipes_limit)
            recipes = recipes[:recipes_limit]

        return {
            "id": instance.id,
            "username": instance.username,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "email": instance.email,
            "is_subscribed": True,
            "recipes": RecipeShortSerializer(
                recipes,
                many=True,
                context={'request': request}
            ).data,
            "recipes_count": instance.recipes.count(),
            "avatar": request.build_absolute_uri(instance.avatar.url) if
            instance.avatar else None
        }


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


class ReadIngredientRecipeSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id', read_only=True
    )
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe (для читающих запросов)."""
    ingredients = ReadIngredientRecipeSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
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

    def get_is_favorited(self, recipe):
        return self._check_user_relation(Favorite, recipe)

    def get_is_in_shopping_cart(self, recipe):
        return self._check_user_relation(ShoppingCart, recipe)

    def _check_user_relation(self, model, recipe):
        request = self.context.get('request')
        return bool(
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

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class TagIngredientWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating IngredientRecipe."""
    # id = serializers.PrimaryKeyRelatedField(
    #     read_only=True
    # )

    class Meta:
        model = Tag
        fields = ('id',)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи рецепта."""
    image = Base64ImageField(required=True)
    ingredients = RecipeIngredientWriteSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
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
        if len(data) != len(set(data)):
            raise serializers.ValidationError(
                f'{field_name} не должны повторяться: {dict(Counter(data))}'
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
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for ingredient_data in ingredients_data:
            ingredient = ingredient_data['id']
            amount = ingredient_data['amount']
            IngredientRecipe.objects.create(
                recipe=recipe, ingredient=ingredient, amount=amount)

        return recipe

    def update(self, recipe, validated_data):
        # Обработка ингредиентов
        ingredients_data = self.validate_ingredients(
            validated_data.pop('ingredients', []))
        print(ingredients_data)
        if ingredients_data:
            IngredientRecipe.objects.filter(recipe=recipe).delete()
            IngredientRecipe.objects.bulk_create([
                IngredientRecipe(
                    recipe=recipe,
                    ingredient=item['id'],
                    amount=item['amount']
                )
                for item in ingredients_data
            ])

        # Обработка тегов
        tags_data = self.validate_tags(validated_data.pop('tags', []))
        if tags_data:
            recipe.tags.set(tags_data)

        # Обновление остальных полей
        for attr, value in validated_data.items():
            setattr(recipe, attr, value)
        recipe.save()

        return recipe

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context=self.context).data


class RecipePreviewSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    image = Base64ImageField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
