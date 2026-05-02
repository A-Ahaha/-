from __future__ import annotations

import os
import tempfile
from datetime import datetime

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import CollectJob, Comment, Issue, Product, ProductAspectSentiment, SystemLog, SystemSetting, User, db
from utils.decorators import admin_required
from utils.response import err, ok
from utils.security import hash_password

from services.csv_import_service import import_csv, rebuild_for_product
from services.jd_collect_service import collect_and_import_jd_comments
from services.notify_service import send_alert_notifications
from services.scheduler_service import refresh_scheduler
from models import Alert

# bp = Blueprint("admin", __name__, url_prefix="/admin")
bp = Blueprint("admin", __name__)


def to_iso_z(dt):
    if not dt:
        return ""
    s = dt.isoformat()
    if "Z" not in s and "+" not in s and "-" not in s[10:]:
        s = f"{s}Z"
    return s


def log(level: str, message: str):
    db.session.add(SystemLog(level=level, message=(message or "")[:500], created_at=datetime.utcnow()))
    db.session.commit()


@bp.route("/users", methods=["GET"])
@jwt_required()
@admin_required
def list_users():
    keyword = (request.args.get("keyword") or "").strip()
    q = User.query
    if keyword:
        like = f"%{keyword}%"
        q = q.filter((User.username.like(like)) | (User.email.isnot(None) & User.email.like(like)))
    rows = q.order_by(User.id.asc()).all()
    return ok([u.to_public_dict() for u in rows])


@bp.route("/users", methods=["POST"])
@jwt_required()
@admin_required
def create_user():
    payload = request.get_json() or {}
    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip() or None
    role = payload.get("role") or "user"
    status = payload.get("status") or "active"

    if not username:
        return err("用户名不能为空")
    if role not in ("user", "admin"):
        return err("角色无效")
    if status not in ("active", "disabled"):
        return err("状态无效")
    if User.query.filter(User.username == username).first():
        return err("用户名已存在")

    # 前端创建时不传 password，这里给一个默认密码，方便后续登录调试
    password = (payload.get("password") or "123456").strip()

    try:
        user = User(
            username=username,
            email=email,
            phone=(payload.get("phone") or "").strip() or None,
            role=role,
            status=status,
            password_hash=hash_password(password),
        )
        db.session.add(user)
        db.session.commit()
        log("info", f"创建用户：{username}")
        return ok(user.to_public_dict(), "创建成功")
    except Exception as e:
        db.session.rollback()
        return err(f"创建用户失败：{str(e)}", code=500, http_status=500)


@bp.route("/users/<int:user_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return err("用户不存在", code=404, http_status=404)
    payload = request.get_json() or {}

    # 确保所有字段都转换为字符串或 None
    if "email" in payload:
        email = payload.get("email")
        user.email = email.strip() if email and isinstance(email, str) else None
    
    if "status" in payload:
        status = payload.get("status")
        if status not in ("active", "disabled"):
            return err("状态无效")
        user.status = status
    
    if "phone" in payload:
        phone = payload.get("phone")
        user.phone = phone.strip() if phone and isinstance(phone, str) else None
    
    try:
        db.session.commit()
        log("info", f"更新用户：{user.username}")
        return ok(user.to_public_dict())
    except Exception as e:
        db.session.rollback()
        return err(f"更新失败：{str(e)}", code=500, http_status=500)


@bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return err("用户不存在", code=404, http_status=404)

    current_uid = get_jwt_identity()
    if str(current_uid) == str(user_id):
        return err("不能删除当前登录账号", code=400, http_status=400)

    username = user.username
    db.session.delete(user)
    db.session.commit()
    log("warn", f"删除用户：{username}")
    return ok(None, "删除成功")


@bp.route("/users/<int:user_id>/role", methods=["PATCH"])
@jwt_required()
@admin_required
def assign_role(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return err("用户不存在", code=404, http_status=404)

    payload = request.get_json() or {}
    role = payload.get("role")
    if role not in ("user", "admin"):
        return err("角色无效")
    user.role = role
    try:
        db.session.commit()
        log("info", f"分配角色：{user.username} → {role}")
        return ok(user.to_public_dict())
    except Exception as e:
        db.session.rollback()
        return err(f"分配角色失败：{str(e)}", code=500, http_status=500)


@bp.route("/system/config", methods=["GET"])
@jwt_required()
@admin_required
def get_system_config():
    s = SystemSetting.query.first()
    if not s:
        s = SystemSetting()
        db.session.add(s)
        db.session.commit()
    return ok(
        {
            "collectFrequencyMinutes": s.collect_frequency_minutes,
            "collectEnabled": bool(s.collect_enabled),
            "collectItemUrl": s.collect_item_url or "",
            "collectSku": s.collect_sku or "",
            "collectProductName": s.collect_product_name or "",
            "collectIsCompetitor": bool(s.collect_is_competitor),
            "collectClearExisting": bool(s.collect_clear_existing),
            "collectIncludeAlerts": bool(s.collect_include_alerts),
            "collectMaxPages": int(s.collect_max_pages or 20),
            "alertThreshold": s.alert_threshold,
            "emailEnabled": bool(s.email_enabled),
            "emailTo": s.email_to or "",
            "smtpHost": s.smtp_host or "",
            "smtpPort": int(s.smtp_port or 465),
            "smtpUser": s.smtp_user or "",
            "smtpPassword": s.smtp_password or "",
            "smtpUseSsl": bool(s.smtp_use_ssl),
            "webhookEnabled": bool(s.webhook_enabled),
            "webhookUrl": s.webhook_url or "",
        }
    )


@bp.route("/system/config", methods=["PUT"])
@jwt_required()
@admin_required
def put_system_config():
    payload = request.get_json() or {}
    cf = payload.get("collectFrequencyMinutes", None)
    at = payload.get("alertThreshold", None)
    smtp_port = payload.get("smtpPort", None)
    collect_max_pages = payload.get("collectMaxPages", None)

    if cf is not None and int(cf) <= 0:
        return err("采集频率必须大于 0")
    if at is not None:
        at = int(at)
        if at < 1 or at > 100:
            return err("预警阈值需在 1-100 之间")
    if smtp_port is not None and int(smtp_port) <= 0:
        return err("SMTP 端口无效")
    if collect_max_pages is not None and int(collect_max_pages) <= 0:
        return err("采集最大页数必须大于 0")

    s = SystemSetting.query.first()
    if not s:
        s = SystemSetting()
        db.session.add(s)

    if cf is not None:
        s.collect_frequency_minutes = int(cf)
    if "collectEnabled" in payload:
        s.collect_enabled = bool(payload.get("collectEnabled"))
    if "collectItemUrl" in payload:
        s.collect_item_url = (payload.get("collectItemUrl") or "").strip() or None
    if "collectSku" in payload:
        s.collect_sku = (payload.get("collectSku") or "").strip() or None
    if "collectProductName" in payload:
        s.collect_product_name = (payload.get("collectProductName") or "").strip() or None
    if "collectIsCompetitor" in payload:
        s.collect_is_competitor = bool(payload.get("collectIsCompetitor"))
    if "collectClearExisting" in payload:
        s.collect_clear_existing = bool(payload.get("collectClearExisting"))
    if "collectIncludeAlerts" in payload:
        s.collect_include_alerts = bool(payload.get("collectIncludeAlerts"))
    if "collectMaxPages" in payload and collect_max_pages is not None:
        s.collect_max_pages = int(collect_max_pages)
    if at is not None:
        s.alert_threshold = int(at)
    if "emailEnabled" in payload:
        s.email_enabled = bool(payload.get("emailEnabled"))
    if "emailTo" in payload:
        s.email_to = (payload.get("emailTo") or "").strip() or None
    if "smtpHost" in payload:
        s.smtp_host = (payload.get("smtpHost") or "").strip() or None
    if "smtpPort" in payload and smtp_port is not None:
        s.smtp_port = int(smtp_port)
    if "smtpUser" in payload:
        s.smtp_user = (payload.get("smtpUser") or "").strip() or None
    if "smtpPassword" in payload:
        s.smtp_password = (payload.get("smtpPassword") or "").strip() or None
    if "smtpUseSsl" in payload:
        s.smtp_use_ssl = bool(payload.get("smtpUseSsl"))
    if "webhookEnabled" in payload:
        s.webhook_enabled = bool(payload.get("webhookEnabled"))
    if "webhookUrl" in payload:
        s.webhook_url = (payload.get("webhookUrl") or "").strip() or None
    
    try:
        db.session.commit()
        refresh_scheduler(current_app._get_current_object())
        log("info", "更新系统设置")
        return ok(
            {
                "collectFrequencyMinutes": s.collect_frequency_minutes,
                "collectEnabled": bool(s.collect_enabled),
                "collectItemUrl": s.collect_item_url or "",
                "collectSku": s.collect_sku or "",
                "collectProductName": s.collect_product_name or "",
                "collectIsCompetitor": bool(s.collect_is_competitor),
                "collectClearExisting": bool(s.collect_clear_existing),
                "collectIncludeAlerts": bool(s.collect_include_alerts),
                "collectMaxPages": int(s.collect_max_pages or 20),
                "alertThreshold": s.alert_threshold,
                "emailEnabled": bool(s.email_enabled),
                "emailTo": s.email_to or "",
                "smtpHost": s.smtp_host or "",
                "smtpPort": int(s.smtp_port or 465),
                "smtpUser": s.smtp_user or "",
                "smtpPassword": s.smtp_password or "",
                "smtpUseSsl": bool(s.smtp_use_ssl),
                "webhookEnabled": bool(s.webhook_enabled),
                "webhookUrl": s.webhook_url or "",
            }
        )
    except Exception as e:
        db.session.rollback()
        return err(f"更新系统设置失败：{str(e)}", code=500, http_status=500)


@bp.route("/system/logs", methods=["GET"])
@jwt_required()
@admin_required
def system_logs():
    page = request.args.get("page", type=int) or 1
    page_size = request.args.get("pageSize", type=int) or 10
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    q = SystemLog.query.order_by(SystemLog.created_at.desc())
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()

    data = [
        {
            "id": str(r.id),
            "level": r.level,
            "message": r.message,
            "createdAt": to_iso_z(r.created_at),
        }
        for r in rows
    ]
    return ok({"list": data, "total": total})


@bp.route("/products", methods=["GET"])
@jwt_required()
@admin_required
def list_products():
    page = request.args.get("page", type=int) or 1
    page_size = request.args.get("pageSize", type=int) or 10
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    q = Product.query.order_by(Product.id.desc())
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()

    data = [
        {
            "id": str(p.id),
            "sku": p.sku,
            "name": p.name,
            "platform": p.platform,
            "isCompetitor": bool(p.is_competitor),
            "createdAt": to_iso_z(p.created_at),
        }
        for p in rows
    ]
    return ok({"list": data, "total": total})


@bp.route("/products", methods=["POST"])
@jwt_required()
@admin_required
def create_product():
    payload = request.get_json() or {}
    sku = (payload.get("sku") or "").strip()
    name = (payload.get("name") or "").strip()
    platform = (payload.get("platform") or "").strip() or None
    is_competitor = bool(payload.get("isCompetitor", False))

    if not sku or not name:
        return err("SKU 与名称不能为空")
    if Product.query.filter(Product.sku == sku).first():
        return err("SKU 已存在")

    try:
        p = Product(sku=sku, name=name, platform=platform, is_competitor=is_competitor)
        db.session.add(p)
        db.session.commit()
        log("info", f"新增商品：{name} ({sku})")
        return ok(
            {
                "id": str(p.id),
                "sku": p.sku,
                "name": p.name,
                "platform": p.platform,
                "isCompetitor": bool(p.is_competitor),
                "createdAt": to_iso_z(p.created_at),
            },
            "创建成功",
        )
    except Exception as e:
        db.session.rollback()
        return err(f"创建商品失败：{str(e)}", code=500, http_status=500)


@bp.route("/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_product(product_id: int):
    """
    删除商品（含关联数据）：
    - comments / issues / alerts / product_aspect_sentiment / collect_jobs
    由于 alerts.issue_id 外键指向 issues.id，必须先清理 alerts。
    """
    p = Product.query.get(product_id)
    if not p:
        return err("商品不存在", code=404, http_status=404)

    try:
        # 1) alerts -> issues
        issue_ids = [row[0] for row in db.session.query(Issue.id).filter(Issue.product_id == product_id).all()]
        if issue_ids:
            Alert.query.filter(Alert.issue_id.in_(issue_ids)).delete(synchronize_session=False)

        # 2) comments 先断开 issue_id，避免外键约束（若存在）
        Comment.query.filter(Comment.product_id == product_id).update({Comment.issue_id: None}, synchronize_session=False)

        # 3) 删除评论、问题、属性情感
        Comment.query.filter(Comment.product_id == product_id).delete(synchronize_session=False)
        Issue.query.filter(Issue.product_id == product_id).delete(synchronize_session=False)
        ProductAspectSentiment.query.filter(ProductAspectSentiment.product_id == product_id).delete(synchronize_session=False)

        # 4) 删除采集任务记录（按 sku 关联）
        if p.sku:
            CollectJob.query.filter(CollectJob.sku == p.sku).delete(synchronize_session=False)

        # 5) 删除商品
        db.session.delete(p)
        db.session.commit()
        log("warn", f"删除商品：{p.name} ({p.sku}) id={product_id}")
        return ok({"productId": product_id}, "删除成功")
    except Exception as e:
        db.session.rollback()
        return err(f"删除失败：{str(e)}", code=500, http_status=500)


@bp.route("/import-csv", methods=["POST"])
@jwt_required()
@admin_required
def import_csv_api():
    data = request.get_json() or {}

    file_path = data.get("filePath")
    product_name = data.get("productName") or data.get("sku")
    sku = data.get("sku") or product_name
    is_competitor = bool(data.get("isCompetitor", False))
    clear_existing = bool(data.get("clearExisting", False))
    use_transformer = data.get("useTransformer")
    if use_transformer is None:
        use_transformer = bool(current_app.config.get("ABSA_IMPORT_USE_TRANSFORMER", False))
    else:
        use_transformer = bool(use_transformer)

    if not file_path or not sku:
        return err("缺少必要参数")

    result = import_csv(
        file_path,
        product_name,
        sku,
        is_competitor=is_competitor,
        clear_existing=clear_existing,
        use_transformer=use_transformer,
    )
    return ok(result)


@bp.route("/import-csv-upload", methods=["POST"])
@jwt_required()
@admin_required
def import_csv_upload():
    if "file" not in request.files:
        return err("未上传 CSV 文件")

    f = request.files["file"]
    sku = (request.form.get("sku") or "").strip()
    product_name = (request.form.get("productName") or sku).strip()
    if not sku:
        return err("sku 不能为空")

    is_competitor = str(request.form.get("isCompetitor", "false")).lower() in ("1", "true", "yes")
    clear_existing = str(request.form.get("clearExisting", "false")).lower() in ("1", "true", "yes")
    raw_ut = request.form.get("useTransformer")
    if raw_ut is None or raw_ut == "":
        use_transformer = bool(current_app.config.get("ABSA_IMPORT_USE_TRANSFORMER", False))
    else:
        use_transformer = str(raw_ut).lower() in ("1", "true", "yes")

    fd, temp_path = tempfile.mkstemp(prefix="commodity_", suffix=".csv")
    os.close(fd)
    try:
        f.save(temp_path)
        result = import_csv(
            temp_path,
            product_name=product_name,
            sku=sku,
            is_competitor=is_competitor,
            clear_existing=clear_existing,
            use_transformer=use_transformer,
        )
        log("info", f"导入CSV成功：{sku}，条数={result.get('count', 0)}")
        return ok(result, "导入完成")
    except Exception as e:
        db.session.rollback()
        return err(f"导入失败：{str(e)}", code=500, http_status=500)
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass


@bp.route("/system/test-notify", methods=["POST"])
@jwt_required()
@admin_required
def test_notify():
    s = SystemSetting.query.first()
    if not s:
        s = SystemSetting()
        db.session.add(s)
        db.session.commit()

    demo_alert = Alert(issue_name="测试预警", rule="手动测试发送", status="pending")
    result = send_alert_notifications(demo_alert, s)
    log("info", f"测试通知发送：{result}")
    return ok(result)


@bp.route("/products/<int:product_id>/rebuild-absa", methods=["POST"])
@jwt_required()
@admin_required
def rebuild_absa(product_id: int):
    payload = request.get_json() or {}
    include_alerts = str(payload.get("includeAlerts", False)).lower() in ("1", "true", "yes")
    result = rebuild_for_product(product_id, include_alerts=include_alerts)
    if result.get("error") == "product_not_found":
        return err("商品不存在", code=404, http_status=404)
    log("info", f"重建 ABSA 聚合：product_id={product_id}, include_alerts={include_alerts}")
    return ok(result, "重建完成")


@bp.route("/collect/jd", methods=["POST"])
@jwt_required()
@admin_required
def collect_jd():
    payload = request.get_json() or {}
    item_url = (payload.get("itemUrl") or "").strip()
    sku = (payload.get("sku") or "").strip()
    product_name = (payload.get("productName") or "").strip() or None
    is_competitor = bool(payload.get("isCompetitor", False))
    clear_existing = bool(payload.get("clearExisting", False))
    include_alerts = bool(payload.get("includeAlerts", False))
    max_pages = int(payload.get("maxPages", 20) or 20)

    if not item_url or not sku:
        return err("itemUrl 与 sku 不能为空")

    try:
        result = collect_and_import_jd_comments(
            item_url=item_url,
            sku=sku,
            product_name=product_name,
            is_competitor=is_competitor,
            clear_existing=clear_existing,
            include_alerts=include_alerts,
            max_pages=max_pages,
        )
        log("info", f"京东采集完成：sku={sku}, count={result.get('count', 0)}")
        return ok(result, "采集并导入完成")
    except Exception as e:
        db.session.rollback()
        return err(f"京东采集失败：{str(e)}", code=500, http_status=500)


@bp.route("/collect/jobs", methods=["GET"])
@jwt_required()
@admin_required
def list_collect_jobs():
    page = request.args.get("page", type=int) or 1
    page_size = request.args.get("pageSize", type=int) or 10
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    q = CollectJob.query.order_by(CollectJob.started_at.desc(), CollectJob.id.desc())
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()

    data = [
        {
            "id": str(r.id),
            "platform": r.platform,
            "sku": r.sku,
            "productName": r.product_name or "",
            "itemUrl": r.item_url or "",
            "status": r.status,
            "totalCollected": int(r.total_collected or 0),
            "totalImported": int(r.total_imported or 0),
            "errorMessage": r.error_message or "",
            "startedAt": to_iso_z(r.started_at),
            "finishedAt": to_iso_z(r.finished_at),
        }
        for r in rows
    ]
    return ok({"list": data, "total": total})