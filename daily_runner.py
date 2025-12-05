import schedule
import time
from datetime import datetime
from app import generate_daily_report_smtp

def job():
    print(f"[{datetime.now()}] Running daily AWS report...")
    generate_daily_report_smtp("your_email@gmail.com")   # <-- change this

# Run daily at 8:00 AM
schedule.every().day.at("08:00").do(job)

print("Daily scheduler started. Waiting for next trigger...")

while True:
    schedule.run_pending()
    time.sleep(60)
