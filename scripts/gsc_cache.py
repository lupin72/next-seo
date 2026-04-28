#!/usr/bin/env python3
"""
Google Search Console Cache Manager

Manages intelligent caching of GSC data to minimize API calls and optimize token usage.

Features:
- Configurable TTL (default: 7 days)
- Automatic cache expiry and cleanup
- Per-URL caching strategy
- Fallback to API when cache expired
- Manual cache invalidation

Dependencies:
    pip install python-dotenv

Usage:
    from gsc_cache import GSCCache

    cache = GSCCache(db_path="images/images.db")
    data = cache.get_or_fetch(url="https://example.com/page", force_refresh=False)
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class GSCCache:
    """Manages Google Search Console data caching."""

    def __init__(self, db_path: str, config: Optional[Dict] = None):
        """
        Initialize GSC cache manager.

        Args:
            db_path: Path to SQLite database
            config: Optional config dict (otherwise reads from env)
        """
        self.db_path = Path(db_path)
        self.config = config or {}

        # Load configuration from env
        self.ttl_days = int(self.config.get('GSC_CACHE_TTL_DAYS') or os.getenv('GSC_CACHE_TTL_DAYS', 7))
        self.date_range_days = int(self.config.get('GSC_DATE_RANGE_DAYS') or os.getenv('GSC_DATE_RANGE_DAYS', 90))
        self.min_impressions = int(self.config.get('GSC_MIN_IMPRESSIONS') or os.getenv('GSC_MIN_IMPRESSIONS', 10))
        self.max_queries = int(self.config.get('GSC_MAX_QUERIES') or os.getenv('GSC_MAX_QUERIES', 50))
        self.force_refresh = self.config.get('GSC_FORCE_REFRESH') or os.getenv('GSC_FORCE_REFRESH', 'false').lower() == 'true'

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create gsc_page_cache table if not exists."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gsc_page_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_url TEXT UNIQUE NOT NULL,
                queries_data TEXT,
                page_impressions INTEGER,
                page_clicks INTEGER,
                avg_position REAL,
                total_queries INTEGER,
                cached_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                cache_ttl_days INTEGER DEFAULT 7,
                gsc_start_date TEXT,
                gsc_end_date TEXT,
                status TEXT DEFAULT 'valid',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gsc_cache_url ON gsc_page_cache(page_url)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gsc_cache_status ON gsc_page_cache(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gsc_cache_expires ON gsc_page_cache(expires_at)")
        conn.commit()
        conn.close()

    def get_cached_data(self, page_url: str) -> Optional[Dict]:
        """
        Retrieve cached GSC data for a URL if valid.

        Args:
            page_url: Target page URL

        Returns:
            Cached data dict or None if expired/missing
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM gsc_page_cache
            WHERE page_url = ? AND status = 'valid'
            ORDER BY cached_at DESC
            LIMIT 1
        """, (page_url,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Check if expired
        expires_at = datetime.fromisoformat(row['expires_at'])
        if datetime.now() > expires_at:
            # Mark as expired
            self._update_cache_status(page_url, 'expired')
            return None

        # Parse JSON queries data
        queries_data = json.loads(row['queries_data']) if row['queries_data'] else []

        return {
            'page_url': row['page_url'],
            'queries': queries_data,
            'page_impressions': row['page_impressions'],
            'page_clicks': row['page_clicks'],
            'avg_position': row['avg_position'],
            'total_queries': row['total_queries'],
            'cached_at': row['cached_at'],
            'expires_at': row['expires_at'],
            'gsc_start_date': row['gsc_start_date'],
            'gsc_end_date': row['gsc_end_date']
        }

    def fetch_and_cache(self, page_url: str) -> Optional[Dict]:
        """
        Fetch fresh GSC data and cache it.

        Args:
            page_url: Target page URL

        Returns:
            GSC data dict or None if API unavailable
        """
        try:
            # Check if google-api-python-client is available
            try:
                import googleapiclient
            except ImportError:
                # Google API client not installed - cannot use GSC
                self._save_cache(page_url, None, status='error')
                return None

            # Import gsc_query module
            import sys
            script_dir = Path(__file__).parent
            sys.path.insert(0, str(script_dir))

            from gsc_query import GSCQuery

            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=self.date_range_days)

            # Fetch GSC data
            gsc = GSCQuery()
            result = gsc.query_page(
                page_url=page_url,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                dimensions=['query'],
                row_limit=self.max_queries
            )

            if not result.get('success'):
                # Cache error status
                self._save_cache(page_url, None, status='error')
                return None

            # Parse query data
            queries = []
            total_impressions = 0
            total_clicks = 0
            total_position_weighted = 0

            for row in result.get('rows', []):
                if row.get('impressions', 0) < self.min_impressions:
                    continue

                query_data = {
                    'query': row['keys'][0],
                    'impressions': row['impressions'],
                    'clicks': row['clicks'],
                    'ctr': row['ctr'],
                    'position': row['position']
                }
                queries.append(query_data)

                total_impressions += row['impressions']
                total_clicks += row['clicks']
                total_position_weighted += row['position'] * row['impressions']

            avg_position = total_position_weighted / total_impressions if total_impressions > 0 else 0

            # Prepare cache data
            cache_data = {
                'queries': queries,
                'page_impressions': total_impressions,
                'page_clicks': total_clicks,
                'avg_position': round(avg_position, 2),
                'total_queries': len(queries),
                'gsc_start_date': start_date.isoformat(),
                'gsc_end_date': end_date.isoformat()
            }

            # Save to cache
            self._save_cache(page_url, cache_data, status='valid')

            return {
                'page_url': page_url,
                **cache_data,
                'cached_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=self.ttl_days)).isoformat()
            }

        except Exception as e:
            print(f"GSC fetch error: {str(e)}", file=sys.stderr)
            self._save_cache(page_url, None, status='error')
            return None

    def get_or_fetch(self, page_url: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get cached data or fetch fresh if expired.

        Args:
            page_url: Target page URL
            force_refresh: Force fresh API call even if cached

        Returns:
            GSC data dict or None
        """
        if force_refresh or self.force_refresh:
            return self.fetch_and_cache(page_url)

        # Try cache first
        cached = self.get_cached_data(page_url)
        if cached:
            return cached

        # Cache miss or expired - fetch fresh
        return self.fetch_and_cache(page_url)

    def _save_cache(self, page_url: str, data: Optional[Dict], status: str = 'valid'):
        """
        Save or update cache entry.

        Args:
            page_url: Target page URL
            data: GSC data dict (or None for error status)
            status: Cache status ('valid', 'expired', 'error')
        """
        conn = sqlite3.connect(self.db_path)
        now = datetime.now().isoformat()
        expires_at = (datetime.now() + timedelta(days=self.ttl_days)).isoformat()

        if data:
            conn.execute("""
                INSERT INTO gsc_page_cache (
                    page_url, queries_data, page_impressions, page_clicks,
                    avg_position, total_queries, cached_at, expires_at,
                    cache_ttl_days, gsc_start_date, gsc_end_date, status, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(page_url) DO UPDATE SET
                    queries_data = excluded.queries_data,
                    page_impressions = excluded.page_impressions,
                    page_clicks = excluded.page_clicks,
                    avg_position = excluded.avg_position,
                    total_queries = excluded.total_queries,
                    cached_at = excluded.cached_at,
                    expires_at = excluded.expires_at,
                    cache_ttl_days = excluded.cache_ttl_days,
                    gsc_start_date = excluded.gsc_start_date,
                    gsc_end_date = excluded.gsc_end_date,
                    status = excluded.status,
                    updated_at = excluded.updated_at
            """, (
                page_url,
                json.dumps(data['queries']),
                data['page_impressions'],
                data['page_clicks'],
                data['avg_position'],
                data['total_queries'],
                now,
                expires_at,
                self.ttl_days,
                data['gsc_start_date'],
                data['gsc_end_date'],
                status,
                now
            ))
        else:
            # Save error status
            conn.execute("""
                INSERT INTO gsc_page_cache (page_url, status, cached_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(page_url) DO UPDATE SET
                    status = excluded.status,
                    cached_at = excluded.cached_at,
                    updated_at = excluded.updated_at
            """, (page_url, status, now, now))

        conn.commit()
        conn.close()

    def _update_cache_status(self, page_url: str, status: str):
        """Update cache status (e.g., mark as expired)."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE gsc_page_cache
            SET status = ?, updated_at = ?
            WHERE page_url = ?
        """, (status, datetime.now().isoformat(), page_url))
        conn.commit()
        conn.close()

    def invalidate_cache(self, page_url: Optional[str] = None):
        """
        Invalidate cache for specific URL or all URLs.

        Args:
            page_url: Optional URL to invalidate (None = all)
        """
        conn = sqlite3.connect(self.db_path)
        if page_url:
            conn.execute("UPDATE gsc_page_cache SET status = 'expired' WHERE page_url = ?", (page_url,))
        else:
            conn.execute("UPDATE gsc_page_cache SET status = 'expired'")
        conn.commit()
        conn.close()

    def cleanup_expired(self, days_old: int = 30):
        """
        Delete expired cache entries older than N days.

        Args:
            days_old: Remove entries older than this many days
        """
        cutoff = (datetime.now() - timedelta(days=days_old)).isoformat()
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            DELETE FROM gsc_page_cache
            WHERE status = 'expired' AND cached_at < ?
        """, (cutoff,))
        conn.commit()
        conn.close()

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM gsc_page_cache WHERE status = 'valid'")
        valid = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM gsc_page_cache WHERE status = 'expired'")
        expired = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM gsc_page_cache WHERE status = 'error'")
        error = cursor.fetchone()[0]

        conn.close()

        return {
            'valid': valid,
            'expired': expired,
            'error': error,
            'total': valid + expired + error
        }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='GSC Cache Manager')
    parser.add_argument('--db', required=True, help='Path to images.db')
    parser.add_argument('--url', help='Page URL')
    parser.add_argument('--stats', action='store_true', help='Show cache stats')
    parser.add_argument('--invalidate', action='store_true', help='Invalidate cache for URL')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup old expired entries')
    parser.add_argument('--force', action='store_true', help='Force refresh from API')

    args = parser.parse_args()

    cache = GSCCache(db_path=args.db)

    if args.stats:
        stats = cache.get_cache_stats()
        print(json.dumps(stats, indent=2))

    elif args.invalidate:
        cache.invalidate_cache(args.url)
        print(json.dumps({'success': True, 'message': f'Cache invalidated for {args.url or "all URLs"}'}))

    elif args.cleanup:
        cache.cleanup_expired()
        print(json.dumps({'success': True, 'message': 'Expired cache cleaned up'}))

    elif args.url:
        data = cache.get_or_fetch(args.url, force_refresh=args.force)
        print(json.dumps(data, indent=2))

    else:
        parser.print_help()
