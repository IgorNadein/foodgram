from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Exists, OuterRef

from .models import Subscription


class BaseBooleanFilter(SimpleListFilter):
    """Базовый класс для фильтров с вариантами Да/Нет"""
    LOOKUPS = (('yes', 'Да'), ('no', 'Нет'))

    def lookups(self, request, model_admin):
        return self.LOOKUPS


class BaseSubscriptionFilter(BaseBooleanFilter):
    """Базовый класс для фильтров подписок"""

    def queryset(self, request, queryset):
        if self.value() not in ('yes', 'no'):
            return queryset

        subquery = Subscription.objects.filter(**{
            self.subscription_field: OuterRef('pk')
        })
        annotation = {self.annotation_name: Exists(subquery)}
        return queryset.annotate(**annotation).filter(**{
            f'{self.annotation_name}__exact': self.value() == 'yes'
        })


class HasSubscriptionsFilter(BaseSubscriptionFilter):
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'
    subscription_field = 'subscriber'
    annotation_name = 'has_subs'


class HasFollowersFilter(BaseSubscriptionFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_followers'
    subscription_field = 'author'
    annotation_name = 'has_fol'


class HasRecipesFilter(BaseBooleanFilter):
    title = 'Наличие в рецептах'
    parameter_name = 'has_recipes'

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipe_count__gt=0)
        if self.value() == 'no':
            return queryset.filter(recipe_count=0)
        return queryset


class CustomTagListFilter(admin.RelatedFieldListFilter):
    """Кастомный фильтр для тегов"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = 'Теги'

    def choices(self, changelist):
        for choice in super().choices(changelist):
            if choice['query_string']:
                choice['display'] = choice['display'].replace('Тег: ', '')
                yield choice
