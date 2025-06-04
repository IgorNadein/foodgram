import os

import django
from django.core.management.base import BaseCommand
from django.db import models

from food.models import Ingredient


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()


class Command(BaseCommand):
    def handle(self, *args, **options):
        remove_duplicate_ingredients()


def remove_duplicate_ingredients():
    duplicates = Ingredient.objects.values(
        'name', 'measurement_unit'
    ).annotate(
        count_id=models.Count('id')
    ).filter(count_id__gt=1)

    for duplicate in duplicates:
        ingredients = Ingredient.objects.filter(
            name=duplicate['name'],
            measurement_unit=duplicate['measurement_unit']
        ).order_by('id')

        first_ingredient = ingredients.first()
        ingredients.exclude(id=first_ingredient.id).delete()

    print("Дубликаты ингредиентов удалены.")
