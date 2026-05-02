ALTER TABLE system_settings
  ADD COLUMN collect_enabled TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN collect_item_url VARCHAR(1024) NULL,
  ADD COLUMN collect_sku VARCHAR(128) NULL,
  ADD COLUMN collect_product_name VARCHAR(255) NULL,
  ADD COLUMN collect_is_competitor TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN collect_clear_existing TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN collect_include_alerts TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN collect_max_pages INT NOT NULL DEFAULT 20;
