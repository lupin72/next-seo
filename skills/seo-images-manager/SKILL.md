# SEO Image Manager

## Overview

Complete image SEO optimization workflow with **Google Search Console integration** (v1.1), **subfolder context** (v1.2), **project specs integration** (v1.2), **interactive questions** (v1.3), **GSC Image search** (v1.3), **multilingual support** (v1.3), **visual AI analysis** (v1.3), **competitor discovery** (v1.3), **global rules system** (v1.4), and **keyword scoring system** (v1.5).

**Problem Solved:** Managing dozens of images for a blog post is tedious. You need SEO-friendly filenames, alt text, descriptions, and to avoid keyword cannibalization across images. This skill automates the entire workflow from analysis to WordPress upload.

**v1.5 Features (NEW - hotel-image-seo.skill inspired):**
- 📊 **3-Variant Keyword Scoring**: Proposes 3 keyword options per image with scoring
  - **Opportunity (1-10)**: Search volume potential from GSC data + context relevance
  - **Gap (1-10)**: Competitor weakness exploitation + unique features
  - **SEO (1-10)**: Keyword structure quality + SEO best practices
- 📁 **Folder-Based Context**: No more target_url! Context determined by subfolder name
  - Images in `original/Piscina Hotel/` → "Piscina Hotel" becomes primary context
  - Combined with PROJECT.md brand context for richer keyword generation
- 🎯 **Domain-Level GSC**: Queries Google Search Console on domain, not specific page
- ✅ **Human Selection**: Choose best keyword variant from 3 scored options

**v1.3 Features (NEW):**
- 🤖 **Interactive Questions**: Skill asks 3 questions at start of plan:
  - "Analizzare i competitor?" (analyze competitor GSC image queries)
  - "Fare analisi visiva delle immagini?" (AI visual descriptions)
  - "Lingua target per metadata?" (target language for alt text/title/caption)
- 🖼️ **GSC Image Search**: Queries Google Search Console with `search_type='image'` in addition to `web`
- 🌍 **Multilingual Metadata**: Generates alt text, captions in target language (es, it, en, fr, de, pt, nl)
- 👁️ **Visual Context**: AI describes image content (e.g. "children playing in hotel pool") for richer keywords
- 🔍 **Competitor Analysis**: Analyzes competitor domains via GSC image queries for keyword discovery

**v1.2 Features:**
- 📁 **Subfolder Context**: Images in `original/SPA Hotel/` use "SPA Hotel" as semantic context to filter GSC keywords
- 📋 **Project Specs**: Reads tone of voice, competitors, focus keywords from PROJECT.md
- 🎯 **Context + GSC Combined**: Subfolder name guides GSC keyword selection (context-relevant queries get +15 boost)
- 🔤 **Tone-aware Alt Text**: Alt text style adapts to brand tone (formal, luxury, conversational)

**v1.1 Features:**
- 🔍 **Search Console Integration**: Uses real GSC query data instead of heuristics
- 📊 **Opportunity Scoring**: 0-100 score prioritizes quick wins (high impressions + low CTR + page 2 position)
- ⚡ **Intelligent Cache**: 7-day cache reduces API calls by >90%
- 🎯 **Quick Wins Detection**: Auto-identifies keywords in position 11-20 with low CTR

See [GSC-INTEGRATION.md](GSC-INTEGRATION.md) for technical details.

## Use Cases

- Optimize images before publishing blog posts
- Rename images with SEO-friendly filenames based on page context
- Generate alt text, titles, and captions that avoid keyword cannibalization
- Track which images have been uploaded to WordPress (synced vs pending)
- Bulk optimize and upload images from `images/original/` folder

## Global Rules System (v1.4)

**NEW in v1.4:** SEO image optimization now follows a **two-tier rules system**:

### 1. Global Rules (Base Layer)

Located in `skills/seo-images-manager/references/seo-rules.md`, these apply to **ALL projects** and include:

- **File Naming Conventions**: Lowercase, hyphens, max 5-7 words, `.webp` preferred
- **Structure Pattern**: `[subject]-[qualifier]-[location/brand].webp`
- **Anti-Cannibalization Rules**: No duplicate keywords, synonym strategies by language
- **Alt Text Guidelines**: Max 125 chars, descriptive, one keyword, no "Image of" prefix
- **Title Attribute**: 3-8 words, complementary to alt text
- **Caption Guidelines**: User-facing, natural, CTA-friendly
- **WordPress Implementation**: Upload checklist, SEO plugin integration, performance optimization

**Industry-Specific Patterns:**
- Hospitality: `[amenity]-[feature]-[hotel-name]-[location].webp`
- E-commerce: `[product]-[variant]-[brand]-[color/size].webp`
- Real Estate: `[property-type]-[rooms]-[location]-[feature].webp`
- Blog/Content: `[topic]-[subtopic]-[year/context].webp`

### 2. Project Overrides (PROJECT.md)

Each project can override global rules in its `PROJECT.md` file under:

```markdown
## Image SEO Overrides

### Naming Convention Overrides
- Max 3-4 words (shorter than global 5-7)
- Always include brand name at end

### Alt Text Overrides
- Max 100 characters (shorter than global 125)
- Always include year for blog posts

### Language-Specific Rules
- **Primary Language:** es
- **Secondary Language:** en
- **Tertiary Language:** fr
```

### How Rules Are Applied

During `/seo-images-manager plan`:

1. **Load Global Rules** from `references/seo-rules.md`
2. **Load Project Specs** from `clients/{client}/{project}/PROJECT.md`
3. **Merge Rules** with PROJECT.md overrides taking priority
4. **Generate Metadata** using merged rules:
   - Alt text max length: PROJECT.md override OR global default (125)
   - Filename max words: PROJECT.md override OR global default (5-7)
   - Language: PROJECT.md override OR `--language` flag OR auto-detect

**Example Merge:**
```python
# Global rule: max_alt_text_chars = 125
# PROJECT.md override: max_alt_text_chars = 100
# Final applied rule: 100 characters
```

### Rule Priority Chain

```
PROJECT.md Overrides > CLI Flags > Project Specs > Global Rules
```

**Example:**
- Global rule: Max 125 chars
- PROJECT.md: Max 100 chars
- CLI flag: `--language it`
- Result: Alt text in Italian, max 100 chars

### Benefits

✅ **Consistency**: Global rules ensure baseline quality across all projects
✅ **Flexibility**: Per-project overrides for special requirements
✅ **Maintainability**: Update global rules once, affects all projects
✅ **Industry Templates**: Pre-defined patterns for common industries
✅ **Multi-Language Support**: Language-specific synonym strategies built-in

### Reference Files

- **Global Rules**: `skills/seo-images-manager/references/seo-rules.md` (v1.0)
- **Project Template**: `scripts/client_manager.py` (creates PROJECT.md with override sections)
- **Implementation**: `scripts/image_seo_planner.py` (_load_global_rules, _merge_rules methods)

---

## Workflow (v1.3 Interactive)

```
images/original/          images/optimized/        WordPress
    |                          |                        |
    | 0. Interactive Setup     |                        |
    | ❓ Analizzare competitor?|                        |
    | ❓ Analisi visiva?       |                        |
    | ❓ Lingua target?        |                        |
    |                          |                        |
    | 1. Analyze               |                        |
    | (EXIF, dimensions)       |                        |
    | + Visual AI (optional)   |                        |
    | INCREMENTAL ✓            |                        |
    |                          |                        |
    | 2. Plan                  |                        |
    | ┌─ GSC Cache Check       |                        |
    | │  (web + image types)   |                        |
    | ├─ Competitor GSC (opt)  |                        |
    | ├─ Visual Context (opt)  |                        |
    | ├─ Opportunity Score     |                        |
    | │  (0-100, +5 image)     |                        |
    | └─ Cannibalization       |                        |
    | 🔘 CHECKPOINT #1         |                        |
    |                          |                        |
    | 3. Rename & Optimize     |                        |
    | (SEO filename, compress) |--------> ✓             |
    |                          |                        |
    | 4. Upload                |                        |
    | 🔘 CHECKPOINT #2 ⚠️      |                 -----> ✓
    | (OBBLIGATORIO)           |                        |
    |                          |                        |
    | (synced = true)          |                        |
```

**Key Features:**
- ✅ **Interactive Questions**: 3 questions before plan (competitor, visual, language)
- ✅ **Incremental Analysis**: Scans ONLY new images not yet in database
- ✅ **Interactive Checkpoints**: User confirms selections via checkbox at key stages
- ✅ **Keyword Cannibalization**: Automatic detection and prevention
- ✅ **WordPress Integration**: Direct upload with metadata sync
- ✅ **Multilingual**: Generates metadata in target language

---

## Interactive Checkpoints

This skill uses **interactive checkpoints** to give you full control over which images to process at each stage.

### Checkpoint #1: After Plan (Keyword Selection)

**When:** After `/seo-images-manager plan <url>` generates keyword proposals

**Purpose:** Select which images to optimize with the proposed keywords

**UI:** Multi-select checkbox with:
- Image ID and original filename
- Proposed SEO filename
- Target keyword
- Alt text preview
- ⚠️ Cannibalization warnings

**Action:** System saves SEO metadata ONLY for selected images

**Example:**
```
🔘 Quali immagini vuoi ottimizzare?

☑ ID 1: IMG_1234.jpg → hotels-in-rome-luxury-suite.jpg
  Keyword: hotels in rome luxury suite

☐ ID 3: photo_01.png → rome-hotel-rooftop.jpg
  Keyword: rome hotel rooftop ⚠️ Low quality

[Conferma: 4/5 images selected]
```

---

### Checkpoint #2: Before Upload (OBBLIGATORIO)

**When:** ALWAYS before `/seo-images-manager upload`

**Purpose:** Confirm WordPress upload to prevent accidental uploads

**UI:** Multi-select checkbox with:
- WordPress URL and media folder
- Image filename and size
- Alt text that will be set
- Upload confirmation

**Action:** Upload proceeds ONLY for confirmed images

**Example:**
```
⚠️ CONFERMA UPLOAD SU WORDPRESS

WordPress: https://example.com
Folder: seo-optimized/

🔘 Confermi l'upload?

☑ ID 1: hotels-in-rome-luxury-suite.jpg | 450 KB
  Alt: Hotels in rome luxury suite - Top 10...

[Conferma: 3/4 images]
```

---

**Implementation Details:** See [UX-CHECKPOINTS.md](UX-CHECKPOINTS.md) for complete checkpoint implementation guide.

---

## Commands

### `/seo-images-manager analyze [--visual]`

Scan `images/original/` directory **and all subdirectories**, extract EXIF metadata, save to database.

**v1.3: Visual Analysis Option** — Use `--visual` flag to mark images for AI visual description.

**Subfolder Context (v1.2):**

Images can be organized in subdirectories of `original/`. The subdirectory name becomes the **semantic context** for the image, used during planning to filter and prioritize relevant GSC keywords.

```
images/original/
  ├── IMG_0001.jpg                    # No context (root)
  ├── SPA Hotel/                      # Context: "SPA Hotel"
  │   ├── IMG_0002.jpg
  │   └── IMG_0003.jpg
  ├── Animazione infantile/           # Context: "Animazione infantile"
  │   └── IMG_0004.jpg
  └── Ristorante/                     # Context: "Ristorante"
      ├── IMG_0005.jpg
      └── IMG_0006.jpg
```

**Actions:**
- Scans recursively for `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp` files
- Extracts subfolder name as `image_context` (e.g. "SPA Hotel")
- Extracts EXIF data (camera, lens, date, GPS, etc.)
- Calculates dimensions, filesize, MIME type
- **NEW v1.3**: If `--visual` flag set, marks images for visual analysis
  - Actual AI descriptions generated during `plan` command
  - Uses Claude's vision via Read tool
  - Stores in `visual_context` column (e.g. "children playing in pool with water slides")
- Saves to SQLite database with `synced = false`, `image_context`, `visual_context`
- Updates existing records if file already analyzed

**Note:** Analysis is **incremental** - only scans images not yet in database.

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

**Note:** Analysis is **incremental** - only scans images not yet in database.

---

### `/seo-images-manager list [--filter <status>]`

List all images with status badges for visual inspection.

**Arguments:**
- `--filter` (optional): Filter by status
  - `pending`: Images analyzed but not planned
  - `planned`: Images with keywords but not optimized
  - `optimized`: Images optimized but not uploaded
  - `synced`: Images already uploaded to WordPress
  - `all`: All images (default)

**Output:**
```
📊 Immagini da pianificare

📸 ID 1 | IMG_1234.jpg | 2.5 MB
📸 ID 2 | IMG_5678.jpg | 3.8 MB
📝 ID 3 | rome-hotel.jpg | KW: rome hotel breakfast
⚙️ ID 4 | hotels-rome.jpg | 450 KB | KW: hotels in rome
✅ ID 5 | colosseum.jpg | WP #123 | KW: rome colosseum

Total: 5 images
```

**Status Badges:**
- 📸 **Pending**: Not yet planned
- 📝 **Planned**: Keywords assigned, ready for optimization
- ⚙️ **Optimized**: File optimized, ready for upload
- ✅ **Synced**: Uploaded to WordPress

**Implementation:**
```bash
python scripts/image_manager.py list --project clients/prova/test --filter pending
```

**Use Cases:**
- Check which images are ready for planning
- Verify optimized images before upload
- Inspect synced images with WordPress Media IDs
- Quick status overview at any stage

---

### `/seo-images-manager plan [options]`

Generate 3 scored keyword variants per image for human selection.

**v1.5: Scoring System** — Proposes exactly 3 keyword variants per image with:
- **Opportunity Score (1-10)**: Search volume potential + context relevance
- **Gap Score (1-10)**: Competitor weakness exploitation + unique features
- **SEO Score (1-10)**: Keyword structure quality + best practices
- **Average Score**: Mean of the 3 scores for quick comparison

**Arguments:**
- `--ids` (optional): Process only specific image IDs (comma-separated)
- `--language <lang>` (optional): Target language (es, it, en, fr, de, pt, nl)
- `--competitors` (optional): Analyze competitor domains via GSC image queries
- `--force-refresh` (optional): Force fresh GSC API call (bypass cache)

**Context Sources:**
1. **Subfolder Name**: Primary context (e.g., `original/Piscina Hotel/` → "Piscina Hotel")
2. **PROJECT.md**: Brand context, focus keywords, competitor analysis
3. **GSC Data**: Optional domain-level search queries (web + image)
4. **seo-rules.md**: Global naming patterns + synonym strategies

**Actions:**
1. Reads site_url from PROJECT.md
2. Fetches GSC data on domain (optional):
   - `search_type='web'` (standard web queries)
   - `search_type='image'` (Google Images queries)
   - Competitor domains (if --competitors flag set)
3. For each image:
   - Reads subfolder context (e.g., "SPA Hotel")
   - Reads visual context if available (AI description)
   - Generates 3 keyword variants:
     - Variant 1: Context + focus keyword
     - Variant 2: Context + GSC query (if available)
     - Variant 3: Context + synonym variation
   - Scores each variant (Opportunity, Gap, SEO)
   - Checks cannibalization
4. **🔘 CHECKPOINT**: User selects best variant for each image
5. Generates full metadata (alt text, title, caption) for selected variant

**Output:**
```json
{
  "site_url": "https://hotelacuazul.com",
  "site_context": {
    "project_specs": {
      "industry": "Hospitality",
      "focus_keywords": ["hotel familiar peniscola", "hotel playa"]
    }
  },
  "images": [
    {
      "image_id": 1,
      "original_filename": "IMG_1234.jpg",
      "image_context": "Piscina Hotel",
      "variants": [
        {
          "rank": 1,
          "keyword": "piscina-hotel-acuazul-peniscola",
          "filename": "piscina-hotel-acuazul-peniscola.jpg",
          "opportunity_score": 8,
          "gap_score": 7,
          "seo_score": 9,
          "avg_score": 8.0,
          "cannibalization_risk": false
        },
        {
          "rank": 2,
          "keyword": "piscina-exterior-hotel-familiar",
          "filename": "piscina-exterior-hotel-familiar.jpg",
          "opportunity_score": 7,
          "gap_score": 8,
          "seo_score": 7,
          "avg_score": 7.3,
          "cannibalization_risk": false
        },
        {
          "rank": 3,
          "keyword": "zona-bano-hotel-peniscola",
          "filename": "zona-bano-hotel-peniscola.jpg",
          "opportunity_score": 6,
          "gap_score": 6,
          "seo_score": 8,
          "avg_score": 6.7,
          "cannibalization_risk": false
        }
      ],
      "gsc_powered": true,
      "language": "es"
    }
  ],
  "total": 1,
  "gsc_sources": {
    "web": true,
    "image": true,
    "competitors": 0
  }
}
```

**Implementation:**
```bash
# Plan all pending images
python scripts/image_manager.py plan --project clients/prova/test

# Plan specific images with language
python scripts/image_manager.py plan \
  --project clients/prova/test \
  --ids 1,2,5 \
  --language es

# Plan with competitor analysis
python scripts/image_manager.py plan \
  --project clients/prova/test \
  --competitors
```

**Human Selection Workflow:**
After seeing the 3 scored variants, you'll choose the best one for each image. The skill will then generate full SEO metadata (alt text, title, caption) for your selected variant and save it to the database.

---

### `/seo-images-manager rename [--ids <id1,id2,id3>]`

Rename and optimize images based on SEO plan.

**Arguments:**
- `--ids` (optional): Process only specific image IDs (comma-separated)

**Actions:**
1. Reads images with `seo_filename` but no `optimized_path` (or specified via --ids)
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
# Rename all planned images
python scripts/image_manager.py rename --project clients/prova/test

# Rename only specific images
python scripts/image_manager.py rename --project clients/prova/test --ids 1,2,4
```

---

### `/seo-images-manager upload [--all | --id <id> | --ids <id1,id2,id3>]`

Upload optimized images to WordPress with **mandatory confirmation checkpoint**.

**Arguments:**
- `--all` (optional): Show all pending images for selection
- `--id <id>` (optional): Upload specific image by database ID
- `--ids <id1,id2,id3>` (optional): Show specific images for selection

**Actions:**
1. Reads WordPress credentials from `.env`
2. Detects REST API path (`/wp-json/` or `/index.php?rest_route=/`)
3. **🔘 CHECKPOINT #2 (OBBLIGATORIO)**: Shows confirmation with:
   - WordPress URL and media folder
   - List of images with size and alt text
   - Multi-select checkbox for confirmation
4. For each CONFIRMED image:
   - Reads optimized file
   - Uploads via WordPress REST API
   - Sets alt text, title, caption
   - Updates database with WordPress media ID and URL
   - Sets `synced = true`
5. Tracks skipped images for later upload

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
# Show all pending for confirmation
python scripts/image_manager.py upload --project clients/prova/test --all

# Show specific image for confirmation
python scripts/image_manager.py upload --project clients/prova/test --id 1

# Show multiple specific images for confirmation
python scripts/image_manager.py upload --project clients/prova/test --ids 1,2,4
```

**⚠️ Important:** Upload ALWAYS requires user confirmation via checkbox, even when using `--all` or `--id`. This prevents accidental uploads to WordPress.

**Checkpoint Behavior:**
After showing the list of images ready for upload, skill will use `AskUserQuestion` to confirm WordPress upload. User can deselect images from the confirmation dialog. See [UX-CHECKPOINTS.md](UX-CHECKPOINTS.md) for details.

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
| image_context | TEXT | Subfolder name providing semantic context (e.g. "SPA Hotel") |
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
  ├── PROJECT.md                 # SEO specs (tone, competitors, keywords)
  ├── images/
  │   ├── original/              # Source images (user uploads here)
  │   │   ├── IMG_0001.jpg       # Root: no context
  │   │   ├── SPA Hotel/         # Subfolder = context "SPA Hotel"
  │   │   │   ├── IMG_0002.jpg
  │   │   │   └── IMG_0003.jpg
  │   │   ├── Ristorante/        # Subfolder = context "Ristorante"
  │   │   │   └── IMG_0004.jpg
  │   │   └── Animazione/        # Subfolder = context "Animazione"
  │   │       └── IMG_0005.jpg
  │   ├── optimized/             # SEO-optimized images (generated)
  │   │   ├── hotel-spa-wellness-centro.jpg
  │   │   ├── ristorante-colazione-buffet.jpg
  │   │   └── animazione-bambini-piscina.jpg
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

## User Workflow Example (with Checkpoints)

**Scenario:** User has 5 images to optimize for a blog post about Rome hotels.

**Step 1: Upload images**
```bash
# User manually copies images to images/original/
cp ~/Photos/*.jpg clients/prova/test/images/original/
```

**Step 2: Analyze images (INCREMENTAL)**
```
/seo-images-manager analyze
```

**Output:**
```
🔍 Scanning images/original/...

✅ Found 5 NEW images (5 total in database)

New images:
  1. IMG_1234.jpg (3000x2000, 2.5 MB)
  2. IMG_5678.jpg (4000x3000, 3.8 MB)
  3. photo_01.png (2400x1600, 1.2 MB)
  4. IMG_9999.jpg (1920x1080, 900 KB)
  5. colosseum.jpg (2560x1440, 1.5 MB)

Database updated: 5 new records
```

**Step 3: Review pending images (optional)**
```
/seo-images-manager list --filter pending
```

**Output:**
```
📊 Immagini da pianificare

📸 ID 1 | IMG_1234.jpg | 2.5 MB
📸 ID 2 | IMG_5678.jpg | 3.8 MB
📸 ID 3 | photo_01.png | 1.2 MB
📸 ID 4 | IMG_9999.jpg | 900 KB
📸 ID 5 | colosseum.jpg | 1.5 MB

Total: 5 images
```

**Step 4: Plan SEO metadata**
```
/seo-images-manager plan https://example.com/blog/top-10-hotels-rome
```

**Output with CHECKPOINT #1:**
```
📊 Page Context
   URL: https://example.com/blog/top-10-hotels-rome
   Title: Best Hotels in Rome 2026 | Travel Guide
   H1: Top 10 Hotels in Rome
   Primary Keyword: hotels in rome

📸 Keyword Proposals

Image 1: IMG_1234.jpg
  ✓ hotels in rome luxury suite (RECOMMENDED)
  ✗ rome hotels (too similar to primary - 100%)

  SEO Metadata:
    Filename: hotels-in-rome-luxury-suite.jpg
    Alt: Hotels in rome luxury suite - Top 10 Hotels in Rome

Image 2: IMG_5678.jpg
  ✓ rome hotel breakfast buffet (RECOMMENDED)

  SEO Metadata:
    Filename: rome-hotel-breakfast-buffet.jpg
    Alt: Rome hotel breakfast buffet - Top 10 Hotels in Rome

[... Images 3, 4, 5 ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔘 CHECKPOINT: Quali immagini vuoi ottimizzare?

☑ ID 1: IMG_1234.jpg → hotels-in-rome-luxury-suite.jpg
  Keyword: hotels in rome luxury suite

☑ ID 2: IMG_5678.jpg → rome-hotel-breakfast-buffet.jpg
  Keyword: rome hotel breakfast buffet

☐ ID 3: photo_01.png → rome-hotel-rooftop.jpg
  ⚠️ Low quality image

☑ ID 4: IMG_9999.jpg → rome-hotel-spa-wellness.jpg
  Keyword: rome hotel spa wellness

☑ ID 5: colosseum.jpg → rome-colosseum-hotel-view.jpg
  Keyword: rome colosseum hotel view

[Conferma selezione: 4/5]
```

**User selects 4/5 images (skips ID 3 for low quality):**

```
✅ SEO plan saved for 4 images
⏭️ Skipped 1 image (ID 3)

Next: /seo-images-manager rename
```

**Step 5: Rename and optimize**
```
/seo-images-manager rename
```

**Output:**
```
⚙️ Optimizing 4 images...

✓ ID 1: hotels-in-rome-luxury-suite.jpg
  3000x2000 → 1600x1067 | 2.5 MB → 450 KB | 82% saved

✓ ID 2: rome-hotel-breakfast-buffet.jpg
  4000x3000 → 1600x1200 | 3.8 MB → 520 KB | 86% saved

✓ ID 4: rome-hotel-spa-wellness.jpg
  1920x1080 → 1600x900 | 900 KB → 320 KB | 64% saved

✓ ID 5: rome-colosseum-hotel-view.jpg
  2560x1440 → 1600x900 | 1.5 MB → 420 KB | 72% saved

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Total saved: 8.70 MB → 1.71 MB (80% reduction)

Files ready in: clients/prova/test/images/optimized/
```

**Step 6: Review optimized images (optional)**
```
/seo-images-manager list --filter optimized
```

**Output:**
```
📊 Immagini ottimizzate (pronte per upload)

⚙️ ID 1 | hotels-in-rome-luxury-suite.jpg | 450 KB | KW: hotels in rome luxury suite
⚙️ ID 2 | rome-hotel-breakfast-buffet.jpg | 520 KB | KW: rome hotel breakfast buffet
⚙️ ID 4 | rome-hotel-spa-wellness.jpg | 320 KB | KW: rome hotel spa wellness
⚙️ ID 5 | rome-colosseum-hotel-view.jpg | 420 KB | KW: rome colosseum hotel view

Total: 4 images ready for upload
```

**Step 7: Upload to WordPress (CHECKPOINT #2 OBBLIGATORIO)**
```
/seo-images-manager upload --all
```

**Output with CHECKPOINT #2:**
```
⚠️ CONFERMA UPLOAD SU WORDPRESS

WordPress: https://example.com
Media Folder: seo-optimized/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔘 CHECKPOINT: Confermi l'upload di 4 immagini?

☑ ID 1: hotels-in-rome-luxury-suite.jpg | 450 KB
  Alt: Hotels in rome luxury suite - Top 10 Hotels in Rome

☑ ID 2: rome-hotel-breakfast-buffet.jpg | 520 KB
  Alt: Rome hotel breakfast buffet - Top 10 Hotels in Rome

☐ ID 4: rome-hotel-spa-wellness.jpg | 320 KB
  Alt: Rome hotel spa wellness center - Top 10 Hotels in Rome
  (Voglio rivedere questa prima)

☑ ID 5: rome-colosseum-hotel-view.jpg | 420 KB
  Alt: Rome colosseum hotel view - Top 10 Hotels in Rome

[Conferma selezione: 3/4]
```

**User confirms 3/4 images (temporarily skips ID 4):**

```
⬆️ Uploading 3 images to WordPress...

✓ hotels-in-rome-luxury-suite.jpg
  WordPress Media ID: 123
  URL: https://example.com/wp-content/uploads/2026/04/hotels-in-rome-luxury-suite.jpg

✓ rome-hotel-breakfast-buffet.jpg
  WordPress Media ID: 124
  URL: https://example.com/wp-content/uploads/2026/04/rome-hotel-breakfast-buffet.jpg

✓ rome-colosseum-hotel-view.jpg
  WordPress Media ID: 125
  URL: https://example.com/wp-content/uploads/2026/04/rome-colosseum-hotel-view.jpg

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 3 images uploaded successfully
⏭️ 1 image skipped (ID 4) - upload later with: /seo-images-manager upload --id 4
```

**Step 8: Check status**
```
/seo-images-manager status
```

**Output:**
```
📊 Image SEO Status

Total images: 5
  Synced: 3 ✅
  Optimized: 1 ⚙️ (ready to upload)
  Pending: 1 📸

Recent activity:
  ✅ Uploaded today: 3 images
  ⚙️ Ready: ID 4 (rome-hotel-spa-wellness.jpg)
  📸 Not planned: ID 3 (photo_01.png)
```

**Step 9 (optional): Upload skipped image**
```
/seo-images-manager upload --id 4
```

**Output:**
```
⬆️ Uploading 1 image...

✓ rome-hotel-spa-wellness.jpg
  WordPress Media ID: 126
  URL: https://example.com/wp-content/uploads/2026/04/rome-hotel-spa-wellness.jpg

✅ Upload complete!
```

---

**Key Improvements with Checkpoints:**
- ✅ Full control at each stage (plan, upload)
- ✅ Can skip low-quality images during planning
- ✅ Can defer upload of specific images for review
- ✅ No accidental WordPress uploads
- ✅ Clear next steps after each action

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

## Implementation Reference

For detailed checkpoint implementation with code examples, see:
- **[UX-CHECKPOINTS.md](UX-CHECKPOINTS.md)** - Complete guide with `AskUserQuestion` examples, helper functions, and testing checklist
- **[NEXT-SEO-SPEC.md](../../NEXT-SEO-SPEC.md)** - Full project specifications with database schema and workflow details

---

**Version:** 1.5.0
**Last Updated:** 2026-05-04
**Skill Type:** Workflow Automation
**Dependencies:** `pillow`, `requests`, `beautifulsoup4`, `python-dotenv`

## Changelog

### v1.5.0 (2026-05-04)
- 📊 **3-Variant Scoring System**: Proposes 3 keyword options per image (hotel-image-seo.skill inspired)
  - Opportunity score (1-10): GSC impressions + context relevance + long-tail bonus
  - Gap score (1-10): Competitor analysis + unique features + focus keyword alignment
  - SEO score (1-10): Keyword structure + relevance + best practices
- 📁 **Folder-Based Context**: Removed target_url dependency
  - Context from subfolder name (e.g., `original/Piscina Hotel/`)
  - Combined with PROJECT.md brand context
- 🎯 **Domain-Level GSC**: Queries on site domain, not specific page
- ✅ **Human Selection**: Choose best variant from 3 scored options
- 🔄 **Simplified Workflow**: `plan` → select variant → `rename` → `upload`
- 📖 **Enhanced PROJECT.md Template**: Detailed examples for brand context, competitors, keyword universe

### v1.4.0 (2026-04-30)
- 📚 **Global Rules System**: Two-tier rules (global baseline + project overrides)
- 📖 **Reference File**: `references/seo-rules.md` with naming, alt text, cannibalization rules
- 🔧 **PROJECT.md Overrides**: Per-project customization of max lengths, naming patterns
- 🏭 **Industry Templates**: Pre-defined patterns for hospitality, e-commerce, real estate, blog
- 🌐 **Multi-Language Synonyms**: Built-in synonym strategies for es, it, en, fr, de, pt, nl
- ⚖️ **Rule Priority Chain**: PROJECT.md > CLI flags > Project specs > Global rules
- 🔀 **Merge Logic**: `_load_global_rules()`, `_merge_rules()` methods in planner

### v1.3.0 (2026-04-30)
- ✨ **Interactive Questions**: 3 pre-plan questions (competitor, visual, language)
- 🖼️ **GSC Image Search**: Dual GSC queries (web + image search types)
- 🌍 **Multilingual Support**: Target language for alt text, title, caption
- 👁️ **Visual Context**: AI-generated image descriptions for richer keywords
- 🔍 **Competitor Analysis**: Analyzes competitor GSC image queries
- 🎯 **Enhanced Scoring**: Image queries get +5 boost, source tracking (web/image/competitor)

### v1.2.0 (2026-04-28)
- 📁 Subfolder context filtering (+15 boost for relevant queries)
- 📋 PROJECT.md integration (tone, competitors, focus keywords)
- 🔤 Tone-aware alt text generation

### v1.1.0 (2026-04-27)
- 🔍 Google Search Console integration
- 📊 Opportunity scoring (0-100)
- ⚡ Intelligent caching (7-day TTL)
