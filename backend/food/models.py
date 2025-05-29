from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import (EmailValidator, MaxLengthValidator,
                                    MinValueValidator, RegexValidator)
from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import (COOKING_TIME_MIN_VALUE, EMAIL_MAX_LENGTH,
                        FIRST_NAME_MAX_LENGTH, INGREDIENT_AMOUNT_MIN_VALUE,
                        LAST_NAME_MAX_LENGTH, USERNAME_MAX_LENGTH)
from .validators import validate_username


class User(AbstractUser):

    username_validator = UnicodeUsernameValidator()
    name_validator = RegexValidator(
        regex=r'^[^\d\W_]+$',
        message=_('Имя/Фамилия должны содержать только буквы')
    )

    email = models.EmailField(
        _('email address'),
        unique=True,
        blank=False,
        null=False,
        max_length=EMAIL_MAX_LENGTH,
        validators=[
            MaxLengthValidator(EMAIL_MAX_LENGTH),
            EmailValidator()
        ],
        error_messages={
            'unique': _('Пользователь с таким email уже существует.'),
            'blank': _('Email обязателен для заполнения.'),
            'null': _('Email не может быть null.')
        }
    )

    username = models.CharField(
        _('username'),
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        help_text=_(
            f'''
            Обязательное поле. Не более {USERNAME_MAX_LENGTH} символов.
            Разрешены буквы, цифры и @/./+/-/_
            '''
        ),
        validators=[
            validate_username,
            username_validator
        ],
        error_messages={
            'unique': _("Пользователь с таким именем уже существует."),
        }
    )

    first_name = models.CharField(
        _('first name'),
        max_length=FIRST_NAME_MAX_LENGTH,
        blank=False,
        validators=[name_validator]
    )

    last_name = models.CharField(
        _('last name'),
        max_length=LAST_NAME_MAX_LENGTH,
        blank=False,
        validators=[name_validator]
    )

    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True,
        verbose_name='Аватарка пользователя',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписок."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Автор'
    )
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписчик'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'author'],
                name='unique_subscriber_author'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'


class Tag(models.Model):
    name = models.CharField(
        max_length=32,
        unique=True,
        verbose_name='Название',
    )
    slug = models.SlugField(
        max_length=32,
        unique=True,
        verbose_name='Слаг',
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

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'


class Recipe(models.Model):
    """Модель рецептров."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации (пользователь)',
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Картинка',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег',
    )
    cooking_time = models.IntegerField(
        validators=[
            MinValueValidator(
                COOKING_TIME_MIN_VALUE
            )
        ],
        verbose_name='Время приготовления в минутах'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    amount = models.IntegerField(
        default=1,
        verbose_name='Количество ингредиентов',
        validators=[
            MinValueValidator(
                INGREDIENT_AMOUNT_MIN_VALUE
            )
        ]
    )

    class Meta:
        verbose_name = 'Рецептурный продукт'
        verbose_name_plural = 'Рецептурные продукты'
        default_related_name = 'recipe_ingredients'


class BaseFavoriteShoppingCart(models.Model):
    """
    Base class for Favorite and ShoppingCart models, handling common fields
    and constraints.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(class)s_unique'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Favorite(BaseFavoriteShoppingCart):
    class Meta(BaseFavoriteShoppingCart.Meta):
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(BaseFavoriteShoppingCart):
    class Meta(BaseFavoriteShoppingCart.Meta):
        default_related_name = 'shopping_cart_recipes'
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
