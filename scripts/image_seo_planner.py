#!/usr/bin/env python3
"""
Image SEO Planner

Plans SEO keywords and metadata for images:
- Analyzes target page context
- Proposes keywords based on page content
- Checks keyword cannibalization
- Generates SEO-friendly filenames
- Creates alt text, titles, captions

Dependencies:
    pip install requests beautifulsoup4
"""

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "Required libraries missing. Install with: pip install requests beautifulsoup4"
    }))
    exit(1)


class ImageSEOPlanner:
    """Plans SEO strategy for images."""

    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.db_path = self.project_path / "images" / "images.db"

    def create_plan(self, target_url):
        """
        Create SEO plan for all unsynced images.

        Args:
            target_url: URL of page where images will be used

        Returns:
            dict: Plan with keyword proposals for each image
        """
        # Analyze page context
        page_context = self.analyze_page(target_url)

        # Get unsynced images from database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        images = conn.execute("""
            SELECT id, original_filename, dimensions, exif_data
            FROM images
            WHERE synced = 0 AND target_url IS NULL
            ORDER BY created_at ASC
        """).fetchall()

        if not images:
            conn.close()
            return {
                "page_context": page_context,
                "images": [],
                "message": "No images found to plan"
            }

        # Create proposals for each image
        proposals = []
        for img in images:
            proposal = self.propose_keywords(
                image_id=img['id'],
                filename=img['original_filename'],
                page_context=page_context,
                existing_keywords=self.get_existing_keywords(conn)
            )
            proposals.append(proposal)

            # Save SEO metadata to database
            seo_meta = proposal['seo_metadata']
            conn.execute("""
                UPDATE images
                SET seo_filename = ?,
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
                seo_meta['filename'],
                seo_meta['alt_text'],
                seo_meta['title'],
                seo_meta['caption'],
                proposal['selected_keyword'],
                target_url,
                page_context.get('h1', ''),
                page_context.get('title', ''),
                json.dumps(page_context),
                datetime.now().isoformat(),
                img['id']
            ))
            conn.commit()

        conn.close()

        return {
            "target_url": target_url,
            "page_context": page_context,
            "images": proposals,
            "total": len(proposals)
        }

    def analyze_page(self, url):
        """
        Analyze target page for SEO context.

        Extracts:
        - Title, H1, meta description
        - Existing images and alt texts
        - Main content keywords
        """
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract meta tags
            title_tag = soup.find('title')
            title = title_tag.text.strip() if title_tag else ""

            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_description = meta_desc['content'] if meta_desc and 'content' in meta_desc.attrs else ""

            # Extract H1
            h1_tag = soup.find('h1')
            h1 = h1_tag.text.strip() if h1_tag else ""

            # Extract existing images
            existing_images = []
            for img in soup.find_all('img'):
                existing_images.append({
                    "src": img.get('src', ''),
                    "alt": img.get('alt', ''),
                    "title": img.get('title', '')
                })

            # Extract main content
            content = ""
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|post|article'))
            if main_content:
                content = main_content.get_text(separator=' ', strip=True)

            # Extract primary keyword (heuristic: from title + H1)
            primary_keyword = self.extract_primary_keyword(title, h1)

            return {
                "url": url,
                "title": title,
                "h1": h1,
                "meta_description": meta_description,
                "primary_keyword": primary_keyword,
                "existing_images": existing_images,
                "content_preview": content[:500] if content else ""
            }

        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "title": "",
                "h1": "",
                "primary_keyword": ""
            }

    def extract_primary_keyword(self, title, h1):
        """
        Extract likely primary keyword from title and H1.

        Simple heuristic: longest common phrase between title and H1
        """
        if not title or not h1:
            return title.lower()[:50] if title else h1.lower()[:50]

        # Normalize
        title_lower = title.lower()
        h1_lower = h1.lower()

        # Find common phrases (3+ words)
        title_words = title_lower.split()
        h1_words = h1_lower.split()

        # Find longest common substring
        for length in range(min(len(title_words), len(h1_words)), 2, -1):
            for i in range(len(title_words) - length + 1):
                phrase = ' '.join(title_words[i:i+length])
                if phrase in h1_lower:
                    return phrase

        # Fallback: return title
        return title_lower[:50]

    def propose_keywords(self, image_id, filename, page_context, existing_keywords):
        """
        Propose SEO keywords for an image.

        Generates:
        - Primary keyword
        - Long-tail variants
        - SEO filename
        - Alt text
        - Title
        - Caption
        """
        primary_kw = page_context.get('primary_keyword', '')

        # Generate keyword variants
        base_keywords = self.generate_keyword_variants(filename, page_context)

        # Check cannibalization for each variant
        keyword_proposals = []
        for kw in base_keywords[:5]:  # Top 5 candidates
            cannibalization = self.check_cannibalization(kw, existing_keywords, page_context)
            keyword_proposals.append({
                "keyword": kw,
                "cannibalization_risk": cannibalization['risk'],
                "cannibalization_note": cannibalization.get('message', ''),
                "recommended": not cannibalization['risk']
            })

        # Select best keyword (first non-cannibalizing)
        selected_keyword = next(
            (kw['keyword'] for kw in keyword_proposals if not kw['cannibalization_risk']),
            base_keywords[0] if base_keywords else filename
        )

        # Generate SEO metadata
        seo_filename = self.generate_seo_filename(selected_keyword)
        alt_text = self.generate_alt_text(selected_keyword, page_context)
        title = self.generate_title(selected_keyword, page_context)
        caption = self.generate_caption(selected_keyword, page_context)

        return {
            "image_id": image_id,
            "original_filename": filename,
            "keyword_proposals": keyword_proposals,
            "selected_keyword": selected_keyword,
            "seo_metadata": {
                "filename": seo_filename,
                "alt_text": alt_text,
                "title": title,
                "caption": caption
            }
        }

    def generate_keyword_variants(self, filename, page_context):
        """Generate keyword variants based on filename and page context."""
        variants = []

        primary_kw = page_context.get('primary_keyword', '')
        h1 = page_context.get('h1', '')

        # Variant 1: Primary keyword + filename context
        if primary_kw:
            filename_clean = re.sub(r'[^a-z0-9]+', ' ', filename.lower())
            variants.append(f"{primary_kw} {filename_clean}".strip())

        # Variant 2: H1 + filename
        if h1:
            h1_clean = h1.lower()[:30]
            variants.append(f"{h1_clean} {filename_clean}".strip())

        # Variant 3: Just primary keyword
        if primary_kw:
            variants.append(primary_kw)

        # Variant 4: Filename-based
        variants.append(filename_clean)

        # Clean and deduplicate
        variants = [v.strip() for v in variants if v.strip()]
        variants = list(dict.fromkeys(variants))  # Remove duplicates

        return variants[:5]

    def generate_seo_filename(self, keyword):
        """Generate SEO-friendly filename from keyword."""
        # Clean keyword
        filename = keyword.lower()
        filename = re.sub(r'[^\w\s-]', '', filename)
        filename = re.sub(r'[\s_]+', '-', filename)
        filename = filename.strip('-')

        # Limit length
        if len(filename) > 60:
            filename = filename[:60].rsplit('-', 1)[0]

        return f"{filename}.jpg"

    def generate_alt_text(self, keyword, page_context):
        """Generate descriptive alt text including keyword."""
        # Format: [Keyword] + [context detail]
        h1 = page_context.get('h1', '')
        site_name = urlparse(page_context.get('url', '')).netloc

        if h1:
            return f"{keyword.capitalize()} - {h1}"
        else:
            return keyword.capitalize()

    def generate_title(self, keyword, page_context):
        """Generate image title."""
        return keyword.title()

    def generate_caption(self, keyword, page_context):
        """Generate image caption."""
        h1 = page_context.get('h1', '')
        if h1:
            return f"{keyword.capitalize()} en {h1}"
        return ""

    def check_cannibalization(self, keyword, existing_keywords, page_context):
        """
        Check if keyword causes cannibalization.

        Returns:
            dict: {risk: bool, message: str}
        """
        # Check 1: Keyword already used by another image?
        if keyword in existing_keywords:
            return {
                "risk": True,
                "type": "image_keyword_duplicate",
                "message": f"Keyword '{keyword}' already used by another image"
            }

        # Check 2: Too similar to primary keyword? (>80% similarity)
        primary_kw = page_context.get('primary_keyword', '')
        if primary_kw and keyword != primary_kw:
            similarity = self.calculate_similarity(keyword, primary_kw)
            if similarity > 0.8:
                return {
                    "risk": True,
                    "type": "keyword_similarity",
                    "message": f"Too similar to primary keyword: '{primary_kw}' (similarity: {similarity:.0%})"
                }

        # No cannibalization detected
        return {"risk": False}

    def calculate_similarity(self, str1, str2):
        """Calculate simple word overlap similarity between two strings."""
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def get_existing_keywords(self, conn):
        """Get all existing target keywords from database."""
        rows = conn.execute("""
            SELECT DISTINCT target_keyword
            FROM images
            WHERE target_keyword IS NOT NULL
        """).fetchall()

        return [row[0] for row in rows]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python image_seo_planner.py <project_path> <target_url>")
        sys.exit(1)

    planner = ImageSEOPlanner(sys.argv[1])
    plan = planner.create_plan(sys.argv[2])
    print(json.dumps(plan, indent=2))
