#!/usr/bin/env python3
"""
容器進入點。
- 無參數：啟動常駐服務 = APScheduler（週一至週五台北時間 12:00 自動執行）
  + Flask 手動觸發網頁（0.0.0.0:5000），對應 `docker compose up -d`。
- 有參數（例如 --dry-run / --force）：委派給 main.main() 執行一次後結束，
  相容舊有 `docker compose run --rm notifier --dry-run` 用法。
"""
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("server")


def run_persistent_service():
    from zoneinfo import ZoneInfo
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    import web

    taipei = ZoneInfo("Asia/Taipei")

    def scheduled_job():
        logger.info("⏰ 排程觸發（週一至週五 12:00 Asia/Taipei），開始執行檢查")
        web.run_scheduled_check()

    scheduler = BackgroundScheduler(timezone=taipei)
    scheduler.add_job(
        scheduled_job,
        trigger=CronTrigger(day_of_week="mon-fri", hour=12, minute=0, timezone=taipei),
        id="daily_check_mon_fri_noon",
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("📅 排程已啟動：週一至週五 12:00（Asia/Taipei）自動執行檢查")

    port = 5000
    logger.info(f"🏸 Web 手動觸發介面啟動於 http://0.0.0.0:{port}")
    try:
        web.app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        from main import main as run_once
        run_once()
    else:
        run_persistent_service()
