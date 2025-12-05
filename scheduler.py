import time
import schedule
from app import start_instances_by_tag, stop_instances_by_tag

TAG_KEY = "Schedule"
TAG_VALUE = "Auto"

def morning_start():
    print("⏰ Starting scheduled EC2 instances...")
    start_instances_by_tag(TAG_KEY, TAG_VALUE)

def night_stop():
    print("🌙 Stopping scheduled EC2 instances...")
    stop_instances_by_tag(TAG_KEY, TAG_VALUE)

def main():
    # Run at 9 AM every day
    schedule.every().day.at("09:00").do(morning_start)

    # Run at 7 PM every day
    schedule.every().day.at("19:00").do(night_stop)

    print("Scheduler running... Press CTRL+C to exit")

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
