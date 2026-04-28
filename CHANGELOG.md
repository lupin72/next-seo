# Changelog

All notable changes to Claude Next SEO will be documented in this file.

## [1.1.0] - 2026-04-27

### Added - Google Search Console Integration

#### Image SEO Workflow (`/seo-images-manager`)
- **GSC Integration**: Keyword generation now uses real Search Console query data instead of heuristics
- **Opportunity Scoring**: 0-100 score identifies quick wins based on impressions + CTR + position
- **Intelligent Cache**: 7-day cache system reduces API calls by >90%
- **Quick Win Detection**: Auto-prioritizes keywords in position 11-20 with CTR <2%
- **Real Metrics**: Each keyword proposal includes impressions, clicks, CTR, position from GSC
- **Fallback Support**: Graceful fallback to page context analysis when GSC unavailable

#### Database Schema
- New table `gsc_page_cache` for Search Console data caching
- Extended `image_keywords` table with GSC metrics columns
- Cache status tracking (`valid`, `expired`, `error`)
- TTL configuration per cache entry

#### Configuration
- New `.env` variables for GSC cache control:
  - `GSC_CACHE_TTL_DAYS` (default: 7)
  - `GSC_DATE_RANGE_DAYS` (default: 90)
  - `GSC_MIN_IMPRESSIONS` (default: 10)
  - `GSC_MAX_QUERIES` (default: 50)
  - `GSC_FORCE_REFRESH` (default: false)

#### Scripts
- `scripts/gsc_cache.py` - Cache management
- `scripts/image_seo_planner.py` - GSC-powered keyword generation
- `scripts/image_analyzer.py` - EXIF extraction
- `scripts/image_optimizer.py` - Image optimization
- `scripts/image_uploader.py` - WordPress upload
- `scripts/image_manager.py` - CLI orchestrator
- `scripts/image_db_schema.sql` - Complete database schema

#### Documentation
- `GSC-INTEGRATION.md` - Complete GSC integration guide
- Updated `SKILL.md` with GSC workflow
- Updated `README.md` with v1.1 features

### Changed
- Keyword generation algorithm now prioritizes GSC data over heuristics
- Opportunity scoring replaces basic keyword ranking
- Cache-first approach for page URL queries

### Technical Details
**Algorithm Improvements:**
- **Impressions scoring** (0-40 points): >1000=40, >500=35, >100=25, >50=15
- **CTR scoring** (0-30 points): <1%=30, <2%=20, <3%=10 (lower = more opportunity)
- **Position scoring** (0-30 points): 11-20=30, 6-10=20, 1-5=15 (page 2 = quick win)

**Cache Strategy:**
- SQLite-based with configurable TTL
- Automatic expiry and cleanup (>30 days old)
- Manual invalidation support
- Per-URL caching

---

## [1.0.0] - 2026-04-23

### Initial Release - Next SEO Fork

#### Multi-Client Management
- Client/project organization with SQLite database
- Active project context for auto-saving reports
- Folder structure: `clients/{client}/{project}/`
- Audit history tracking

#### WordPress Integration
- REST API connection with Application Password
- Direct image upload with metadata
- Configuration storage in `.env` (gitignored)

#### Image SEO Workflow
- Incremental analysis (new images only)
- Keyword cannibalization prevention
- Interactive checkpoints (plan + upload)
- Status tracking (pending/planned/optimized/synced)
- WordPress upload automation

#### Core Features
- Based on Claude SEO v1.9.0
- 20+ SEO sub-skills
- PDF report generation
- Google SEO APIs integration

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes

## Links
- [GSC Integration Guide](skills/seo-images-manager/GSC-INTEGRATION.md)
- [Claude SEO (upstream)](https://github.com/AgriciDaniel/claude-seo)
