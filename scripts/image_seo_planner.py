#!/usr/bin/env python3
"""
Image SEO Planner (v1.1 - GSC Integration)

Plans SEO keywords and metadata for images:
- Analyzes target page context
- Fetches Google Search Console data (cached)
- Calculates opportunity scores (0-100) based on impressions, CTR, position
- Proposes keywords based on real search queries
- Checks keyword cannibalization
- Generates SEO-friendly filenames
- Creates alt text, titles, captions

Dependencies:
    pip install requests beautifulsoup4
"""

import json
import os
import re
import sqlite3
import sys
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

# Import GSC cache module
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from gsc_cache import GSCCache
    GSC_AVAILABLE = True
except ImportError:
    GSC_AVAILABLE = False


class ImageSEOPlanner:
    """Plans SEO strategy for images with GSC integration."""

    def __init__(self, project_path, use_gsc=True):
        self.project_path = Path(project_path)
        self.db_path = self.project_path / "images" / "images.db"
        self.use_gsc = use_gsc and GSC_AVAILABLE

        # Initialize GSC cache if available
        if self.use_gsc:
            try:
                self.gsc_cache = GSCCache(db_path=str(self.db_path))
            except Exception as e:
                print(f"GSC cache init failed: {e}", file=sys.stderr)
                self.use_gsc = False

    def create_plan(self, target_url, selected_ids=None, force_refresh=False):
        """
        Create SEO plan for all unsynced images (or selected images).

        Args:
            target_url: URL of page where images will be used
            selected_ids: Optional list of image IDs to process
            force_refresh: Force fresh GSC API call

        Returns:
            dict: Plan with keyword proposals for each image
        """
        # Analyze page context
        page_context = self.analyze_page(target_url)

        # Fetch GSC data if available
        gsc_data = None
        if self.use_gsc:
            try:
                gsc_data = self.gsc_cache.get_or_fetch(target_url, force_refresh=force_refresh)
                if gsc_data:
                    page_context['gsc_enabled'] = True
                    page_context['gsc_queries'] = gsc_data.get('total_queries', 0)
                    page_context['gsc_cached_at'] = gsc_data.get('cached_at', '')
            except Exception as e:
                print(f"GSC fetch failed: {e}", file=sys.stderr)
                gsc_data = None

        # Get unsynced images from database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        if selected_ids:
            # Filter by specific IDs
            placeholders = ','.join('?' * len(selected_ids))
            query = f"""
                SELECT id, original_filename, dimensions, exif_data
                FROM images
                WHERE id IN ({placeholders})
                ORDER BY created_at ASC
            """
            images = conn.execute(query, selected_ids).fetchall()
        else:
            # Get all unsynced images without target_url
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
                existing_keywords=self.get_existing_keywords(conn),
                gsc_data=gsc_data
            )
            proposals.append(proposal)

            # Save keyword proposals to image_keywords table
            if gsc_data and proposal.get('keyword_proposals'):
                self.save_keyword_proposals(conn, img['id'], proposal['keyword_proposals'])

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

    def propose_keywords(self, image_id, filename, page_context, existing_keywords, gsc_data=None):
        """
        Propose SEO keywords for an image using GSC data or fallback heuristics.

        v1.1: Prioritizes real GSC queries with opportunity scoring
        Fallback: Uses page context-based keyword generation

        Args:
            image_id: Database image ID
            filename: Original filename
            page_context: Page metadata dict
            existing_keywords: List of already-used keywords
            gsc_data: Optional GSC data dict with queries

        Returns:
            dict: Keyword proposals with opportunity scores and SEO metadata
        """
        primary_kw = page_context.get('primary_keyword', '')

        # Strategy 1: GSC-powered keyword generation (v1.1)
        if gsc_data and gsc_data.get('queries'):
            keyword_proposals = self.generate_keywords_from_gsc(
                gsc_queries=gsc_data['queries'],
                filename=filename,
                existing_keywords=existing_keywords,
                page_context=page_context
            )
        else:
            # Strategy 2: Fallback to heuristic generation
            keyword_proposals = self.generate_keywords_heuristic(
                filename=filename,
                page_context=page_context,
                existing_keywords=existing_keywords
            )

        # Select best keyword (highest opportunity score or first non-cannibalizing)
        if gsc_data:
            # Sort by opportunity score descending
            sorted_proposals = sorted(
                [kw for kw in keyword_proposals if not kw['cannibalization_risk']],
                key=lambda x: x.get('opportunity_score', 0),
                reverse=True
            )
            selected_keyword = sorted_proposals[0]['keyword'] if sorted_proposals else keyword_proposals[0]['keyword']
        else:
            # Select first non-cannibalizing
            selected_keyword = next(
                (kw['keyword'] for kw in keyword_proposals if not kw['cannibalization_risk']),
                keyword_proposals[0]['keyword'] if keyword_proposals else filename
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
            "gsc_powered": bool(gsc_data),
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

    def generate_keywords_from_gsc(self, gsc_queries, filename, existing_keywords, page_context):
        """
        Generate keyword proposals from GSC queries with opportunity scoring.

        v1.1: Uses real search queries from Search Console
        Prioritizes keywords with:
        - High impressions (traffic potential)
        - Low CTR (optimization opportunity)
        - Position 11-20 (quick win - page 2)

        Returns:
            list: Keyword proposals with GSC metrics and opportunity scores
        """
        proposals = []

        # Filter and score GSC queries
        for query_data in gsc_queries[:50]:  # Top 50 queries
            keyword = query_data['query']
            impressions = query_data['impressions']
            clicks = query_data['clicks']
            ctr = query_data['ctr']
            position = query_data['position']

            # Calculate opportunity score (0-100)
            opportunity_score = self.calculate_opportunity_score(impressions, clicks, ctr, position)

            # Check cannibalization
            cannibalization = self.check_cannibalization(keyword, existing_keywords, page_context)

            proposals.append({
                "keyword": keyword,
                "cannibalization_risk": cannibalization['risk'],
                "cannibalization_note": cannibalization.get('message', ''),
                "recommended": not cannibalization['risk'],
                "gsc_impressions": impressions,
                "gsc_clicks": clicks,
                "gsc_ctr": round(ctr * 100, 2),  # Convert to percentage
                "gsc_position": round(position, 1),
                "opportunity_score": opportunity_score,
                "quick_win": position >= 11 and position <= 20 and ctr < 0.02  # Page 2 + low CTR
            })

        # Sort by opportunity score descending
        proposals.sort(key=lambda x: x['opportunity_score'], reverse=True)

        return proposals[:10]  # Top 10 opportunities

    def generate_keywords_heuristic(self, filename, page_context, existing_keywords):
        """
        Fallback: Generate keywords using page context heuristics.

        Used when GSC data unavailable.
        """
        base_keywords = self.generate_keyword_variants(filename, page_context)

        proposals = []
        for kw in base_keywords[:5]:
            cannibalization = self.check_cannibalization(kw, existing_keywords, page_context)
            proposals.append({
                "keyword": kw,
                "cannibalization_risk": cannibalization['risk'],
                "cannibalization_note": cannibalization.get('message', ''),
                "recommended": not cannibalization['risk']
            })

        return proposals

    def calculate_opportunity_score(self, impressions, clicks, ctr, position):
        """
        Calculate SEO opportunity score (0-100).

        Algorithm:
        - Impressions (0-40 points): >1000=40, >500=35, >100=25, >50=15, >10=10
        - CTR (0-30 points): <1%=30, <2%=20, <3%=10 (lower = more opportunity)
        - Position (0-30 points): 11-20=30, 6-10=20, 1-5=15 (page 2 = quick win)

        High score = high impressions + low CTR + page 2 position = QUICK WIN

        Returns:
            int: Score 0-100
        """
        score = 0

        # Impressions scoring (0-40 points)
        if impressions > 1000:
            score += 40
        elif impressions > 500:
            score += 35
        elif impressions > 100:
            score += 25
        elif impressions > 50:
            score += 15
        elif impressions > 10:
            score += 10
        else:
            score += 5

        # CTR scoring (0-30 points) - INVERSE: lower CTR = more opportunity
        if ctr < 0.01:  # <1%
            score += 30
        elif ctr < 0.02:  # <2%
            score += 20
        elif ctr < 0.03:  # <3%
            score += 10
        elif ctr < 0.05:  # <5%
            score += 5

        # Position scoring (0-30 points) - page 2 = quick win
        if 11 <= position <= 20:
            score += 30  # Page 2 = best opportunity
        elif 6 <= position <= 10:
            score += 20  # Bottom of page 1
        elif 1 <= position <= 5:
            score += 15  # Top of page 1
        elif 21 <= position <= 30:
            score += 10  # Page 3
        elif position > 30:
            score += 5   # Page 4+

        return min(score, 100)

    def save_keyword_proposals(self, conn, image_id, proposals):
        """
        Save keyword proposals to image_keywords table with GSC metrics.

        Args:
            conn: SQLite connection
            image_id: Image ID
            proposals: List of keyword proposal dicts
        """
        # Delete existing proposals for this image
        conn.execute("DELETE FROM image_keywords WHERE image_id = ?", (image_id,))

        # Insert new proposals
        for i, proposal in enumerate(proposals[:5], start=1):  # Top 5 proposals
            conn.execute("""
                INSERT INTO image_keywords (
                    image_id, keyword, priority, cannibalization_risk,
                    cannibalization_note, gsc_impressions, gsc_clicks,
                    gsc_ctr, gsc_position, opportunity_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                image_id,
                proposal['keyword'],
                i,  # Priority based on opportunity score
                1 if proposal['cannibalization_risk'] else 0,
                proposal.get('cannibalization_note', ''),
                proposal.get('gsc_impressions'),
                proposal.get('gsc_clicks'),
                proposal.get('gsc_ctr'),
                proposal.get('gsc_position'),
                proposal.get('opportunity_score')
            ))

        conn.commit()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python image_seo_planner.py <project_path> <target_url>")
        sys.exit(1)

    planner = ImageSEOPlanner(sys.argv[1])
    plan = planner.create_plan(sys.argv[2])
    print(json.dumps(plan, indent=2))
