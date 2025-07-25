from django.core.management.base import BaseCommand

from food.models import Tag
from .data_loader import load_from_json


class Command(BaseCommand):
    def handle(self, *args, **options):
        load_from_json(Tag, 'data/tags.json')
