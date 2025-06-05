import json

from django.core.management.base import BaseCommand
from django.db import transaction

from food.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из JSON файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к JSON файлу с ингредиентами'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ingredients_data = json.load(f)
        except FileNotFoundError:
            self.stderr.write(f"Файл {file_path} не найден")
            return
        except json.JSONDecodeError:
            self.stderr.write("Ошибка декодирования JSON")
            return

        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            for item in ingredients_data:
                try:
                    # Пытаемся найти или создать ингредиент
                    obj, created_flag = Ingredient.objects.update_or_create(
                        name=item['name'],
                        defaults={
                            'measurement_unit': item['measurement_unit']
                        }
                    )
                    if created_flag:
                        created += 1
                    else:
                        updated += 1
                except KeyError as e:
                    self.stderr.write(f"Ошибка в структуре данных: {e}")
                    skipped += 1
                except Exception as e:
                    self.stderr.write(f"Ошибка при обработке {item}: {e}")
                    skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Загрузка завершена!\n"
                f"Создано: {created}\n"
                f"Обновлено: {updated}\n"
                f"Пропущено: {skipped}"
            )
        )
