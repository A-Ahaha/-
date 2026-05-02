from datetime import datetime

from models import SystemLog, SystemSetting, User, db
from utils.security import hash_password


def seed_if_empty():
    """只保留最小初始化，不写入任何业务演示数据。"""
    if User.query.count() == 0:
        db.session.add(
            User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin",
                email="admin@local.test",
                status="active",
            )
        )
        db.session.add(
            User(
                username="demo",
                password_hash=hash_password("demo123"),
                role="user",
                email="demo@local.test",
                phone="13800000000",
                status="active",
            )
        )
        db.session.commit()

    # system settings/logs
    if SystemSetting.query.count() == 0:
        db.session.add(
            SystemSetting(
                collect_frequency_minutes=30,
                collect_enabled=False,
                collect_max_pages=20,
                alert_threshold=50,
            )
        )
        db.session.commit()

    if SystemLog.query.count() == 0:
        db.session.add(SystemLog(level="info", message="系统初始化完成（无业务seed数据）", created_at=datetime.utcnow()))
        db.session.commit()

