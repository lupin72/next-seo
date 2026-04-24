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

    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.images_dir = self.project_path / "images" / "original"
        self.db_path = self.project_path / "images" / "images.db"

    def scan_directory(self):
        """Scan images/original/ directory for image files."""
        if not self.images_dir.exists():
            return []

        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        image_files = [
            f for f in self.images_dir.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]

        results = []
        conn = sqlite3.connect(self.db_path)

        for img_file in image_files:
            metadata = self.analyze_image(img_file)

            # Check if already in database
            existing = conn.execute(
                "SELECT id FROM images WHERE original_path = ?",
                (str(img_file),)
            ).fetchone()

            if existing:
                # Update existing record
                conn.execute("""
                    UPDATE images SET
                        dimensions = ?,
                        filesize = ?,
                        mime_type = ?,
                        exif_data = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    json.dumps(metadata['dimensions']),
                    metadata['filesize'],
                    metadata['mime_type'],
                    json.dumps(metadata['exif']),
                    datetime.now().isoformat(),
                    existing[0]
                ))
                image_id = existing[0]
            else:
                # Insert new record
                cursor = conn.execute("""
                    INSERT INTO images (
                        original_filename,
                        original_path,
                        dimensions,
                        filesize,
                        mime_type,
                        exif_data,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    img_file.name,
                    str(img_file),
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
                **metadata
            })

        conn.close()
        return results

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
                    # Convert bytes to string if needed
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


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python image_analyzer.py <project_path>")
        sys.exit(1)

    analyzer = ImageAnalyzer(sys.argv[1])
    results = analyzer.scan_directory()
    print(json.dumps(results, indent=2))
