from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=32,
        unique=True,
        verbose_name='Уникальное название',
    )
    slug = models.SlugField(
        max_length=32,
        unique=True,
        verbose_name='Уникальный слаг',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)
        default_related_name = 'tags'

    def __str__(self):
        return f'{self._meta.verbose_name}: {self.name}'


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения',
    )


class Recipe(models.Model):
    """Модель рецептров."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор публикации (пользователь)',
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Рецепт',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Картинка',
    )
    text = models.TextField(
        verbose_name='Текстовое описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиенты',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег',
        related_name='recipes'
    )
    cooking_time = models.IntegerField(
        validators=[
            MinValueValidator(
                1, 'Нужно указать время приготовления!'
            )
        ],
        verbose_name='Время приготовления в минутах'
    )


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    amount = models.IntegerField(
        default=1,
        verbose_name='Количество ингредиентов',
        validators=[
            MinValueValidator(
                1, 'Количество ингредиентов должно быть не менее 1!'
            )
        ]
    )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='in_shopping_cart'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
