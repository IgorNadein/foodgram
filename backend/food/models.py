from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model


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
        verbose_name='Автор публикации (пользователь',
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название',
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
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег'
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
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.IntegerField(
        max_digits=6,
        decimal_places=2,
        default=1,
        verbose_name='Количество ингредиентов',
        validators=[
            MinValueValidator(
                1, 'Количество ингредиентов должно быть не менее 1!'
            )
        ]
    )
