from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from models import Alert, Comment, Issue, Product, db
from utils.decorators import admin_required
from utils.response import err, ok

# bp = Blueprint("alert", __name__, url_prefix="/alert")
bp = Blueprint("alert", __name__)

def to_iso_z(dt):
    if not dt:
        return ""
    s = dt.isoformat()
    if "Z" not in s and "+" not in s and "-" not in s[10:]:
        s = f"{s}Z"
    return s


def _to_comment_dict(c: Comment):
    return {
        "id": str(c.id),
        "username": c.username or "匿名用户",
        "content": c.content,
        "sentiment": float(c.sentiment) if c.sentiment is not None else 0.5,
        "rating": int(c.rating) if c.rating is not None else None,
        "purchaseTime": to_iso_z(c.purchase_time),
        "createdAt": to_iso_z(c.created_at),
        "rawProductVariant": c.raw_product_variant or "",
    }


@bp.route("/list", methods=["GET"])
@jwt_required()
@admin_required
def list_alerts():
    status = request.args.get("status")
    q = Alert.query
    if status in ("pending", "handled"):
        q = q.filter(Alert.status == status)
    rows = q.order_by(Alert.triggered_at.desc()).all()

    data = [
        {
            "id": str(a.id),
            "issueName": a.issue_name,
            "rule": a.rule,
            "triggeredAt": to_iso_z(a.triggered_at),
            "status": a.status,
        }
        for a in rows
    ]
    return ok(data)


@bp.route("/handle", methods=["POST"])
@jwt_required()
@admin_required
def handle_alert():
    payload = request.get_json() or {}
    aid = payload.get("id")
    if not aid or not str(aid).isdigit():
        return err("无效参数")
    alert = db.session.get(Alert, int(aid))
    if not alert:
        return err("预警不存在", code=404, http_status=404)
    alert.status = "handled"
    try:
        db.session.commit()
        return ok(None, "已处理")
    except Exception as e:
        db.session.rollback()
        return err(f"处理预警失败：{str(e)}", code=500, http_status=500)


@bp.route("/<alert_id>/detail", methods=["GET"])
@jwt_required()
@admin_required
def alert_detail(alert_id: str):
    if not alert_id or not str(alert_id).isdigit():
        return err("无效参数")

    aid = int(alert_id)
    alert = db.session.get(Alert, aid)
    if not alert:
        return err("预警不存在", code=404, http_status=404)

    size = request.args.get("size", type=int) or 30
    size = max(5, min(200, size))

    issue = db.session.get(Issue, int(alert.issue_id)) if alert.issue_id else None
    product = db.session.get(Product, int(issue.product_id)) if issue else None

    comments = []
    if issue:
        rows = (
            Comment.query.filter(Comment.issue_id == issue.id)
            .order_by(Comment.created_at.desc())
            .limit(size)
            .all()
        )
        comments = [_to_comment_dict(c) for c in rows]

    return ok(
        {
            "alert": {
                "id": str(alert.id),
                "issueName": alert.issue_name,
                "rule": alert.rule,
                "triggeredAt": to_iso_z(alert.triggered_at),
                "status": alert.status,
            },
            "issue": (
                {
                    "id": str(issue.id),
                    "name": issue.name,
                    "mentions": int(issue.mentions or 0),
                    "severity": int(issue.severity or 0),
                    "sentimentMean": float(issue.sentiment_mean or 0),
                }
                if issue
                else None
            ),
            "product": (
                {
                    "id": str(product.id),
                    "sku": product.sku,
                    "name": product.name,
                    "platform": product.platform or "",
                }
                if product
                else None
            ),
            "comments": comments,
        }
    )
