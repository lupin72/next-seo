# UX Checkpoints: Implementazione Pratica

**Documento di riferimento per implementare i checkpoint interattivi nella skill seo-images-manager**

---

## 1. Overview

Questo documento fornisce esempi pratici di come usare `AskUserQuestion` con `multiSelect: true` per implementare i checkpoint di selezione nelle fasi:
1. **Plan** → Selezione immagini da ottimizzare
2. **Rename** → Verifica compressione (opzionale)
3. **Upload** → Conferma upload WordPress (OBBLIGATORIO)

---

## 2. Checkpoint #1: Selezione dopo Plan

### 2.1 Quando Attivare

**Trigger:** Dopo aver generato keyword proposals con `/seo-images-manager plan <url>`

**Condizione:** Ci sono 2+ immagini con proposte di keyword

### 2.2 Codice Implementazione

```python
# Dopo aver eseguito: python scripts/image_manager.py plan --project <path> --url <url>
# E ricevuto il JSON con le proposte

plan_result = json.loads(plan_output)
images = plan_result['plan']['images']

# Formatta opzioni per AskUserQuestion
options = []
for img in images:
    # Label: breve descrizione (max 60 chars)
    label = f"ID {img['id']}: {img['original_filename'][:30]}"

    # Description: dettagli SEO proposti
    description = (
        f"Keyword: {img['selected_keyword']} | "
        f"Filename: {img['seo_metadata']['filename'][:40]} | "
        f"Alt: {img['seo_metadata']['alt_text'][:50]}..."
    )

    # Aggiungi warning se c'è rischio cannibalization
    if img.get('cannibalization_risk'):
        description += " ⚠️ Rischio cannibalization"

    options.append({
        "label": label,
        "description": description
    })

# Usa AskUserQuestion
AskUserQuestion(
    questions=[{
        "question": "Quali immagini vuoi ottimizzare con queste keyword proposte?",
        "header": "Selezione",
        "multiSelect": True,
        "options": options
    }]
)
```

### 2.3 Output Atteso (UI)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Quali immagini vuoi ottimizzare con queste keyword proposte?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

☑ ID 1: IMG_1234.jpg
  Keyword: hotels in rome luxury suite | Filename: hotels-in-rome-luxu... | Alt: Hotels in rome luxury suite - Top 10...

☑ ID 2: IMG_5678.jpg
  Keyword: rome hotel breakfast buffet | Filename: rome-hotel-breakfas... | Alt: Rome hotel breakfast buffet - Top...

☐ ID 3: photo_01.png
  Keyword: rome hotel rooftop | Filename: rome-hotel-rooftop... | Alt: Rome hotel rooftop terrace - Top... ⚠️ Rischio cannibalization

☑ ID 4: IMG_9999.jpg
  Keyword: rome hotel spa wellness | Filename: rome-hotel-spa-welln... | Alt: Rome hotel spa wellness center - Top...

[Conferma selezione]
```

### 2.4 Post-Selezione

```python
# Ricevi la risposta dall'utente
selected_labels = user_answers['question_1']  # Lista di label selezionati

# Estrai gli ID dalle label (formato: "ID 1: filename")
selected_ids = []
for label in selected_labels:
    match = re.match(r'ID (\d+):', label)
    if match:
        selected_ids.append(int(match.group(1)))

# Aggiorna database SOLO per le immagini selezionate
for img in images:
    if img['id'] in selected_ids:
        # Salva seo_filename, alt_text, etc.
        save_seo_metadata_to_db(img['id'], img['seo_metadata'])

# Conferma all'utente
print(f"✅ SEO plan saved for {len(selected_ids)} images")
print(f"⏭️ Skipped {len(images) - len(selected_ids)} images")
print(f"\nNext: /seo-images-manager rename --ids {','.join(map(str, selected_ids))}")
```

---

## 3. Checkpoint #2: Verifica Compressione (Opzionale)

### 3.1 Quando Attivare

**Trigger:** Dopo aver eseguito `/seo-images-manager rename`

**Condizione:** Almeno 1 immagine ha compression_ratio > 85% (molto aggressivo)

**Nota:** Questo checkpoint è OPZIONALE. Attivare solo se ci sono warning sulla compressione.

### 3.2 Codice Implementazione

```python
# Dopo rename, controlla risultati
optimization_results = json.loads(rename_output)['results']

# Filtra immagini con compressione molto aggressiva
high_compression = [
    img for img in optimization_results
    if img['compression_ratio'] > 0.85  # >85% riduzione
]

if high_compression:
    # Mostra warning e chiedi conferma
    options = []
    for img in high_compression:
        label = f"ID {img['id']}: {img['seo_filename']}"
        description = (
            f"Original: {img['original_size_mb']:.1f} MB → "
            f"Optimized: {img['optimized_size_mb']:.1f} MB | "
            f"⚠️ {img['compression_ratio_percent']}% riduzione (molto aggressivo)"
        )
        options.append({"label": label, "description": description})

    AskUserQuestion(
        questions=[{
            "question": "Alcune immagini hanno compressione molto aggressiva. Vuoi tenerle o escluderle?",
            "header": "Verifica",
            "multiSelect": True,
            "options": options
        }]
    )

    # Se user deseleziona alcune immagini, eliminale da images/optimized/
    # e rimuovi optimized_path dal database
else:
    # Nessun warning, procedi
    print("✅ All images optimized successfully")
```

### 3.3 Output Atteso

```
⚠️ Alcune immagini hanno compressione molto aggressiva

Vuoi tenerle o escluderle?

☑ ID 2: rome-hotel-breakfast-buffet.jpg
  Original: 3.8 MB → Optimized: 0.5 MB | ⚠️ 86% riduzione (molto aggressivo)

☑ ID 5: rome-colosseum-hotel-view.jpg
  Original: 1.5 MB → Optimized: 0.2 MB | ⚠️ 87% riduzione (molto aggressivo)

[Conferma selezione]
```

**Se user deseleziona ID 2:**
```
✅ Kept 1 image (ID 5)
🗑️ Removed 1 image (ID 2) - you can re-optimize later with lower compression
```

---

## 4. Checkpoint #3: Conferma Upload WordPress (OBBLIGATORIO)

### 4.1 Quando Attivare

**Trigger:** SEMPRE prima di `/seo-images-manager upload`

**Condizione:** Ci sono 1+ immagini con `optimized_path` e `synced = false`

**Nota:** Questo checkpoint è **SEMPRE OBBLIGATORIO** per evitare upload accidentali.

### 4.2 Codice Implementazione

```python
# Prima di upload, SEMPRE chiedere conferma
# Leggi immagini pronte per upload
pending_uploads = get_pending_uploads(project_path)

if not pending_uploads:
    print("❌ No images ready for upload")
    print("Run /seo-images-manager list --filter optimized to see pending images")
    exit(1)

# Leggi configurazione WordPress
wp_config = load_wordpress_config(project_path)
wp_url = wp_config['site_url']
wp_folder = wp_config.get('media_folder', 'seo-optimized')

# Mostra riepilogo
print(f"⚠️ CONFERMA UPLOAD SU WORDPRESS\n")
print(f"Stai per caricare {len(pending_uploads)} immagini su:")
print(f"  WordPress: {wp_url}")
print(f"  Media Folder: {wp_folder}/\n")
print("━" * 60 + "\n")

# Formatta opzioni per checkbox
options = []
for img in pending_uploads:
    label = f"ID {img['id']}: {img['seo_filename']}"

    # Calcola dimensione in KB o MB
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

# CHECKPOINT OBBLIGATORIO
AskUserQuestion(
    questions=[{
        "question": f"Confermi l'upload di queste {len(pending_uploads)} immagini su WordPress?",
        "header": "Conferma",
        "multiSelect": True,
        "options": options
    }]
)
```

### 4.3 Output Atteso

```
⚠️ CONFERMA UPLOAD SU WORDPRESS

Stai per caricare 4 immagini su:
  WordPress: https://example.com
  Media Folder: seo-optimized/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Confermi l'upload di queste 4 immagini su WordPress?

☑ ID 1: hotels-in-rome-luxury-suite.jpg
  450 KB | Alt: Hotels in rome luxury suite - Top 10 Hotels in Rome

☑ ID 2: rome-hotel-breakfast-buffet.jpg
  520 KB | Alt: Rome hotel breakfast buffet - Top 10 Hotels in Rome

☑ ID 4: rome-hotel-spa-wellness.jpg
  320 KB | Alt: Rome hotel spa wellness center - Top 10 Hotels in Rome

☑ ID 5: rome-colosseum-hotel-view.jpg
  420 KB | Alt: Rome colosseum hotel view - Top 10 Hotels in Rome

[Conferma selezione]
```

### 4.4 Post-Conferma

```python
# Ricevi selezione utente
selected_labels = user_answers['question_1']

# Estrai ID selezionati
selected_ids = extract_ids_from_labels(selected_labels)

if not selected_ids:
    print("❌ No images selected. Upload cancelled.")
    exit(0)

# Upload solo delle immagini confermate
print(f"\n⬆️ Uploading {len(selected_ids)} images to WordPress...\n")

upload_results = []
for img_id in selected_ids:
    try:
        result = upload_to_wordpress(img_id, project_path)
        upload_results.append(result)

        print(f"✓ {result['filename']}")
        print(f"  WordPress Media ID: {result['wordpress_media_id']}")
        print(f"  URL: {result['wordpress_url']}\n")

        # Aggiorna database: synced = true
        update_sync_status(img_id, True, result)

    except Exception as e:
        print(f"✗ Failed to upload ID {img_id}: {str(e)}\n")

# Riepilogo
print("━" * 60)
print(f"\n✅ {len(upload_results)} images uploaded successfully")

skipped = len(pending_uploads) - len(selected_ids)
if skipped > 0:
    skipped_ids = [img['id'] for img in pending_uploads if img['id'] not in selected_ids]
    print(f"⏭️ {skipped} image(s) skipped - can be uploaded later with:")
    print(f"   /seo-images-manager upload --ids {','.join(map(str, skipped_ids))}")
```

---

## 5. Esempio Completo: Flusso con 3 Checkpoint

```python
# ═══════════════════════════════════════════════════════════
# FASE 1: ANALYZE
# ═══════════════════════════════════════════════════════════
result = run_command("python scripts/image_manager.py analyze --project clients/prova/test")
print(f"✅ Found {result['images_found']} new images")

# ═══════════════════════════════════════════════════════════
# FASE 2: LIST PENDING
# ═══════════════════════════════════════════════════════════
result = run_command("python scripts/image_manager.py list --project clients/prova/test --filter pending")
print(f"📊 {result['total']} images ready for planning")

# ═══════════════════════════════════════════════════════════
# FASE 3: PLAN + CHECKPOINT #1
# ═══════════════════════════════════════════════════════════
result = run_command("python scripts/image_manager.py plan --project clients/prova/test --url https://example.com/blog/post")
images = result['plan']['images']

# CHECKPOINT: Selezione keyword
options = [
    {
        "label": f"ID {img['id']}: {img['original_filename'][:30]}",
        "description": f"Keyword: {img['selected_keyword']} | Alt: {img['seo_metadata']['alt_text'][:50]}..."
    }
    for img in images
]

selected = AskUserQuestion(
    questions=[{
        "question": "Quali immagini vuoi ottimizzare?",
        "header": "Selezione",
        "multiSelect": True,
        "options": options
    }]
)

selected_ids = extract_ids_from_labels(selected['answers']['question_1'])
save_selected_plans(selected_ids, images)

# ═══════════════════════════════════════════════════════════
# FASE 4: RENAME
# ═══════════════════════════════════════════════════════════
result = run_command(f"python scripts/image_manager.py rename --project clients/prova/test --ids {','.join(map(str, selected_ids))}")
print(f"✅ {result['processed']} images optimized")

# CHECKPOINT #2 (opzionale): Solo se compressione > 85%
high_compression = [r for r in result['results'] if r['compression_ratio'] > 0.85]
if high_compression:
    # Mostra warning...
    pass

# ═══════════════════════════════════════════════════════════
# FASE 5: LIST OPTIMIZED
# ═══════════════════════════════════════════════════════════
result = run_command("python scripts/image_manager.py list --project clients/prova/test --filter optimized")
print(f"📊 {result['total']} images ready for upload")

# ═══════════════════════════════════════════════════════════
# FASE 6: UPLOAD + CHECKPOINT #3 (OBBLIGATORIO)
# ═══════════════════════════════════════════════════════════
pending = get_pending_uploads("clients/prova/test")

# CHECKPOINT: Conferma upload (SEMPRE)
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
        "question": f"Confermi l'upload di {len(pending)} immagini su WordPress?",
        "header": "Conferma",
        "multiSelect": True,
        "options": options
    }]
)

confirmed_ids = extract_ids_from_labels(confirmed['answers']['question_1'])
upload_images(confirmed_ids)

# ═══════════════════════════════════════════════════════════
# FASE 7: STATUS FINALE
# ═══════════════════════════════════════════════════════════
result = run_command("python scripts/image_manager.py status --project clients/prova/test")
print(f"📊 Synced: {result['synced']} | Pending: {result['pending']}")
```

---

## 6. Helper Functions

### 6.1 Estrazione ID da Label

```python
import re

def extract_ids_from_labels(labels):
    """
    Estrae gli ID dalle label selezionate dall'utente.

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

### 6.2 Formattazione Dimensione File

```python
def format_filesize(bytes):
    """Formatta dimensione file in KB o MB."""
    kb = bytes / 1024
    if kb > 1024:
        return f"{kb/1024:.1f} MB"
    else:
        return f"{kb:.0f} KB"
```

### 6.3 Salvataggio Piano SEO

```python
def save_selected_plans(selected_ids, all_images):
    """
    Salva seo_filename, alt_text, etc. SOLO per le immagini selezionate.

    Args:
        selected_ids: Lista di ID selezionati dall'utente
        all_images: Lista completa di immagini con proposte
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
- Breve e scannable: `ID 1: filename.jpg`
- Include ID per tracciabilità
- Max 60 caratteri

**DON'T:**
- Troppo lungo: `ID 1: IMG_1234_final_version_edited_compressed.jpg → hotels-in-rome-luxury-suite-top-10-best-hotels.jpg`
- Senza ID: `filename.jpg` (impossibile estrarre ID dopo)

### 7.2 Description Format

**DO:**
- Informazioni chiave separate da `|`
- Preview troncati con `...`
- Warning con emoji: `⚠️`

**DON'T:**
- Troppo verboso
- Informazioni ridondanti

### 7.3 Checkpoint Frequency

**SEMPRE:**
- Prima di upload WordPress (modifiche remote)
- Quando ci sono alternative da valutare (keyword cannibalization)

**MAI:**
- Dopo operazioni reversibili (list, status)
- Quando c'è solo 1 opzione possibile

**OPZIONALE:**
- Dopo compressione (solo se warning)
- Prima di batch operations (solo se >10 items)

---

## 8. Testing Checklist

- [ ] Checkpoint #1 mostra tutte le immagini pianificate
- [ ] Label formato: `ID {id}: {filename}`
- [ ] Description include keyword, filename, alt (troncati)
- [ ] Selezione multipla funziona (2+ checkbox)
- [ ] Deselezionare alcune immagini funziona
- [ ] ID estratti correttamente dalle label
- [ ] Database aggiornato SOLO per immagini selezionate
- [ ] Checkpoint #3 SEMPRE attivo prima upload
- [ ] URL WordPress mostrato prima conferma
- [ ] Upload procede SOLO per immagini confermate
- [ ] Immagini skipped tracciate correttamente

---

**Version:** 1.0.0
**Last Updated:** 2026-04-27
**Maintainer:** Pier Paolo Gorelli
