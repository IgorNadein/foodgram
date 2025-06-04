import os

import django
from django.core.management.base import BaseCommand
from django.db import models

from food.models import Ingredient


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram_backend.settings')
django.setup()


class Command(BaseCommand):
    help = 'Обновляет единицы измерения ингредиентов в базе данных'

    # Словарь замен (можно расширять)
    REPLACEMENTS = {
        'банка': 'г',
        'батон': 'г',
        'веточка': 'г',
        'капля': 'мл',
        'кусок': 'г',
        'ст. л.': 'г',
        'стакан': 'мл',
        'ч. л.': 'г',
        'щепотка': 'г',
        'горсть': 'г',
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Пропустить подтверждение изменений'
        )

    def handle(self, *args, **options):
        # Собираем статистику
        stats = {new: 0 for new in self.REPLACEMENTS.values()}
        total_changes = 0

        # Формируем условия для фильтрации
        update_conditions = models.Q()
        for old_unit in self.REPLACEMENTS:
            update_conditions |= models.Q(measurement_unit=old_unit)

        # Находим подходящие записи
        queryset = Ingredient.objects.filter(update_conditions)
        count_to_update = queryset.count()

        if count_to_update == 0:
            self.stdout.write(self.style.NOTICE('Нет записей для обновления'))
            return

        # Подтверждение действия
        if not options['force']:
            self.stdout.write(self.style.WARNING(
                f'Будет обновлено {count_to_update} записей. Замены:'
            ))
            for old, new in self.REPLACEMENTS.items():
                self.stdout.write(f'  {old} → {new}')

            confirm = input('Продолжить? [y/N] ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.NOTICE('Отмена операции'))
                return

        # Выполняем массовое обновление
        for old_unit, new_unit in self.REPLACEMENTS.items():
            updated = queryset.filter(
                measurement_unit=old_unit
            ).update(measurement_unit=new_unit)
            stats[new_unit] += updated
            total_changes += updated

        # Вывод результатов
        self.stdout.write(self.style.SUCCESS(
            f'Успешно обновлено {total_changes} записей:'
        ))
        for unit, count in stats.items():
            if count > 0:
                self.stdout.write(f'  {unit}: {count}')

        # Предупреждение о возможных дублях
        if total_changes != count_to_update:
            self.stdout.write(self.style.WARNING(
                'Некоторые записи не были обновлены. '
                'Возможно, изменились условия фильтрации во время выполнения.'
            ))
