ALTER TABLE comments
  ADD COLUMN source_platform VARCHAR(32) NULL,
  ADD COLUMN source_comment_id VARCHAR(128) NULL,
  ADD COLUMN source_hash VARCHAR(64) NULL;

CREATE INDEX ix_comments_source_platform ON comments (source_platform);
CREATE INDEX ix_comments_source_comment_id ON comments (source_comment_id);
CREATE INDEX ix_comments_source_hash ON comments (source_hash);

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
);
