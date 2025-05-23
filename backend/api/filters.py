import django_filters
from food.models import Recipe, Tag, Favorite, ShoppingCart, Ingredient
from django.db.models import Exists, OuterRef


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = django_filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart')
    author = django_filters.NumberFilter(
        field_name='author__id')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited',
                  'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset
        if value:
            value = bool(int(value))
            return queryset.annotate(
                is_favorited_flag=Exists(
                    Favorite.objects.filter(
                        user=user,
                        recipe=OuterRef('pk')
                    )
                )
            ).filter(is_favorited_flag=value)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset
        if value:
            value = bool(int(value))
            return queryset.annotate(
                is_in_shopping_cart_flag=Exists(
                    ShoppingCart.objects.filter(
                        user=user,
                        recipe=OuterRef('pk')
                    )
                )
            ).filter(is_in_shopping_cart_flag=value)
        return queryset





class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
