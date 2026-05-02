from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from apscheduler.schedulers.background import BackgroundScheduler

from models import SystemLog, SystemSetting, db
from services.jd_collect_service import collect_and_import_jd_comments

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None
_job_id = "scheduled_jd_collect"


def _write_log(level: str, message: str):
    db.session.add(SystemLog(level=level, message=(message or "")[:500], created_at=datetime.utcnow()))
    db.session.commit()


def _scheduled_collect(app):
    with app.app_context():
        settings = SystemSetting.query.first()
        if not settings or not settings.collect_enabled:
            return
        if not settings.collect_item_url or not settings.collect_sku:
            _write_log("warn", "定时采集已开启，但未配置 item_url 或 sku")
            return

        try:
            result = collect_and_import_jd_comments(
                item_url=settings.collect_item_url,
                sku=settings.collect_sku,
                product_name=settings.collect_product_name,
                is_competitor=bool(settings.collect_is_competitor),
                clear_existing=bool(settings.collect_clear_existing),
                include_alerts=bool(settings.collect_include_alerts),
                max_pages=int(settings.collect_max_pages or 20),
            )
            _write_log("info", f"定时采集完成：sku={settings.collect_sku}，导入={result.get('count', 0)}")
        except Exception as e:  # pragma: no cover
            logger.exception("Scheduled JD collect failed: %s", e)
            _write_log("error", f"定时采集失败：{str(e)}")


def init_scheduler(app):
    global _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
    except Exception as e:  # pragma: no cover
        logger.warning("APScheduler not installed, scheduler disabled: %s", e)
        return
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        _scheduler.start()
    refresh_scheduler(app)


def refresh_scheduler(app):
    global _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler  # noqa: F401  # type: ignore
        from apscheduler.triggers.interval import IntervalTrigger  # type: ignore
    except Exception as e:  # pragma: no cover
        logger.warning("APScheduler not installed, scheduler disabled: %s", e)
        return
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        _scheduler.start()

    settings = SystemSetting.query.first()
    existing = _scheduler.get_job(_job_id)

    if not settings or not settings.collect_enabled:
        if existing:
            _scheduler.remove_job(_job_id)
        return

    minutes = max(1, int(settings.collect_frequency_minutes or 30))
    trigger = IntervalTrigger(minutes=minutes)

    if existing:
        _scheduler.reschedule_job(_job_id, trigger=trigger)
        existing.modify(args=[app])
    else:
        _scheduler.add_job(
            _scheduled_collect,
            trigger=trigger,
            id=_job_id,
            args=[app],
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )


def should_start_scheduler(app) -> bool:
    if os.environ.get("WERKZEUG_RUN_MAIN") == "false":
        return False
    return True
