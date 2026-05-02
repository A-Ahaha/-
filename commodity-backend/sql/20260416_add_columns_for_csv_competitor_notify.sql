-- 适用数据库：commodity_quality（MySQL 8.x）
-- 用途：补齐本次功能新增字段（CSV接入/竞品分析/通知配置）
-- 执行方式（示例）：
--   mysql -h127.0.0.1 -uroot -proot commodity_quality < 20260416_add_columns_for_csv_competitor_notify.sql

USE commodity_quality;

-- products: 竞品标记
ALTER TABLE products
  ADD COLUMN IF NOT EXISTS is_competitor TINYINT(1) NOT NULL DEFAULT 0,
  ADD INDEX IF NOT EXISTS idx_products_is_competitor (is_competitor);

-- comments: 回购次数、原始规格字段
ALTER TABLE comments
  ADD COLUMN IF NOT EXISTS repurchase_count INT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS raw_product_variant VARCHAR(255) NULL;

-- system_settings: 通知配置
ALTER TABLE system_settings
  ADD COLUMN IF NOT EXISTS email_enabled TINYINT(1) NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS email_to VARCHAR(255) NULL,
  ADD COLUMN IF NOT EXISTS smtp_host VARCHAR(128) NULL,
  ADD COLUMN IF NOT EXISTS smtp_port INT NULL DEFAULT 465,
  ADD COLUMN IF NOT EXISTS smtp_user VARCHAR(128) NULL,
  ADD COLUMN IF NOT EXISTS smtp_password VARCHAR(255) NULL,
  ADD COLUMN IF NOT EXISTS smtp_use_ssl TINYINT(1) NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS webhook_enabled TINYINT(1) NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS webhook_url VARCHAR(512) NULL;

