from apscheduler.schedulers.background import BackgroundScheduler
from app.back.src.schedulers.scheduler_jobs import refresh_user_tokens, update_tracks_data

def start_scheduler(app):
    scheduler = BackgroundScheduler()

    # 🔑 Atualiza tokens a cada 50 minutos
    scheduler.add_job(refresh_user_tokens, args=[app], trigger='interval', minutes=50, id="refresh_tokens_job")

    # 🎵 Atualiza músicas a cada 15 minutos
    scheduler.add_job(update_tracks_data, args=[app], trigger='interval', minutes=60, id="update_tracks_job")

    scheduler.start()
    return scheduler
