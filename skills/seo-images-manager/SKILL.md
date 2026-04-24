# SEO Image Manager

## Overview

Complete image SEO optimization workflow with keyword cannibalization prevention, SQLite tracking, and WordPress synchronization.

**Problem Solved:** Managing dozens of images for a blog post is tedious. You need SEO-friendly filenames, alt text, descriptions, and to avoid keyword cannibalization across images. This skill automates the entire workflow from analysis to WordPress upload.

## Use Cases

- Optimize images before publishing blog posts
- Rename images with SEO-friendly filenames based on page context
- Generate alt text, titles, and captions that avoid keyword cannibalization
- Track which images have been uploaded to WordPress (synced vs pending)
- Bulk optimize and upload images from `images/original/` folder

## Workflow

```
images/original/          images/optimized/        WordPress
    |                          |                        |
    | 1. Analyze               |                        |
    | (EXIF, dimensions)       |                        |
    |                          |                        |
    | 2. Plan                  |                        |
    | (keywords, page context) |                        |
    |                          |                        |
    | 3. Rename & Optimize     |                        |
    | (SEO filename, compress) |--------> ✓             |
    |                          |                        |
    | 4. Upload                |                        |
    | (synced = false)         |                 -----> ✓
    |                          |                        |
    | (synced = true)          |                        |
```

## Commands

### `/seo-images-manager analyze`

Scan `images/original/` directory, extract EXIF metadata, save to database.

**Actions:**
- Scans for `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp` files
- Extracts EXIF data (camera, lens, date, GPS, etc.)
- Calculates dimensions, filesize, MIME type
- Saves to SQLite database with `synced = false`
- Updates existing records if file already analyzed

**Output:**
```json
{
  "images_found": 3,
  "images": [
    {
      "id": 1,
      "filename": "IMG_1234.jpg",
      "dimensions": {"width": 3000, "height": 2000},
      "filesize": 2500000,
      "exif": {
        "Make": "Canon",
        "Model": "EOS R5",
        "DateTime": "2026:04:20 14:30:00"
      }
    }
  ]
}
```

**Implementation:**
```bash
python scripts/image_manager.py analyze --project clients/prova/test
```

---

### `/seo-images-manager plan <target-url>`

Analyze target page and propose SEO keywords for each image, checking for cannibalization.

**Arguments:**
- `target-url` (required): URL of page where images will be used

**Actions:**
1. Fetches target page (title, H1, meta description, existing images)
2. Extracts primary keyword from page context
3. For each unsynced image:
   - Generates 5 keyword variants based on filename + page context
   - Checks cannibalization against existing image keywords
   - Checks similarity to page primary keyword (>80% = risk)
   - Proposes SEO filename, alt text, title, caption
4. Returns proposals for user review

**Output:**
```json
{
  "target_url": "https://example.com/blog/post",
  "page_context": {
    "title": "Best Hotels in Rome",
    "h1": "Top 10 Hotels in Rome 2026",
    "primary_keyword": "hotels in rome"
  },
  "images": [
    {
      "image_id": 1,
      "original_filename": "IMG_1234.jpg",
      "keyword_proposals": [
        {
          "keyword": "hotels in rome luxury suite",
          "cannibalization_risk": false,
          "recommended": true
        },
        {
          "keyword": "rome hotels",
          "cannibalization_risk": true,
          "cannibalization_note": "Too similar to primary keyword (90%)"
        }
      ],
      "selected_keyword": "hotels in rome luxury suite",
      "seo_metadata": {
        "filename": "hotels-in-rome-luxury-suite.jpg",
        "alt_text": "Hotels in rome luxury suite - Top 10 Hotels in Rome 2026",
        "title": "Hotels In Rome Luxury Suite",
        "caption": "Hotels in rome luxury suite en Top 10 Hotels in Rome 2026"
      }
    }
  ]
}
```

**Implementation:**
```bash
python scripts/image_manager.py plan \
  --project clients/prova/test \
  --url https://example.com/blog/post
```

---

### `/seo-images-manager rename`

Rename and optimize images based on SEO plan.

**Actions:**
1. Reads images with `seo_filename` but no `optimized_path`
2. For each image:
   - Opens original image
   - Resizes if needed (max 1600px width, maintains aspect ratio)
   - Compresses to quality 85% (progressive JPEG)
   - Saves to `images/optimized/` with SEO filename
   - Records optimization metrics (original size, optimized size, compression ratio)
3. Updates database with `optimized_path`

**Output:**
```json
{
  "processed": 3,
  "results": [
    {
      "image_id": 1,
      "original_filename": "IMG_1234.jpg",
      "seo_filename": "hotels-in-rome-luxury-suite.jpg",
      "original_size": 2500000,
      "optimized_size": 450000,
      "compression_ratio": "82.0%",
      "saved_bytes": 2050000,
      "dimensions": {
        "original": {"width": 3000, "height": 2000},
        "optimized": {"width": 1600, "height": 1067}
      }
    }
  ]
}
```

**Implementation:**
```bash
python scripts/image_manager.py rename --project clients/prova/test
```

---

### `/seo-images-manager upload [--all | --id <id>]`

Upload optimized images to WordPress.

**Arguments:**
- `--all` (optional): Upload all pending images
- `--id <id>` (optional): Upload specific image by database ID

**Actions:**
1. Reads WordPress credentials from `.env`
2. Detects REST API path (`/wp-json/` or `/index.php?rest_route=/`)
3. For each image:
   - Reads optimized file
   - Uploads via WordPress REST API
   - Sets alt text, title, caption
   - Updates database with WordPress media ID and URL
   - Sets `synced = true`

**Output:**
```json
{
  "uploaded": 3,
  "results": [
    {
      "image_id": 1,
      "filename": "hotels-in-rome-luxury-suite.jpg",
      "wordpress_media_id": 123,
      "wordpress_url": "https://example.com/wp-content/uploads/2026/04/hotels-in-rome-luxury-suite.jpg",
      "alt_text": "Hotels in rome luxury suite - Top 10 Hotels in Rome 2026",
      "title": "Hotels In Rome Luxury Suite",
      "caption": "Hotels in rome luxury suite en Top 10 Hotels in Rome 2026"
    }
  ]
}
```

**Implementation:**
```bash
# Upload all pending
python scripts/image_manager.py upload --project clients/prova/test --all

# Upload specific image
python scripts/image_manager.py upload --project clients/prova/test --id 1
```

---

### `/seo-images-manager status`

Show image SEO status for current project.

**Actions:**
- Counts total images, synced, pending
- Lists pending images with details

**Output:**
```json
{
  "total": 10,
  "synced": 7,
  "pending": 3,
  "pending_images": [
    {
      "id": 8,
      "original_filename": "IMG_5678.jpg",
      "seo_filename": "rome-hotel-breakfast.jpg",
      "target_keyword": "rome hotel breakfast",
      "synced": false
    }
  ]
}
```

**Implementation:**
```bash
python scripts/image_manager.py status --project clients/prova/test
```

---

## Database Schema

SQLite database at `clients/{client}/{project}/images/images.db`:

### Table: `images`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| original_filename | TEXT | Original filename from images/original/ |
| original_path | TEXT | Full path to original file |
| seo_filename | TEXT | SEO-friendly filename (generated by planner) |
| optimized_path | TEXT | Path to optimized file in images/optimized/ |
| alt_text | TEXT | Generated alt text |
| title | TEXT | Generated title |
| caption | TEXT | Generated caption |
| description | TEXT | Extended description (optional) |
| target_url | TEXT | Page URL where image will be used |
| target_keyword | TEXT | Selected SEO keyword |
| page_h1 | TEXT | H1 of target page |
| page_title | TEXT | Title of target page |
| page_context | TEXT | JSON string with page metadata |
| dimensions | TEXT | JSON: {"width": 1600, "height": 1066} |
| filesize | INTEGER | Original filesize in bytes |
| mime_type | TEXT | MIME type (image/jpeg, image/png, etc.) |
| exif_data | TEXT | JSON string with EXIF metadata |
| synced | INTEGER | Boolean: 0=false, 1=true |
| wordpress_media_id | INTEGER | WordPress media library ID |
| wordpress_url | TEXT | WordPress media URL |
| uploaded_at | TEXT | ISO timestamp of upload |
| created_at | TEXT | ISO timestamp of creation |
| updated_at | TEXT | ISO timestamp of last update |

### Table: `image_keywords`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| image_id | INTEGER | Foreign key to images.id |
| keyword | TEXT | Keyword variant |
| priority | INTEGER | 1=primary, 2=secondary, etc. |
| search_volume | INTEGER | Monthly search volume (optional) |
| competition | TEXT | low/medium/high |
| cannibalization_risk | INTEGER | Boolean: 0=false, 1=true |
| cannibalization_note | TEXT | Explanation of risk |

### Table: `image_optimizations`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| image_id | INTEGER | Foreign key to images.id |
| original_size | INTEGER | Original filesize in bytes |
| optimized_size | INTEGER | Optimized filesize in bytes |
| compression_ratio | REAL | (original - optimized) / original |
| format_original | TEXT | Original format (JPEG, PNG, etc.) |
| format_optimized | TEXT | Optimized format (JPEG, WebP, etc.) |
| optimized_at | TEXT | ISO timestamp |

---

## Keyword Cannibalization Prevention

The planner checks two types of cannibalization:

### 1. Image Keyword Duplication

**Rule:** No two images should target the exact same keyword.

**Check:**
```python
if keyword in existing_keywords:
    return {"risk": True, "message": "Keyword already used by another image"}
```

**Example:**
- Image 1: `rome hotel lobby`
- Image 2: `rome hotel lobby` ❌ REJECTED (duplicate)

### 2. Primary Keyword Similarity

**Rule:** Image keywords should not be >80% similar to page primary keyword.

**Check:**
```python
similarity = word_overlap(image_keyword, page_primary_keyword)
if similarity > 0.8:
    return {"risk": True, "message": "Too similar to primary keyword"}
```

**Algorithm:** Jaccard similarity (word-level overlap)

**Example:**
- Page primary keyword: `hotels in rome`
- Image keyword: `rome hotels` → 100% similarity ❌ REJECTED
- Image keyword: `hotels in rome luxury suite` → 66% similarity ✓ ACCEPTED

---

## Folder Structure

```
clients/{client-slug}/{project-slug}/
  ├── images/
  │   ├── original/              # Source images (user uploads here)
  │   │   ├── IMG_1234.jpg
  │   │   ├── IMG_5678.jpg
  │   │   └── photo.png
  │   ├── optimized/             # SEO-optimized images (generated)
  │   │   ├── hotels-in-rome-luxury-suite.jpg
  │   │   ├── rome-hotel-breakfast.jpg
  │   │   └── rome-colosseum-view.jpg
  │   └── images.db              # SQLite database
  ├── wordpress/
  │   ├── config.json            # WordPress connection metadata
  │   └── publish-log.json       # Upload history
  └── .env                       # WordPress credentials
```

---

## Integration with WordPress

Requires `/seo-wordpress setup` to be run first.

**.env format:**
```bash
WP_URL=https://example.com
WP_USERNAME=admin
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx
WP_MEDIA_FOLDER=seo-optimized
WP_VERIFY_SSL=true
```

**Upload behavior:**
1. Detects REST API path automatically (`/wp-json/` vs `/index.php?rest_route=/`)
2. Uploads to WordPress Media Library
3. Creates folder `seo-optimized` if `WP_MEDIA_FOLDER` specified
4. Sets alt text, title, caption via API
5. Updates database with WordPress media ID and URL
6. Sets `synced = true`

---

## User Workflow Example

**Scenario:** User has 5 images to optimize for a blog post about Rome hotels.

**Step 1: Upload images**
```bash
# User manually copies images to images/original/
cp ~/Photos/*.jpg clients/prova/test/images/original/
```

**Step 2: Analyze images**
```
/seo-images-manager analyze
```

**Output:**
```
✅ Found 5 images in images/original/

Images analyzed:
  1. IMG_1234.jpg (3000x2000, 2.5 MB)
  2. IMG_5678.jpg (4000x3000, 3.8 MB)
  3. photo_01.png (2400x1600, 1.2 MB)
  4. IMG_9999.jpg (1920x1080, 900 KB)
  5. colosseum.jpg (2560x1440, 1.5 MB)

Database updated: 5 new records
```

**Step 3: Plan SEO metadata**
```
/seo-images-manager plan https://example.com/blog/top-10-hotels-rome
```

**Output:**
```
📊 Page Context
   URL: https://example.com/blog/top-10-hotels-rome
   Title: Best Hotels in Rome 2026 | Travel Guide
   H1: Top 10 Hotels in Rome
   Primary Keyword: hotels in rome

📸 Keyword Proposals

Image 1: IMG_1234.jpg
  ✓ hotels in rome luxury suite (selected)
  ✗ rome hotels (too similar to primary keyword)
  ✓ luxury suite rome

  SEO Metadata:
    Filename: hotels-in-rome-luxury-suite.jpg
    Alt text: Hotels in rome luxury suite - Top 10 Hotels in Rome
    Title: Hotels In Rome Luxury Suite

Image 2: IMG_5678.jpg
  ✓ rome hotel breakfast buffet (selected)
  ✓ italian breakfast rome

  SEO Metadata:
    Filename: rome-hotel-breakfast-buffet.jpg
    Alt text: Rome hotel breakfast buffet - Top 10 Hotels in Rome
    Title: Rome Hotel Breakfast Buffet

[... 3 more images ...]

✅ SEO plan created for 5 images
```

**Step 4: Rename and optimize**
```
/seo-images-manager rename
```

**Output:**
```
⚙️ Optimizing 5 images...

✓ hotels-in-rome-luxury-suite.jpg (3000x2000 → 1600x1067, 2.5 MB → 450 KB, 82% saved)
✓ rome-hotel-breakfast-buffet.jpg (4000x3000 → 1600x1200, 3.8 MB → 520 KB, 86% saved)
✓ rome-hotel-rooftop-terrace.jpg (2400x1600 → 1600x1067, 1.2 MB → 380 KB, 68% saved)
✓ rome-hotel-spa-wellness.jpg (1920x1080 → 1600x900, 900 KB → 320 KB, 64% saved)
✓ rome-colosseum-hotel-view.jpg (2560x1440 → 1600x900, 1.5 MB → 420 KB, 72% saved)

✅ 5 images optimized
   Total saved: 6.83 MB → 2.09 MB (69% reduction)

   Files ready in: clients/prova/test/images/optimized/
```

**Step 5: Upload to WordPress**
```
/seo-images-manager upload --all
```

**Output:**
```
⬆️ Uploading to WordPress...

✓ hotels-in-rome-luxury-suite.jpg → WordPress Media ID: 123
  URL: https://example.com/wp-content/uploads/2026/04/hotels-in-rome-luxury-suite.jpg

✓ rome-hotel-breakfast-buffet.jpg → WordPress Media ID: 124
  URL: https://example.com/wp-content/uploads/2026/04/rome-hotel-breakfast-buffet.jpg

[... 3 more uploads ...]

✅ 5 images uploaded to WordPress
   All images marked as synced ✓
```

**Step 6: Check status**
```
/seo-images-manager status
```

**Output:**
```
📊 Image SEO Status

Total images: 5
Synced: 5 ✓
Pending: 0

All images synced to WordPress ✓
```

---

## Error Handling

| Scenario | Action |
|----------|--------|
| No images in original/ | Return empty list, suggest uploading images |
| Target URL unreachable | Show error, skip planning, allow manual metadata entry |
| WordPress .env missing | Suggest running `/seo-wordpress setup` first |
| WordPress upload failure | Show error details, keep image as `synced = false` for retry |
| Duplicate keyword detected | Flag in proposals, recommend alternative keyword |
| Database locked | Retry with exponential backoff (3 attempts) |

---

## Dependencies

**Python packages:**
```bash
pip install pillow requests beautifulsoup4 python-dotenv
```

**Scripts:**
- `scripts/image_manager.py` - Main CLI
- `scripts/image_analyzer.py` - EXIF extraction
- `scripts/image_seo_planner.py` - Keyword planning
- `scripts/image_optimizer.py` - Image optimization
- `scripts/image_uploader.py` - WordPress upload
- `scripts/image_db_schema.sql` - Database schema

---

## Best Practices

### 1. Image Naming Strategy

**Do:**
- Use descriptive keywords: `rome-hotel-breakfast.jpg`
- Include location modifiers: `luxury-suite-rome-center.jpg`
- Keep under 60 characters
- Use hyphens, not underscores

**Don't:**
- Generic names: `image01.jpg`
- Camera defaults: `IMG_1234.jpg`
- Keyword stuffing: `hotels-rome-best-hotels-luxury-hotels-rome.jpg`

### 2. Alt Text Strategy

**Do:**
- Include target keyword naturally
- Describe what's in the image
- Add context from page: `Rome hotel breakfast buffet - Top 10 Hotels in Rome`

**Don't:**
- Keyword stuffing: `rome hotels best hotels luxury hotels`
- Generic: `Image of hotel`
- Too long (>125 characters)

### 3. Cannibalization Prevention

**Strategy:**
- Each image targets a **unique long-tail variant**
- Avoid >80% similarity to page primary keyword
- Use semantic variations:
  - Image 1: `luxury suite rome`
  - Image 2: `rome hotel breakfast`
  - Image 3: `rooftop terrace rome`

---

## Future Enhancements

### Phase 2: Google Search Console Integration

Fetch actual keyword data from GSC:
- Import GSC query data for target URL
- Suggest keywords based on real search queries
- Prioritize keywords with impressions but low CTR
- Use keyword difficulty and search volume

### Phase 3: Advanced Optimization

- WebP conversion with fallback
- Responsive srcset generation
- Lazy loading HTML snippets
- Image CDN integration
- AVIF support

### Phase 4: Bulk Operations

- Batch rename from CSV
- Bulk update alt text
- WordPress media library sync (download + update)
- Audit existing WordPress images

---

**Version:** 1.0.0
**Last Updated:** 2026-04-24
**Skill Type:** Workflow Automation
**Dependencies:** `pillow`, `requests`, `beautifulsoup4`, `python-dotenv`
