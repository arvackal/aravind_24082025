from django.core.management.base import BaseCommand
import csv
from storeapi.models import Store

class Command(BaseCommand):
    help = "Import Store data from csv"

    def add_arguments(self, parser):
        parser.add_argument('csv_file', 
                            type = str,
                            help = "Path to csv file")
        
    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        with open(csv_file, newline = '', encoding = 'utf-8') as file:
            read = csv.DictReader(file)
            
            for row in read:
                Store.objects.create(
                    id = row['store_id'],
                    timezone = row['timezone_str']
                )