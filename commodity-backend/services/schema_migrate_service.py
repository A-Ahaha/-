from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from models import db

logger = logging.getLogger(__name__)


def _has_column(table: str, column: str) -> bool:
    sql = text(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table
          AND COLUMN_NAME = :column
        """
    )
    n = db.session.execute(sql, {"table": table, "column": column}).scalar() or 0
    return int(n) > 0


def _ensure_column(table: str, column: str, ddl_fragment: str):
    if _has_column(table, column):
        return
    logger.warning("DB migrate: add column %s.%s", table, column)
    db.session.execute(text(f"ALTER TABLE `{table}` ADD COLUMN {ddl_fragment}"))


def _ensure_table_collect_jobs():
    # 只在不存在时创建
    sql = text(
        """
        CREATE TABLE IF NOT EXISTS collect_jobs (
          id INT AUTO_INCREMENT PRIMARY KEY,
          platform VARCHAR(32) NOT NULL,
          sku VARCHAR(128) NOT NULL,
          product_name VARCHAR(255) NULL,
          item_url VARCHAR(1024) NULL,
          status VARCHAR(16) NOT NULL DEFAULT 'pending',
          total_collected INT NOT NULL DEFAULT 0,
          total_imported INT NOT NULL DEFAULT 0,
          error_message VARCHAR(1000) NULL,
          started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          finished_at DATETIME NULL,
          INDEX ix_collect_jobs_platform (platform),
          INDEX ix_collect_jobs_sku (sku),
          INDEX ix_collect_jobs_status (status),
          INDEX ix_collect_jobs_started_at (started_at)
        )
        """
    )
    db.session.execute(sql)


def ensure_schema():
    """
    轻量 schema 迁移（无 Alembic）：
    - 只做“缺什么补什么”，避免影响已有数据
    - 主要用于开发/答辩环境快速启动
    """
    try:
        # products: 老库可能缺失的平台/竞品/创建时间字段
        _ensure_column("products", "platform", "`platform` VARCHAR(64) NULL")
        _ensure_column("products", "is_competitor", "`is_competitor` TINYINT(1) NOT NULL DEFAULT 0")
        _ensure_column("products", "created_at", "`created_at` DATETIME NULL DEFAULT CURRENT_TIMESTAMP")

        # system_settings: 基础列（老库可能缺失）
        _ensure_column("system_settings", "collect_frequency_minutes", "`collect_frequency_minutes` INT NOT NULL DEFAULT 30")
        _ensure_column("system_settings", "alert_threshold", "`alert_threshold` INT NOT NULL DEFAULT 50")
        _ensure_column("system_settings", "email_enabled", "`email_enabled` TINYINT(1) NOT NULL DEFAULT 0")
        _ensure_column("system_settings", "email_to", "`email_to` VARCHAR(255) NULL")
        _ensure_column("system_settings", "smtp_host", "`smtp_host` VARCHAR(128) NULL")
        _ensure_column("system_settings", "smtp_port", "`smtp_port` INT NOT NULL DEFAULT 465")
        _ensure_column("system_settings", "smtp_user", "`smtp_user` VARCHAR(128) NULL")
        _ensure_column("system_settings", "smtp_password", "`smtp_password` VARCHAR(255) NULL")
        _ensure_column("system_settings", "smtp_use_ssl", "`smtp_use_ssl` TINYINT(1) NOT NULL DEFAULT 1")
        _ensure_column("system_settings", "webhook_enabled", "`webhook_enabled` TINYINT(1) NOT NULL DEFAULT 0")
        _ensure_column("system_settings", "webhook_url", "`webhook_url` VARCHAR(512) NULL")

        # system_settings: 定时采集配置
        _ensure_column("system_settings", "collect_enabled", "`collect_enabled` TINYINT(1) NOT NULL DEFAULT 0")
        _ensure_column("system_settings", "collect_item_url", "`collect_item_url` VARCHAR(1024) NULL")
        _ensure_column("system_settings", "collect_sku", "`collect_sku` VARCHAR(128) NULL")
        _ensure_column("system_settings", "collect_product_name", "`collect_product_name` VARCHAR(255) NULL")
        _ensure_column("system_settings", "collect_is_competitor", "`collect_is_competitor` TINYINT(1) NOT NULL DEFAULT 0")
        _ensure_column("system_settings", "collect_clear_existing", "`collect_clear_existing` TINYINT(1) NOT NULL DEFAULT 0")
        _ensure_column("system_settings", "collect_include_alerts", "`collect_include_alerts` TINYINT(1) NOT NULL DEFAULT 0")
        _ensure_column("system_settings", "collect_max_pages", "`collect_max_pages` INT NOT NULL DEFAULT 20")

        # comments: 去重字段
        _ensure_column("comments", "source_platform", "`source_platform` VARCHAR(32) NULL")
        _ensure_column("comments", "source_comment_id", "`source_comment_id` VARCHAR(128) NULL")
        _ensure_column("comments", "source_hash", "`source_hash` VARCHAR(64) NULL")
        # comments: 规格/追评/回购等（老库常缺列）
        _ensure_column("comments", "purchase_time", "`purchase_time` DATETIME NULL")
        _ensure_column("comments", "is_append_review", "`is_append_review` TINYINT(1) NOT NULL DEFAULT 0")
        _ensure_column("comments", "repurchase_count", "`repurchase_count` INT NOT NULL DEFAULT 0")
        _ensure_column("comments", "raw_product_variant", "`raw_product_variant` VARCHAR(255) NULL")

        # collect_jobs: 采集任务表
        _ensure_table_collect_jobs()

        db.session.commit()
    except OperationalError as e:
        db.session.rollback()
        logger.error("DB migrate failed: %s", e)
        raise
