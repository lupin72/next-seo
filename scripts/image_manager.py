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
    python image_manager.py plan --project PATH [--ids 1,2,3] [--language es]
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

    # Migrate legacy tables before creating indexes from the current schema.
    # Older project DBs can have gsc_page_cache without search_type, which would
    # make schema bootstrap fail when creating idx_gsc_cache_url_type.
    existing_tables = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    if "gsc_page_cache" in existing_tables:
        gsc_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(gsc_page_cache)").fetchall()
        }
        if "search_type" not in gsc_columns:
            conn.execute(
                "ALTER TABLE gsc_page_cache ADD COLUMN search_type TEXT NOT NULL DEFAULT 'web'"
            )
            conn.commit()

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

def analyze_images(project_path, visual_analysis=False):
    """
    Analyze images in images/original/ directory.

    Scans for images, extracts metadata, saves to database.
    When visual_analysis=True, marks images for AI visual description.
    """
    from image_analyzer import ImageAnalyzer

    analyzer = ImageAnalyzer(project_path, visual_analysis=visual_analysis)
    results = analyzer.scan_directory()

    return {
        "success": True,
        "images_found": len(results),
        "visual_analysis": visual_analysis,
        "images": results
    }

def plan_seo(project_path, selected_ids=None, language=None,
             use_image_search=True, use_competitors=False, force_refresh=False,
             visual_analysis=False):
    """
    Plan SEO keywords and metadata for images.

    v1.5: Auto-analyzes new images before planning.
    Uses site URL from PROJECT.md, folder name as context.
    Generates 3 scored keyword variants per image for human selection.
    """
    from image_seo_planner import ImageSEOPlanner
    from image_analyzer import ImageAnalyzer

    # Step 1: Auto-analyze new images (incremental)
    analyzer = ImageAnalyzer(project_path, visual_analysis=visual_analysis)
    analysis_results = analyzer.scan_directory()

    # Step 2: Generate SEO plan
    planner = ImageSEOPlanner(
        project_path,
        language=language,
        use_image_search=use_image_search,
        use_competitors=use_competitors
    )
    plan = planner.create_plan(selected_ids, force_refresh=force_refresh)

    return {
        "success": True,
        "language": language,
        "images_analyzed": len(analysis_results),
        "new_images": len([r for r in analysis_results if r.get('new', False)]),
        "plan": plan
    }

def rename_images(project_path, selected_ids=None):
    """
    Rename and optimize images based on SEO plan.

    Renames files, optimizes, adds IPTC metadata.
    """
    from image_optimizer import ImageOptimizer

    optimizer = ImageOptimizer(project_path)
    results = optimizer.process_all(selected_ids)

    return {
        "success": True,
        "processed": len(results),
        "results": results
    }

def upload_images(project_path, image_id=None, upload_all=False, selected_ids=None):
    """
    Upload optimized images to WordPress.

    Uploads images, sets metadata, updates sync status.
    """
    from image_uploader import ImageUploader

    uploader = ImageUploader(project_path)

    if selected_ids:
        results = uploader.upload_by_ids(selected_ids)
    elif upload_all:
        results = uploader.upload_all_pending()
    elif image_id:
        results = uploader.upload_by_id(image_id)
    else:
        return {
            "success": False,
            "error": "Specify --all, --id <id>, or --ids <id1,id2,id3>"
        }

    return {
        "success": True,
        "uploaded": len(results),
        "results": results
    }

def list_images_cmd(project_path, filter_status='all'):
    """List images with status information."""
    from image_selector import list_images
    images = list_images(project_path, filter_status)

    return {
        "success": True,
        "total": len(images),
        "filter": filter_status,
        "images": images
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
    analyze_parser.add_argument("--visual", action="store_true",
                                help="Enable visual analysis (mark images for AI description)")

    # List command
    list_parser = subparsers.add_parser("list", help="List images with status")
    list_parser.add_argument("--project", required=True, help="Project path")
    list_parser.add_argument("--filter", choices=['all', 'pending', 'planned', 'optimized', 'synced'],
                            default='all', help="Filter images by status")

    # Plan command
    plan_parser = subparsers.add_parser("plan", help="Plan SEO keywords for images (auto-analyzes new images + 3 variants with scoring)")
    plan_parser.add_argument("--project", required=True, help="Project path")
    plan_parser.add_argument("--ids", help="Comma-separated image IDs to process (e.g., 1,2,3)")
    plan_parser.add_argument("--language", "-l", help="Target language for metadata (e.g., es, it, en)")
    plan_parser.add_argument("--visual", action="store_true",
                             help="Enable visual AI analysis (generate image descriptions)")
    plan_parser.add_argument("--image-search", action="store_true", default=True,
                             help="Also query GSC with search_type='image' (default: true)")
    plan_parser.add_argument("--no-image-search", action="store_true",
                             help="Disable GSC image search queries")
    plan_parser.add_argument("--competitors", action="store_true",
                             help="Analyze competitor domains via GSC image queries")
    plan_parser.add_argument("--force-refresh", action="store_true",
                             help="Force fresh GSC API call (bypass cache)")

    # Rename command
    rename_parser = subparsers.add_parser("rename", help="Rename and optimize images")
    rename_parser.add_argument("--project", required=True, help="Project path")
    rename_parser.add_argument("--ids", help="Comma-separated image IDs to process (e.g., 1,2,3)")

    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload images to WordPress")
    upload_parser.add_argument("--project", required=True, help="Project path")
    upload_parser.add_argument("--all", action="store_true", help="Upload all pending images")
    upload_parser.add_argument("--id", type=int, help="Upload specific image by ID")
    upload_parser.add_argument("--ids", help="Comma-separated image IDs to upload (e.g., 1,2,3)")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show image SEO status")
    status_parser.add_argument("--project", required=True, help="Project path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize database for project
    if args.command in ['analyze', 'plan', 'rename', 'upload', 'list']:
        db_path = get_db_path(args.project)
        init_database(db_path)

    # Parse IDs if provided
    selected_ids = None
    if hasattr(args, 'ids') and args.ids:
        try:
            selected_ids = [int(id.strip()) for id in args.ids.split(',')]
        except ValueError:
            result = {"success": False, "error": "Invalid IDs format. Use: 1,2,3"}
            print(json.dumps(result, indent=2))
            sys.exit(1)

    # Execute command
    if args.command == "analyze":
        result = analyze_images(args.project, visual_analysis=getattr(args, 'visual', False))
    elif args.command == "list":
        result = list_images_cmd(args.project, args.filter)
    elif args.command == "plan":
        result = plan_seo(
            args.project,
            selected_ids,
            language=getattr(args, 'language', None),
            use_image_search=not getattr(args, 'no_image_search', False),
            use_competitors=getattr(args, 'competitors', False),
            force_refresh=getattr(args, 'force_refresh', False),
            visual_analysis=getattr(args, 'visual', False)
        )
    elif args.command == "rename":
        result = rename_images(args.project, selected_ids)
    elif args.command == "upload":
        if selected_ids:
            result = upload_images(args.project, None, False, selected_ids)
        else:
            result = upload_images(args.project, args.id, args.all)
    elif args.command == "status":
        result = show_status(args.project)
    else:
        result = {"success": False, "error": "Unknown command"}

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("success") else 1)

if __name__ == "__main__":
    main()
