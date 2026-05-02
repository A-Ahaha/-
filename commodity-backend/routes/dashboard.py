from __future__ import annotations

from collections import defaultdict

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from models import Comment, Issue, Product
from models import issue_trend_list
from utils.response import ok

# bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")
bp = Blueprint("dashboard", __name__)

def to_iso_z(dt):
    if not dt:
        return ""
    s = dt.isoformat()
    # datetime.utcnow() is naive -> isoformat has no timezone; append Z for frontend parsing.
    if "Z" not in s and "+" not in s and "-" not in s[10:]:
        s = f"{s}Z"
    return s


@bp.route("/top-issues", methods=["GET"])
@jwt_required()
def top_issues():
    product = Product.query.filter(Product.is_competitor == False).order_by(Product.created_at.desc()).first()  # noqa: E712
    if not product:
        return ok([])
    # Top10 高危问题：优先级按“严重等级”与“情感偏负向（sentiment_mean 越低风险越高）”
    rows = (
        Issue.query.filter(Issue.product_id == product.id)
        .order_by(Issue.severity.desc(), Issue.sentiment_mean.asc(), Issue.mentions.desc())
        .limit(10)
        .all()
    )
    data = [
        {
            "id": str(i.id),
            "name": i.name,
            "mentions": i.mentions,
            "sentiment": float(i.sentiment_mean or 0),
            "severity": int(i.severity),
        }
        for i in rows
    ]
    return ok(data)


@bp.route("/trend", methods=["GET"])
@jwt_required()
def trend():
    days = request.args.get("days", type=int) or 14
    days = max(7, min(30, days))
    product = Product.query.filter(Product.is_competitor == False).order_by(Product.created_at.desc()).first()  # noqa: E712
    if not product:
        return ok([])
    rows = Issue.query.filter(Issue.product_id == product.id).order_by(Issue.mentions.desc()).limit(6).all()

    merged: dict[str, float] = defaultdict(float)
    for issue in rows:
        points = issue_trend_list(issue) or []
        # 只取最后 days 个点
        for p in points[-days:]:
            date = p.get("date")
            value = p.get("value", 0)
            if date:
                merged[date] += float(value or 0)

    out = [{"date": d, "value": round(merged[d], 2)} for d in sorted(merged.keys())]
    return ok(out)


@bp.route("/comments", methods=["GET"])
@jwt_required()
def latest_comments():
    size = request.args.get("size", type=int) or 12
    size = max(5, min(30, size))

    product = Product.query.filter(Product.is_competitor == False).order_by(Product.created_at.desc()).first()  # noqa: E712
    if not product:
        return ok([])
    rows = (
        Comment.query.filter(Comment.issue_id.isnot(None), Comment.product_id == product.id)
        .order_by(Comment.created_at.desc())
        .limit(size)
        .all()
    )

    out = []
    for c in rows:
        out.append(
            {
                "id": str(c.id),
                "issueId": str(c.issue_id),
                "username": c.username or "匿名用户",
                "content": c.content,
                "sentiment": float(c.sentiment) if c.sentiment is not None else 0.5,
                "createdAt": to_iso_z(c.created_at),
            }
        )

    return ok(out)


@bp.route("/comments-page", methods=["GET"])
@jwt_required()
def comments_page():
    page = request.args.get("page", type=int) or 1
    page_size = request.args.get("pageSize", type=int) or 20
    page = max(1, page)
    page_size = max(5, min(100, page_size))

    product = Product.query.filter(Product.is_competitor == False).order_by(Product.created_at.desc()).first()  # noqa: E712
    if not product:
        return ok({"list": [], "total": 0})

    q = Comment.query.filter(Comment.issue_id.isnot(None), Comment.product_id == product.id).order_by(Comment.created_at.desc())
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()

    out = []
    for c in rows:
        out.append(
            {
                "id": str(c.id),
                "issueId": str(c.issue_id),
                "username": c.username or "匿名用户",
                "content": c.content,
                "sentiment": float(c.sentiment) if c.sentiment is not None else 0.5,
                "createdAt": to_iso_z(c.created_at),
            }
        )

    return ok({"list": out, "total": total})

