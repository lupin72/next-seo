#!/usr/bin/env python3
"""
Helper Functions for SEO Images Manager Checkpoints

Provides utility functions for interactive checkpoint implementation:
- ID extraction from AskUserQuestion labels
- File size formatting
- Image data formatting for checkbox display
- Database updates for selected plans
"""

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


def extract_ids_from_labels(labels: List[str]) -> List[int]:
    """
    Extract image IDs from AskUserQuestion selected labels.

    Args:
        labels: List of selected labels in format "ID {id}: filename"

    Returns:
        List of extracted integer IDs

    Example:
        >>> extract_ids_from_labels(["ID 1: IMG_1234.jpg", "ID 5: photo.png"])
        [1, 5]
    """
    ids = []
    for label in labels:
        match = re.match(r'ID\s+(\d+):', label)
        if match:
            ids.append(int(match.group(1)))
    return ids


def format_filesize(bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        bytes: File size in bytes

    Returns:
        Formatted string (e.g., "450 KB", "2.5 MB")

    Example:
        >>> format_filesize(460800)
        "450 KB"
        >>> format_filesize(2621440)
        "2.5 MB"
    """
    kb = bytes / 1024
    if kb > 1024:
        mb = kb / 1024
        return f"{mb:.1f} MB"
    else:
        return f"{kb:.0f} KB"


def format_image_for_checkbox(
    image_data: Dict[str, Any],
    mode: str = "plan"
) -> Dict[str, str]:
    """
    Format image data for AskUserQuestion checkbox option.

    Args:
        image_data: Image dictionary with id, filename, metadata, etc.
        mode: Checkpoint mode ("plan", "rename", "upload")

    Returns:
        Dict with "label" and "description" keys for checkbox

    Example:
        >>> img = {
        ...     "id": 1,
        ...     "original_filename": "IMG_1234.jpg",
        ...     "seo_filename": "hotels-in-rome.jpg",
        ...     "selected_keyword": "hotels in rome luxury suite",
        ...     "alt_text": "Hotels in rome luxury suite - Top 10...",
        ...     "filesize": 460800,
        ...     "cannibalization_risk": False
        ... }
        >>> format_image_for_checkbox(img, "plan")
        {
            "label": "ID 1: IMG_1234.jpg → hotels-in-rome.jpg",
            "description": "Keyword: hotels in rome luxury suite | Alt: Hotels in rome luxury suite - Top 10..."
        }
    """
    image_id = image_data['id']
    original_filename = image_data.get('original_filename', '')

    if mode == "plan":
        # Plan checkpoint: show original → SEO filename, keyword, alt
        seo_filename = image_data.get('seo_filename', '')
        keyword = image_data.get('selected_keyword', '')
        alt_text = image_data.get('alt_text', '')[:50]

        label = f"ID {image_id}: {original_filename[:30]}"
        if seo_filename:
            label += f" → {seo_filename[:30]}"

        description = f"Keyword: {keyword} | Alt: {alt_text}..."

        # Add warning if cannibalization risk
        if image_data.get('cannibalization_risk'):
            description += " ⚠️ Rischio cannibalization"

    elif mode == "rename":
        # Rename checkpoint: show compression metrics
        seo_filename = image_data.get('seo_filename', '')
        original_size = image_data.get('original_size', 0)
        optimized_size = image_data.get('optimized_size', 0)
        compression_ratio = ((original_size - optimized_size) / original_size) if original_size > 0 else 0

        label = f"ID {image_id}: {seo_filename}"
        description = (
            f"Original: {format_filesize(original_size)} → "
            f"Optimized: {format_filesize(optimized_size)} | "
            f"{compression_ratio*100:.0f}% saved"
        )

        # Add warning if very aggressive compression (>85%)
        if compression_ratio > 0.85:
            description += " ⚠️ Compressione molto aggressiva"

    elif mode == "upload":
        # Upload checkpoint: show filename, size, alt text
        seo_filename = image_data.get('seo_filename', '')
        filesize = image_data.get('filesize', 0)
        alt_text = image_data.get('alt_text', '')[:60]

        label = f"ID {image_id}: {seo_filename}"
        description = f"{format_filesize(filesize)} | Alt: {alt_text}..."

    else:
        # Generic format
        label = f"ID {image_id}: {original_filename}"
        description = "Image data"

    return {
        "label": label,
        "description": description
    }


def save_selected_plans(
    selected_ids: List[int],
    all_images: List[Dict[str, Any]],
    db_path: Path
) -> None:
    """
    Save SEO metadata to database ONLY for selected images.

    Args:
        selected_ids: List of image IDs selected by user
        all_images: List of all images with proposed metadata
        db_path: Path to SQLite database

    Side Effects:
        Updates `images` table with seo_filename, alt_text, etc. for selected IDs

    Example:
        >>> selected_ids = [1, 2, 5]
        >>> all_images = [...]  # From plan result
        >>> save_selected_plans(selected_ids, all_images, db_path)
        # Updates database for images 1, 2, 5 only
    """
    conn = sqlite3.connect(db_path)
    now = datetime.utcnow().isoformat()

    try:
        for img in all_images:
            if img['id'] in selected_ids:
                # Update database with SEO metadata
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
                        page_context = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    img['seo_metadata']['filename'],
                    img['seo_metadata']['alt_text'],
                    img['seo_metadata']['title'],
                    img['seo_metadata'].get('caption', ''),
                    img['selected_keyword'],
                    img.get('target_url', ''),
                    img.get('page_h1', ''),
                    img.get('page_title', ''),
                    img.get('page_context', ''),
                    now,
                    img['id']
                ))

        conn.commit()
    finally:
        conn.close()


def get_pending_images(
    db_path: Path,
    status: str = "pending"
) -> List[Dict[str, Any]]:
    """
    Get images by status for checkpoint display.

    Args:
        db_path: Path to SQLite database
        status: Image status to filter
            - "pending": Images without seo_filename
            - "planned": Images with seo_filename but no optimized_path
            - "optimized": Images with optimized_path but synced=0
            - "synced": Images with synced=1

    Returns:
        List of image dictionaries

    Example:
        >>> pending = get_pending_images(db_path, "optimized")
        >>> # Returns images ready for upload
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    if status == "pending":
        query = """
            SELECT id, original_filename, filesize, created_at
            FROM images
            WHERE seo_filename IS NULL
            ORDER BY created_at ASC
        """
    elif status == "planned":
        query = """
            SELECT id, original_filename, seo_filename, target_keyword, filesize
            FROM images
            WHERE seo_filename IS NOT NULL AND optimized_path IS NULL
            ORDER BY created_at ASC
        """
    elif status == "optimized":
        query = """
            SELECT id, original_filename, seo_filename, target_keyword,
                   optimized_path, filesize, alt_text, title, caption
            FROM images
            WHERE optimized_path IS NOT NULL AND synced = 0
            ORDER BY created_at ASC
        """
    elif status == "synced":
        query = """
            SELECT id, original_filename, seo_filename, target_keyword,
                   wordpress_media_id, wordpress_url, uploaded_at
            FROM images
            WHERE synced = 1
            ORDER BY uploaded_at DESC
        """
    else:
        query = """
            SELECT id, original_filename, seo_filename, synced
            FROM images
            ORDER BY created_at ASC
        """

    results = conn.execute(query).fetchall()
    conn.close()

    return [dict(row) for row in results]


def update_sync_status(
    image_id: int,
    synced: bool,
    wordpress_data: Optional[Dict[str, Any]],
    db_path: Path
) -> None:
    """
    Update image sync status after WordPress upload.

    Args:
        image_id: Image ID to update
        synced: Sync status (True = uploaded, False = failed)
        wordpress_data: Dict with wordpress_media_id, wordpress_url (if synced=True)
        db_path: Path to SQLite database

    Side Effects:
        Updates `synced`, `wordpress_media_id`, `wordpress_url`, `uploaded_at` in database

    Example:
        >>> wp_data = {
        ...     "wordpress_media_id": 123,
        ...     "wordpress_url": "https://example.com/wp-content/uploads/image.jpg"
        ... }
        >>> update_sync_status(1, True, wp_data, db_path)
    """
    conn = sqlite3.connect(db_path)
    now = datetime.utcnow().isoformat()

    try:
        if synced and wordpress_data:
            conn.execute("""
                UPDATE images SET
                    synced = 1,
                    wordpress_media_id = ?,
                    wordpress_url = ?,
                    uploaded_at = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                wordpress_data.get('wordpress_media_id'),
                wordpress_data.get('wordpress_url'),
                now,
                now,
                image_id
            ))
        else:
            # Failed upload - keep synced = 0
            conn.execute("""
                UPDATE images SET
                    updated_at = ?
                WHERE id = ?
            """, (now, image_id))

        conn.commit()
    finally:
        conn.close()


def format_checkpoint_summary(
    total: int,
    selected: int,
    action: str
) -> str:
    """
    Format summary message after checkpoint selection.

    Args:
        total: Total number of images shown
        selected: Number of images selected by user
        action: Action performed ("plan", "upload", etc.)

    Returns:
        Formatted summary string

    Example:
        >>> format_checkpoint_summary(5, 3, "plan")
        "✅ SEO plan saved for 3 images\\n⏭️ Skipped 2 images"
    """
    skipped = total - selected

    if action == "plan":
        msg = f"✅ SEO plan saved for {selected} image{'s' if selected != 1 else ''}"
    elif action == "upload":
        msg = f"✅ {selected} image{'s' if selected != 1 else ''} uploaded successfully"
    else:
        msg = f"✅ {selected} image{'s' if selected != 1 else ''} processed"

    if skipped > 0:
        msg += f"\n⏭️ Skipped {skipped} image{'s' if skipped != 1 else ''}"

    return msg


if __name__ == "__main__":
    # Self-test
    print("Testing helper functions...")

    # Test extract_ids_from_labels
    labels = ["ID 1: IMG_1234.jpg", "ID 5: photo.png", "ID 10: test.jpg"]
    ids = extract_ids_from_labels(labels)
    assert ids == [1, 5, 10], f"Expected [1, 5, 10], got {ids}"
    print("✓ extract_ids_from_labels")

    # Test format_filesize
    assert format_filesize(460800) == "450 KB"
    assert format_filesize(2621440) == "2.5 MB"
    assert format_filesize(1024) == "1 KB"
    print("✓ format_filesize")

    # Test format_image_for_checkbox
    img = {
        "id": 1,
        "original_filename": "IMG_1234.jpg",
        "seo_filename": "hotels-in-rome.jpg",
        "selected_keyword": "hotels in rome",
        "alt_text": "Hotels in rome luxury suite",
        "filesize": 460800,
        "cannibalization_risk": False
    }
    result = format_image_for_checkbox(img, "plan")
    assert "ID 1:" in result["label"]
    assert "Keyword:" in result["description"]
    print("✓ format_image_for_checkbox")

    # Test format_checkpoint_summary
    summary = format_checkpoint_summary(5, 3, "plan")
    assert "3 images" in summary
    assert "Skipped 2" in summary
    print("✓ format_checkpoint_summary")

    print("\n✅ All tests passed!")
