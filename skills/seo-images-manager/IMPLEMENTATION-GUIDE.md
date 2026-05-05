# Implementation Guide: Interactive Checkpoints

**For Claude Code: Exact logic to follow when user executes commands with checkpoints**

---

## Checkpoint #1: After `/seo-images-manager plan <url>`

### Step-by-Step Logic

```
1. User runs: /seo-images-manager plan https://example.com/blog/post

2. Execute Python script:
   ```bash
   python scripts/image_manager.py plan \
     --project clients/{client}/{project} \
     --url https://example.com/blog/post
   ```

3. Receive JSON output with proposals:
   {
     "success": true,
     "target_url": "...",
     "page_context": {...},
     "plan": {
       "images": [
         {
           "id": 1,
           "original_filename": "IMG_1234.jpg",
           "selected_keyword": "hotels in rome luxury suite",
           "seo_metadata": {
             "filename": "hotels-in-rome-luxury-suite.jpg",
             "alt_text": "Hotels in rome luxury suite - Top 10...",
             "title": "Hotels In Rome Luxury Suite"
           },
           "cannibalization_risk": false
         },
         ...
       ]
     }
   }

4. Display proposals to user in readable format:
   ```
   📊 Page Context
      URL: {...}
      Primary Keyword: {...}

   📸 Keyword Proposals

   Image 1: IMG_1234.jpg
     ✓ hotels in rome luxury suite (RECOMMENDED)

     SEO Metadata:
       Filename: hotels-in-rome-luxury-suite.jpg
       Alt: Hotels in rome luxury suite - Top 10...

   [... other images ...]
   ```

5. Create options for AskUserQuestion:
   ```python
   from skills.seo-images-manager.helpers import format_image_for_checkbox

   options = []
   for img in plan['images']:
       option = format_image_for_checkbox(img, mode="plan")
       options.append(option)
   ```

6. Use AskUserQuestion with multiSelect:
   ```python
   AskUserQuestion(
       questions=[{
           "question": "Which images do you want to optimize with these proposed keywords?",
           "header": "Selection",
           "multiSelect": True,
           "options": options
       }]
   )
   ```

7. Receive user response:
   user_answers = {
       "question_1": [
           "ID 1: IMG_1234.jpg → hotels-in-rome-luxury-suite.jpg",
           "ID 2: IMG_5678.jpg → rome-hotel-breakfast.jpg",
           "ID 5: colosseum.jpg → rome-colosseum-view.jpg"
       ]
   }

8. Extract selected IDs:
   ```python
   from skills.seo-images-manager.helpers import extract_ids_from_labels

   selected_ids = extract_ids_from_labels(user_answers['question_1'])
   # Result: [1, 2, 5]
   ```

9. Save metadata ONLY for selected images:
   ```python
   from skills.seo-images-manager.helpers import save_selected_plans

   db_path = Path(project_path) / "images" / "images.db"
   save_selected_plans(selected_ids, plan['images'], db_path)
   ```

10. Show confirmation to user:
    ```python
    from skills.seo-images-manager.helpers import format_checkpoint_summary

    total = len(plan['images'])
    selected = len(selected_ids)
    summary = format_checkpoint_summary(total, selected, "plan")
    print(summary)
    # ✅ SEO plan saved for 3 images
    # ⏭️ Skipped 2 images

    print(f"\nNext: /seo-images-manager rename --ids {','.join(map(str, selected_ids))}")
    ```
```

---

## Checkpoint #2: Before `/seo-images-manager upload`

### Step-by-Step Logic

```
1. User runs: /seo-images-manager upload --all
   (or --id 1, or --ids 1,2,3)

2. Read images ready for upload:
   ```python
   from skills.seo-images-manager.helpers import get_pending_images

   db_path = Path(project_path) / "images" / "images.db"
   pending_images = get_pending_images(db_path, status="optimized")
   ```

3. If no images ready:
   ```python
   if not pending_images:
       print("❌ No images ready for upload")
       print("Run /seo-images-manager list --filter optimized to see status")
       exit()
   ```

4. Read WordPress configuration:
   ```python
   env_path = Path(project_path) / ".env"
   if not env_path.exists():
       print("❌ WordPress not configured")
       print("Run /seo-wordpress setup first")
       exit()

   from dotenv import load_dotenv
   load_dotenv(env_path)

   wp_url = os.getenv("WP_URL")
   wp_folder = os.getenv("WP_MEDIA_FOLDER", "seo-optimized")
   ```

5. Show warning and summary:
   ```
   ⚠️ CONFIRM WORDPRESS UPLOAD

   You are about to upload {len(pending_images)} images to:
     WordPress: {wp_url}
     Media Folder: {wp_folder}/

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

6. Create options for AskUserQuestion:
   ```python
   from skills.seo-images-manager.helpers import format_image_for_checkbox

   options = []
   for img in pending_images:
       option = format_image_for_checkbox(img, mode="upload")
       options.append(option)
   ```

7. Use AskUserQuestion with multiSelect (MANDATORY):
   ```python
   AskUserQuestion(
       questions=[{
           "question": f"Confirm upload of {len(pending_images)} images to WordPress?",
           "header": "Confirmation",
           "multiSelect": True,
           "options": options
       }]
   )
   ```

8. Receive user response:
   user_answers = {
       "question_1": [
           "ID 1: hotels-in-rome-luxury-suite.jpg",
           "ID 2: rome-hotel-breakfast.jpg"
       ]
   }

9. Extract confirmed IDs:
   ```python
   from skills.seo-images-manager.helpers import extract_ids_from_labels

   confirmed_ids = extract_ids_from_labels(user_answers['question_1'])
   # Result: [1, 2]
   ```

10. If no images confirmed:
    ```python
    if not confirmed_ids:
        print("❌ No images selected. Upload cancelled.")
        exit()
    ```

11. Upload ONLY confirmed images:
    ```bash
    python scripts/image_manager.py upload \
      --project clients/{client}/{project} \
      --ids {','.join(map(str, confirmed_ids))}
    ```

12. Receive upload results:
    {
      "success": true,
      "uploaded": 2,
      "results": [
        {
          "image_id": 1,
          "filename": "hotels-in-rome-luxury-suite.jpg",
          "wordpress_media_id": 123,
          "wordpress_url": "https://..."
        },
        ...
      ]
    }

13. Show results to user:
    ```
    ⬆️ Uploading 2 images to WordPress...

    ✓ hotels-in-rome-luxury-suite.jpg
      WordPress Media ID: 123
      URL: https://...

    ✓ rome-hotel-breakfast.jpg
      WordPress Media ID: 124
      URL: https://...

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ✅ 2 images uploaded successfully
    ```

14. If some images were skipped:
    ```python
    total = len(pending_images)
    uploaded = len(confirmed_ids)
    skipped = total - uploaded

    if skipped > 0:
        skipped_ids = [img['id'] for img in pending_images if img['id'] not in confirmed_ids]
        print(f"⏭️ {skipped} image(s) skipped - upload later with:")
        print(f"   /seo-images-manager upload --ids {','.join(map(str, skipped_ids))}")
    ```
```

---

## Available Helper Files

- **helpers.py**: Helper functions for checkpoints
  - `extract_ids_from_labels(labels)` → List[int]
  - `format_image_for_checkbox(img_data, mode)` → dict
  - `save_selected_plans(selected_ids, images, db_path)`
  - `get_pending_images(db_path, status)` → List[dict]
  - `format_checkpoint_summary(total, selected, action)` → str
  - `update_sync_status(image_id, synced, wp_data, db_path)`

- **UX-CHECKPOINTS.md**: Detailed examples with complete code

---

## Complete Flowchart

```
User: /seo-images-manager plan https://example.com/blog/post
  ↓
Run: python scripts/image_manager.py plan ...
  ↓
Receive: JSON with proposals
  ↓
Show: Formatted proposals to user
  ↓
┌─────────────────────────────────────┐
│ CHECKPOINT #1: AskUserQuestion      │
│ Multi-select checkbox               │
│ User selects which images to proceed│
└─────────────────────────────────────┘
  ↓
Extract: IDs from selected labels
  ↓
Save: Metadata only for selected IDs
  ↓
Show: Confirmation + next steps
  ↓
───────────────────────────────────────

User: /seo-images-manager rename
  ↓
Run: python scripts/image_manager.py rename ...
  ↓
Show: Optimization metrics
  ↓
───────────────────────────────────────

User: /seo-images-manager upload --all
  ↓
Check: Images ready for upload (optimized but not synced)
  ↓
Load: WordPress config from .env
  ↓
Show: Warning + WordPress URL + list
  ↓
┌─────────────────────────────────────┐
│ CHECKPOINT #2: AskUserQuestion      │
│ Multi-select checkbox               │
│ User confirms which images to upload│
│ ⚠️ MANDATORY - ALWAYS ACTIVE       │
└─────────────────────────────────────┘
  ↓
Extract: IDs from confirmed labels
  ↓
Upload: Only confirmed images to WordPress
  ↓
Show: Results + skipped images info
```

---

## Best Practices

1. **ALWAYS show checkpoint before upload**
   - Even if user uses --id 1 (single image)
   - Even if there's only 1 pending image
   - It's a safety feature

2. **Format options to be readable**
   - Label: brief and scannable (max 60 chars)
   - Description: useful details separated by `|`
   - Warnings with emoji: ⚠️

3. **Show next steps after each checkpoint**
   - After plan: "Next: /seo-images-manager rename --ids 1,2,3"
   - After upload: "Upload later with: /seo-images-manager upload --ids 4,5"

4. **Handle edge cases**
   - No images selected → confirm cancellation
   - All images skipped → show how to retry
   - Upload error → keep synced=false for retry

---

**Version:** 1.0.0
**Last Updated:** 2026-04-27
**For:** Claude Code execution of seo-images-manager skill
