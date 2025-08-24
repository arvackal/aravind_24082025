from django.core.management.base import BaseCommand
import csv
from storeapi.models import BussinessHours, Store

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

            BussinessHours.objects.all().delete()

            for row in read:
                try:
                    store = Store.objects.get(id = row['store_id'])
                                      
                    BussinessHours.objects.create(
                        store_id = store,
                        dayOfWeek = row['dayOfWeek'],
                        startTimeLocal = row['start_time_local'],
                        endTimeLocal = row['end_time_local']
                )
                except Store.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Skipping row, store_id {row['store_id']} not found."))
                    continue
           