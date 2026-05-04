#!/usr/bin/env python3
"""
Image Selector - Interactive Image Selection

Shows list of images with checkboxes for selection.
Saves selection to temporary file for use by other commands.

v1.6: Added variant selection functions for interactive keyword selection.

Usage:
    python image_selector.py --project <path> --command <plan|rename|upload>
"""

import json
import sqlite3
import sys
from pathlib import Path


def list_images(project_path, filter_status=None):
    """
    List all images with their current status.

    Args:
        project_path: Path to project directory
        filter_status: Optional filter (all|pending|optimized|synced)

    Returns:
        list: Image records with status information
    """
    db_path = Path(project_path) / "images" / "images.db"

    if not db_path.exists():
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Build query based on filter
    if filter_status == "pending":
        # Images analyzed but not planned
        query = """
            SELECT id, original_filename, seo_filename, target_keyword,
                   optimized_path, synced, filesize
            FROM images
            WHERE seo_filename IS NULL
            ORDER BY created_at ASC
        """
    elif filter_status == "planned":
        # Images planned but not optimized
        query = """
            SELECT id, original_filename, seo_filename, target_keyword,
                   optimized_path, synced, filesize
            FROM images
            WHERE seo_filename IS NOT NULL AND optimized_path IS NULL
            ORDER BY created_at ASC
        """
    elif filter_status == "optimized":
        # Images optimized but not synced
        query = """
            SELECT id, original_filename, seo_filename, target_keyword,
                   optimized_path, synced, filesize
            FROM images
            WHERE optimized_path IS NOT NULL AND synced = 0
            ORDER BY created_at ASC
        """
    elif filter_status == "synced":
        # Images already synced
        query = """
            SELECT id, original_filename, seo_filename, target_keyword,
                   optimized_path, synced, filesize, wordpress_media_id
            FROM images
            WHERE synced = 1
            ORDER BY created_at ASC
        """
    else:
        # All images
        query = """
            SELECT id, original_filename, seo_filename, target_keyword,
                   optimized_path, synced, filesize
            FROM images
            ORDER BY created_at ASC
        """

    images = conn.execute(query).fetchall()
    conn.close()

    # Convert to dict and add status badges
    result = []
    for img in images:
        img_dict = dict(img)

        # Determine status badge
        if img['synced']:
            img_dict['status'] = 'synced'
            img_dict['status_emoji'] = '✅'
        elif img['optimized_path']:
            img_dict['status'] = 'optimized'
            img_dict['status_emoji'] = '⚙️'
        elif img['seo_filename']:
            img_dict['status'] = 'planned'
            img_dict['status_emoji'] = '📝'
        else:
            img_dict['status'] = 'pending'
            img_dict['status_emoji'] = '📸'

        # Format filesize
        if img['filesize']:
            kb = img['filesize'] / 1024
            img_dict['filesize_formatted'] = f"{kb:.1f} KB"

        result.append(img_dict)

    return result


def format_image_list(images, for_selection=False):
    """Format images as selectable list for Claude."""
    if not images:
        return "No images found."

    output = []

    if for_selection:
        output.append("**Seleziona le immagini da processare:**\n")

    for img in images:
        status = img['status_emoji']
        filename = img['original_filename']
        seo_name = img['seo_filename'] or "—"
        keyword = img['target_keyword'] or "—"
        size = img.get('filesize_formatted', '—')

        line = f"{status} **ID {img['id']}** | {filename}"

        if img['status'] == 'planned':
            line += f" → {seo_name}"
        elif img['status'] == 'optimized':
            line += f" → {seo_name} | {size}"
        elif img['status'] == 'synced':
            line += f" → {seo_name} | WP #{img.get('wordpress_media_id', '?')}"

        if keyword != "—":
            line += f" | KW: {keyword}"

        output.append(line)

    return "\n".join(output)


def format_variant_selection_data(plan_data):
    """
    Format plan data for variant selection checkpoint.

    Returns structured data ready for AskUserQuestion tool.
    Each image gets a question with 3 variant options + "Proponi altra".

    Args:
        plan_data: Output from ImageSEOPlanner.create_plan()

    Returns:
        dict: Formatted data for variant selection
    """
    selections_data = []

    for image_proposal in plan_data['images']:
        image_id = image_proposal['image_id']
        original_filename = image_proposal['original_filename']
        image_context = image_proposal.get('image_context', '')
        variants = image_proposal['variants']

        # Build options for this image (3 variants)
        options = []
        for v in variants[:3]:
            # Format: "Variante 1 (Score: 8.0): piscina-hotel-acuazul"
            option_label = f"Variante {v['rank']} (Score: {v['avg_score']}): {v['keyword']}"

            # Description with scoring breakdown
            desc_parts = [
                f"Filename: {v['filename']}",
                f"Opportunity: {v['opportunity_score']}/10",
                f"Gap: {v['gap_score']}/10",
                f"SEO: {v['seo_score']}/10"
            ]

            if v['cannibalization_risk']:
                desc_parts.append(f"⚠️ {v['cannibalization_note']}")

            option_desc = " | ".join(desc_parts)

            options.append({
                "label": option_label,
                "description": option_desc
            })

        selections_data.append({
            "image_id": image_id,
            "original_filename": original_filename,
            "image_context": image_context,
            "variants": variants,
            "options": options
        })

    return selections_data


def format_upload_selection_data(project_path):
    """
    Format optimized images for upload checkpoint.

    Returns structured data ready for AskUserQuestion tool.
    Shows images ready for WordPress upload with metadata preview.

    Args:
        project_path: Project path

    Returns:
        dict: Formatted data for upload checkpoint
    """
    db_path = Path(project_path) / "images" / "images.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get images ready for upload
    images = conn.execute("""
        SELECT id, original_filename, seo_filename, optimized_path,
               alt_text, title, caption, target_keyword, filesize
        FROM images
        WHERE synced = 0 AND optimized_path IS NOT NULL
        ORDER BY created_at ASC
    """).fetchall()

    conn.close()

    if not images:
        return {
            "ready_count": 0,
            "images": [],
            "options": []
        }

    # Build options for AskUserQuestion
    options = []
    images_data = []

    for img in images:
        # Calculate optimized filesize
        optimized_path = Path(img['optimized_path'])
        if optimized_path.exists():
            optimized_size = optimized_path.stat().st_size
            size_kb = optimized_size / 1024
            size_formatted = f"{size_kb:.1f} KB"
        else:
            size_formatted = "—"

        # Format option label
        option_label = f"ID {img['id']}: {img['seo_filename']} ({size_formatted})"

        # Format option description with metadata preview
        desc_parts = [
            f"Alt: {img['alt_text'][:60]}..." if img['alt_text'] and len(img['alt_text']) > 60 else f"Alt: {img['alt_text'] or '—'}",
            f"Keyword: {img['target_keyword'] or '—'}"
        ]
        option_desc = " | ".join(desc_parts)

        options.append({
            "label": option_label,
            "description": option_desc
        })

        images_data.append({
            "image_id": img['id'],
            "original_filename": img['original_filename'],
            "seo_filename": img['seo_filename'],
            "optimized_path": img['optimized_path'],
            "size_formatted": size_formatted,
            "alt_text": img['alt_text'],
            "title": img['title'],
            "caption": img['caption'],
            "target_keyword": img['target_keyword']
        })

    return {
        "ready_count": len(images),
        "images": images_data,
        "options": options
    }


def save_selected_variants(selections, plan_data, project_path, planner):
    """
    Save selected keyword variants to database with full metadata.

    Args:
        selections: Dict mapping image_id -> dict with:
            - variant_rank: 1, 2, or 3
            - custom_keyword: Optional custom keyword if user chose "Proponi altra"
        plan_data: Original plan data from ImageSEOPlanner.create_plan()
        project_path: Project path
        planner: ImageSEOPlanner instance for generating metadata

    Returns:
        dict: Result with saved count and details
    """
    db_path = Path(project_path) / "images" / "images.db"
    conn = sqlite3.connect(db_path)

    saved_images = []
    skipped_images = []

    # Build lookup for plan data by image_id
    plan_lookup = {img['image_id']: img for img in plan_data['images']}

    for image_id, selection_data in selections.items():
        if not selection_data or selection_data.get('variant_rank') is None:
            skipped_images.append(image_id)
            continue

        # Get plan data for this image
        image_plan = plan_lookup.get(image_id)
        if not image_plan:
            skipped_images.append(image_id)
            continue

        # Get selected variant or custom keyword
        custom_keyword = selection_data.get('custom_keyword')
        if custom_keyword:
            keyword = custom_keyword
        else:
            variant_rank = selection_data['variant_rank']
            # Find variant by rank
            selected_variant = next(
                (v for v in image_plan['variants'] if v['rank'] == variant_rank),
                None
            )
            if not selected_variant:
                skipped_images.append(image_id)
                continue
            keyword = selected_variant['keyword']

        # Get image context
        image_context = image_plan.get('image_context')
        visual_context = image_plan.get('visual_context')

        # Get site context
        site_context = {'project_specs': planner.project_specs}

        # Generate SEO filename (check for collisions)
        existing_filenames = planner.get_existing_seo_filenames(conn)
        seo_filename = planner.generate_seo_filename(keyword, existing_filenames)

        # Generate metadata
        alt_text = planner.generate_alt_text(keyword, image_context, site_context)
        title = planner.generate_title(keyword)
        caption = planner.generate_caption(keyword, image_context)

        # Save to database
        conn.execute("""
            UPDATE images
            SET target_keyword = ?,
                seo_filename = ?,
                alt_text = ?,
                title = ?,
                caption = ?,
                language = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            keyword,
            seo_filename,
            alt_text,
            title,
            caption,
            planner.language,
            image_id
        ))

        saved_images.append({
            "image_id": image_id,
            "keyword": keyword,
            "seo_filename": seo_filename,
            "alt_text": alt_text
        })

    conn.commit()
    conn.close()

    return {
        "saved_count": len(saved_images),
        "skipped_count": len(skipped_images),
        "saved_images": saved_images,
        "skipped_images": skipped_images
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="List and select images")
    parser.add_argument("--project", required=True, help="Project path")
    parser.add_argument("--filter", choices=['all', 'pending', 'planned', 'optimized', 'synced'],
                       default='all', help="Filter images by status")
    parser.add_argument("--format", choices=['json', 'text'], default='json',
                       help="Output format")

    args = parser.parse_args()

    images = list_images(args.project, args.filter)

    if args.format == 'json':
        print(json.dumps({
            "success": True,
            "total": len(images),
            "images": images
        }, indent=2))
    else:
        print(format_image_list(images, for_selection=True))
