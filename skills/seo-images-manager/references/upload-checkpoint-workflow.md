# Upload Checkpoint Workflow

**Version:** 1.6.0
**Purpose:** Mandatory confirmation before WordPress upload

---

## Overview

Before uploading images to WordPress, the skill presents a mandatory checkpoint where the user selects which images to upload. This prevents accidental uploads and gives full control over what goes to production.

## Workflow

```python
# 1. Get images ready for upload
from scripts.image_selector import format_upload_selection_data

upload_data = format_upload_selection_data(project_path)

# Check if any images are ready
if upload_data['ready_count'] == 0:
    print("No images ready for upload. Run 'rename' first.")
    exit()

# 2. Present checkpoint to user via AskUserQuestion
question = {
    "question": f"Select the images to upload to WordPress ({upload_data['ready_count']} ready)",
    "header": "Upload",
    "multiSelect": True,  # Allow multiple selections
    "options": upload_data['options']
}

answers = AskUserQuestion(questions=[question])

# 3. Parse answers to get selected image IDs
selected_ids = []
for answer_key, answer_value in answers.items():
    # Parse answer to extract image ID
    # Answer format depends on AskUserQuestion implementation
    # Example: "ID 1: hotel-pool-acuazul.jpg (450 KB)"
    # Extract "1" from the string

    if answer_value:  # If checkbox is checked
        # Extract ID from option label
        import re
        match = re.match(r'ID (\d+):', answer_value)
        if match:
            selected_ids.append(int(match.group(1)))

# 4. Upload selected images
from scripts.image_uploader import ImageUploader

uploader = ImageUploader(project_path)
results = uploader.upload_by_ids(selected_ids)

# 5. Show confirmation
successful = [r for r in results if r.get('success')]
failed = [r for r in results if not r.get('success')]

print(f"✅ Uploaded {len(successful)} images")
for r in successful:
    print(f"  {r['filename']}")
    print(f"  WordPress ID: {r['wordpress_media_id']}")
    print(f"  URL: {r['wordpress_url']}")

if failed:
    print(f"\n❌ Failed to upload {len(failed)} images:")
    for r in failed:
        print(f"  Image {r['image_id']}: {r['error']}")
```

---

## Function Reference

### `format_upload_selection_data(project_path)`

**Input:** Project path

**Output:** Dict with upload-ready images:
```json
{
  "ready_count": 4,
  "images": [
    {
      "image_id": 1,
      "original_filename": "IMG_1234.jpg",
      "seo_filename": "hotel-pool-acuazul.jpg",
      "optimized_path": "/path/to/optimized/hotel-pool-acuazul.jpg",
      "size_formatted": "450.3 KB",
      "alt_text": "Hotel pool acuazul peñíscola | Family hotel with pool",
      "title": "Hotel Pool Acuazul Peñíscola",
      "caption": "Hotel pool acuazul peñíscola at Family Hotel",
      "target_keyword": "hotel-pool-acuazul-peniscola"
    }
  ],
  "options": [
    {
      "label": "ID 1: hotel-pool-acuazul.jpg (450.3 KB)",
      "description": "Alt: Hotel pool acuazul peñíscola | Family hotel... | Keyword: hotel-pool-acuazul-peniscola"
    }
  ]
}
```

**What it does:**
1. Queries database for images where `synced = 0` AND `optimized_path IS NOT NULL`
2. For each image, reads optimized file size
3. Formats alt text preview (truncated to 60 chars)
4. Builds options array for AskUserQuestion

**Returns empty** if no images ready for upload.

---

## AskUserQuestion Format

```python
{
  "question": "Select the images to upload to WordPress (4 ready)",
  "header": "Upload",
  "multiSelect": True,  # IMPORTANT: Allow multiple selections
  "options": [
    {
      "label": "ID 1: hotel-pool-acuazul.jpg (450 KB)",
      "description": "Alt: Hotel pool acuazul peñíscola | Family hotel... | Keyword: hotel-pool-acuazul-peniscola"
    },
    {
      "label": "ID 2: restaurant-breakfast-buffet.jpg (520 KB)",
      "description": "Alt: Restaurant breakfast buffet hotel | Hotel br... | Keyword: restaurant-breakfast-buffet"
    }
  ]
}
```

**Key points:**
- **multiSelect: True** — User can select multiple images
- **Label format:** "ID {id}: {filename} ({size})"
- **Description:** Alt text preview + keyword
- Answers will be a dict with selected options

---

## WordPress Upload Details

After user confirms, `ImageUploader.upload_by_ids()` performs:

1. **Read optimized file** from `optimized_path`
2. **Authenticate** with WordPress (Basic Auth using app password)
3. **Upload image** via `POST /wp-json/wp/v2/media`
4. **Set metadata** via `POST /wp-json/wp/v2/media/{id}`:
   - Alt text
   - Title
   - Caption
5. **Update database**:
   - `wordpress_media_id` = media ID
   - `wordpress_url` = source URL
   - `synced` = 1
   - `uploaded_at` = timestamp

---

## Error Handling

**No images ready:**
```json
{
  "ready_count": 0,
  "images": [],
  "options": []
}
```
→ Show message: "No images ready for upload. Run 'rename' first."

**WordPress credentials missing:**
```
FileNotFoundError: No .env file found at {path}.
Run /seo-wordpress setup first.
```

**Upload failure:**
```json
{
  "image_id": 1,
  "error": "Upload failed: 403 - Invalid credentials",
  "success": False
}
```
→ Show error, keep `synced = 0` for retry

**Partial success:**
- 3 images uploaded successfully
- 1 image failed
→ Show both successful and failed uploads

---

## Example: Full Skill Flow

```
User: /seo-images-manager upload

Step 1: Check optimized images
  → Found 4 images ready for upload

Step 2: Load WordPress config
  → URL: https://hotelacuazul.com
  → REST API: /wp-json/wp/v2/media
  → Folder: seo-optimized/

Step 3: Present checkpoint (MANDATORY)
  → AskUserQuestion with 4 options (multiSelect)
  → User selects 3/4 images (skips ID 4)

Step 4: Upload selected images
  → Upload ID 1: ✓ Media ID 123
  → Upload ID 2: ✓ Media ID 124
  → Upload ID 5: ✓ Media ID 125

Step 5: Update database
  → Mark 3 images as synced = 1
  → Save WordPress media IDs and URLs

Step 6: Confirm
  → Show uploaded images with WordPress URLs
  → Note skipped image (ID 4) for later upload

Next: Images are now available in WordPress Media Library
```

---

## Skipped Images

If user skips an image during checkpoint, it remains `synced = 0` and can be uploaded later:

```bash
# Upload specific image later
/seo-images-manager upload --id 4

# Or show all pending for selection
/seo-images-manager upload --all
```

---

## WordPress Configuration

Required `.env` file in project root:

```bash
WP_URL=https://hotelacuazul.com
WP_USERNAME=admin
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx
WP_MEDIA_FOLDER=seo-optimized
WP_VERIFY_SSL=true
```

**App Password generation:**
1. WordPress Admin → Users → Profile
2. Scroll to "Application Passwords"
3. Enter name: "SEO Image Manager"
4. Click "Add New Application Password"
5. Copy generated password (spaces included)
6. Add to `.env` as `WP_APP_PASSWORD`

---

## Testing Checklist

- [ ] format_upload_selection_data() returns correct data
- [ ] Options show filename, size, alt text preview
- [ ] AskUserQuestion displays with multiSelect
- [ ] User can select multiple images
- [ ] User can deselect images
- [ ] Upload only proceeds for selected images
- [ ] WordPress metadata (alt/title/caption) is set correctly
- [ ] Database updated with media ID and URL
- [ ] synced = 1 set correctly
- [ ] Skipped images remain available for later upload
- [ ] Error handling for missing .env
- [ ] Error handling for upload failures
- [ ] Partial success handled correctly
