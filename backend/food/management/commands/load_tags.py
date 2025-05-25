import json

from django.core.management.base import BaseCommand
from food.models import Tag


class Command(BaseCommand):
    def handle(self, *args, **options):
        load_from_json()


def load_from_json():
    try:
        with open('data/tags.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            for item in data:
                Tag.objects.create(
                    name=item['name'],
                    slug=item['slug']
                )
    except FileNotFoundError:
        print("Файл ingredients.json не найден")
    except json.JSONDecodeError:
        print("Ошибка при чтении JSON файла")
