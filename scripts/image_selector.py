#!/usr/bin/env python3
"""
Image Selector - Interactive Image Selection

Shows list of images with checkboxes for selection.
Saves selection to temporary file for use by other commands.

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
