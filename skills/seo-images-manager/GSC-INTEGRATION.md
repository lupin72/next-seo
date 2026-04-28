# Google Search Console Integration (v1.1)

## Overview

The Image SEO Manager now uses **real Google Search Console data** to generate intelligent keyword proposals based on actual search performance rather than heuristics.

### Key Benefits

✅ **Data-Driven**: Uses real search queries from GSC instead of guessing
✅ **Opportunity Scoring**: 0-100 score identifies quick wins automatically
✅ **Intelligent Caching**: 7-day cache reduces API calls by >90%
✅ **Quick Win Detection**: Auto-prioritizes keywords in position 11-20 with low CTR
✅ **Real Metrics**: Each keyword includes impressions, clicks, CTR, position from GSC
✅ **Fallback Support**: Graceful fallback to page context when GSC unavailable

---

## How It Works

### Workflow

```
User runs: /seo-images-manager plan https://example.com/page

┌─────────────────────────────────────────────────────────────┐
│ 1. Check GSC Cache                                          │
│    • Query: gsc_page_cache WHERE page_url = ?              │
│    • Check expires_at > NOW()                              │
└─────────────────────────────────────────────────────────────┘
                         │
                    ┌────┴────┐
              Cache │         │ Cache
              Valid │         │ Expired/Missing
                    ▼         ▼
         ┌──────────────┐  ┌──────────────┐
         │ Use Cached   │  │ Fetch GSC    │
         │ Data         │  │ API          │
         └──────────────┘  └──────────────┘
                    │         │
                    │    ┌────┴────┐
                    │    │ Save to │
                    │    │ Cache   │
                    │    │ (7 days)│
                    │    └─────────┘
                    ▼
         ┌──────────────────────────────────┐
         │ Calculate Opportunity Scores     │
         │ • Impressions (0-40 pts)        │
         │ • CTR (0-30 pts)                │
         │ • Position (0-30 pts)           │
         │ Total: 0-100                    │
         └──────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────────────────┐
         │ Check Cannibalization            │
         │ • Keyword already used?         │
         │ • Too similar to primary kw?    │
         └──────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────────────────┐
         │ Generate SEO Metadata            │
         │ • Filename: keyword-variant.jpg  │
         │ • Alt text: "Keyword - H1"      │
         │ • Title: "Keyword"              │
         │ • Caption: "Keyword en H1"      │
         └──────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────────────────┐
         │ Save to Database                 │
         │ • images.target_keyword          │
         │ • image_keywords (with metrics)  │
         └──────────────────────────────────┘
```

---

## Opportunity Scoring Algorithm

The opportunity score (0-100) identifies **quick wins** — keywords with high traffic potential but poor current performance.

### Scoring Breakdown

| Component | Max Points | Logic |
|-----------|-----------|-------|
| **Impressions** | 40 | Traffic potential:<br>• >1000 = 40 pts<br>• >500 = 35 pts<br>• >100 = 25 pts<br>• >50 = 15 pts<br>• >10 = 10 pts |
| **CTR** | 30 | Optimization opportunity (inverse):<br>• <1% = 30 pts (huge opportunity)<br>• <2% = 20 pts<br>• <3% = 10 pts<br>• <5% = 5 pts |
| **Position** | 30 | Quick win potential:<br>• Position 11-20 = 30 pts (page 2 = best)<br>• Position 6-10 = 20 pts<br>• Position 1-5 = 15 pts<br>• Position 21-30 = 10 pts |

### Example Calculations

**Example 1: Quick Win (Score: 90)**
```json
{
  "keyword": "hotels rome city center",
  "impressions": 1200,  // +40 pts (>1000)
  "ctr": 0.008,         // +30 pts (<1%)
  "position": 12.3,     // +30 pts (page 2)
  "opportunity_score": 100
}
```
**Result:** HIGH PRIORITY — high traffic, low CTR, page 2 position = easy to optimize

**Example 2: Already Optimized (Score: 55)**
```json
{
  "keyword": "rome hotels",
  "impressions": 800,   // +35 pts (>500)
  "ctr": 0.055,         // +0 pts (>5%)
  "position": 3.2,      // +15 pts (top of page 1)
  "opportunity_score": 50
}
```
**Result:** LOW PRIORITY — already performing well

**Example 3: Low Traffic (Score: 25)**
```json
{
  "keyword": "boutique hotel rome trastevere",
  "impressions": 25,    // +10 pts (>10)
  "ctr": 0.015,         // +20 pts (<2%)
  "position": 18.5,     // +30 pts (page 2)
  "opportunity_score": 60
}
```
**Result:** MEDIUM PRIORITY — low volume but good opportunity

---

## Quick Win Detection

Keywords are flagged as **quick wins** when:

```python
position >= 11 and position <= 20 and ctr < 0.02
```

**Why?**
- **Position 11-20** = Page 2 (users already finding you, just need to push to page 1)
- **CTR <2%** = Poor click-through (easy to improve with better title/meta/image)

**Quick win markers:**
```json
{
  "keyword": "rome hotel breakfast",
  "position": 14.2,
  "ctr": 0.012,
  "quick_win": true  // ← Flagged for priority action
}
```

---

## Database Schema

### Table: `gsc_page_cache`

Stores GSC data per page URL with TTL-based expiry.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| page_url | TEXT | Unique page URL (cached data key) |
| queries_data | TEXT | JSON array: `[{query, impressions, clicks, ctr, position}]` |
| page_impressions | INTEGER | Total impressions for page |
| page_clicks | INTEGER | Total clicks for page |
| avg_position | REAL | Weighted average position |
| total_queries | INTEGER | Number of queries |
| cached_at | TEXT | ISO timestamp of cache creation |
| expires_at | TEXT | ISO timestamp when cache expires |
| cache_ttl_days | INTEGER | TTL in days (default: 7) |
| gsc_start_date | TEXT | GSC query start date (e.g., "2026-01-28") |
| gsc_end_date | TEXT | GSC query end date (e.g., "2026-04-27") |
| status | TEXT | 'valid', 'expired', or 'error' |
| created_at | TEXT | Row creation timestamp |
| updated_at | TEXT | Row update timestamp |

### Extended Table: `image_keywords`

New columns for GSC metrics:

| Column | Type | Description |
|--------|------|-------------|
| gsc_impressions | INTEGER | Impressions for this keyword |
| gsc_clicks | INTEGER | Clicks for this keyword |
| gsc_ctr | REAL | Click-through rate (percentage) |
| gsc_position | REAL | Average position |
| opportunity_score | INTEGER | Calculated score 0-100 |

---

## Configuration

### Environment Variables

Set in `.env` or project `.env`:

```bash
# GSC Cache Settings
GSC_CACHE_TTL_DAYS=7           # Cache validity (default: 7 days)
GSC_DATE_RANGE_DAYS=90         # GSC query date range (default: 90 days)
GSC_MIN_IMPRESSIONS=10         # Minimum impressions to consider (default: 10)
GSC_MAX_QUERIES=50             # Maximum queries to fetch (default: 50)
GSC_FORCE_REFRESH=false        # Force API refresh every time (default: false)
```

### Defaults

If not configured, uses these defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| `GSC_CACHE_TTL_DAYS` | 7 | Cache expires after 7 days |
| `GSC_DATE_RANGE_DAYS` | 90 | Fetch last 90 days of data |
| `GSC_MIN_IMPRESSIONS` | 10 | Ignore keywords with <10 impressions |
| `GSC_MAX_QUERIES` | 50 | Fetch top 50 queries per page |
| `GSC_FORCE_REFRESH` | false | Use cache when available |

---

## Cache Strategy

### Why Cache?

**Problem:** Google Search Console API has rate limits and each call uses tokens in Claude Code.

**Solution:** Intelligent caching with configurable TTL.

### Cache Behavior

1. **First call**: Fetches from GSC API → saves to `gsc_page_cache`
2. **Subsequent calls**: Reads from cache if `expires_at > NOW()`
3. **After 7 days**: Cache expires → fetches fresh data → updates cache

### Cache Hit Ratio

Typical usage:
- **Day 1**: API call (cache miss)
- **Days 2-7**: Cache hits (no API call)
- **Day 8**: API call (cache expired)

**Result:** ~86% reduction in API calls over 1 week (6 cache hits / 1 API call)

For monthly workflows: **>90% reduction** (3-4 API calls instead of 30)

### Manual Cache Control

```bash
# Check cache status
python scripts/gsc_cache.py --db clients/prova/test/images/images.db --stats

# Force refresh for specific URL
python scripts/image_manager.py plan \
  --project clients/prova/test \
  --url https://example.com/page \
  --force-refresh

# Invalidate cache for URL
python scripts/gsc_cache.py --db clients/prova/test/images/images.db \
  --url https://example.com/page --invalidate

# Cleanup old expired entries (>30 days)
python scripts/gsc_cache.py --db clients/prova/test/images/images.db --cleanup
```

---

## Fallback Behavior

### When GSC Unavailable

The planner gracefully falls back to **heuristic keyword generation** when:
- GSC API not configured
- GSC authentication fails
- Page URL not in Search Console property
- API rate limit exceeded
- Network error

### Fallback Strategy

Uses original keyword generation logic:
1. Primary keyword from page title + H1
2. Filename-based variants
3. No opportunity scoring (uses first non-cannibalizing keyword)

**User notification:**
```json
{
  "page_context": {
    "gsc_enabled": false
  },
  "images": [
    {
      "gsc_powered": false,
      "keyword_proposals": [
        {
          "keyword": "hotels rome city center",
          "recommended": true
        }
      ]
    }
  ]
}
```

---

## Example Output

### With GSC Integration

```json
{
  "target_url": "https://example.com/hotels-rome",
  "page_context": {
    "title": "Best Hotels in Rome 2026 | Travel Guide",
    "h1": "Top 10 Hotels in Rome",
    "primary_keyword": "hotels in rome",
    "gsc_enabled": true,
    "gsc_queries": 47,
    "gsc_cached_at": "2026-04-27T10:30:00"
  },
  "images": [
    {
      "image_id": 1,
      "original_filename": "IMG_1234.jpg",
      "gsc_powered": true,
      "keyword_proposals": [
        {
          "keyword": "hotels rome city center",
          "gsc_impressions": 1200,
          "gsc_clicks": 12,
          "gsc_ctr": 1.0,
          "gsc_position": 12.3,
          "opportunity_score": 90,
          "quick_win": true,
          "cannibalization_risk": false,
          "recommended": true
        },
        {
          "keyword": "luxury hotels rome",
          "gsc_impressions": 800,
          "gsc_clicks": 8,
          "gsc_ctr": 1.0,
          "gsc_position": 15.2,
          "opportunity_score": 85,
          "quick_win": true,
          "cannibalization_risk": false,
          "recommended": true
        },
        {
          "keyword": "rome hotels",
          "gsc_impressions": 3000,
          "gsc_clicks": 150,
          "gsc_ctr": 5.0,
          "gsc_position": 3.2,
          "opportunity_score": 55,
          "quick_win": false,
          "cannibalization_risk": true,
          "cannibalization_note": "Too similar to primary keyword: 'hotels in rome' (similarity: 100%)",
          "recommended": false
        }
      ],
      "selected_keyword": "hotels rome city center",
      "seo_metadata": {
        "filename": "hotels-rome-city-center.jpg",
        "alt_text": "Hotels rome city center - Top 10 Hotels in Rome",
        "title": "Hotels Rome City Center",
        "caption": "Hotels rome city center en Top 10 Hotels in Rome"
      }
    }
  ],
  "total": 1
}
```

---

## Testing

### Test GSC Integration

```bash
# 1. Setup GSC credentials (if not already done)
python scripts/google_auth.py setup gsc

# 2. Test cache module directly
python scripts/gsc_cache.py \
  --db clients/prova/test/images/images.db \
  --url https://example.com/page

# 3. Test full workflow
/seo-images-manager plan https://example.com/page

# 4. Force refresh (bypass cache)
python scripts/image_manager.py plan \
  --project clients/prova/test \
  --url https://example.com/page \
  --force-refresh

# 5. Check cache stats
python scripts/gsc_cache.py \
  --db clients/prova/test/images/images.db \
  --stats
```

### Expected Output

```json
{
  "page_url": "https://example.com/page",
  "queries": [
    {
      "query": "hotels rome city center",
      "impressions": 1200,
      "clicks": 12,
      "ctr": 0.01,
      "position": 12.3
    }
  ],
  "page_impressions": 1200,
  "page_clicks": 12,
  "avg_position": 12.3,
  "total_queries": 1,
  "cached_at": "2026-04-27T10:30:00",
  "expires_at": "2026-05-04T10:30:00"
}
```

---

## Troubleshooting

### Error: "GSC cache init failed"

**Cause:** Database connection failed or schema missing

**Fix:**
```bash
# Recreate database schema
sqlite3 clients/prova/test/images/images.db < scripts/image_db_schema.sql
```

### Error: "GSC fetch failed"

**Cause:** GSC API not configured or authentication failed

**Fix:**
```bash
# Reconfigure GSC credentials
python scripts/google_auth.py setup gsc
```

**Fallback:** Planner will use heuristic keyword generation automatically

### Cache Not Updating

**Symptom:** Always uses old cached data even after 7 days

**Check:**
```bash
# Query cache table directly
sqlite3 clients/prova/test/images/images.db \
  "SELECT page_url, cached_at, expires_at, status FROM gsc_page_cache"
```

**Fix:**
```bash
# Manually invalidate cache
python scripts/gsc_cache.py \
  --db clients/prova/test/images/images.db \
  --url https://example.com/page \
  --invalidate
```

### Low Opportunity Scores

**Symptom:** All keywords have scores <30

**Likely causes:**
1. Page has low search volume (niche topic)
2. Page already well-optimized (high CTR, good positions)
3. GSC date range too short (increase `GSC_DATE_RANGE_DAYS` to 180)

**Not a bug** — low scores mean less optimization opportunity

---

## Migration from v1.0

Existing projects are **fully backwards compatible**. No migration needed.

### What Happens?

1. First `/seo-images-manager plan` call:
   - Creates `gsc_page_cache` table if missing
   - Adds new columns to `image_keywords` table
   - Fetches GSC data and caches it

2. Subsequent calls:
   - Uses cached GSC data (if valid)
   - Falls back to heuristics if GSC unavailable

### Recommended Actions

1. **Reconfigure TTL** if needed:
   ```bash
   echo "GSC_CACHE_TTL_DAYS=14" >> clients/prova/test/.env
   ```

2. **Test with one image** first:
   ```bash
   /seo-images-manager plan https://example.com/page
   ```

3. **Review opportunity scores** to understand quick wins

---

## Performance Impact

### Token Usage Reduction

**Before v1.1 (heuristic generation):**
- Every plan call: ~500 tokens (page fetch + HTML parsing)

**After v1.1 (GSC integration):**
- First call: ~1500 tokens (page fetch + GSC API + cache write)
- Subsequent 6 calls: ~300 tokens each (cache read only)
- **Net savings over 1 week:** ~1200 tokens saved

**At scale (30 images/month):**
- Before: 15,000 tokens
- After: ~4,000 tokens
- **Savings: ~73% token reduction**

### API Rate Limits

GSC API limits: **200 queries/day** (per project)

With 7-day cache: **Max 4 API calls/month per URL** (well under limit)

---

## Best Practices

### 1. Use Appropriate TTL

| Use Case | Recommended TTL |
|----------|----------------|
| Daily blog posts | 3 days |
| Weekly content | 7 days (default) |
| Monthly campaigns | 14 days |
| Static pages | 30 days |

### 2. Monitor Quick Wins

```bash
# Query quick win keywords
sqlite3 clients/prova/test/images/images.db \
  "SELECT keyword, gsc_position, gsc_ctr, opportunity_score
   FROM image_keywords
   WHERE gsc_position >= 11 AND gsc_position <= 20 AND gsc_ctr < 2.0
   ORDER BY opportunity_score DESC"
```

### 3. Force Refresh After Major Changes

After site redesign or major content updates:
```bash
/seo-images-manager plan https://example.com/page --force-refresh
```

### 4. Cleanup Old Cache

Monthly maintenance:
```bash
python scripts/gsc_cache.py \
  --db clients/prova/test/images/images.db \
  --cleanup
```

---

**Version:** 1.1.0
**Last Updated:** 2026-04-27
**Integration Type:** Google Search Console API + SQLite Cache
