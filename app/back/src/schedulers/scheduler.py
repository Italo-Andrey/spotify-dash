from apscheduler.schedulers.background import BackgroundScheduler
from app.back.src.schedulers.scheduler_jobs import update_user_data

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_user_data, trigger='interval', minutes=15)
    scheduler.start()
    return scheduler
