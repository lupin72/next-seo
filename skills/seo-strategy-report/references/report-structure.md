# SEO Strategy Report Structure

This document details the 10-section structure used in all SEO strategy reports,
regardless of industry or language.

## Report Overview

Every report follows the same structure:
1. Executive Summary
2. Current Website Analysis
3. Competitive Landscape
4. SWOT Analysis
5. Keyword Research & Gaps
6. Identified SEO Opportunities
7. Pages to Create
8. Editorial Calendar
9. Technical SEO Recommendations
10. Prioritized Action Plan

---

## Section 1: Executive Summary

**Purpose**: Give stakeholders an at-a-glance understanding of the business, current state, and key findings.

### Fields Required:
- `business_profile` (string): 2-3 sentence description covering:
  - What the business does
  - Unique differentiators
  - Target audience
- `key_findings` (list): 6-8 bullet points, each combining a metric with strategic implication

### Guidelines:
- Use concrete numbers from GSC data
- Compare to largest competitor (URL count, traffic estimates)
- Highlight 1-2 major gaps
- Mention 1-2 quick wins
- Keep bullets under 25 words each
- Balance positive (strengths) with opportunities

### Example Finding:
"Currently ranking in positions 5-20 for 47 high-intent keywords with 15K+ monthly impressions — improving these to top 3 could double organic traffic."

---

## Section 2: Current Website Analysis

**Purpose**: Baseline assessment of existing pages and content.

### 2.1 Page Structure (Sitemap)

Fields:
- `sitemap_pages` (list of dicts):
  - `url`: The page URL (relative or absolute)
  - `title`: Current meta title
  - `rating`: ✓ (good) / ⚠ (needs improvement) / ✗ (poor)

Rating heuristics:
- ✓ = 50-60 chars, includes primary keyword, includes differentiator, no duplication
- ⚠ = Too short/long, generic, missing keyword, or minor issues
- ✗ = Duplicate, no title, keyword stuffing, or major issues

### 2.2 Blog Content Assessment

Fields:
- `blog_articles` (list of dicts):
  - `title`: Article title
  - `section`: Blog category/section
  - `keyword`: Inferred target keyword
  - `seo`: ✓ / ⚠ / ✗

- `critical_gap_summary` (string): One sentence summarizing missing foundational pages

---

## Section 3: Competitive Landscape

**Purpose**: Understand who you're competing against and what they're doing well.

### 3.1 Competitor Table

Fields:
- `competitors` (list of dicts):
  - `name`: Business name (put client LAST with 🚀 prefix "OUR BUSINESS — [Name]")
  - `positioning`: Use 🔴 (high) 🟡 (medium) 🟢 (low) + description
  - `urls`: "308+" (indexed URL count)
  - `rating`: "4.5★ (834 reviews)" (Google rating)
  - `price_from`: Starting price (if applicable)
  - `audience`: Target audience description

### 3.2 Competitor Insights

Fields:
- `competitor_insights` (list): 3-5 bullets naming specific things competitors do well

Example: "Competitor A: Dedicated 'Romantic Getaway' landing page ranking #1 for that exact query. Active blog (2 posts/week). Live webcam feature. FAQ schema. 6 languages."

---

## Section 4: SWOT Analysis

**Purpose**: Strategic framework for understanding market position.

Fields:
- `swot` (dict):
  - `strengths` (list): 8-12 short bullets (5-12 words each)
  - `weaknesses` (list): 8-12 short bullets
  - `opportunities` (list): 8-12 short bullets (should foreshadow Section 6)
  - `threats` (list): 6-8 short bullets (name specific competitors and platforms)

Guidelines:
- Strengths: Product/service differentiators, existing assets, competitive advantages
- Weaknesses: Content gaps, technical issues, missing features vs competitors
- Opportunities: Untapped keywords, seasonal angles, new content types, markets
- Threats: Aggregators/platforms, strong competitors, algorithm changes, market trends

---

## Section 5: Keyword Research & Gaps

**Purpose**: Show what keywords to target and what you're missing.

### 5.1 Keywords Table

Fields:
- `keywords` (list of dicts):
  - `keyword`: The search term
  - `type`: Branded / Transactional / Informational / Seasonal
  - `volume`: High / Medium / Low (or numeric if available)
  - `difficulty`: High / Medium / Low
  - `current_position`: "3" / "Not ranking" / "Maps pack"
  - `action`: "Create landing" / "Optimize homepage" / "Create guide" / "Improve position"

Mix:
- 3-5 branded keywords (positions 1-3, just to confirm)
- 10-15 transactional keywords (high commercial intent)
- 5-8 seasonal keywords
- 8-12 informational keywords

### 5.2 Gaps

Fields:
- `gaps` (list of dicts):
  - `level`: "critical" (red box) or "important" (yellow box)
  - `title`: Short gap name (e.g., "No product category pages")
  - `text`: 1-2 sentence description naming competitor who's winning

Include: 3 critical gaps + 2 important gaps

---

## Section 6: Identified SEO Opportunities

**Purpose**: Prioritize the most impactful actions.

### 6.1 Opportunities Table

Fields:
- `opportunities` (list of dicts):
  - `opportunity`: Description (15-30 words)
  - `keywords`: Comma-separated keyword list
  - `impact`: 🔴 Very High / 🟡 High / 🟢 Medium
  - `difficulty`: High / Medium / Low

8-10 opportunities total, sorted by impact/effort ratio.

### 6.2 Brand Opportunities

Fields:
- `brand_opportunities` (list of dicts):
  - `type`: "ok" (green) / "hl" (yellow) / "alert" (red)
  - `title`: "🌟 [Unique differentiator]"
  - `text`: 2-3 sentences explaining the opportunity

1-3 boxes highlighting unique assets/differentiators.

---

## Section 7: Pages to Create

**Purpose**: Detailed roadmap of what content to build.

### 7.1 Structural Pages

Fields:
- `structural_pages` (list of dicts):
  - `page`: Page name/description
  - `slug`: Recommended URL slug (kebab-case)
  - `h1_keyword`: Exact H1 to use (phrased as search query)
  - `content`: Key content points (2-3 sentences)

Industry examples:
- Hospitality: Rooms, Spa, Restaurant, Pool, Events
- E-commerce: Category pages, Collections, Sale
- SaaS: Features, Pricing, Integrations, Use Cases

### 7.2 Experience Pages

Fields: Same structure as 7.1

Industry examples:
- Hospitality: Romantic Getaway, Wellness Package, Family Package
- E-commerce: Buying Guides, Gift Guides, Style Guides
- SaaS: Industry Solutions, Role-Based Pages, Comparison Pages

### 7.3 Blog Guides

Fields:
- `blog_guides` (list of dicts):
  - `article`: Article title
  - `slug`: Recommended URL slug
  - `h1_keyword`: Target keyword
  - `intent`: Informational / Problem-solution / Comparison / Guide

10-15 blog articles covering informational keywords and supporting the sales funnel.

---

## Section 8: Editorial Calendar

**Purpose**: Month-by-month publishing schedule.

Fields:
- `editorial_calendar` (list of dicts):
  - `month_label`: "January 2026 — Launch Phase" (descriptive label)
  - `rows` (list of dicts):
    - `week`: "W1" / "W2" / "W3" / "W4"
    - `type`: "New Page" / "Offer Landing" / "Blog" / "Update"
    - `title`: Content title
    - `slug`: URL slug (reuse from Section 7)
    - `keyword`: Target keyword

12 months, each with 2-4 entries (24-48 total items).

Guidelines:
- Phase 1 (months 1-2): Structural pages
- Phase 2 (months 3-6): Experience pages + seasonal content
- Phase 3 (months 7-12): Blog scaling + optimization
- Align with seasonal events (holidays, industry peak times)

---

## Section 9: Technical SEO Recommendations

**Purpose**: Quick wins and technical improvements.

### 9.1 Quick Wins

Fields:
- `quick_wins` (list of dicts):
  - `action`: What to do
  - `where`: Where to do it
  - `impact`: High / Medium / Low
  - `effort`: Low / Medium / High

8-12 items sorted by impact/effort ratio.

Examples:
- Fix image alt text
- Add schema markup
- Improve internal linking
- Fix broken links
- Optimize Core Web Vitals
- Add breadcrumbs

### 9.2 URL Architecture

Fields:
- `url_architecture` (string): Multiline ASCII tree using `├─` and `└─`

Example:
```
/
├─ /products/
│  ├─ /products/category-a/
│  ├─ /products/category-b/
│  └─ /products/sale/
├─ /blog/
│  ├─ /blog/guides/
│  └─ /blog/news/
└─ /about/
```

### 9.3 Re-optimize Existing Pages

Fields:
- `reoptimize` (list of dicts):
  - `page`: Page URL
  - `problem`: What's wrong (1 sentence)
  - `solution`: How to fix (1 sentence)

5-8 existing pages that need improvement.

---

## Section 10: Prioritized Action Plan

**Purpose**: Phased roadmap with clear owners and KPIs.

### 10.1 Phase 1: Foundations

Fields:
- `phase1_period`: "January — February 2026"
- `phase1_tasks` (list of dicts):
  - `task`: Task description
  - `responsible`: Team/person
  - `deadline`: Date or "Week 4"
  - `kpi`: Measurable outcome

6-10 tasks focused on structural pages and critical gaps.

### 10.2 Phase 2: Growth

Fields: Same structure as Phase 1
- `phase2_period`: "March — June 2026"
- `phase2_tasks`

8-12 tasks focused on experience pages, seasonal content, blog.

### 10.3 Phase 3: Consolidation

Fields: Same structure
- `phase3_period`: "July — December 2026"
- `phase3_tasks`

8-12 tasks focused on scaling, optimization, internationalization.

### 10.4 Tracking KPIs

Fields:
- `kpis` (list of dicts):
  - `metric`: Metric name
  - `tool`: Where to track it
  - `frequency`: Weekly / Monthly / Quarterly
  - `target`: 12-month goal

8-10 KPIs covering:
- Organic traffic
- Keyword rankings
- Conversion rate
- Page speed
- Indexed pages
- Backlinks
- Domain authority
- Engagement metrics

---

## Footer

Fields used:
- `business_domain`
- `business_name`
- `client_group`
- `report_date`

The footer is automatically generated in the template.

---

## Template Placeholders

All placeholders use the format `{{PLACEHOLDER_NAME}}`.

See `scripts/strategy_report_builder.py` for the complete mapping of JSON fields to template placeholders.
