from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime

from models import Alert, Comment, Issue, Product, SystemSetting, db
from services.absa_service import analyze_comment_text, analyze_comment_text_fast
from services.notify_service import send_alert_notifications

_ISSUE_PATTERNS = [
    (r"电池|续航|电量|充电", "电池续航"),
    (r"屏幕|显示|坏点|触控", "屏幕显示"),
    (r"发热|发烫|温度", "发热散热"),
    (r"卡顿|流畅|系统|掉帧", "系统性能"),
    (r"包装|破损|磕碰", "包装品控"),
    (r"配送|物流|快递", "物流配送"),
    (r"外观|做工|缝隙|异响", "外观做工"),
]

_SEVERE_WORDS = ["退货", "投诉", "差评", "严重", "无法", "坏了", "不耐用", "垃圾"]
_NEGATIVE_ISSUE_THRESHOLD = 0.45


def _parse_dt(value: str):
    if not value:
        return datetime.utcnow()
    raw = str(value).strip()
    if not raw:
        return datetime.utcnow()

    # 常见导出里可能出现 "2026-04-17T09:50:00Z"
    iso_candidate = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_candidate)
    except Exception:
        pass

    # 兼容常见 CSV/Excel 时间格式（含斜杠、无秒、仅日期、中文日期）
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y年%m月%d日 %H:%M:%S",
        "%Y年%m月%d日 %H:%M",
        "%Y年%m月%d日",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            continue

    return datetime.utcnow()


def _to_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _pick_issue_name(text: str, aspects: list[str]) -> str:
    source = f"{text or ''} {' '.join(aspects)}"
    for pattern, issue_name in _ISSUE_PATTERNS:
        if re.search(pattern, source):
            return issue_name
    return "综合体验"


def _score_to_sentiment(label: str, confidence: float) -> float:
    if label == "negative":
        return max(0.01, 0.5 - confidence * 0.5)
    if label == "positive":
        return min(0.99, 0.5 + confidence * 0.5)
    return 0.5


def _issue_to_aspects(issue_name: str) -> list[str]:
    """
    将“问题(issue_name)”映射到 ABSA aspect 粒度的属性标签。
    """
    mapping = {
        "电池续航": ["电池续航"],
        "屏幕显示": ["屏幕"],
        "发热散热": ["散热"],
        "系统性能": ["系统性能"],
        "包装品控": ["包装"],
        "物流配送": ["物流"],
        "外观做工": ["外观结构"],
        "综合体验": ["综合体验"],
    }
    return mapping.get(issue_name, ["综合体验"])


def _calc_issue_sentiment_score(issue_name: str, absa_result: dict) -> float:
    """
    针对某个 issue_name，从 aspect_sentiments 里取“对应属性”的情感分数。
    多属性时取最差（最接近 negative 的值）。
    """
    aspect_sentiments = absa_result.get("aspect_sentiments") or []
    aspect_map = {str(x.get("aspect")): x for x in aspect_sentiments if x.get("aspect")}
    candidates = _issue_to_aspects(issue_name)

    scores: list[float] = []
    for asp in candidates:
        item = aspect_map.get(asp)
        if not item:
            continue
        label = str(item.get("sentiment") or "neutral")
        conf = float(item.get("confidence") or 0.5)
        scores.append(_score_to_sentiment(label, conf))

    if scores:
        return min(scores)  # 越差越低

    # fallback：用整段情感
    return _score_to_sentiment(
        str(absa_result.get("sentiment") or "neutral"),
        float(absa_result.get("confidence") or 0.5),
    )


def _calc_severity(mentions: int, sentiment_mean: float, negative_ratio: float, severe_hits: int) -> int:
    score = 0
    if mentions >= 50:
        score += 1
    if mentions >= 100:
        score += 1
    if sentiment_mean < 0.4:
        score += 1
    if negative_ratio >= 0.4:
        score += 1
    if severe_hits >= 5:
        score += 1
    return max(1, min(5, score))


def _delete_issues_for_product(product_id: int, *, null_comment_issue_ids: bool) -> None:
    """
    删除某商品下的 issues。须先于 alerts（外键）并解除 comments.issue_id。
    """
    issue_id_rows = db.session.query(Issue.id).filter(Issue.product_id == product_id).all()
    issue_ids = [row[0] for row in issue_id_rows]
    if issue_ids:
        Alert.query.filter(Alert.issue_id.in_(issue_ids)).delete(synchronize_session=False)
    if null_comment_issue_ids:
        Comment.query.filter(Comment.product_id == product_id).update(
            {Comment.issue_id: None},
            synchronize_session=False,
        )
    Issue.query.filter(Issue.product_id == product_id).delete(synchronize_session=False)


def _make_comment_source_hash(row: dict) -> str:
    """
    当没有平台原生 comment id 时，使用稳定字段拼接做弱去重。
    """
    base = "||".join(
        [
            str(row.get("昵称") or row.get("nickName") or row.get("username") or "").strip(),
            str(row.get("日期") or row.get("commentTime") or "").strip(),
            str(row.get("评分") or row.get("rating") or "").strip(),
            str(row.get("产品") or row.get("variant") or row.get("productVariant") or "").strip(),
            str(row.get("评论") or row.get("comment") or row.get("content") or "").strip(),
        ]
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def import_comment_rows(
    rows: list[dict],
    product_name: str,
    sku: str,
    *,
    platform: str = "manual",
    is_competitor: bool = False,
    clear_existing: bool = False,
    include_alerts: bool = True,
    use_transformer: bool = False,
):
    product = Product.query.filter_by(sku=sku).first()
    if not product:
        product = Product(sku=sku, name=product_name, platform=platform, is_competitor=is_competitor)
        db.session.add(product)
        db.session.flush()
    else:
        product.name = product_name or product.name
        product.platform = platform or product.platform
        product.is_competitor = bool(is_competitor)

    if clear_existing:
        Comment.query.filter(Comment.product_id == product.id).delete()
        _delete_issues_for_product(product.id, null_comment_issue_ids=False)

    existing_hashes = set()
    existing_source_ids = set()
    if not clear_existing:
        for source_hash, source_comment_id in db.session.query(Comment.source_hash, Comment.source_comment_id).filter(
            Comment.product_id == product.id
        ):
            if source_hash:
                existing_hashes.add(source_hash)
            if source_comment_id:
                existing_source_ids.add(source_comment_id)

    _analyze = analyze_comment_text if use_transformer else analyze_comment_text_fast

    comments = []
    imported_count = 0
    skipped_duplicates = 0
    for row in rows:
        content = (row.get("评论") or row.get("comment") or row.get("content") or "").strip()
        if not content:
            continue

        source_platform = str(row.get("sourcePlatform") or platform or "").strip() or None
        source_comment_id = str(row.get("commentId") or row.get("sourceCommentId") or "").strip() or None
        source_hash = _make_comment_source_hash(row)

        if source_comment_id and source_comment_id in existing_source_ids:
            skipped_duplicates += 1
            continue
        if source_hash in existing_hashes:
            skipped_duplicates += 1
            continue

        absa = _analyze(content)
        sentiment_score = _score_to_sentiment(absa["sentiment"], float(absa["confidence"] or 0.5))
        repurchase_count = _to_int(row.get("回购次数", row.get("回购", row.get("repurchaseCount", 0))), 0)
        comment = Comment(
            product_id=product.id,
            username=(row.get("昵称") or row.get("nickName") or row.get("username") or "").strip() or "匿名用户",
            content=content,
            rating=_to_int(row.get("评分", row.get("rating", 5)), 5),
            purchase_time=_parse_dt(row.get("日期", row.get("commentTime", ""))),
            created_at=_parse_dt(row.get("日期", row.get("commentTime", ""))),
            is_append_review=bool(row.get("isAppendReview", False)) or repurchase_count > 1,
            repurchase_count=repurchase_count,
            raw_product_variant=(row.get("产品") or row.get("variant") or row.get("productVariant") or "").strip() or None,
            source_platform=source_platform,
            source_comment_id=source_comment_id,
            source_hash=source_hash,
            sentiment=sentiment_score,
        )
        comments.append(comment)
        imported_count += 1
        existing_hashes.add(source_hash)
        if source_comment_id:
            existing_source_ids.add(source_comment_id)

    if comments:
        db.session.bulk_save_objects(comments)
        db.session.commit()
    else:
        db.session.commit()

    if not product.is_competitor:
        build_issues(product.id, use_transformer=use_transformer)
        if include_alerts:
            _build_alerts(product.id)

    return {
        "msg": "导入成功",
        "count": imported_count,
        "skippedDuplicates": skipped_duplicates,
        "productId": product.id,
        "isCompetitor": product.is_competitor,
        "platform": product.platform,
    }


def import_csv(
    file_path: str,
    product_name: str,
    sku: str,
    is_competitor: bool = False,
    clear_existing: bool = False,
    use_transformer: bool = False,
):
    rows: list[dict] = []
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    return import_comment_rows(
        rows,
        product_name=product_name,
        sku=sku,
        platform="csv",
        is_competitor=is_competitor,
        clear_existing=clear_existing,
        include_alerts=True,
        use_transformer=use_transformer,
    )


def build_issues(product_id: int, *, use_transformer: bool = False):
    comments = Comment.query.filter(Comment.product_id == product_id).all()
    _delete_issues_for_product(product_id, null_comment_issue_ids=True)
    db.session.flush()

    if not comments:
        db.session.commit()
        return

    _analyze = analyze_comment_text if use_transformer else analyze_comment_text_fast

    issue_buckets = defaultdict(lambda: {"mentions": 0, "sentiments": [], "neg": 0, "trend": defaultdict(int), "severe_hits": 0})
    comment_issue_name = {}

    for c in comments:
        absa = _analyze(c.content or "")
        issue_name = _pick_issue_name(c.content, absa["aspects"])
        issue_sent_score = _calc_issue_sentiment_score(issue_name, absa)
        # 质量问题榜只统计负向评论，避免好评将“问题提及”抬高。
        if float(issue_sent_score) >= _NEGATIVE_ISSUE_THRESHOLD:
            continue
        bucket = issue_buckets[issue_name]
        bucket["mentions"] += 1
        bucket["sentiments"].append(float(issue_sent_score))
        bucket["neg"] += 1
        day_key = (c.created_at or datetime.utcnow()).date().isoformat()
        bucket["trend"][day_key] += 1
        if any(w in (c.content or "") for w in _SEVERE_WORDS):
            bucket["severe_hits"] += 1
        comment_issue_name[c.id] = issue_name

    competitor_products = Product.query.filter(Product.is_competitor == True).all()  # noqa: E712
    competitor_issue_map = defaultdict(lambda: defaultdict(list))
    for cp in competitor_products:
        cp_comments = Comment.query.filter(Comment.product_id == cp.id).all()
        for cc in cp_comments:
            cc_absa = _analyze(cc.content or "")
            cc_issue_name = _pick_issue_name(cc.content, cc_absa["aspects"])
            cc_issue_sent_score = _calc_issue_sentiment_score(cc_issue_name, cc_absa)
            if float(cc_issue_sent_score) >= _NEGATIVE_ISSUE_THRESHOLD:
                continue
            competitor_issue_map[cc_issue_name][cp.name].append(float(cc_issue_sent_score))

    issue_entities = {}
    for issue_name, bucket in issue_buckets.items():
        mentions = bucket["mentions"]
        sentiments = bucket["sentiments"]
        sentiment_mean = sum(sentiments) / max(1, len(sentiments))
        neg_ratio = bucket["neg"] / max(1, mentions)
        severity = _calc_severity(mentions, sentiment_mean, neg_ratio, bucket["severe_hits"])
        trend = [{"date": d, "value": v} for d, v in sorted(bucket["trend"].items())]

        competitors = [{"brand": "本品", "mentions": mentions, "sentiment": round(sentiment_mean, 4)}]
        for brand_name, s_list in competitor_issue_map.get(issue_name, {}).items():
            competitors.append(
                {
                    "brand": brand_name,
                    "mentions": len(s_list),
                    "sentiment": round(sum(s_list) / max(1, len(s_list)), 4),
                }
            )

        issue = Issue(
            product_id=product_id,
            name=issue_name,
            mentions=mentions,
            sentiment_mean=round(sentiment_mean, 4),
            severity=severity,
            trend_json=json.dumps(trend, ensure_ascii=False),
            competitors_json=json.dumps(competitors, ensure_ascii=False),
        )
        db.session.add(issue)
        db.session.flush()
        issue_entities[issue_name] = issue.id

    for c in comments:
        issue_name = comment_issue_name.get(c.id)
        if issue_name and issue_name in issue_entities:
            c.issue_id = issue_entities[issue_name]
        else:
            # 清理旧聚合结果，避免 comment.issue_id 残留
            c.issue_id = None

    db.session.commit()


def _build_alerts(product_id: int):
    settings = SystemSetting.query.first()
    threshold = settings.alert_threshold if settings else 50
    issues = Issue.query.filter(Issue.product_id == product_id).all()

    Alert.query.filter(Alert.issue_id.in_([i.id for i in issues])).delete(synchronize_session=False)

    for issue in issues:
        trend = json.loads(issue.trend_json or "[]")
        if len(trend) < 14:
            continue
        prev = sum(int(x.get("value", 0)) for x in trend[-14:-7])
        curr = sum(int(x.get("value", 0)) for x in trend[-7:])
        if prev > 0 and ((curr - prev) / prev) * 100 >= threshold:
            db.session.add(Alert(issue_id=issue.id, issue_name=issue.name, rule=f"周环比增长超过 {threshold}%", status="pending"))
        if issue.sentiment_mean < 0.35:
            db.session.add(Alert(issue_id=issue.id, issue_name=issue.name, rule="情感强度突降", status="pending"))
    db.session.commit()
    settings = SystemSetting.query.first()
    new_alerts = Alert.query.filter(Alert.issue_id.in_([i.id for i in issues]), Alert.status == "pending").all()
    for a in new_alerts:
        send_alert_notifications(a, settings)


def rebuild_for_product(product_id: int, *, include_alerts: bool = False) -> dict:
    """
    手动重算：
    - 重新 build_issues（用当前 ABSA 逻辑）
    - 可选重算告警（include_alerts）

    如果是竞品（is_competitor=True），issue 聚合不会生成，但主商品的竞品对比会受影响；
    因此这里会重算所有主商品的 issues/告警（取决于 include_alerts）。
    """
    product = Product.query.get(product_id)
    if not product:
        return {"error": "product_not_found"}

    rebuilt_main_ids: list[int] = []

    if product.is_competitor:
        main_products = Product.query.filter(Product.is_competitor == False).all()  # noqa: E712
        for mp in main_products:
            build_issues(mp.id, use_transformer=True)
            rebuilt_main_ids.append(mp.id)
            if include_alerts:
                _build_alerts(mp.id)
    else:
        build_issues(product_id, use_transformer=True)
        rebuilt_main_ids.append(product_id)
        if include_alerts:
            _build_alerts(product_id)

    return {
        "productId": product_id,
        "status": "ok",
        "rebuiltMainProductIds": rebuilt_main_ids,
        "alertRebuilt": bool(include_alerts),
    }