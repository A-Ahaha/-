from __future__ import annotations

import json
import smtplib
import ssl
from email.mime.text import MIMEText
from urllib import request as urlrequest

from models import Alert, SystemSetting


def _compose_message(alert: Alert) -> str:
    return f"质量预警触发\n问题：{alert.issue_name}\n规则：{alert.rule}\n时间：{alert.triggered_at.isoformat() if alert.triggered_at else ''}"


def send_alert_notifications(alert: Alert, settings: SystemSetting):
    results = {"email": None, "webhook": None}
    msg = _compose_message(alert)

    if settings and settings.email_enabled and settings.email_to and settings.smtp_host:
        try:
            mime = MIMEText(msg, "plain", "utf-8")
            mime["Subject"] = f"[质量预警] {alert.issue_name}"
            mime["From"] = settings.smtp_user or "quality-alert@local"
            mime["To"] = settings.email_to

            if settings.smtp_use_ssl:
                with smtplib.SMTP_SSL(
                    settings.smtp_host,
                    int(settings.smtp_port or 465),
                    context=ssl.create_default_context(),
                    timeout=8,
                ) as server:
                    if settings.smtp_user and settings.smtp_password:
                        server.login(settings.smtp_user, settings.smtp_password)
                    server.send_message(mime)
            else:
                with smtplib.SMTP(settings.smtp_host, int(settings.smtp_port or 25), timeout=8) as server:
                    server.starttls(context=ssl.create_default_context())
                    if settings.smtp_user and settings.smtp_password:
                        server.login(settings.smtp_user, settings.smtp_password)
                    server.send_message(mime)
            results["email"] = "ok"
        except Exception as e:
            results["email"] = f"failed: {str(e)}"

    if settings and settings.webhook_enabled and settings.webhook_url:
        try:
            payload = {
                "type": "quality_alert",
                "issueName": alert.issue_name,
                "rule": alert.rule,
                "triggeredAt": alert.triggered_at.isoformat() if alert.triggered_at else "",
                "status": alert.status,
            }
            req = urlrequest.Request(
                settings.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlrequest.urlopen(req, timeout=8) as resp:
                results["webhook"] = f"ok:{resp.status}"
        except Exception as e:
            results["webhook"] = f"failed: {str(e)}"

    return results

