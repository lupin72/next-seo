#!/usr/bin/env python3
"""
SEO Image Manager - Main CLI

Manages image SEO optimization workflow:
1. Analyze images (EXIF, dimensions, content)
2. Plan SEO (keywords, cannibalization check)
3. Rename & optimize
4. Upload to WordPress
5. Track sync status

Usage:
    python image_manager.py analyze --project PATH
    python image_manager.py plan --project PATH --url URL
    python image_manager.py rename --project PATH
    python image_manager.py upload --project PATH [--all | --id ID]
    python image_manager.py status --project PATH

Dependencies:
    pip install pillow iptcinfo3 python-dotenv requests
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Database path
def get_db_path(project_path):
    """Get SQLite database path for project."""
    return Path(project_path) / "images" / "images.db"

def init_database(db_path):
    """Initialize SQLite database with schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)

    # Read and execute schema
    schema_path = Path(__file__).parent / "image_db_schema.sql"
    with open(schema_path, 'r') as f:
        schema = f.read()

    conn.executescript(schema)
    conn.commit()
    conn.close()

    # Set secure permissions
    os.chmod(db_path, 0o600)

    return db_path

def analyze_images(project_path):
    """
    Analyze images in images/original/ directory.

    Scans for images, extracts metadata, saves to database.
    """
    from image_analyzer import ImageAnalyzer

    analyzer = ImageAnalyzer(project_path)
    results = analyzer.scan_directory()

    return {
        "success": True,
        "images_found": len(results),
        "images": results
    }

def plan_seo(project_path, target_url):
    """
    Plan SEO keywords and metadata for images.

    Analyzes page context, proposes keywords, checks cannibalization.
    """
    from image_seo_planner import ImageSEOPlanner

    planner = ImageSEOPlanner(project_path)
    plan = planner.create_plan(target_url)

    return {
        "success": True,
        "target_url": target_url,
        "plan": plan
    }

def rename_images(project_path):
    """
    Rename and optimize images based on SEO plan.

    Renames files, optimizes, adds IPTC metadata.
    """
    from image_optimizer import ImageOptimizer

    optimizer = ImageOptimizer(project_path)
    results = optimizer.process_all()

    return {
        "success": True,
        "processed": len(results),
        "results": results
    }

def upload_images(project_path, image_id=None, upload_all=False):
    """
    Upload optimized images to WordPress.

    Uploads images, sets metadata, updates sync status.
    """
    from image_uploader import ImageUploader

    uploader = ImageUploader(project_path)

    if upload_all:
        results = uploader.upload_all_pending()
    elif image_id:
        results = uploader.upload_by_id(image_id)
    else:
        return {
            "success": False,
            "error": "Specify --all or --id <id>"
        }

    return {
        "success": True,
        "uploaded": len(results),
        "results": results
    }

def show_status(project_path):
    """Show image SEO status."""
    db_path = get_db_path(project_path)

    if not db_path.exists():
        return {
            "success": False,
            "error": "No images database found. Run 'analyze' first."
        }

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get totals
    total = conn.execute("SELECT COUNT(*) as count FROM images").fetchone()['count']
    synced = conn.execute("SELECT COUNT(*) as count FROM images WHERE synced = 1").fetchone()['count']
    pending = total - synced

    # Get pending images with details
    pending_images = conn.execute("""
        SELECT id, original_filename, seo_filename, target_keyword, synced
        FROM images
        WHERE synced = 0
        ORDER BY created_at ASC
    """).fetchall()

    conn.close()

    return {
        "success": True,
        "total": total,
        "synced": synced,
        "pending": pending,
        "pending_images": [dict(img) for img in pending_images]
    }

def main():
    """CLI interface."""
    parser = argparse.ArgumentParser(
        description="SEO Image Manager - Optimize images for WordPress SEO"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze images in original/ folder")
    analyze_parser.add_argument("--project", required=True, help="Project path")

    # Plan command
    plan_parser = subparsers.add_parser("plan", help="Plan SEO keywords for images")
    plan_parser.add_argument("--project", required=True, help="Project path")
    plan_parser.add_argument("--url", required=True, help="Target page URL")

    # Rename command
    rename_parser = subparsers.add_parser("rename", help="Rename and optimize images")
    rename_parser.add_argument("--project", required=True, help="Project path")

    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload images to WordPress")
    upload_parser.add_argument("--project", required=True, help="Project path")
    upload_parser.add_argument("--all", action="store_true", help="Upload all pending images")
    upload_parser.add_argument("--id", type=int, help="Upload specific image by ID")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show image SEO status")
    status_parser.add_argument("--project", required=True, help="Project path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize database for project
    if args.command in ['analyze', 'plan', 'rename', 'upload']:
        db_path = get_db_path(args.project)
        init_database(db_path)

    # Execute command
    if args.command == "analyze":
        result = analyze_images(args.project)
    elif args.command == "plan":
        result = plan_seo(args.project, args.url)
    elif args.command == "rename":
        result = rename_images(args.project)
    elif args.command == "upload":
        result = upload_images(args.project, args.id, args.all)
    elif args.command == "status":
        result = show_status(args.project)
    else:
        result = {"success": False, "error": "Unknown command"}

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("success") else 1)

if __name__ == "__main__":
    main()
