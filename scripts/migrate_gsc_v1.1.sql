-- Migration script for v1.1 GSC integration
-- Adds GSC columns to existing image_keywords table

-- Add GSC metrics columns to image_keywords table
ALTER TABLE image_keywords ADD COLUMN gsc_impressions INTEGER;
ALTER TABLE image_keywords ADD COLUMN gsc_clicks INTEGER;
ALTER TABLE image_keywords ADD COLUMN gsc_ctr REAL;
ALTER TABLE image_keywords ADD COLUMN gsc_position REAL;
ALTER TABLE image_keywords ADD COLUMN opportunity_score INTEGER;

-- GSC page cache table is created automatically by gsc_cache.py
-- No manual migration needed
