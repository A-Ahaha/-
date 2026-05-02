from __future__ import annotations

import logging
import re
from collections import defaultdict
from functools import lru_cache
from typing import Any

from flask import current_app

from models import Comment, Product, db

logger = logging.getLogger(__name__)


_ASPECT_PATTERNS: list[tuple[str, str]] = [
    (r"电池|续航|电量|充电", "电池续航"),
    (r"屏幕|显示|坏点|触控", "屏幕"),
    (r"发热|发烫|温度", "散热"),
    (r"包装|破损|漏液", "包装"),
    (r"口感|味道|异味", "口感味道"),
    (r"配送|物流|快递", "物流"),
    (r"标签|保质期|日期|信息不清", "标签信息"),
    (r"外观|瑕疵|变形|塌陷", "外观结构"),
    (r"重量|分量|不足", "重量规格"),
    (r"卡顿|流畅|系统", "系统性能"),
]

_pipeline = None


def _extract_focus_snippets(text: str, pattern: str, *, window_chars: int = 40, max_snippets: int = 2) -> list[str]:
    """
    从命中 aspect 的位置附近截取少量上下文，尽量让情感模型“看到”对应属性相关表述。
    """
    if not text:
        return []
    snippets: list[str] = []
    for m in re.finditer(pattern, text):
        start = max(0, m.start() - window_chars)
        end = min(len(text), m.end() + window_chars)
        snippet = (text[start:end] or "").strip()
        if snippet and snippet not in snippets:
            snippets.append(snippet)
        if len(snippets) >= max_snippets:
            break
    return snippets


@lru_cache(maxsize=4096)
def _run_sentiment_cached(text: str) -> tuple[str, float]:
    # NOTE: 这里缓存的是“输入文本片段”级别结果，适合我们对同一句话截取相同窗口的场景。
    return _run_sentiment(text)


def _get_pipeline():
    global _pipeline
    if current_app.config.get("USE_MOCK_ABSA"):
        return None
    if _pipeline is not None:
        return _pipeline
    try:
        from transformers import pipeline

        model = current_app.config.get("ABSA_MODEL", "tabularisai/multilingual-sentiment-analysis")
        _pipeline = pipeline("sentiment-analysis", model=model, tokenizer=model)
        logger.info("ABSA pipeline loaded: %s", model)
    except Exception as e:  # pragma: no cover
        # 兼容情况：当 transformers 模型无法加载时，回退到启发式情感，保证系统可用。
        logger.warning("ABSA pipeline load failed, fallback to heuristic. error=%s", e)
        _pipeline = None
    return _pipeline


def _detect_aspects(text: str) -> list[str]:
    found: list[str] = []
    for pattern, aspect in _ASPECT_PATTERNS:
        if re.search(pattern, text or ""):
            found.append(aspect)
    if not found:
        return ["综合体验"]
    # 去重保持顺序
    return list(dict.fromkeys(found))


def _heuristic_sentiment(text: str) -> tuple[str, float]:
    # 简易正负向词打分（用于开发联调/无法加载 transformers 时）
    text = text or ""
    neg_words = ["差", "坏", "慢", "烫", "漏", "破", "退", "假", "臭", "卡", "发热"]
    pos_words = ["好", "赞", "棒", "满意", "快", "稳", "安全", "清晰"]
    neg = sum(1 for w in neg_words if w in text)
    pos = sum(1 for w in pos_words if w in text)
    raw = (pos - neg) * 0.2
    if raw >= 0.15:
        return "positive", min(1.0, 0.5 + raw / 2)
    if raw <= -0.15:
        return "negative", min(1.0, 0.5 - raw / 2)
    return "neutral", 0.55


def _run_sentiment(text: str) -> tuple[str, float]:
    pl = _get_pipeline()
    if not pl:
        return _heuristic_sentiment(text)
    try:
        out = pl((text or "")[:512])[0]
        label = str(out.get("label", "")).lower()
        score = float(out.get("score", 0.5))
        # 兼容不同模型的标签命名
        if "neg" in label:
            return "negative", score
        if "pos" in label:
            return "positive", score
        return "neutral", score
    except Exception as e:  # pragma: no cover
        logger.debug("sentiment error: %s", e)
        return "neutral", 0.5


def _run_aspect_sentiments(text: str, aspects: list[str]) -> list[dict[str, Any]]:
    """
    近似 ABSA：
    - 规则先给出 aspects
    - 针对每个 aspect，用其关键词匹配位置截取少量上下文
    - 对截取片段分别做 sentiment 得到 aspect 粒度情感与置信度
    """
    if not text:
        return []

    # 如果是“综合体验”，就直接对整段做情感
    if aspects == ["综合体验"]:
        sentiment, confidence = _run_sentiment_cached(text)
        return [{"aspect": "综合体验", "sentiment": sentiment, "confidence": float(confidence)}]

    # 反查每个 aspect 对应哪些 regex pattern
    aspect_patterns: dict[str, list[str]] = defaultdict(list)
    for pattern, aspect in _ASPECT_PATTERNS:
        aspect_patterns[aspect].append(pattern)

    out: list[dict[str, Any]] = []
    for asp in aspects:
        patterns = aspect_patterns.get(asp) or []
        if not patterns:
            # 兜底：回退到整段
            sentiment, confidence = _run_sentiment_cached(text)
            out.append({"aspect": asp, "sentiment": sentiment, "confidence": float(confidence)})
            continue

        snippets: list[str] = []
        for pattern in patterns:
            snippets.extend(_extract_focus_snippets(text, pattern))
            if len(snippets) >= 2:
                break

        focused_text = " ".join(snippets).strip() or text
        # 给情感模型一个明确的“这是在评价哪个属性”锚点
        focused_text = f"【{asp}】{focused_text}"
        sentiment, confidence = _run_sentiment_cached(focused_text)
        out.append({"aspect": asp, "sentiment": sentiment, "confidence": float(confidence)})

    return out


def analyze_product(product_id: int) -> dict[str, Any]:
    product = db.session.get(Product, product_id)
    if not product:
        return {"error": "product_not_found"}

    comments = (
        Comment.query.filter(Comment.product_id == product_id)
        .order_by(Comment.created_at.desc())
        .limit(current_app.config.get("ABSA_MAX_COMMENTS", 800))
        .all()
    )

    if not comments:
        return {"product_name": product.name, "aspects": []}

    aspect_data: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "conf_sum": 0.0, "pos": 0, "neg": 0, "neu": 0})

    for c in comments:
        text = (c.content or "").strip()
        if not text:
            continue
        aspects = _detect_aspects(text)
        aspect_sentiments = _run_aspect_sentiments(text, aspects)
        for asp_item in aspect_sentiments:
            asp = str(asp_item.get("aspect") or "")
            if not asp:
                continue
            bucket = aspect_data[asp]
            bucket["count"] += 1
            conf = float(asp_item.get("confidence") or 0.5)
            bucket["conf_sum"] += conf
            sentiment = str(asp_item.get("sentiment") or "neutral")
            if sentiment == "positive":
                bucket["pos"] += 1
            elif sentiment == "negative":
                bucket["neg"] += 1
            else:
                bucket["neu"] += 1

    order = {"negative": 0, "neutral": 1, "positive": 2}

    aspects_out: list[dict[str, Any]] = []
    for asp, bucket in aspect_data.items():
        n = bucket["count"] or 1
        sentiment = max(
            ["negative", "neutral", "positive"],
            key=lambda s: (bucket["neg"] if s == "negative" else bucket["neu"] if s == "neutral" else bucket["pos"], -order[s]),
        )
        aspects_out.append(
            {
                "aspect": asp,
                "sentiment": sentiment,
                "confidence": round(bucket["conf_sum"] / n, 4),
            }
        )

    return {"product_name": product.name, "aspects": aspects_out}


def analyze_comment_text(text: str) -> dict[str, Any]:
    """单条评论 ABSA 结果，供 CSV 导入与质量问题聚合复用。"""
    normalized = (text or "").strip()
    aspects = _detect_aspects(normalized)
    sentiment, confidence = _run_sentiment_cached(normalized)
    aspect_sentiments = _run_aspect_sentiments(normalized, aspects)
    return {
        "aspects": aspects,
        "sentiment": sentiment,
        "confidence": confidence,
        "aspect_sentiments": aspect_sentiments,
    }


def analyze_comment_text_fast(text: str) -> dict[str, Any]:
    """
    批量导入/聚合用：仅关键词属性 + 启发式情感，不调用 Transformer。
    写库与 issue 统计足够快；需要模型精度时在后台点「重建 ABSA」。
    """
    normalized = (text or "").strip()
    aspects = _detect_aspects(normalized)
    sentiment, confidence = _heuristic_sentiment(normalized)
    conf_f = float(confidence)
    aspect_sentiments = [{"aspect": asp, "sentiment": sentiment, "confidence": conf_f} for asp in aspects]
    return {
        "aspects": aspects,
        "sentiment": sentiment,
        "confidence": confidence,
        "aspect_sentiments": aspect_sentiments,
    }

