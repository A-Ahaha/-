import json
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="user")  # user | admin
    email = db.Column(db.String(128), nullable=True)
    phone = db.Column(db.String(32), nullable=True)
    status = db.Column(db.String(16), nullable=False, default="active")  # active | disabled

    def to_public_dict(self):
        return {
            "id": str(self.id),
            "username": self.username,
            "role": self.role,
            "email": self.email or None,
            "phone": self.phone or None,
            "status": self.status,
        }


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sku = db.Column(db.String(128), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    platform = db.Column(db.String(64), nullable=True)
    is_competitor = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

   
class ProductAspectSentiment(db.Model):
    __tablename__ = "product_aspect_sentiment"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    aspect = db.Column(db.String(64), nullable=False)
    sentiment = db.Column(db.String(16), nullable=False)
    confidence = db.Column(db.Float, nullable=False)


class Issue(db.Model):
    __tablename__ = "issues"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    mentions = db.Column(db.Integer, default=0)
    sentiment_mean = db.Column(db.Float, default=0.0)  # 0..1
    severity = db.Column(db.SmallInteger, default=3)  # 1-5
    trend_json = db.Column(db.Text, nullable=True)  # [{\"date\",\"value\"}, ...]
    competitors_json = db.Column(db.Text, nullable=True)  # [{\"brand\",\"mentions\",\"sentiment\"}, ...]


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=True, index=True)
    username = db.Column(db.String(64), nullable=True)
    content = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.Float, nullable=True)  # 0..1
    rating = db.Column(db.SmallInteger, nullable=True)
    purchase_time = db.Column(db.DateTime, nullable=True)
    is_append_review = db.Column(db.Boolean, default=False)
    repurchase_count = db.Column(db.Integer, default=0)
    raw_product_variant = db.Column(db.String(255), nullable=True)
    source_platform = db.Column(db.String(32), nullable=True, index=True)
    source_comment_id = db.Column(db.String(128), nullable=True, index=True)
    source_hash = db.Column(db.String(64), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=True, index=True)
    issue_name = db.Column(db.String(255), nullable=False)
    rule = db.Column(db.String(512), nullable=False)
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(16), default="pending")  # pending | handled


class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    collect_frequency_minutes = db.Column(db.Integer, default=30)
    collect_enabled = db.Column(db.Boolean, default=False)
    collect_item_url = db.Column(db.String(1024), nullable=True)
    collect_sku = db.Column(db.String(128), nullable=True)
    collect_product_name = db.Column(db.String(255), nullable=True)
    collect_is_competitor = db.Column(db.Boolean, default=False)
    collect_clear_existing = db.Column(db.Boolean, default=False)
    collect_include_alerts = db.Column(db.Boolean, default=False)
    collect_max_pages = db.Column(db.Integer, default=20)
    alert_threshold = db.Column(db.Integer, default=50)
    email_enabled = db.Column(db.Boolean, default=False)
    email_to = db.Column(db.String(255), nullable=True)
    smtp_host = db.Column(db.String(128), nullable=True)
    smtp_port = db.Column(db.Integer, default=465)
    smtp_user = db.Column(db.String(128), nullable=True)
    smtp_password = db.Column(db.String(255), nullable=True)
    smtp_use_ssl = db.Column(db.Boolean, default=True)
    webhook_enabled = db.Column(db.Boolean, default=False)
    webhook_url = db.Column(db.String(512), nullable=True)


class SystemLog(db.Model):
    __tablename__ = "system_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    level = db.Column(db.String(16), nullable=False)  # info | warn | error
    message = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class CollectJob(db.Model):
    __tablename__ = "collect_jobs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    platform = db.Column(db.String(32), nullable=False, index=True)  # jd | tmall | csv | ...
    sku = db.Column(db.String(128), nullable=False, index=True)
    product_name = db.Column(db.String(255), nullable=True)
    item_url = db.Column(db.String(1024), nullable=True)
    status = db.Column(db.String(16), nullable=False, default="pending", index=True)  # pending | running | success | failed
    total_collected = db.Column(db.Integer, default=0)
    total_imported = db.Column(db.Integer, default=0)
    error_message = db.Column(db.String(1000), nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    finished_at = db.Column(db.DateTime, nullable=True)


def issue_trend_list(issue: Issue):
    if not issue.trend_json:
        return []
    try:
        return json.loads(issue.trend_json)
    except json.JSONDecodeError:
        return []


def issue_competitors_list(issue: Issue):
    if not issue.competitors_json:
        return []
    try:
        return json.loads(issue.competitors_json)
    except json.JSONDecodeError:
        return []

