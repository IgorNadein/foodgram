import json

from django.core.management.base import BaseCommand
from food.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        load_from_json(Ingredient, 'data/ingredients.json')


def load_from_json(model, file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            object_to_create = [model(**item) for item in data]
            model.objects.bulk_create(object_to_create)
            print(
                f'Успешно загружено {len(object_to_create)} объекта.'
            )

    except Exception:
        print(f'Произошла ошибка при обработке файла {file_path}.')
