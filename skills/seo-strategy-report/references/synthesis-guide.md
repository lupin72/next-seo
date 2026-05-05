# Synthesis Guide: Building the Content JSON

This guide provides step-by-step instructions for synthesizing all collected data
into the final content JSON that feeds the report template.

## Prerequisites

Before starting synthesis, you should have:
- ✅ GSC data JSON (from `gsc_query.py`)
- ✅ Client site crawler JSON (from `site_crawler.py`)
- ✅ 3-6 competitor crawler JSONs
- ✅ Industry type identified
- ✅ Target language confirmed
- ✅ Business profile information from client

---

## Step-by-Step Synthesis

### Step 1: Set Up Report Metadata

Start with the basic information:

```json
{
  "report_title": "SEO Strategy [Business Name] [Year]",
  "business_name": "...",
  "business_tagline": "Industry | Location | Positioning",
  "year": "2026",
  "report_subtitle": "Analysis based on GSC + Competition",
  "report_date": "Month Year",
  "business_domain": "example.com",
  "client_group": "Parent Company (if any)"
}
```

**Sources**:
- User input / AskUserQuestion responses
- Client site crawler `domain` field

---

### Step 2: Write Business Profile

Craft 2-3 sentences covering:
1. What the business does + industry
2. Key differentiators (2-3 specific features)
3. Target audience

**Template**:
> [Business Name], [industry/positioning], [location/reach]. [Unique feature 1], [unique feature 2], [unique feature 3]. Managed by [company]. Target audience: [demographic + psychographic].

**Sources**:
- User input about business
- Client site homepage title/description
- About page content

**Example**:
> "Acme Corp, leading B2B SaaS platform for marketing automation, serving 5000+ companies globally. AI-powered email campaigns, advanced segmentation, native CRM integrations. Managed by Acme Group. Target audience: marketing teams at mid-market B2B companies."

---

### Step 3: Extract Key Findings

Pull 6-8 bullets from:

1. **URL count gap** (from crawler data):
   - Client: `total_urls` from client crawler
   - Competitor: largest `total_urls` from competitor crawlers
   - Example: "The website currently has only 27 pages. The main competitor has 308+ indexed URLs."

2. **Missing structural pages** (from crawler `summary` flags):
   - Check `has_product_pages`, `has_pricing_page`, `has_services_page`, etc.
   - Example: "No dedicated product category pages, no pricing page, no case studies section."

3. **GSC highlights** (from GSC data):
   - `totals.clicks`, `totals.impressions`, `totals.ctr`, `totals.position`
   - `low_hanging_fruit` count
   - `branded_vs_non_branded` split
   - Example: "Currently ranking in positions 5-20 for 47 keywords with 15K monthly impressions — opportunity to double traffic."

4. **Competitive advantages** (from manual analysis):
   - Better rating, better price, unique features
   - Example: "Google rating 4.5★ with 834 reviews — higher than all direct competitors."

5. **Technical issues** (from crawler):
   - `images_without_alt` totals
   - Missing schema types
   - Example: "73% of images lack descriptive alt text — major SEO opportunity."

6. **Content opportunity** (from blog analysis):
   - `blog_post_count` vs competitors
   - Example: "Blog has only 10 posts in 12 months. Top competitor publishes 2x/week."

**Formatting**:
- Use concrete numbers
- Pair problem with opportunity
- Keep under 25 words per bullet
- Mix positive (what's working) with gaps

---

### Step 4: Analyze Sitemap Pages

From client crawler `pages` array, create `sitemap_pages`:

```python
for page in client_crawler['pages']:
    url = page['url']
    title = page['title']

    # Rate the title
    if is_well_optimized(title, url):
        rating = "✓ Well optimized"
    elif has_minor_issues(title):
        rating = "⚠ Needs improvement"
    else:
        rating = "✗ Poor optimization"

    sitemap_pages.append({
        "url": url,
        "title": title,
        "rating": rating
    })
```

**Rating heuristics**:
- ✓ = 50-60 chars, includes primary keyword, includes differentiator, no duplication
- ⚠ = Too short (<30), too long (>70), generic, missing keyword
- ✗ = Duplicate, no title, keyword stuffing, just "Contact" or "About"

Include top 15-20 pages only (most important ones).

---

### Step 5: Identify Critical Gaps

Compare client `summary` flags to competitor `summary` flags:

```python
critical_gaps = []

# Industry-specific checks
if industry == "E-commerce":
    if not client['summary']['has_product_pages']:
        if any(comp['summary']['has_product_pages'] for comp in competitors):
            critical_gaps.append("No product category pages")

if industry == "SaaS":
    if not client['summary']['has_pricing_page']:
        critical_gaps.append("No pricing page")

# Join into summary
critical_gap_summary = ", ".join(critical_gaps) + "."
```

**One sentence maximum**, listing 2-4 missing page types.

---

### Step 6: Assess Blog Content

From client crawler `blog_posts`:

```python
for post in client_crawler['blog_posts']:
    # Infer keyword from title
    keyword = infer_keyword_from_title(post['title'])

    # Rate SEO quality
    if keyword and len(post['title']) < 70:
        seo = "✓"
    elif keyword:
        seo = "⚠"
    else:
        seo = "✗"

    blog_articles.append({
        "title": post['title'],
        "section": "Blog",  # or extract from URL path
        "keyword": keyword,
        "seo": seo
    })
```

Include all blog posts (typically 10-20).

---

### Step 7: Build Competitor Table

For each competitor (put client LAST):

```python
for i, comp in enumerate(competitors):
    # Determine positioning (manual analysis or WebSearch)
    positioning = analyze_positioning(comp)  # 🔴/🟡/🟢 + description

    competitors_table.append({
        "name": comp['domain'],
        "positioning": positioning,
        "urls": f"{comp['total_urls']}+",
        "rating": get_google_rating(comp),  # from WebSearch or manual
        "price_from": get_starting_price(comp),  # if applicable
        "audience": identify_target_audience(comp)
    })

# Add client last with 🚀
competitors_table.append({
    "name": f"🚀 OUR BUSINESS — {client_name}",
    "positioning": "🟢 Medium-Low: visible in maps + AI Overview but lacks dedicated landing pages",
    "urls": f"{client['total_urls']} pages",
    "rating": get_google_rating(client),
    "price_from": client_price,
    "audience": client_audience
})
```

**Competitor insights** (3-5 bullets):
- Name specific features each competitor has
- Example: "Competitor A: Dedicated 'Romantic Getaway' page ranking #1. Active blog (2/week). Live webcam. FAQ schema. 6 languages."

---

### Step 8: SWOT Analysis

Pull from all data sources:

**Strengths** (8-12 bullets):
- Better rating/reviews than competitors
- Unique product features
- Better location/access
- Premium materials/quality
- Existing rankings (from GSC)
- Brand recognition

**Weaknesses** (8-12 bullets):
- Fewer pages than competitors
- Missing page types (from crawler)
- Low blog frequency
- Technical issues (images, schema)
- Missing languages
- No FAQ section

**Opportunities** (8-12 bullets):
- Keywords with good impressions but position 5-20 (from GSC `low_hanging_fruit`)
- Missing content types competitors have
- Seasonal content gaps
- International markets
- Schema markup improvements
- New content formats

**Threats** (6-8 bullets):
- Name 1-2 strongest competitors
- Industry aggregators (Booking.com, Amazon, etc.)
- Algorithm changes
- Market trends

Keep each bullet 5-12 words.

---

### Step 9: Keywords Table

Mix from GSC data and gap analysis:

1. **Branded keywords** (3-5): From GSC where `branded: true`, positions 1-3
2. **Transactional keywords** (10-15): High commercial intent
3. **Seasonal keywords** (5-8): Holidays, events, seasons
4. **Informational keywords** (8-12): Guides, how-tos

```python
for query in gsc_data['top_queries']:
    if query['branded']:
        keyword_type = "Branded"
        action = "Maintain position"
    elif is_transactional(query['query']):
        keyword_type = "Transactional"
        action = determine_action(query['position'])
    # ... etc

    keywords.append({
        "keyword": query['query'],
        "type": keyword_type,
        "volume": estimate_volume(query['impressions']),
        "difficulty": estimate_difficulty(query),
        "current_position": str(round(query['position'])),
        "action": action
    })
```

**Action heuristics**:
- Position 1-3: "Maintain position"
- Position 4-10: "Improve to top 3"
- Position 11-20: "Create dedicated landing" or "Improve position"
- Not ranking: "Create landing" or "Create blog guide"

---

### Step 10: Identify Gaps

Critical gaps (3) + Important gaps (2):

```python
gaps = []

# Check for missing page types
if not has_pricing_page and competitors_have_pricing:
    gaps.append({
        "level": "critical",
        "title": "No pricing page",
        "text": "Competitor A and B both rank #1-3 for '[product] pricing' with dedicated transparent pricing pages. We have no pricing page and miss this high-intent traffic."
    })

# Check for keyword gaps from GSC
for kw in high_intent_keywords_not_ranking:
    if competitor_ranks_for(kw):
        gaps.append({
            "level": "important",
            "title": f"Not ranking for '{kw}'",
            "text": f"Competitor X ranks #2 with a dedicated landing page. 2,400+ monthly searches, high purchase intent."
        })
```

Name the specific competitor URL winning each gap.

---

### Step 11: Opportunities Table

8-10 opportunities sorted by impact/effort:

```python
opportunities = [
    {
        "opportunity": "Create product category pages to capture transactional searches",
        "keywords": "buy [product], [product] online, [product] shop",
        "impact": "🔴 Very High",
        "difficulty": "Medium"
    },
    {
        "opportunity": "Target low-hanging fruit keywords (positions 5-20) with on-page optimization",
        "keywords": gsc_low_hanging_fruit_keywords,
        "impact": "🟡 High",
        "difficulty": "Low"
    },
    # ... 6-8 more
]
```

**Brand opportunities** (1-3 boxes):
```python
brand_opportunities = [
    {
        "type": "ok",  # green box
        "title": "🌟 Unique Differentiator: [Feature]",
        "text": "Leverage this unique asset by creating a dedicated landing page and mentioning it in all service pages. Potential to own this niche keyword cluster."
    }
]
```

---

### Step 12: Pages to Create

Based on industry template + gap analysis:

**Structural pages** (6-10):
```python
structural_pages = [
    {
        "page": "Product Category Page — [Category]",
        "slug": "/products/category-name/",
        "h1_keyword": "Buy [Category] Online",
        "content": "Full product listing with filters, reviews, comparison tool. Include trust signals, shipping info, return policy."
    },
    # ... more based on industry
]
```

**Experience pages** (6-10):
```python
experience_pages = [
    {
        "page": "Buying Guide — [Product Type]",
        "slug": "/guides/how-to-choose-[product]/",
        "h1_keyword": "How to Choose the Best [Product]",
        "content": "Comparison of features, use cases, price points. Include product recommendations from our catalog."
    },
    # ... more
]
```

**Blog guides** (10-15):
```python
blog_guides = [
    {
        "article": "Ultimate Guide to [Topic]",
        "slug": "/blog/ultimate-guide-[topic]/",
        "h1_keyword": "[Topic]: Complete Guide for Beginners",
        "intent": "Informational — Top of funnel"
    },
    # ... more
]
```

---

### Step 13: Editorial Calendar

12 months, each with 2-4 entries (24-48 total):

```python
editorial_calendar = []

for month_num in range(1, 13):
    month_name = get_month_name(month_num, language)
    seasonal_angle = get_seasonal_angle(month_num, industry)

    rows = []

    # Phase 1 (months 1-2): Structural pages
    if month_num <= 2:
        for page in structural_pages[:2]:
            rows.append({
                "week": f"W{week_num}",
                "type": "New Page",
                "title": page['page'],
                "slug": page['slug'],
                "keyword": page['h1_keyword']
            })

    # Phase 2 (months 3-6): Experience pages + seasonal
    elif month_num <= 6:
        # Mix experience pages and blog
        rows.append({...})  # experience page
        rows.append({...})  # blog post

    # Phase 3 (months 7-12): Blog scaling
    else:
        # 2-3 blog posts per month
        rows.append({...})
        rows.append({...})

    editorial_calendar.append({
        "month_label": f"{month_name} {year} — {seasonal_angle}",
        "rows": rows
    })
```

**Seasonal angles by month**:
- January: New Year, Fresh Start, Planning
- February: Valentine's, Winter, Love
- March-April: Spring, Easter, Renewal
- May-June: Summer Prep, Graduates, Weddings
- July-August: Summer Peak, Vacation, Back to School
- September: Fall, New Season, Harvest
- October: Halloween, Autumn
- November: Thanksgiving, Black Friday, Gratitude
- December: Holidays, Christmas, Year-End

---

### Step 14: Technical SEO Quick Wins

8-12 actionable items:

```python
quick_wins = [
    {
        "action": "Add descriptive alt text to all images",
        "where": "All pages (priority: homepage, product pages)",
        "impact": "High",
        "effort": "Low"
    },
    {
        "action": "Implement [Industry] schema markup",
        "where": "Homepage, service/product pages",
        "impact": "High",
        "effort": "Medium"
    },
    {
        "action": "Fix broken internal links",
        "where": "Site-wide (23 broken links detected)",
        "impact": "Medium",
        "effort": "Low"
    },
    # ... 5-9 more
]
```

Sort by impact/effort ratio (high impact + low effort first).

---

### Step 15: URL Architecture

Create ASCII tree based on planned structure:

```
/
├─ /products/
│  ├─ /products/category-a/
│  │  └─ /products/category-a/product-name/
│  ├─ /products/category-b/
│  └─ /products/sale/
├─ /guides/
│  ├─ /guides/buying-guides/
│  └─ /guides/how-to/
├─ /blog/
│  ├─ /blog/industry-news/
│  ├─ /blog/case-studies/
│  └─ /blog/tips/
├─ /about/
│  ├─ /about/team/
│  └─ /about/contact/
└─ /support/
   ├─ /support/faq/
   └─ /support/documentation/
```

Use `├─` for items with siblings below, `└─` for last item in a group.

---

### Step 16: Re-optimize Existing Pages

From crawler data, identify 5-8 pages with issues:

```python
for page in client_crawler['pages']:
    problems = []

    if page['title_length'] < 30:
        problems.append("Title too short")
    if page['images_without_alt'] > 0:
        problems.append(f"{page['images_without_alt']} images missing alt")
    if page['word_count'] < 300:
        problems.append("Thin content")
    if not page['schema_types']:
        problems.append("No schema markup")

    if problems:
        reoptimize.append({
            "page": page['url'],
            "problem": "; ".join(problems),
            "solution": generate_solution(problems)
        })
```

---

### Step 17: Phased Action Plan

**Phase 1** (months 1-2): 6-10 foundational tasks
```python
phase1_tasks = [
    {
        "task": "Create [missing structural pages]",
        "responsible": "Content Team",
        "deadline": "Week 6",
        "kpi": "+15 indexed pages, +3 ranking keywords"
    },
    # ... more
]
```

**Phase 2** (months 3-6): 8-12 growth tasks
**Phase 3** (months 7-12): 8-12 consolidation tasks

Each phase builds on the previous one.

---

### Step 18: KPIs Table

8-10 metrics covering all aspects:

```python
kpis = [
    {
        "metric": "Organic traffic (non-branded)",
        "tool": "Google Analytics 4",
        "frequency": "Weekly",
        "target": "+150% (from 5K to 12.5K monthly)"
    },
    {
        "metric": "Top 3 keyword rankings",
        "tool": "Google Search Console",
        "frequency": "Weekly",
        "target": "45 keywords (from 12)"
    },
    # ... 6-8 more
]
```

Cover: traffic, rankings, conversion, technical, engagement, authority.

---

## Final Checklist

Before rendering the report:

- [ ] All required fields present (no `{{PLACEHOLDERS}}` will remain)
- [ ] Numbers match source data (GSC, crawler)
- [ ] Client appears LAST in competitor table with 🚀
- [ ] Industry-appropriate page types in Section 7
- [ ] Language-appropriate seasonal events in calendar
- [ ] Quick wins sorted by impact/effort
- [ ] URL architecture uses proper tree characters
- [ ] All slugs in kebab-case
- [ ] KPIs are SMART (specific, measurable, achievable, relevant, time-bound)
- [ ] Tone matches target language (professional, data-driven)

---

## Example Workflow

```bash
# 1. Collect data
python scripts/gsc_query.py --site "sc-domain:example.com" --days 90 --out gsc.json
python scripts/site_crawler.py --domain https://example.com --out client.json
python scripts/site_crawler.py --domain https://competitor1.com --out c1.json

# 2. Claude synthesizes content.json following this guide

# 3. Render
python scripts/strategy_report_builder.py \
  --content content.json \
  --template skills/seo-strategy-report/assets/template.html \
  --out report.doc

# 4. Validate
grep -c "{{" report.doc  # should be 0
```

---

## Tips for Quality

1. **Use real data**: Never invent GSC numbers, competitor URLs, or ratings
2. **Be specific**: Name competitors, cite sources, use concrete examples
3. **Balance**: Mix positive findings with opportunities
4. **Actionable**: Every recommendation should be implementable
5. **Prioritized**: Sort by impact/effort, urgency, dependency
6. **Consistent**: Use same emojis, terminology throughout
7. **Professional**: Data-driven tone, no marketing fluff

The goal is a report that a client can immediately use to guide their SEO strategy for the next 12 months.
