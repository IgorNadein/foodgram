from django.contrib import admin
from django.contrib.admin import SimpleListFilter


class HasRecipesFilter(SimpleListFilter):
    title = 'Наличие в рецептах'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Есть в рецептах'),
            ('no', 'Нет в рецептах'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipe_count__gt=0)
        if self.value() == 'no':
            return queryset.filter(recipe_count=0)
        return queryset


class CustomTagListFilter(admin.RelatedFieldListFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = 'Теги'

    def choices(self, changelist):
        for choice in super().choices(changelist):
            if choice['query_string']:
                choice['display'] = choice['display'].replace('Тег: ', '')
                yield choice
