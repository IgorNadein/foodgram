from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (
    Favorite, Ingredient, IngredientRecipe, Recipe,
    ShoppingCart, Subscription, Tag, User
)


@admin.register(User)
class ExtendedUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'get_full_name',
                    'email', 'avatar_preview', 'following_count',
                    'followers_count', 'recipe_count', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined')
    ordering = ('id',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipe_count=Count('recipes', distinct=True)
        )

    @admin.display(description='Рецептов', ordering='recipe_count')
    def recipe_count(self, obj):
        return obj.recipe_count

    @admin.display(description='ФИО')
    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    @admin.display(description='Аватар')
    def avatar_preview(self, obj):
        if obj.avatar:
            return mark_safe(
                f'<img src="{obj.avatar.url}" '
                'style="max-height: 50px; max-width: 50px;" />'
            )
        return 'No Avatar'

    @admin.display(description='Подписок')
    def following_count(self, obj):
        return obj.authors.count()

    @admin.display(description='Подписчиков')
    def followers_count(self, obj):
        return obj.followers.count()


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
    @admin.display(
        description='Рецепты',
        ordering='recipe_count'
    )
    def recipe_count(self, obj):
        return obj.recipes.count()

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipe_count=Count('recipes')
        )


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
                    'get_likes', 'ingredients_list', 'image_preview',
                    'tags_list')
    search_fields = ('name', 'text', 'author__username')
    list_filter = ('tags', 'author')
    filter_horizontal = ('tags',)
    readonly_fields = ('image_preview',)
    inlines = (IngredientRecipeInline,)
    fieldsets = (
        (None, {'fields': ('name', 'author', 'tags')}),
        ('Содержимое', {'fields': ('image', 'image_preview', 'text')}),
        ('Детали', {'fields': ('cooking_time',)}),
    )

    @admin.display(description='Изображение')
    def image_preview(self, recipe):
        if recipe.image:
            return mark_safe(
                f'<img src="{recipe.image.url}" '
                'style="max-height: 200px;" />'
            )
        return 'Нет изображения'

    @admin.display(description='Количество лайков')
    def get_likes(self, recipe):
        return recipe.favorites.count()

    @admin.display(description='Ингредиенты')
    def ingredients_list(self, recipe):
        return '\n'.join(
            f'{ingredient.name} - {ingredient.amount}'
            f'{ingredient.measurement_unit}'
            for ingredient in recipe.ingredients.through.objects.filter(
                recipe=recipe
            ).select_related('ingredient')
        )

    @admin.display(description='Теги')
    def tags_list(self, obj):
        return ', '.join(tag.name for tag in obj.tags.all())


class FavoriteShoppingCartAdminMixin:
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
