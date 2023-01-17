import logging
import os.path
from csv import DictReader

from django.core.management import BaseCommand

from recipes.models import Ingredient

DATA_DIR = 'static/data/'
DATA_PATCH = {
    'ingredients': os.path.join(DATA_DIR, 'ingredients.csv'),
}

logging.getLogger().setLevel(logging.INFO)


class Command(BaseCommand):
    """ Команда для загрузки данных в БД"""

    def handle(self, *args, **options):
        Ingredient.objects.bulk_create(
            [Ingredient(id=row['id'], name=row['name'],
                        measurement_unit=row['measurement_unit'])
             for row in DictReader(
                open(DATA_PATCH['ingredients'], encoding='utf-8'))
             ]
        )

        logging.info('База Ингредиентов загружена')