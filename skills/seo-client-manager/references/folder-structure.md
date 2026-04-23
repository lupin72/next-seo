# Client Manager Folder Structure

## Overview

This document describes the complete folder structure created by the SEO Client Manager.

## Repository Root

```
next-seo/
├── .active-project              # Active project context (JSON)
├── clients/                     # Client data (gitignored)
│   ├── .clients.db             # SQLite database
│   └── {client-slug}/          # Individual clients...
└── templates/                   # Templates for CLIENT.md and PROJECT.md
```

## Client Level

Each client gets a dedicated folder:

```
clients/{client-slug}/
├── CLIENT.md                    # Client information and notes
└── {project-slug}/             # Projects for this client...
```

### CLIENT.md Template

```markdown
# {Client Name}

## Contact Information
- **Company:** {Client Name}
- **Contact Person:**
- **Email:**
- **Phone:**
- **Billing Contact:**

## Business Information
- **Industry:**
- **Target Markets:**
- **Main Competitors:**

## Projects
<!-- Auto-populated list of projects -->

## Notes
<!-- Client-specific notes -->
```

## Project Level

Each project gets a complete folder structure:

```
clients/{client-slug}/{project-slug}/
├── PROJECT.md                   # Project configuration
├── reports/                     # SEO audit reports
│   ├── YYYY-MM-DD_technical-audit.md
│   ├── YYYY-MM-DD_technical-audit.pdf
│   ├── YYYY-MM-DD_page-audit.md
│   ├── YYYY-MM-DD_content-audit.md
│   ├── YYYY-MM-DD_schema-audit.md
│   ├── YYYY-MM-DD_local-audit.md
│   ├── YYYY-MM-DD_full-audit.md
│   └── YYYY-MM-DD_drift-report.md
├── images/
│   ├── original/               # Original images (before optimization)
│   │   ├── hero-image.jpg
│   │   └── product-photo.png
│   ├── optimized/              # Optimized images (ready for upload)
│   │   ├── hero-image-optimized.jpg
│   │   └── product-photo-optimized.webp
│   └── metadata.json           # Image optimization history
├── data/
│   ├── baseline.json           # SEO drift baseline
│   ├── audit-history.json      # Historical audit results
│   ├── crux-history.json       # Core Web Vitals trends (CrUX API)
│   ├── backlinks.json          # Backlink profile snapshots
│   └── gsc-data.json           # Google Search Console exports
└── wordpress/
    ├── config.json             # WordPress REST API credentials
    ├── publish-log.json        # Publishing history
    └── .gitkeep
```

### PROJECT.md Template

```markdown
# {Project Name}

## Project Information
- **Client:** {Client Name}
- **URL:** {URL}
- **Industry:**
- **Launch Date:**
- **CMS:**

## SEO Goals
- [ ] Goal 1
- [ ] Goal 2

## WordPress Integration
- **REST API Endpoint:** {url}/wp-json
- **Authentication:** (configured separately)

## Audit History
| Date | Type | Score | Report |
|------|------|-------|--------|
| - | - | - | - |

## Notes
<!-- Project notes -->
```

## Active Project Context

When a project is set as active via `/seo-project set`, a file is created at repo root:

**`.active-project`**
```json
{
  "client": "example-client",
  "client_name": "Example Client",
  "project": "main-site",
  "project_name": "Main Site",
  "url": "https://example.com",
  "path": "clients/example-client/main-site",
  "set_at": "2026-04-23T14:30:00Z"
}
```

This file is read by all SEO skills to determine where to save reports.

## Database Schema

**`clients/.clients.db`** (SQLite)

### Tables

#### `clients`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| slug | TEXT UNIQUE | URL-safe client identifier |
| name | TEXT | Display name |
| created_at | TEXT | ISO 8601 timestamp |
| updated_at | TEXT | ISO 8601 timestamp |

#### `projects`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| client_id | INTEGER | Foreign key to clients.id |
| slug | TEXT | URL-safe project identifier |
| name | TEXT | Display name |
| url | TEXT | Project URL |
| created_at | TEXT | ISO 8601 timestamp |
| updated_at | TEXT | ISO 8601 timestamp |
| last_audit_at | TEXT | Last audit timestamp |

**Unique constraint:** (client_id, slug)

#### `audits`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| project_id | INTEGER | Foreign key to projects.id |
| audit_type | TEXT | Audit type (technical, content, etc) |
| audit_date | TEXT | ISO 8601 timestamp |
| report_path | TEXT | Relative path to report file |
| score | INTEGER | Audit score (0-100) |

#### `active_project`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Always 1 (single row) |
| project_id | INTEGER | Foreign key to projects.id |
| set_at | TEXT | ISO 8601 timestamp |

## Report File Naming

Reports follow a consistent naming pattern:

**Format:** `YYYY-MM-DD_<audit-type>-audit.<ext>`

**Examples:**
- `2026-04-23_technical-audit.md`
- `2026-04-23_technical-audit.pdf`
- `2026-04-23_page-audit.md`
- `2026-04-23_content-audit.md`
- `2026-04-23_full-audit.md`

**Audit types:**
- `technical` - Technical SEO audit (/seo-technical)
- `page` - Single page analysis (/seo-page)
- `content` - Content quality audit (/seo-content)
- `schema` - Structured data audit (/seo-schema)
- `local` - Local SEO audit (/seo-local)
- `full` - Complete site audit (/seo-audit)
- `drift` - SEO drift comparison (/seo-drift compare)

## Image Organization

### `images/original/`
Store source images before optimization:
- High-resolution photos
- Screenshots
- Graphics from design team
- User-uploaded images

### `images/optimized/`
Optimized versions ready for WordPress:
- Format conversion (JPEG → WebP)
- Compression
- Resizing for web
- IPTC/XMP metadata injection

### `images/metadata.json`
Tracks optimization history:

```json
{
  "hero-image.jpg": {
    "original": {
      "path": "original/hero-image.jpg",
      "size": 2458930,
      "width": 3840,
      "height": 2160,
      "format": "JPEG"
    },
    "optimized": {
      "path": "optimized/hero-image-optimized.webp",
      "size": 145678,
      "width": 1920,
      "height": 1080,
      "format": "WebP",
      "quality": 85,
      "optimization_date": "2026-04-23T15:00:00Z"
    },
    "wordpress": {
      "media_id": 456,
      "uploaded_at": "2026-04-23T15:05:00Z",
      "url": "https://example.com/wp-content/uploads/2026/04/hero-image.webp"
    }
  }
}
```

## Data Files

### `data/baseline.json`
SEO drift baseline (created by `/seo-drift baseline`):

```json
{
  "url": "https://example.com",
  "captured_at": "2026-04-23T14:00:00Z",
  "title": "Page Title",
  "meta_description": "Meta description...",
  "canonical": "https://example.com/",
  "h1": ["Main Heading"],
  "structured_data": [...],
  "word_count": 1250
}
```

### `data/crux-history.json`
Core Web Vitals trends (from CrUX API):

```json
{
  "url": "https://example.com",
  "history": [
    {
      "date": "2026-04-23",
      "lcp": {
        "p75": 2.3,
        "category": "GOOD"
      },
      "inp": {
        "p75": 180,
        "category": "GOOD"
      },
      "cls": {
        "p75": 0.08,
        "category": "GOOD"
      }
    }
  ]
}
```

### `data/backlinks.json`
Backlink profile snapshots:

```json
{
  "url": "https://example.com",
  "snapshots": [
    {
      "date": "2026-04-23",
      "total_backlinks": 1250,
      "referring_domains": 85,
      "domain_authority": 42,
      "spam_score": 3,
      "top_backlinks": [...]
    }
  ]
}
```

## WordPress Integration

### `wordpress/config.json`
WordPress REST API credentials (encrypted):

```json
{
  "endpoint": "https://example.com/wp-json",
  "auth_method": "jwt",
  "username": "admin",
  "application_password": "xxxx xxxx xxxx xxxx",
  "media_library_path": "/wp-content/uploads/seo-optimized/"
}
```

### `wordpress/publish-log.json`
Publishing history:

```json
{
  "uploads": [
    {
      "date": "2026-04-23T15:05:00Z",
      "file": "hero-image-optimized.webp",
      "media_id": 456,
      "url": "https://example.com/wp-content/uploads/...",
      "status": "success"
    }
  ]
}
```

## Security & Privacy

### `.gitignore`

The following should be gitignored to protect sensitive data:

```gitignore
# Client data (sensitive)
/clients/*
!/clients/.gitkeep

# Active project (local state)
/.active-project

# WordPress credentials
**/wordpress/config.json

# Backups
*.db-backup
```

### File Permissions

- `clients/.clients.db` → `600` (owner read/write only)
- `wordpress/config.json` → `600` (owner read/write only)
- All other files → `644` (standard)

## Backup Strategy

**Recommended:**
1. Exclude `clients/` from git (already in .gitignore)
2. Backup `clients/.clients.db` daily to secure location
3. Backup client folders to encrypted storage (separate from repo)
4. Use `.db-backup` suffix for database backups (gitignored)

**Backup command:**
```bash
cp clients/.clients.db clients/.clients.db-backup-$(date +%Y%m%d)
tar -czf clients-backup-$(date +%Y%m%d).tar.gz clients/
```

## Scalability

This structure scales to:
- **100+ clients** without performance degradation
- **1000+ projects** (SQLite can handle millions of rows)
- **10,000+ reports** per project
- **100GB+** of images per project

For larger scales, consider:
- PostgreSQL instead of SQLite
- S3/GCS for image storage
- CDN for report delivery
- Separate database server

## Migration Path

To migrate existing reports into this structure:

```bash
# Create client and project
python scripts/client_manager.py add-client --name "Existing Client"
python scripts/client_manager.py add-project \
  --client "existing-client" \
  --name "Migration Project" \
  --url "https://example.com"

# Move reports
mv old-reports/*.md clients/existing-client/migration-project/reports/

# Update audit history
# (TODO: migration script)
```

---

**Last Updated:** 2026-04-23
