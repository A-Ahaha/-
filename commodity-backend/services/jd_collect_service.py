from __future__ import annotations

import re
import time
from typing import Any, Optional

from models import CollectJob, db
from services.csv_import_service import import_comment_rows


def _build_browser():
    try:
        from DrissionPage import ChromiumOptions, ChromiumPage
    except Exception as e:  # pragma: no cover
        raise RuntimeError("未安装 DrissionPage，请先安装依赖后再使用京东采集") from e

    co = ChromiumOptions()
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_user_agent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return ChromiumPage(addr_or_opts=co)


def _clean_variant(raw_spec: str) -> str:
    normalized = (raw_spec or "").strip()
    return re.sub(r"^(已购|买过|已选|购买)\s*", "", normalized).strip()


def _get_product_name(dp) -> str:
    for selector in ("css:.item.ellipsis", "css:.sku-title-name"):
        try:
            ele = dp.ele(selector, timeout=2)
            if ele and ele.text.strip():
                return ele.text.strip()
        except Exception:
            continue
    return "未知商品"


def collect_jd_comments(
    item_url: str,
    *,
    max_pages: int = 20,
    wait_seconds: float = 2.0,
) -> dict[str, Any]:
    """
    使用浏览器采集京东商品评论，并统一返回为项目内部可导入的记录结构。
    """
    if not item_url:
        raise ValueError("item_url 不能为空")

    dp = _build_browser()
    rows: list[dict[str, Any]] = []

    try:
        dp.run_js('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')
        dp.get(item_url)
        time.sleep(wait_seconds)

        try:
            dp.run_js("window.scrollTo(0, document.body.scrollHeight * 0.3);")
        except Exception:
            pass
        time.sleep(1.0)

        product_name = _get_product_name(dp)

        dp.listen.start("client.action")
        all_btn = dp.ele("css:.all-btn", timeout=6)
        if not all_btn:
            raise RuntimeError("未找到【全部评价】按钮")

        try:
            all_btn.hover()
        except Exception:
            pass
        time.sleep(0.8)
        all_btn.click()

        time.sleep(max(1.5, wait_seconds))
        dp.wait.ele_displayed("css:._rateListContainer_1ygkr_45", timeout=12)
        scroll_container = dp.ele("css:._rateListContainer_1ygkr_45")

        page = 0
        while True:
            if page > 0 and scroll_container:
                time.sleep(1.0)
                scroll_container.scroll.to_bottom()
                time.sleep(max(2.0, wait_seconds))

            resp = dp.listen.wait(timeout=12)
            if not resp or not resp.response or not resp.response.body:
                break

            body = resp.response.body
            comments_data = (((body or {}).get("result") or {}).get("floors") or [])
            if len(comments_data) < 3:
                break

            data_list = (((comments_data[2] or {}).get("data")) or [])
            for item in data_list:
                info = item.get("commentInfo") or {}
                content = (info.get("commentData") or "").strip()
                if not content:
                    continue
                rows.append(
                    {
                        "商品": product_name,
                        "昵称": info.get("userNickName") or "匿名用户",
                        "日期": info.get("commentDate") or "",
                        "评分": info.get("commentScore") or 5,
                        "产品": _clean_variant(info.get("productSpecifications") or ""),
                        "评论": content,
                        "回购次数": info.get("buyCount") or 0,
                    }
                )

            page_info = ((body.get("result") or {}).get("pageInfo") or {}).get("data") or {}
            has_next = bool(page_info.get("hasNextPage", False))
            page += 1
            if not has_next or page >= max_pages:
                break

            dp.listen.clear()
            dp.listen.start("client.action")

        return {
            "productName": product_name,
            "count": len(rows),
            "rows": rows,
        }
    finally:
        try:
            dp.quit()
        except Exception:
            pass


def collect_and_import_jd_comments(
    *,
    item_url: str,
    sku: str,
    product_name: Optional[str] = None,
    is_competitor: bool = False,
    clear_existing: bool = False,
    include_alerts: bool = False,
    max_pages: int = 20,
) -> dict[str, Any]:
    job = CollectJob(
        platform="jd",
        sku=sku,
        product_name=(product_name or None),
        item_url=item_url,
        status="running",
    )
    db.session.add(job)
    db.session.commit()

    try:
        collected = collect_jd_comments(item_url=item_url, max_pages=max_pages)
        final_product_name = (product_name or collected.get("productName") or sku or "").strip() or sku
        imported = import_comment_rows(
            collected.get("rows") or [],
            product_name=final_product_name,
            sku=sku,
            platform="jd",
            is_competitor=is_competitor,
            clear_existing=clear_existing,
            include_alerts=include_alerts,
        )
        job.product_name = final_product_name
        job.status = "success"
        job.total_collected = int(collected.get("count", 0) or 0)
        job.total_imported = int(imported.get("count", 0) or 0)
        from datetime import datetime

        job.finished_at = datetime.utcnow()
        db.session.commit()
        return {
            **imported,
            "jobId": job.id,
            "collectedCount": collected.get("count", 0),
            "productName": final_product_name,
            "itemUrl": item_url,
        }
    except Exception as e:
        from datetime import datetime

        job.status = "failed"
        job.error_message = str(e)[:1000]
        job.finished_at = datetime.utcnow()
        db.session.commit()
        raise
