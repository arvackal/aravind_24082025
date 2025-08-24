from django.db import models

# Create your models here.
class Store(models.Model):
    id = models.CharField(max_length = 200, primary_key = True)
    timezone = models.CharField(max_length = 60, default="America/Chicago")

    def __str__(self):
        return self.id

class BussinessHours(models.Model):
    store_id = models.ForeignKey(
                Store,
                on_delete = models.CASCADE
                )
    dayOfWeek = models.IntegerField()
    startTimeLocal = models.TimeField()
    endTimeLocal = models.TimeField()

class StoreStatus(models.Model):
    store_id = models.ForeignKey(Store, on_delete = models.CASCADE)
    timestamp_utc = models.DateTimeField()
    status = models.CharField(max_length = 10, choices=[('active', 'Active'),('inactive', 'Inactive')])

class Report(models.Model):
    status = models.CharField(max_length=50, 
                              choices= [
                                  ("Running", "Running"),
                                  ("Complete", "Complete")
                              ], default= "Running")
    created_at = models.DateTimeField(auto_now_add= True)
    csv_file = models.FileField(upload_to="reports/", null = True, blank = True)


