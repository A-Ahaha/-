from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from models import Comment, Issue, Product, db
from models import issue_competitors_list, issue_trend_list
from utils.response import err, ok

# bp = Blueprint("detail", __name__, url_prefix="/detail")
bp = Blueprint("detail", __name__)


def to_iso_z(dt):
    if not dt:
        return ""
    s = dt.isoformat()
    if "Z" not in s and "+" not in s and "-" not in s[10:]:
        s = f"{s}Z"
    return s


@bp.route("/<issue_id>", methods=["GET"])
@jwt_required()
def issue_detail(issue_id: str):
    if not str(issue_id).isdigit():
        return err("无效的问题 ID", code=400, http_status=400)
    iid = int(issue_id)

    issue = db.session.get(Issue, iid)
    if not issue:
        return err("数据不存在", code=404, http_status=404)

    product = db.session.get(Product, int(issue.product_id)) if issue.product_id else None
    main_product_name = (product.name if product else "").strip() or "主商品"

    competitors = []
    for item in issue_competitors_list(issue):
        brand = str(item.get("brand") or "").strip() or "未知品牌"
        mentions = int(item.get("mentions", 0) or 0)
        sentiment = float(item.get("sentiment", 0) or 0)
        is_main = brand in ("本品", main_product_name)
        competitors.append(
            {
                "brand": brand,
                "displayName": f"主商品：{main_product_name}" if is_main else f"竞品：{brand}",
                "role": "main" if is_main else "competitor",
                "mentions": mentions,
                "sentiment": sentiment,
            }
        )

    data = {
        "id": str(issue.id),
        "name": issue.name,
        "mentions": issue.mentions,
        "sentiment": float(issue.sentiment_mean or 0),
        "severity": int(issue.severity),
        "productName": main_product_name,
        "trend": issue_trend_list(issue),
        "competitors": competitors,
    }
    return ok(data)


@bp.route("/<issue_id>/comments", methods=["GET"])
@jwt_required()
def issue_comments(issue_id: str):
    if not str(issue_id).isdigit():
        return err("无效的问题 ID", code=400, http_status=400)
    iid = int(issue_id)

    issue = db.session.get(Issue, iid)
    if not issue:
        return err("数据不存在", code=404, http_status=404)

    page = request.args.get("page", type=int) or 1
    page_size = request.args.get("pageSize", type=int) or 10
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    q = Comment.query.filter(Comment.issue_id == iid).order_by(Comment.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    lst = [
        {
            "id": str(c.id),
            "issueId": str(issue.id),
            "username": c.username or "匿名用户",
            "content": c.content,
            "sentiment": float(c.sentiment) if c.sentiment is not None else 0.5,
            "createdAt": to_iso_z(c.created_at),
        }
        for c in items
    ]
    return ok({"list": lst, "total": total})


@bp.route("/<issue_id>/batch-trend", methods=["GET"])
@jwt_required()
def issue_batch_trend(issue_id: str):
    """
    批次关联分析（轻量版）：
    - 使用评论里的 `raw_product_variant` 当作“批次/变体”维度
    - 返回近 days 天内，不同批次对该问题的提及次数趋势
    """
    if not str(issue_id).isdigit():
        return err("无效的问题 ID", code=400, http_status=400)
    iid = int(issue_id)

    issue = db.session.get(Issue, iid)
    if not issue:
        return err("数据不存在", code=404, http_status=404)

    days = request.args.get("days", type=int) or 14
    days = max(7, min(30, days))
    top_batches = request.args.get("topBatches", type=int) or 5
    top_batches = max(3, min(10, top_batches))

    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=days - 1)

    q = Comment.query.filter(Comment.issue_id == iid, Comment.created_at.isnot(None), Comment.created_at >= start_dt)
    rows = q.all()

    # batch -> date -> mentions
    batch_date_counts: dict[str, dict[str, int]] = {}
    batch_totals: dict[str, int] = {}
    date_set: set[str] = set()

    for c in rows:
        batch_name = (c.raw_product_variant or "").strip() or "未标注"
        day_key = (c.created_at or end_dt).date().isoformat()
        date_set.add(day_key)

        batch_date_counts.setdefault(batch_name, {})
        batch_date_counts[batch_name][day_key] = batch_date_counts[batch_name].get(day_key, 0) + 1
        batch_totals[batch_name] = batch_totals.get(batch_name, 0) + 1

    # 只保留提及最多的 top batches
    batches_sorted = sorted(batch_totals.items(), key=lambda x: x[1], reverse=True)
    selected_batches = [b for b, _ in batches_sorted[:top_batches]]

    date_list = sorted(date_set)
    out_batches = []
    for b in selected_batches:
        counts_per_date = [batch_date_counts.get(b, {}).get(d, 0) for d in date_list]
        mentions_total = sum(counts_per_date)
        # 简单“新批次/旧批次”趋势：用前半段 vs 后半段对比
        mid = len(date_list) // 2
        first_sum = sum(counts_per_date[:mid])
        last_sum = sum(counts_per_date[mid:])
        change_pct = None
        if first_sum > 0:
            change_pct = round(((last_sum - first_sum) / first_sum) * 100, 2)
        out_batches.append(
            {
                "batchName": b,
                "mentions": mentions_total,
                "changePct": change_pct,
                "series": counts_per_date,
            }
        )

    return ok({"date": date_list, "batches": out_batches})

