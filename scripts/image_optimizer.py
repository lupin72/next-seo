#!/usr/bin/env python3
"""
Image Optimizer

Optimizes images based on SEO plan:
- Renames files with SEO-friendly filenames
- Compresses images (quality 85%)
- Resizes to max 1600px width
- Converts to WebP (optional)
- Moves to optimized/ folder

Dependencies:
    pip install pillow
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "Pillow library required. Install with: pip install pillow"
    }))
    exit(1)


class ImageOptimizer:
    """Optimizes images for web and SEO."""

    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.original_dir = self.project_path / "images" / "original"
        self.optimized_dir = self.project_path / "images" / "optimized"
        self.db_path = self.project_path / "images" / "images.db"

        # Create optimized directory
        self.optimized_dir.mkdir(parents=True, exist_ok=True)

    def process_all(self):
        """
        Process all images with SEO metadata.

        Returns:
            list: Optimization results for each image
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Get images with SEO metadata but not yet optimized
        images = conn.execute("""
            SELECT id, original_filename, original_path, seo_filename,
                   alt_text, title, caption
            FROM images
            WHERE seo_filename IS NOT NULL AND optimized_path IS NULL
            ORDER BY created_at ASC
        """).fetchall()

        if not images:
            conn.close()
            return []

        results = []
        for img in images:
            result = self.optimize_image(
                image_id=img['id'],
                original_path=img['original_path'],
                seo_filename=img['seo_filename'],
                conn=conn
            )
            results.append(result)

        conn.close()
        return results

    def optimize_image(self, image_id, original_path, seo_filename, conn):
        """
        Optimize single image.

        Steps:
        1. Open image
        2. Resize if needed (max 1600px width)
        3. Compress (quality 85%)
        4. Save with SEO filename
        5. Update database with optimized path
        6. Record optimization metrics
        """
        try:
            original_path = Path(original_path)
            img = Image.open(original_path)

            # Get original dimensions and filesize
            original_width, original_height = img.size
            original_size = original_path.stat().st_size

            # Resize if needed (max width 1600px, maintain aspect ratio)
            max_width = 1600
            if original_width > max_width:
                ratio = max_width / original_width
                new_height = int(original_height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)

            # Save optimized image
            optimized_path = self.optimized_dir / seo_filename

            # Convert to RGB if needed (for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            # Save with compression
            img.save(
                optimized_path,
                'JPEG',
                quality=85,
                optimize=True,
                progressive=True
            )

            optimized_size = optimized_path.stat().st_size
            compression_ratio = (original_size - optimized_size) / original_size

            # Update database
            conn.execute("""
                UPDATE images
                SET optimized_path = ?,
                    updated_at = ?
                WHERE id = ?
            """, (str(optimized_path), datetime.now().isoformat(), image_id))

            # Record optimization metrics
            conn.execute("""
                INSERT INTO image_optimizations (
                    image_id, original_size, optimized_size,
                    compression_ratio, format_original, format_optimized,
                    optimized_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                image_id,
                original_size,
                optimized_size,
                compression_ratio,
                img.format or 'JPEG',
                'JPEG',
                datetime.now().isoformat()
            ))

            conn.commit()

            return {
                "image_id": image_id,
                "original_filename": original_path.name,
                "seo_filename": seo_filename,
                "original_size": original_size,
                "optimized_size": optimized_size,
                "compression_ratio": f"{compression_ratio:.1%}",
                "saved_bytes": original_size - optimized_size,
                "dimensions": {
                    "original": {"width": original_width, "height": original_height},
                    "optimized": {"width": img.width, "height": img.height}
                },
                "success": True
            }

        except Exception as e:
            return {
                "image_id": image_id,
                "error": str(e),
                "success": False
            }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python image_optimizer.py <project_path>")
        sys.exit(1)

    optimizer = ImageOptimizer(sys.argv[1])
    results = optimizer.process_all()
    print(json.dumps(results, indent=2))
