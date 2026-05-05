# UX Checkpoints: Practical Implementation

**Reference document for implementing interactive checkpoints in the seo-images-manager skill**

---

## 1. Overview

This document provides practical examples of how to use `AskUserQuestion` with `multiSelect: true` to implement selection checkpoints in the following phases:
1. **Plan** → Select images to optimize
2. **Rename** → Verify compression (optional)
3. **Upload** → Confirm WordPress upload (MANDATORY)

---

## 2. Checkpoint #1: Selection after Plan

### 2.1 When to Trigger

**Trigger:** After generating keyword proposals with `/seo-images-manager plan <url>`

**Condition:** There are 2+ images with keyword proposals

### 2.2 Implementation Code

```python
# After executing: python scripts/image_manager.py plan --project <path> --url <url>
# And receiving the JSON with proposals

plan_result = json.loads(plan_output)
images = plan_result['plan']['images']

# Format options for AskUserQuestion
options = []
for img in images:
    # Label: brief description (max 60 chars)
    label = f"ID {img['id']}: {img['original_filename'][:30]}"

    # Description: proposed SEO details
    description = (
        f"Keyword: {img['selected_keyword']} | "
        f"Filename: {img['seo_metadata']['filename'][:40]} | "
        f"Alt: {img['seo_metadata']['alt_text'][:50]}..."
    )

    # Add warning if there's cannibalization risk
    if img.get('cannibalization_risk'):
        description += " ⚠️ Cannibalization risk"

    options.append({
        "label": label,
        "description": description
    })

# Use AskUserQuestion
AskUserQuestion(
    questions=[{
        "question": "Which images do you want to optimize with these proposed keywords?",
        "header": "Selection",
        "multiSelect": True,
        "options": options
    }]
)
```

### 2.3 Expected Output (UI)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Which images do you want to optimize with these proposed keywords?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

☑ ID 1: IMG_1234.jpg
  Keyword: hotels in rome luxury suite | Filename: hotels-in-rome-luxu... | Alt: Hotels in rome luxury suite - Top 10...

☑ ID 2: IMG_5678.jpg
  Keyword: rome hotel breakfast buffet | Filename: rome-hotel-breakfas... | Alt: Rome hotel breakfast buffet - Top...

☐ ID 3: photo_01.png
  Keyword: rome hotel rooftop | Filename: rome-hotel-rooftop... | Alt: Rome hotel rooftop terrace - Top... ⚠️ Cannibalization risk

☑ ID 4: IMG_9999.jpg
  Keyword: rome hotel spa wellness | Filename: rome-hotel-spa-welln... | Alt: Rome hotel spa wellness center - Top...

[Confirm selection]
```

### 2.4 Post-Selection

```python
# Receive the response from user
selected_labels = user_answers['question_1']  # List of selected labels

# Extract IDs from labels (format: "ID 1: filename")
selected_ids = []
for label in selected_labels:
    match = re.match(r'ID (\d+):', label)
    if match:
        selected_ids.append(int(match.group(1)))

# Update database ONLY for selected images
for img in images:
    if img['id'] in selected_ids:
        # Save seo_filename, alt_text, etc.
        save_seo_metadata_to_db(img['id'], img['seo_metadata'])

# Confirm to user
print(f"✅ SEO plan saved for {len(selected_ids)} images")
print(f"⏭️ Skipped {len(images) - len(selected_ids)} images")
print(f"\nNext: /seo-images-manager rename --ids {','.join(map(str, selected_ids))}")
```

---

## 3. Checkpoint #2: Verify Compression (Optional)

### 3.1 When to Trigger

**Trigger:** After executing `/seo-images-manager rename`

**Condition:** At least 1 image has compression_ratio > 85% (very aggressive)

**Note:** This checkpoint is OPTIONAL. Activate only if there are compression warnings.

### 3.2 Implementation Code

```python
# After rename, check results
optimization_results = json.loads(rename_output)['results']

# Filter images with very aggressive compression
high_compression = [
    img for img in optimization_results
    if img['compression_ratio'] > 0.85  # >85% reduction
]

if high_compression:
    # Show warning and ask for confirmation
    options = []
    for img in high_compression:
        label = f"ID {img['id']}: {img['seo_filename']}"
        description = (
            f"Original: {img['original_size_mb']:.1f} MB → "
            f"Optimized: {img['optimized_size_mb']:.1f} MB | "
            f"⚠️ {img['compression_ratio_percent']}% reduction (very aggressive)"
        )
        options.append({"label": label, "description": description})

    AskUserQuestion(
        questions=[{
            "question": "Some images have very aggressive compression. Do you want to keep them or exclude them?",
            "header": "Verification",
            "multiSelect": True,
            "options": options
        }]
    )

    # If user deselects some images, delete them from images/optimized/
    # and remove optimized_path from database
else:
    # No warnings, proceed
    print("✅ All images optimized successfully")
```

### 3.3 Expected Output

```
⚠️ Some images have very aggressive compression

Do you want to keep them or exclude them?

☑ ID 2: rome-hotel-breakfast-buffet.jpg
  Original: 3.8 MB → Optimized: 0.5 MB | ⚠️ 86% reduction (very aggressive)

☑ ID 5: rome-colosseum-hotel-view.jpg
  Original: 1.5 MB → Optimized: 0.2 MB | ⚠️ 87% reduction (very aggressive)

[Confirm selection]
```

**If user deselects ID 2:**
```
✅ Kept 1 image (ID 5)
🗑️ Removed 1 image (ID 2) - you can re-optimize later with lower compression
```

---

## 4. Checkpoint #3: Confirm WordPress Upload (MANDATORY)

### 4.1 When to Trigger

**Trigger:** ALWAYS before `/seo-images-manager upload`

**Condition:** There are 1+ images with `optimized_path` and `synced = false`

**Note:** This checkpoint is **ALWAYS MANDATORY** to prevent accidental uploads.

### 4.2 Implementation Code

```python
# Before upload, ALWAYS ask for confirmation
# Read images ready for upload
pending_uploads = get_pending_uploads(project_path)

if not pending_uploads:
    print("❌ No images ready for upload")
    print("Run /seo-images-manager list --filter optimized to see pending images")
    exit(1)

# Read WordPress configuration
wp_config = load_wordpress_config(project_path)
wp_url = wp_config['site_url']
wp_folder = wp_config.get('media_folder', 'seo-optimized')

# Show summary
print(f"⚠️ CONFIRM WORDPRESS UPLOAD\n")
print(f"You are about to upload {len(pending_uploads)} images to:")
print(f"  WordPress: {wp_url}")
print(f"  Media Folder: {wp_folder}/\n")
print("━" * 60 + "\n")

# Format options for checkbox
options = []
for img in pending_uploads:
    label = f"ID {img['id']}: {img['seo_filename']}"

    # Calculate size in KB or MB
    size_kb = img['filesize'] / 1024
    if size_kb > 1024:
        size_str = f"{size_kb/1024:.1f} MB"
    else:
        size_str = f"{size_kb:.0f} KB"

    description = f"{size_str} | Alt: {img['alt_text'][:60]}..."

    options.append({
        "label": label,
        "description": description
    })

# MANDATORY CHECKPOINT
AskUserQuestion(
    questions=[{
        "question": f"Confirm upload of these {len(pending_uploads)} images to WordPress?",
        "header": "Confirmation",
        "multiSelect": True,
        "options": options
    }]
)
```

### 4.3 Expected Output

```
⚠️ CONFIRM WORDPRESS UPLOAD

You are about to upload 4 images to:
  WordPress: https://example.com
  Media Folder: seo-optimized/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Confirm upload of these 4 images to WordPress?

☑ ID 1: hotels-in-rome-luxury-suite.jpg
  450 KB | Alt: Hotels in rome luxury suite - Top 10 Hotels in Rome

☑ ID 2: rome-hotel-breakfast-buffet.jpg
  520 KB | Alt: Rome hotel breakfast buffet - Top 10 Hotels in Rome

☑ ID 4: rome-hotel-spa-wellness.jpg
  320 KB | Alt: Rome hotel spa wellness center - Top 10 Hotels in Rome

☑ ID 5: rome-colosseum-hotel-view.jpg
  420 KB | Alt: Rome colosseum hotel view - Top 10 Hotels in Rome

[Confirm selection]
```

### 4.4 Post-Confirmation

```python
# Receive user selection
selected_labels = user_answers['question_1']

# Extract selected IDs
selected_ids = extract_ids_from_labels(selected_labels)

if not selected_ids:
    print("❌ No images selected. Upload cancelled.")
    exit(0)

# Upload only confirmed images
print(f"\n⬆️ Uploading {len(selected_ids)} images to WordPress...\n")

upload_results = []
for img_id in selected_ids:
    try:
        result = upload_to_wordpress(img_id, project_path)
        upload_results.append(result)

        print(f"✓ {result['filename']}")
        print(f"  WordPress Media ID: {result['wordpress_media_id']}")
        print(f"  URL: {result['wordpress_url']}\n")

        # Update database: synced = true
        update_sync_status(img_id, True, result)

    except Exception as e:
        print(f"✗ Failed to upload ID {img_id}: {str(e)}\n")

# Summary
print("━" * 60)
print(f"\n✅ {len(upload_results)} images uploaded successfully")

skipped = len(pending_uploads) - len(selected_ids)
if skipped > 0:
    skipped_ids = [img['id'] for img in pending_uploads if img['id'] not in selected_ids]
    print(f"⏭️ {skipped} image(s) skipped - can be uploaded later with:")
    print(f"   /seo-images-manager upload --ids {','.join(map(str, skipped_ids))}")
```

---

## 5. Complete Example: Flow with 3 Checkpoints

```python
# ═══════════════════════════════════════════════════════════
# PHASE 1: ANALYZE
# ═══════════════════════════════════════════════════════════
result = run_command("python scripts/image_manager.py analyze --project clients/prova/test")
print(f"✅ Found {result['images_found']} new images")

# ═══════════════════════════════════════════════════════════
# PHASE 2: LIST PENDING
# ═══════════════════════════════════════════════════════════
result = run_command("python scripts/image_manager.py list --project clients/prova/test --filter pending")
print(f"📊 {result['total']} images ready for planning")

# ═══════════════════════════════════════════════════════════
# PHASE 3: PLAN + CHECKPOINT #1
# ═══════════════════════════════════════════════════════════
result = run_command("python scripts/image_manager.py plan --project clients/prova/test --url https://example.com/blog/post")
images = result['plan']['images']

# CHECKPOINT: Keyword selection
options = [
    {
        "label": f"ID {img['id']}: {img['original_filename'][:30]}",
        "description": f"Keyword: {img['selected_keyword']} | Alt: {img['seo_metadata']['alt_text'][:50]}..."
    }
    for img in images
]

selected = AskUserQuestion(
    questions=[{
        "question": "Which images do you want to optimize?",
        "header": "Selection",
        "multiSelect": True,
        "options": options
    }]
)

selected_ids = extract_ids_from_labels(selected['answers']['question_1'])
save_selected_plans(selected_ids, images)

# ═══════════════════════════════════════════════════════════
# PHASE 4: RENAME
# ═══════════════════════════════════════════════════════════
result = run_command(f"python scripts/image_manager.py rename --project clients/prova/test --ids {','.join(map(str, selected_ids))}")
print(f"✅ {result['processed']} images optimized")

# CHECKPOINT #2 (optional): Only if compression > 85%
high_compression = [r for r in result['results'] if r['compression_ratio'] > 0.85]
if high_compression:
    # Show warning...
    pass

# ═══════════════════════════════════════════════════════════
# PHASE 5: LIST OPTIMIZED
# ═══════════════════════════════════════════════════════════
result = run_command("python scripts/image_manager.py list --project clients/prova/test --filter optimized")
print(f"📊 {result['total']} images ready for upload")

# ═══════════════════════════════════════════════════════════
# PHASE 6: UPLOAD + CHECKPOINT #3 (MANDATORY)
# ═══════════════════════════════════════════════════════════
pending = get_pending_uploads("clients/prova/test")

# CHECKPOINT: Confirm upload (ALWAYS)
wp_config = load_wordpress_config("clients/prova/test")
print(f"⚠️ Upload to: {wp_config['site_url']}\n")

options = [
    {
        "label": f"ID {img['id']}: {img['seo_filename']}",
        "description": f"{img['filesize']/1024:.0f} KB | Alt: {img['alt_text'][:60]}..."
    }
    for img in pending
]

confirmed = AskUserQuestion(
    questions=[{
        "question": f"Confirm upload of {len(pending)} images to WordPress?",
        "header": "Confirmation",
        "multiSelect": True,
        "options": options
    }]
)

confirmed_ids = extract_ids_from_labels(confirmed['answers']['question_1'])
upload_images(confirmed_ids)

# ═══════════════════════════════════════════════════════════
# PHASE 7: FINAL STATUS
# ═══════════════════════════════════════════════════════════
result = run_command("python scripts/image_manager.py status --project clients/prova/test")
print(f"📊 Synced: {result['synced']} | Pending: {result['pending']}")
```

---

## 6. Helper Functions

### 6.1 Extract ID from Label

```python
import re

def extract_ids_from_labels(labels):
    """
    Extract IDs from user-selected labels.

    Input: ["ID 1: filename.jpg", "ID 5: other.jpg"]
    Output: [1, 5]
    """
    ids = []
    for label in labels:
        match = re.match(r'ID (\d+):', label)
        if match:
            ids.append(int(match.group(1)))
    return ids
```

### 6.2 Format File Size

```python
def format_filesize(bytes):
    """Format file size in KB or MB."""
    kb = bytes / 1024
    if kb > 1024:
        return f"{kb/1024:.1f} MB"
    else:
        return f"{kb:.0f} KB"
```

### 6.3 Save SEO Plan

```python
def save_selected_plans(selected_ids, all_images):
    """
    Save seo_filename, alt_text, etc. ONLY for selected images.

    Args:
        selected_ids: List of user-selected IDs
        all_images: Complete list of images with proposals
    """
    conn = sqlite3.connect(db_path)

    for img in all_images:
        if img['id'] in selected_ids:
            conn.execute("""
                UPDATE images SET
                    seo_filename = ?,
                    alt_text = ?,
                    title = ?,
                    caption = ?,
                    target_keyword = ?,
                    target_url = ?,
                    page_h1 = ?,
                    page_title = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                img['seo_metadata']['filename'],
                img['seo_metadata']['alt_text'],
                img['seo_metadata']['title'],
                img['seo_metadata']['caption'],
                img['selected_keyword'],
                img['target_url'],
                img['page_h1'],
                img['page_title'],
                datetime.now().isoformat(),
                img['id']
            ))

    conn.commit()
    conn.close()

    print(f"✅ SEO plan saved for {len(selected_ids)} images")
    print(f"⏭️ Skipped {len(all_images) - len(selected_ids)} images")
```

---

## 7. Best Practices

### 7.1 Label Format

**DO:**
- Brief and scannable: `ID 1: filename.jpg`
- Include ID for traceability
- Max 60 characters

**DON'T:**
- Too long: `ID 1: IMG_1234_final_version_edited_compressed.jpg → hotels-in-rome-luxury-suite-top-10-best-hotels.jpg`
- Without ID: `filename.jpg` (impossible to extract ID after)

### 7.2 Description Format

**DO:**
- Key information separated by `|`
- Truncated previews with `...`
- Warnings with emoji: `⚠️`

**DON'T:**
- Too verbose
- Redundant information

### 7.3 Checkpoint Frequency

**ALWAYS:**
- Before WordPress upload (remote changes)
- When there are alternatives to evaluate (keyword cannibalization)

**NEVER:**
- After reversible operations (list, status)
- When there's only 1 possible option

**OPTIONAL:**
- After compression (only if warnings)
- Before batch operations (only if >10 items)

---

## 8. Testing Checklist

- [ ] Checkpoint #1 shows all planned images
- [ ] Label format: `ID {id}: {filename}`
- [ ] Description includes keyword, filename, alt (truncated)
- [ ] Multiple selection works (2+ checkboxes)
- [ ] Deselecting some images works
- [ ] IDs extracted correctly from labels
- [ ] Database updated ONLY for selected images
- [ ] Checkpoint #3 ALWAYS active before upload
- [ ] WordPress URL shown before confirmation
- [ ] Upload proceeds ONLY for confirmed images
- [ ] Skipped images tracked correctly

---

**Version:** 1.0.0
**Last Updated:** 2026-04-27
**Maintainer:** Pier Paolo Gorelli
