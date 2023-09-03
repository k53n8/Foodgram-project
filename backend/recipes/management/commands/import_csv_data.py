import csv
import os

from django.conf import settings
from django.core.management import BaseCommand

from recipes.models import Ingredient

file_path = os.path.join(settings.BASE_DIR, 'recipes', 'data', 'ingridietns.csv')


class Command(BaseCommand):
    help = "Loads data from csv"

    def handle(self, *args, **options):

        with open(file_path, 'r', encoding='utf-8') as csvfile:
            dict_reader = csv.DictReader(
                csvfile, fieldnames=['name', 'measurement_unit']
            )

            for row in dict_reader:
                Ingredient.objects.get_or_create(
                    name=row['name'],
                    measurement_unit=row['measurement_unit'])

        self.stdout.write(self.style.SUCCESS(
            'Данные из CSV успешно импортированы!'))
