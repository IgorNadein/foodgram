from django.core.management.base import BaseCommand
import os
import json
from food.models import Tag
from django.conf import settings

class Command(BaseCommand):
    def handle(self, *args, **options):
        load_from_json()

def load_from_json():
    try:
        # Изменили путь к файлу
        with open(os.path.join(settings.BASE_DIR, '..', 'data', 'tags.json'), 'r', encoding='utf-8') as file:
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


