# import csv
import json

from django.core.management.base import BaseCommand

from food.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        load_from_json()
        # load_from_csv()

def load_from_json():
    try:
        with open('static/data/ingredients.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            for item in data:
                Ingredient.objects.create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
    except FileNotFoundError:
        print("Файл ingredients.json не найден")
    except json.JSONDecodeError:
        print("Ошибка при чтении JSON файла")

# def load_from_csv():
#     try:
#         with open('static/data/ingredients.csv', 'r', encoding='utf-8') as file:
#             reader = csv.DictReader(file)
#             for row in reader:
#                 Ingredient.objects.create(
#                     name=row['name'],
#                     measurement_unit=row['measurement_unit']
#                 )
#     except FileNotFoundError:
#         print("Файл ingredients.csv не найден")
#     except csv.Error:
#         print("Ошибка при чтении CSV файла")
