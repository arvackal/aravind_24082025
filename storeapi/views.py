import threading
import csv
from datetime import timedelta
from django.utils import timezone
from django.core.files import File
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Store, StoreStatus, Report, BussinessHours
import pytz

def is_within_business_hours(store_id, local_time):
    '''
        Computes total uptime and downtime for a store between start_ts and end_ts,
        considering store business hours.

        Args:
            store_id (str): ID of the store.
            start_ts (datetime): Start timestamp in UTC.
            end_ts (datetime): End timestamp in UTC.

    '''
    try:
        bh = BussinessHours.objects.filter(
            store_id=store_id, day_of_week=local_time.weekday()
        ).first()
        if not bh:
            return True  # open 24x7 if missing
        return bh.start_time <= local_time.time() <= bh.end_time
    except:
        return True

# Helper function to calculate uptime/downtime
def calculate_uptime_downtime(store_id: str, start_ts, end_ts):
    '''
        Computes total uptime and downtime for a store between start_ts and end_ts,
        considering store business hours.

        Args:
        store_id (str): ID of the store.
        start_ts (datetime): Start timestamp in UTC.
        end_ts (datetime): End timestamp in UTC.

    '''
    try:
        store = Store.objects.get(id=store_id)
    except Store.DoesNotExist:
        return 0, (end_ts - start_ts).total_seconds() / 60

    tz = pytz.timezone(store.timezone)

    # Get all StoreStatus objects in the interval
    statuses = StoreStatus.objects.filter(
        store_id=store,
        timestamp_utc__gte=start_ts,
        timestamp_utc__lte=end_ts
    ).order_by('timestamp_utc')

    total_uptime = 0
    total_downtime = 0

    if not statuses.exists():
        # No data, assume full downtime
        return 0, (end_ts - start_ts).total_seconds() / 60

    # Convert to local time
    local_statuses = [(s.timestamp_utc.astimezone(tz), s.status) for s in statuses]

    for i in range(len(local_statuses)):
        current_ts, status = local_statuses[i]
        next_ts = local_statuses[i + 1][0] if i + 1 < len(local_statuses) else end_ts.astimezone(tz)

        interval_start = max(current_ts, start_ts.astimezone(tz))
        interval_end = min(next_ts, end_ts.astimezone(tz))

        # Skip intervals outside business hours
        if not is_within_business_hours(store_id, interval_start):
            continue

        minutes = (interval_end - interval_start).total_seconds() / 60
        if status == 'active':
            total_uptime += minutes
        else:
            total_downtime += minutes

    return round(total_uptime, 2), round(total_downtime, 2)

# Function to generate report
def generate_report(report_id):
    report = Report.objects.get(id=report_id)
    max_ts_obj = StoreStatus.objects.order_by('-timestamp_utc').first()
    if not max_ts_obj:
        report.status = "Complete"
        report.save()
        return

    max_ts = max_ts_obj.timestamp_utc
    start_hour = max_ts - timedelta(hours=1)
    start_day = max_ts - timedelta(days=1)
    start_week = max_ts - timedelta(days=7)

    file_path = f"media/reports/report_{report.id}.csv"
    with open(file_path, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "store_id",
            "uptime_last_hour(mins)",
            "downtime_last_hour(mins)",
            "uptime_last_day(hrs)",
            "downtime_last_day(hrs)",
            "uptime_last_week(hrs)",
            "downtime_last_week(hrs)"
        ])
        stores = Store.objects.all()

        i = 0

        for store in stores:
            u_h, d_h = calculate_uptime_downtime(store.id, start_hour, max_ts)
            u_d, d_d = calculate_uptime_downtime(store.id, start_day, max_ts)
            u_w, d_w = calculate_uptime_downtime(store.id, start_week, max_ts)

            # Convert day/week minutes to hours
            writer.writerow([
                store.id,
                round(u_h, 2),
                round(d_h, 2),
                round(u_d / 60, 2),
                round(d_d / 60, 2),
                round(u_w / 60, 2),
                round(d_w / 60, 2)
            ])
            i+=1
            print(f"{i}/{len(stores)}")

    with open(file_path, 'rb') as f:
        report.csv_file.save(f"report_{report.id}.csv", File(f))
    report.status = "Complete"
    report.save()

# API to trigger report generation
class TriggerReportAPI(APIView):
    def post(self, request):
        report = Report.objects.create(status="Running")
        thread = threading.Thread(target=generate_report, args=(report.id,))
        thread.start()
        return Response({
            "report_id": report.id,
            "status": report.status,
            "message": "Report generation started"
        }, status=status.HTTP_202_ACCEPTED)

# API to get report status and CSV
class GetReportAPIView(APIView):
    def get(self, request, report_id):
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "report_id": report.id,
            "status": report.status,
            "created_at": report.created_at,
            "csv_file": report.csv_file.url if report.csv_file else None
        })