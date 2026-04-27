# Implementation Guide: Interactive Checkpoints

**Per Claude Code: Logica esatta da seguire quando l'utente esegue i comandi con checkpoint**

---

## Checkpoint #1: Dopo `/seo-images-manager plan <url>`

### Step-by-Step Logic

```
1. User esegue: /seo-images-manager plan https://example.com/blog/post

2. Esegui script Python:
   ```bash
   python scripts/image_manager.py plan \
     --project clients/{client}/{project} \
     --url https://example.com/blog/post
   ```

3. Ricevi JSON output con proposte:
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

4. Mostra proposte all'utente in formato leggibile:
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

   [... altre immagini ...]
   ```

5. Crea opzioni per AskUserQuestion:
   ```python
   from skills.seo-images-manager.helpers import format_image_for_checkbox

   options = []
   for img in plan['images']:
       option = format_image_for_checkbox(img, mode="plan")
       options.append(option)
   ```

6. Usa AskUserQuestion con multiSelect:
   ```python
   AskUserQuestion(
       questions=[{
           "question": "Quali immagini vuoi ottimizzare con queste keyword proposte?",
           "header": "Selezione",
           "multiSelect": True,
           "options": options
       }]
   )
   ```

7. Ricevi risposta dell'utente:
   user_answers = {
       "question_1": [
           "ID 1: IMG_1234.jpg → hotels-in-rome-luxury-suite.jpg",
           "ID 2: IMG_5678.jpg → rome-hotel-breakfast.jpg",
           "ID 5: colosseum.jpg → rome-colosseum-view.jpg"
       ]
   }

8. Estrai IDs selezionati:
   ```python
   from skills.seo-images-manager.helpers import extract_ids_from_labels

   selected_ids = extract_ids_from_labels(user_answers['question_1'])
   # Result: [1, 2, 5]
   ```

9. Salva metadata SOLO per immagini selezionate:
   ```python
   from skills.seo-images-manager.helpers import save_selected_plans

   db_path = Path(project_path) / "images" / "images.db"
   save_selected_plans(selected_ids, plan['images'], db_path)
   ```

10. Mostra conferma all'utente:
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

## Checkpoint #2: Prima di `/seo-images-manager upload`

### Step-by-Step Logic

```
1. User esegue: /seo-images-manager upload --all
   (oppure --id 1, oppure --ids 1,2,3)

2. Leggi immagini pronte per upload:
   ```python
   from skills.seo-images-manager.helpers import get_pending_images

   db_path = Path(project_path) / "images" / "images.db"
   pending_images = get_pending_images(db_path, status="optimized")
   ```

3. Se nessuna immagine pronta:
   ```python
   if not pending_images:
       print("❌ No images ready for upload")
       print("Run /seo-images-manager list --filter optimized to see status")
       exit()
   ```

4. Leggi configurazione WordPress:
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

5. Mostra warning e riepilogo:
   ```
   ⚠️ CONFERMA UPLOAD SU WORDPRESS

   Stai per caricare {len(pending_images)} immagini su:
     WordPress: {wp_url}
     Media Folder: {wp_folder}/

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

6. Crea opzioni per AskUserQuestion:
   ```python
   from skills.seo-images-manager.helpers import format_image_for_checkbox

   options = []
   for img in pending_images:
       option = format_image_for_checkbox(img, mode="upload")
       options.append(option)
   ```

7. Usa AskUserQuestion con multiSelect (OBBLIGATORIO):
   ```python
   AskUserQuestion(
       questions=[{
           "question": f"Confermi l'upload di {len(pending_images)} immagini su WordPress?",
           "header": "Conferma",
           "multiSelect": True,
           "options": options
       }]
   )
   ```

8. Ricevi risposta dell'utente:
   user_answers = {
       "question_1": [
           "ID 1: hotels-in-rome-luxury-suite.jpg",
           "ID 2: rome-hotel-breakfast.jpg"
       ]
   }

9. Estrai IDs confermati:
   ```python
   from skills.seo-images-manager.helpers import extract_ids_from_labels

   confirmed_ids = extract_ids_from_labels(user_answers['question_1'])
   # Result: [1, 2]
   ```

10. Se nessuna immagine confermata:
    ```python
    if not confirmed_ids:
        print("❌ No images selected. Upload cancelled.")
        exit()
    ```

11. Upload SOLO immagini confermate:
    ```bash
    python scripts/image_manager.py upload \
      --project clients/{client}/{project} \
      --ids {','.join(map(str, confirmed_ids))}
    ```

12. Ricevi risultati upload:
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

13. Mostra risultati all'utente:
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

14. Se alcune immagini sono state skippate:
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

## File di Aiuto Disponibili

- **helpers.py**: Funzioni helper per checkpoint
  - `extract_ids_from_labels(labels)` → List[int]
  - `format_image_for_checkbox(img_data, mode)` → dict
  - `save_selected_plans(selected_ids, images, db_path)`
  - `get_pending_images(db_path, status)` → List[dict]
  - `format_checkpoint_summary(total, selected, action)` → str
  - `update_sync_status(image_id, synced, wp_data, db_path)`

- **UX-CHECKPOINTS.md**: Esempi dettagliati con codice completo

---

## Flowchart Completo

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
│ ⚠️ OBBLIGATORIO - SEMPRE ATTIVO    │
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

1. **SEMPRE mostrare checkpoint prima di upload**
   - Anche se user usa --id 1 (single image)
   - Anche se c'è solo 1 immagine pending
   - È una safety feature

2. **Formattare opzioni in modo leggibile**
   - Label: breve e scannable (max 60 chars)
   - Description: dettagli utili separati da `|`
   - Warnings con emoji: ⚠️

3. **Mostrare next steps dopo ogni checkpoint**
   - Dopo plan: "Next: /seo-images-manager rename --ids 1,2,3"
   - Dopo upload: "Upload later with: /seo-images-manager upload --ids 4,5"

4. **Gestire edge cases**
   - Nessuna immagine selezionata → conferma cancellazione
   - Tutte le immagini skippate → mostra come riprovare
   - Errore upload → mantieni synced=false per retry

---

**Version:** 1.0.0
**Last Updated:** 2026-04-27
**For:** Claude Code execution of seo-images-manager skill
