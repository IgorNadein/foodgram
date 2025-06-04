import os

import django
from django.core.management.base import BaseCommand
from food.models import Ingredient

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram_backend.settings')
django.setup()


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Пропустить подтверждение удаления',
        )

    def handle(self, *args, **options):
        total = Ingredient.objects.count()

        if total == 0:
            self.stdout.write(self.style.NOTICE(
                'В базе нет ингредиентов для удаления'
            ))
            return

        if not options['force']:
            confirm = input(
                f'Вы точно хотите удалить ВСЕ ({total}) ингредиенты? [y/N] '
            )
            if confirm.lower() != 'y':
                self.stdout.write(self.style.NOTICE('Отмена операции'))
                return

        deleted, _ = Ingredient.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(f'Успешно удалено {deleted} ингредиентов')
        )
