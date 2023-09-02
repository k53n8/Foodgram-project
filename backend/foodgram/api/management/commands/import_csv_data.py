import csv

from django.core.management import BaseCommand

from foodgram.models import Ingredient

CSV_PATH = '/data/'


class Command(BaseCommand):
    help = "Loads data from csv"

    def handle(self, *args, **options):

        with open('./data/ingredients.csv', 'r', encoding='utf-8') as csvfile:
            dict_reader = csv.DictReader(
                csvfile, fieldnames=['name', 'measurement_unit']
            )

            for row in dict_reader:
                Ingredient.objects.get_or_create(
                    name=row['name'],
                    measurement_unit=row['measurement_unit'])

        self.stdout.write(self.style.SUCCESS(
            'Данные из CSV успешно импортированы!'))
