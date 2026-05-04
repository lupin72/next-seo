# Variant Selection Workflow

**Version:** 1.6.0
**Purpose:** Interactive selection of keyword variants after planning

---

## Overview

After `plan` generates 3 scored keyword variants per image, the skill presents an interactive checkpoint where the user selects the best variant for each image.

## Workflow

```python
# 1. Run plan (auto-analyzes new images)
result = bash("python scripts/image_manager.py plan --project {project_path}")
plan_data = result['plan']

# 2. Format data for variant selection
from scripts.image_selector import format_variant_selection_data

selections_data = format_variant_selection_data(plan_data)

# 3. Present variants to user via AskUserQuestion
# For each image in selections_data, create a question

questions = []
for img_data in selections_data:
    question = {
        "question": f"Seleziona la variante migliore per {img_data['original_filename']}",
        "header": f"Img {img_data['image_id']}",
        "multiSelect": False,
        "options": img_data['options']  # Already formatted with label + description
    }
    questions.append(question)

# Use AskUserQuestion tool
answers = AskUserQuestion(questions=questions)

# 4. Process answers into selections dict
selections = {}
for img_data in selections_data:
    image_id = img_data['image_id']
    answer_key = f"img_{image_id}"  # Or however answers are keyed

    # Parse answer to get variant_rank (1, 2, or 3)
    # If answer is "Proponi altra", ask follow-up question for custom keyword

    selections[image_id] = {
        "variant_rank": variant_rank,  # 1, 2, or 3
        "custom_keyword": None  # or custom keyword if "Proponi altra"
    }

# 5. Save selected variants to database
from scripts.image_selector import save_selected_variants
from scripts.image_seo_planner import ImageSEOPlanner

planner = ImageSEOPlanner(project_path, language=language)
result = save_selected_variants(selections, plan_data, project_path, planner)

# 6. Show confirmation
print(f"✅ Saved {result['saved_count']} images")
for img in result['saved_images']:
    print(f"  {img['seo_filename']}")
    print(f"  Alt: {img['alt_text']}")
```

---

## Function Reference

### `format_variant_selection_data(plan_data)`

**Input:** Plan data from `ImageSEOPlanner.create_plan()`

**Output:** List of dicts, one per image:
```json
[
  {
    "image_id": 1,
    "original_filename": "IMG_1234.jpg",
    "image_context": "Piscina Hotel",
    "variants": [...],  // Original 3 variants with scores
    "options": [  // Formatted for AskUserQuestion
      {
        "label": "Variante 1 (Score: 8.0): piscina-hotel-acuazul",
        "description": "Filename: piscina-hotel-acuazul.jpg | Opportunity: 8/10 | Gap: 7/10 | SEO: 9/10"
      },
      // ... 2 more variants
    ]
  }
]
```

### `save_selected_variants(selections, plan_data, project_path, planner)`

**Input:**
- `selections`: Dict mapping image_id -> selection data
  ```python
  {
    1: {"variant_rank": 1, "custom_keyword": None},
    2: {"variant_rank": 2, "custom_keyword": None},
    5: {"variant_rank": None, "custom_keyword": "animacion-piscina-hotel"}
  }
  ```
- `plan_data`: Original plan data (needed to get variant details)
- `project_path`: Project path
- `planner`: ImageSEOPlanner instance

**Output:**
```json
{
  "saved_count": 3,
  "skipped_count": 1,
  "saved_images": [
    {
      "image_id": 1,
      "keyword": "piscina-hotel-acuazul",
      "seo_filename": "piscina-hotel-acuazul.jpg",
      "alt_text": "Piscina hotel acuazul | Hotel familiar"
    }
  ],
  "skipped_images": [3]
}
```

**What it does:**
1. For each selection, finds the corresponding variant in plan_data
2. Gets the keyword (from selected variant or custom)
3. Generates SEO filename (with collision detection)
4. Generates full metadata (alt text, title, caption) using planner
5. Saves to database
6. Returns summary

---

## AskUserQuestion Format

For each image, create a question like this:

```python
{
  "question": "Seleziona la variante migliore per IMG_1234.jpg (context: Piscina Hotel)",
  "header": "Img 1",
  "multiSelect": False,
  "options": [
    {
      "label": "Variante 1 (Score: 8.0): piscina-hotel-acuazul-peniscola",
      "description": "Filename: piscina-hotel-acuazul-peniscola.jpg | Opportunity: 8/10 | Gap: 7/10 | SEO: 9/10"
    },
    {
      "label": "Variante 2 (Score: 7.3): piscina-exterior-hotel-familiar",
      "description": "Filename: piscina-exterior-hotel-familiar.jpg | Opportunity: 7/10 | Gap: 8/10 | SEO: 7/10"
    },
    {
      "label": "Variante 3 (Score: 6.7): zona-bano-hotel-peniscola",
      "description": "Filename: zona-bano-hotel-peniscola.jpg | Opportunity: 6/10 | Gap: 6/10 | SEO: 8/10"
    }
  ]
}
```

**Note:** "Proponi altra" option is automatically added by AskUserQuestion tool, so don't include it in options.

---

## Handling "Proponi altra" (Custom Keyword)

If user selects "Other" (custom keyword):

1. Detect "Other" selection in answers
2. Use AskUserQuestion again to get custom keyword:
   ```python
   {
     "question": "Inserisci keyword personalizzata per IMG_1234.jpg",
     "header": "Custom",
     "options": [
       {"label": "Conferma", "description": "Usa la keyword inserita"}
     ]
   }
   ```
3. User enters custom keyword in text field
4. Add to selections:
   ```python
   selections[image_id] = {
     "variant_rank": None,
     "custom_keyword": "user-entered-keyword"
   }
   ```

---

## Error Handling

**Skipped images:** If user doesn't select any variant, add to selections with `variant_rank: None`. `save_selected_variants()` will skip these and report in `skipped_images`.

**Cannibalization warnings:** Already shown in variant descriptions. If user selects a variant with cannibalization risk, it's their choice (they saw the warning).

**Collision detection:** `generate_seo_filename()` already handles filename collisions by appending `-2`, `-3`, etc.

---

## Example: Full Skill Flow

```
User: /seo-images-manager plan

Step 1: Auto-analyze new images
  → Found 5 new images

Step 2: Generate 3 variants per image
  → 5 images × 3 variants = 15 keyword options

Step 3: Present checkpoint
  → AskUserQuestion for each image
  → User selects best variant for each (or "Proponi altra")

Step 4: Save selected variants
  → Generate metadata for selected variants
  → Save to database

Step 5: Confirm
  → Show saved images with filenames + alt text

Next: /seo-images-manager rename
```

---

## Testing Checklist

- [ ] Plan generates 3 variants per image
- [ ] Variants are sorted by avg_score (highest first)
- [ ] format_variant_selection_data() creates correct options
- [ ] AskUserQuestion displays variants correctly
- [ ] User can select variant 1, 2, or 3
- [ ] User can select "Proponi altra" and enter custom keyword
- [ ] save_selected_variants() generates correct metadata
- [ ] Filename collision detection works
- [ ] Cannibalization warnings are shown
- [ ] Skipped images are tracked correctly
