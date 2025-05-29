from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Subscription, Tag, User)


@admin.register(User)
class ExtendedUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'get_full_name',
                    'email', 'avatar_preview', 'following_count',
                    'followers_count', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
         'fields': ('first_name', 'last_name', 'email', 'avatar')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined')
    ordering = ('id',)

    @admin.display(description='ФИО')
    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    @admin.display(description='Аватар')
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="" style="max-height: 50px; max-width: 50px;" />',
                obj.avatar.url
            )
        return _('No Avatar')

    @admin.display(description='Подписок')
    def following_count(self, obj):
        return Subscription.objects.filter(subscriber=obj).count()

    @admin.display(description='Подписчиков')
    def followers_count(self, obj):
        return Subscription.objects.filter(author=obj).count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'subscriber', 'author')
    list_filter = ('subscriber', 'author')
    search_fields = ('subscriber__username', 'author__username')


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    min_num = 1
    extra = 0
    fields = ('ingredient', 'amount')
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты рецепта'


class RecipeCountAdminMixin:
    """
    Mixin to add recipe count to admin list views.
    This is designed to be non-destructive.
    """

    @admin.display(
        description='Количество рецептов',
        ordering='recipe_count'
    )
    def recipe_count(self, obj):
        return obj.recipes.count()

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(recipe_count=Count('recipes'))


@admin.register(Tag)
class TagAdmin(RecipeCountAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'recipe_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    list_display_links = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(RecipeCountAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipe_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    list_display_links = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'cooking_time', 'author',
                    'get_likes', 'ingredients_list', 'image_preview')
    search_fields = ('name', 'text', 'author__username')
    list_filter = ('tags', 'author')
    filter_horizontal = ('tags',)
    readonly_fields = ('image_preview',)
    inlines = (IngredientRecipeInline,)
    fieldsets = (
        (None, {
            'fields': ('name', 'author', 'tags')
        }),
        ('Содержимое', {
            'fields': ('image', 'image_preview', 'text')
        }),
        ('Детали', {
            'fields': ('cooking_time',)
        }),
    )

    @admin.display(description='Изображение')
    def image_preview(self, recipe):
        if recipe.image:
            return format_html(
                '<img src="{}" style="max-height: 200px;" />',
                recipe.image.url
            )
        return 'Нет изображения'

    @admin.display(description='Количество лайков')
    def get_likes(self, recipe):
        return Favorite.objects.filter(recipe=recipe).count()

    @admin.display(description='Ингредиенты')
    def ingredients_list(self, recipe):
        ingredients = ', '.join(
            [ingredient.name for ingredient in recipe.ingredients.all()])
        return ingredients


class FavoriteShoppingCartAdminMixin:
    """Mixin for models with user and recipe."""
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)


@admin.register(Favorite)
class FavoriteAdmin(FavoriteShoppingCartAdminMixin, admin.ModelAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(FavoriteShoppingCartAdminMixin, admin.ModelAdmin):
    pass


admin.site.empty_value_display = 'Не задано'
