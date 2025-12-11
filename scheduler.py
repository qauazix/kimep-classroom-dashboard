"""
scheduler.py
-------------
This script automatically fetches updated data from the Google Sheet
on a fixed schedule and writes it to the local CSV file
(latest_schedule.csv). This enables automated data orchestration
for the Streamlit dashboard.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from fetch_from_gsheet import fetch_sheet


def scheduled_job():
    """
    This function is executed at each scheduled interval.
    It calls the Google Sheet fetch function and prints logs.
    """
    print("\n----------------------------------------------------")
    print("Scheduler Triggered at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        fetch_sheet()  # Fetches data from Google Sheets and saves CSV
        print("Fetch successful.")
    except Exception as e:
        print("Error during fetch:", str(e))
    
    print("----------------------------------------------------\n")


if __name__ == "__main__":

    # Create scheduler instance
    scheduler = BlockingScheduler()

    # Schedule the job: runs every 6 hours (you can change the interval)
    scheduler.add_job(scheduled_job, "interval", hours=6)

    print("====================================================")
    print(" AUTONOMOUS DATA SCHEDULER STARTED")
    print(" Updates occur every 6 hours")
    print(" Press CTRL+C to stop")
    print("====================================================\n")

    # Start the scheduler loop
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Scheduler stopped manually.")
