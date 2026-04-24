#!/usr/bin/env python3
"""
Image Uploader

Uploads optimized images to WordPress:
- Reads from images/optimized/
- Uploads via WordPress REST API
- Sets alt text, title, caption
- Updates database with WordPress media ID
- Sets synced = true

Dependencies:
    pip install requests python-dotenv
"""

import base64
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

try:
    import requests
    from dotenv import load_dotenv
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "Required libraries missing. Install with: pip install requests python-dotenv"
    }))
    exit(1)


class ImageUploader:
    """Uploads optimized images to WordPress."""

    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.optimized_dir = self.project_path / "images" / "optimized"
        self.db_path = self.project_path / "images" / "images.db"

        # Load WordPress credentials
        env_path = self.project_path / ".env"
        if not env_path.exists():
            raise FileNotFoundError(
                f"No .env file found at {env_path}. "
                "Run /seo-wordpress setup first."
            )

        load_dotenv(env_path)

        self.wp_url = os.getenv('WP_URL')
        self.wp_username = os.getenv('WP_USERNAME')
        self.wp_password = os.getenv('WP_APP_PASSWORD')
        self.wp_media_folder = os.getenv('WP_MEDIA_FOLDER', 'seo-optimized')

        if not all([self.wp_url, self.wp_username, self.wp_password]):
            raise ValueError("Missing WordPress credentials in .env file")

        # Detect REST API path
        self.api_path = self._detect_api_path()

    def _detect_api_path(self):
        """Detect WordPress REST API path."""
        # Try standard path first
        try:
            response = requests.get(
                f"{self.wp_url}/wp-json/",
                timeout=5
            )
            if response.status_code == 200:
                return "/wp-json"
        except:
            pass

        # Try alternative path (plain permalinks)
        try:
            response = requests.get(
                f"{self.wp_url}/index.php?rest_route=/",
                timeout=5
            )
            if response.status_code == 200:
                return "/index.php?rest_route="
        except:
            pass

        raise Exception("Cannot detect WordPress REST API path")

    def upload_all_pending(self):
        """
        Upload all images that are optimized but not yet synced.

        Returns:
            list: Upload results for each image
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Get images ready for upload
        images = conn.execute("""
            SELECT id, seo_filename, optimized_path,
                   alt_text, title, caption, target_url
            FROM images
            WHERE synced = 0 AND optimized_path IS NOT NULL
            ORDER BY created_at ASC
        """).fetchall()

        if not images:
            conn.close()
            return []

        results = []
        for img in images:
            result = self.upload_image(
                image_id=img['id'],
                optimized_path=img['optimized_path'],
                alt_text=img['alt_text'],
                title=img['title'],
                caption=img['caption'],
                target_url=img['target_url'],
                conn=conn
            )
            results.append(result)

        conn.close()
        return results

    def upload_by_id(self, image_id):
        """Upload single image by database ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        img = conn.execute("""
            SELECT id, seo_filename, optimized_path,
                   alt_text, title, caption, target_url
            FROM images
            WHERE id = ? AND synced = 0
        """, (image_id,)).fetchone()

        if not img:
            conn.close()
            return {"error": f"Image {image_id} not found or already synced"}

        result = self.upload_image(
            image_id=img['id'],
            optimized_path=img['optimized_path'],
            alt_text=img['alt_text'],
            title=img['title'],
            caption=img['caption'],
            target_url=img['target_url'],
            conn=conn
        )

        conn.close()
        return result

    def upload_image(self, image_id, optimized_path, alt_text, title, caption, target_url, conn):
        """
        Upload single image to WordPress.

        Steps:
        1. Read optimized image file
        2. Upload via WordPress REST API
        3. Set alt text, title, caption
        4. Update database with WordPress media ID
        5. Mark as synced = true
        """
        try:
            image_path = Path(optimized_path)

            if not image_path.exists():
                return {
                    "image_id": image_id,
                    "error": f"Optimized file not found: {optimized_path}",
                    "success": False
                }

            # Read image file
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Prepare authentication
            credentials = f"{self.wp_username}:{self.wp_password}"
            token = base64.b64encode(credentials.encode()).decode()

            headers = {
                "Authorization": f"Basic {token}",
                "Content-Disposition": f'attachment; filename="{image_path.name}"',
                "Content-Type": "image/jpeg"
            }

            # Upload to WordPress
            upload_url = f"{self.wp_url}{self.api_path}/wp/v2/media"

            response = requests.post(
                upload_url,
                headers=headers,
                data=image_data,
                timeout=30
            )

            if response.status_code not in [200, 201]:
                return {
                    "image_id": image_id,
                    "error": f"Upload failed: {response.status_code} - {response.text}",
                    "success": False
                }

            media_data = response.json()
            media_id = media_data['id']
            media_url = media_data['source_url']

            # Update media metadata (alt text, title, caption)
            update_url = f"{self.wp_url}{self.api_path}/wp/v2/media/{media_id}"

            metadata = {
                "alt_text": alt_text or title or "",
                "title": title or "",
                "caption": caption or ""
            }

            update_response = requests.post(
                update_url,
                headers={"Authorization": f"Basic {token}"},
                json=metadata,
                timeout=10
            )

            # Update database
            conn.execute("""
                UPDATE images
                SET wordpress_media_id = ?,
                    wordpress_url = ?,
                    synced = 1,
                    uploaded_at = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                media_id,
                media_url,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                image_id
            ))

            conn.commit()

            return {
                "image_id": image_id,
                "filename": image_path.name,
                "wordpress_media_id": media_id,
                "wordpress_url": media_url,
                "alt_text": alt_text,
                "title": title,
                "caption": caption,
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
        print("Usage: python image_uploader.py <project_path> [--all | --id <id>]")
        sys.exit(1)

    uploader = ImageUploader(sys.argv[1])

    if len(sys.argv) > 2 and sys.argv[2] == "--all":
        results = uploader.upload_all_pending()
    elif len(sys.argv) > 3 and sys.argv[2] == "--id":
        results = uploader.upload_by_id(int(sys.argv[3]))
    else:
        results = {"error": "Specify --all or --id <id>"}

    print(json.dumps(results, indent=2))
