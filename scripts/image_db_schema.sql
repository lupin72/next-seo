-- SEO Image Manager Database Schema
-- SQLite database for tracking image SEO optimization and WordPress sync

-- Main images table
CREATE TABLE IF NOT EXISTS images (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER,

  -- File info
  original_filename TEXT NOT NULL,
  original_path TEXT NOT NULL,
  seo_filename TEXT,
  optimized_path TEXT,

  -- SEO metadata
  alt_text TEXT,
  title TEXT,
  caption TEXT,
  description TEXT,

  -- Context
  target_url TEXT,
  target_keyword TEXT,
  page_h1 TEXT,
  page_title TEXT,
  page_context TEXT, -- JSON string

  -- Technical
  dimensions TEXT, -- JSON: {"width": 1600, "height": 1066}
  filesize INTEGER,
  mime_type TEXT,
  exif_data TEXT, -- JSON string

  -- WordPress sync
  synced INTEGER DEFAULT 0, -- BOOLEAN: 0=false, 1=true
  wordpress_media_id INTEGER,
  wordpress_url TEXT,
  uploaded_at TEXT,

  -- Timestamps
  created_at TEXT NOT NULL,
  updated_at TEXT,

  FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Keywords per immagine (evitare cannibalization)
CREATE TABLE IF NOT EXISTS image_keywords (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  image_id INTEGER NOT NULL,
  keyword TEXT NOT NULL,
  priority INTEGER, -- 1=primary, 2=secondary, etc.
  search_volume INTEGER,
  competition TEXT, -- low/medium/high
  cannibalization_risk INTEGER DEFAULT 0, -- BOOLEAN
  cannibalization_note TEXT,

  FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
);

-- Tracking ottimizzazione
CREATE TABLE IF NOT EXISTS image_optimizations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  image_id INTEGER NOT NULL,
  original_size INTEGER,
  optimized_size INTEGER,
  compression_ratio REAL,
  format_original TEXT,
  format_optimized TEXT,
  optimized_at TEXT,

  FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_images_project ON images(project_id);
CREATE INDEX IF NOT EXISTS idx_images_synced ON images(synced);
CREATE INDEX IF NOT EXISTS idx_images_target_url ON images(target_url);
CREATE INDEX IF NOT EXISTS idx_keywords_image ON image_keywords(image_id);
CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON image_keywords(keyword);
