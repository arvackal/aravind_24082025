from django.core.management.base import BaseCommand
from datetime import datetime
import csv
from storeapi.models import Store, StoreStatus
import pytz

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
            StoreStatus.objects.all().delete()

            objs = []
            batch_size = 5000
            
            for row in read:
                try:
                    store = Store.objects.get(id = row['store_id'])
                    date_str  = row['timestamp_utc']
                    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f %Z")

                    objs.append(StoreStatus(
                        store_id = store,
                        status = row['status'],
                        timestamp_utc = dt.replace(tzinfo=pytz.UTC) 
                        ))
                    if len(objs) >= batch_size:
                        StoreStatus.objects.bulk_create(objs)
                        objs = []
                except Store.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Skipping row, store_id {row['store_id']} not found."))
                    continue

            if objs:
                        StoreStatus.objects.bulk_create(objs)
