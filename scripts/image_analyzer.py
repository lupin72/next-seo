#!/usr/bin/env python3
"""
Image Analyzer

Analyzes images in original/ folder:
- Scans directory for image files
- Extracts EXIF metadata
- Calculates dimensions, filesize
- Saves to SQLite database

Dependencies:
    pip install pillow
"""

import json
import mimetypes
import os
import sqlite3
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "Pillow library required. Install with: pip install pillow"
    }))
    exit(1)


class ImageAnalyzer:
    """Analyzes images and saves metadata to database."""

    def __init__(self, project_path, visual_analysis=False):
        """
        Initialize image analyzer.

        Args:
            project_path: Path to project directory
            visual_analysis: If True, generate AI descriptions of image content
        """
        self.project_path = Path(project_path)
        self.images_dir = self.project_path / "images" / "original"
        self.db_path = self.project_path / "images" / "images.db"
        self.visual_analysis = visual_analysis

    def scan_directory(self):
        """
        Scan images/original/ directory and subdirectories for image files.

        Subdirectory names are used as semantic context for the image
        (e.g. "SPA Hotel", "Animazione infantile").
        Images in the root of original/ have no context.
        """
        if not self.images_dir.exists():
            return []

        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

        # Collect images from root and all subdirectories
        image_files = []
        for img_file in self.images_dir.rglob('*'):
            if img_file.is_file() and img_file.suffix.lower() in image_extensions:
                image_files.append(img_file)

        results = []
        conn = sqlite3.connect(self.db_path)

        # Ensure new columns exist (migration for existing DBs)
        self._migrate_db(conn)

        for img_file in image_files:
            metadata = self.analyze_image(img_file)

            # Extract subfolder context: relative path from original/ to the file's parent
            relative_parent = img_file.parent.relative_to(self.images_dir)
            image_context = str(relative_parent) if str(relative_parent) != '.' else None

            # Visual analysis: generate AI description of image content
            visual_context = None
            if self.visual_analysis:
                visual_context = self.describe_image(img_file, image_context)

            # Check if already in database
            existing = conn.execute(
                "SELECT id, visual_context FROM images WHERE original_path = ?",
                (str(img_file),)
            ).fetchone()

            if existing:
                # Update existing record
                update_fields = {
                    'dimensions': json.dumps(metadata['dimensions']),
                    'filesize': metadata['filesize'],
                    'mime_type': metadata['mime_type'],
                    'exif_data': json.dumps(metadata['exif']),
                    'image_context': image_context,
                    'updated_at': datetime.now().isoformat(),
                }
                # Only update visual_context if newly generated (don't overwrite existing)
                if visual_context:
                    update_fields['visual_context'] = visual_context

                set_clause = ', '.join(f"{k} = ?" for k in update_fields)
                conn.execute(
                    f"UPDATE images SET {set_clause} WHERE id = ?",
                    (*update_fields.values(), existing[0])
                )
                image_id = existing[0]
                # Use existing visual_context if not re-analyzed
                if not visual_context and existing[1]:
                    visual_context = existing[1]
            else:
                # Insert new record
                cursor = conn.execute("""
                    INSERT INTO images (
                        original_filename,
                        original_path,
                        image_context,
                        visual_context,
                        dimensions,
                        filesize,
                        mime_type,
                        exif_data,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    img_file.name,
                    str(img_file),
                    image_context,
                    visual_context,
                    json.dumps(metadata['dimensions']),
                    metadata['filesize'],
                    metadata['mime_type'],
                    json.dumps(metadata['exif']),
                    datetime.now().isoformat()
                ))
                image_id = cursor.lastrowid

            conn.commit()

            results.append({
                "id": image_id,
                "filename": img_file.name,
                "path": str(img_file),
                "image_context": image_context,
                "visual_context": visual_context,
                **metadata
            })

        conn.close()
        return results

    def _migrate_db(self, conn):
        """Run database migrations for new columns."""
        columns = [row[1] for row in conn.execute("PRAGMA table_info(images)").fetchall()]

        if 'image_context' not in columns:
            conn.execute("ALTER TABLE images ADD COLUMN image_context TEXT")
        if 'visual_context' not in columns:
            conn.execute("ALTER TABLE images ADD COLUMN visual_context TEXT")
        if 'language' not in columns:
            conn.execute("ALTER TABLE images ADD COLUMN language TEXT")
        conn.commit()

    def analyze_image(self, image_path):
        """Extract metadata from single image."""
        img = Image.open(image_path)

        # Get dimensions
        width, height = img.size

        # Get filesize
        filesize = image_path.stat().st_size

        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(image_path))

        # Extract EXIF data
        exif_data = {}
        try:
            exif = img._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8', errors='ignore')
                        except:
                            value = str(value)
                    exif_data[tag] = value
        except:
            pass

        return {
            "dimensions": {"width": width, "height": height},
            "filesize": filesize,
            "mime_type": mime_type or "image/jpeg",
            "exif": exif_data
        }

    def describe_image(self, image_path, image_context=None):
        """
        Placeholder for visual analysis. Returns None.

        Actual visual analysis is performed by the skill orchestrator using
        Claude's vision capability (Read tool on image files). The skill will:
        1. Read each image with the Read tool
        2. Generate a brief SEO description
        3. Call update_visual_context() to save it

        Args:
            image_path: Path to image file
            image_context: Subfolder context (e.g. "SPA Hotel")

        Returns:
            None (visual analysis done at skill level)
        """
        return None

    @staticmethod
    def update_visual_context(db_path, image_id, visual_context):
        """
        Save AI-generated visual description for an image.

        Called by the skill after Claude analyzes the image visually.

        Args:
            db_path: Path to SQLite database
            image_id: Image ID to update
            visual_context: Brief description (e.g. "children playing in hotel pool")
        """
        conn = sqlite3.connect(db_path)
        conn.execute(
            "UPDATE images SET visual_context = ?, updated_at = ? WHERE id = ?",
            (visual_context, datetime.now().isoformat(), image_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_images_needing_visual_analysis(db_path):
        """
        Get images that have no visual_context yet.

        Returns:
            list: Dicts with id, original_path, image_context
        """
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT id, original_filename, original_path, image_context
            FROM images
            WHERE visual_context IS NULL
            ORDER BY created_at ASC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Image Analyzer')
    parser.add_argument('project_path', help='Project path')
    parser.add_argument('--visual', action='store_true', help='Enable visual analysis')
    args = parser.parse_args()

    analyzer = ImageAnalyzer(args.project_path, visual_analysis=args.visual)
    results = analyzer.scan_directory()
    print(json.dumps(results, indent=2))
