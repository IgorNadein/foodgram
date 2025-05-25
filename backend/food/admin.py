from django.contrib import admin
from django.utils.html import format_html

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag)


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    min_num = 1
    extra = 0
    fields = ('ingredient', 'amount')
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты рецепта'


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    list_display_links = ('name',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_display_links = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientRecipeInline,)
    list_display = ('name', 'author', 'cooking_time',
                    'favorite_count', 'image_preview')
    search_fields = ('name', 'text', 'author__username')
    list_filter = ('tags', 'author')
    filter_horizontal = ('tags',)
    readonly_fields = ('short_link', 'image_preview')
    fieldsets = (
        (None, {
            'fields': ('name', 'author', 'tags')
        }),
        ('Содержимое', {
            'fields': ('image', 'image_preview', 'text')
        }),
        ('Детали', {
            'fields': ('cooking_time', 'short_link')
        }),
    )

    @admin.display(description='Изображение')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 200px;"/>', obj.image.url
            )
        return "Нет изображения"

    @admin.display(description='В избранном')
    def favorite_count(self, obj):
        return obj.favorited_by.count()


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(IngredientRecipe)

admin.site.empty_value_display = 'Не задано'
