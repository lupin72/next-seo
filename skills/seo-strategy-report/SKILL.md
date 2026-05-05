---
name: seo-strategy-report
description: |
  Generate a comprehensive SEO strategy report for any business in HTML-Word
  format (.doc), following a professional structure: executive summary,
  competitor analysis, SWOT, keyword research with gaps, opportunities, page/slug
  recommendations, 12-month editorial calendar, technical recommendations, and
  phased action plan. Use this skill whenever the user asks for an "SEO
  report", "SEO strategy", "content plan", "competitor analysis SEO", "SEO audit
  report", or wants to produce a client-facing strategic SEO document. Also trigger
  when the user mentions Google Search Console data + competitor analysis +
  client deliverable. The skill pulls live data from the Google Search Console
  API, crawls the client site and competitors, synthesizes everything, and
  outputs a styled .doc that opens directly in Word. Supports multiple languages
  and industries.
license: Proprietary
version: 1.0.0
date: 2026-05-05
---

# SEO Strategy Report

Generates a client-ready SEO strategy & content plan for any business, structured as
a 10-section professional report. The output is a single `.doc` file (HTML
inside, but Word opens it natively) styled with a clean professional visual identity
(corporate blues, alert/highlight/success boxes, slug pills, monospace URL trees).

## When to use this skill

Trigger on requests like:

- "Create an SEO report for [business name]"
- "I need an SEO strategy + content plan for my client"
- "Competitor analysis SEO for [business] in [industry]"
- "SEO audit and proposal for [business name]"
- "Generate a strategic SEO document for [client]"

Do NOT trigger for: generic SEO audits unrelated to strategic planning, single-page SEO
reviews, or technical-only audits without strategic content planning.

---

## Workflow overview

The skill follows three stages:

1. **Data collection** — pull GSC data + crawl client site + crawl 3-6 competitors
2. **Analysis & synthesis** — produce a content JSON that fills every section
3. **Render** — fill the HTML template and write `.doc` to outputs

```
User request → ask for inputs → fetch GSC → crawl sites → synthesize content JSON → render HTML/.doc → present_files
```

---

## Stage 1 — Inputs to gather from the user

Before doing any work, use AskUserQuestion to gather information if missing. Do not
proceed until you have at minimum the business name and domain.

**Required**:
- Business name and tagline (industry, location, positioning)
- Business domain (e.g. `example.com`)
- Industry type (Hospitality, E-commerce, SaaS, Local Business, Professional Services, etc.)
- Target year for the editorial calendar
- Report date (month + year)
- Report language (English, Spanish, Italian, French, German - auto-detect from conversation or ask)
- Path to GSC credentials JSON (OAuth2 or service account) — ask the user to
  drop it in `~/.config/claude-seo/google-api.json` or provide a path. If the user does not
  have GSC access, fall back to a manual workflow (see "GSC fallback" below).

**Recommended**:
- GSC site URL (could differ from main domain, e.g. `sc-domain:example.com`)
- 3-6 competitor domains (or ask the skill to detect them via Google search for
  relevant keywords in the industry)
- Business client/group name (parent company)
- Target audience description
- Business USP / differentiators
- Languages currently supported on the site
- Any existing analytics or rank-tracker data

**Useful but optional**:
- Existing rankings or rank-tracker exports
- Internal data on conversion metrics
- Promotional calendar already planned by the marketing team

---

## Stage 2 — Data collection

### 2.1 Google Search Console (preferred)

Run `scripts/gsc_query.py`:

```bash
python scripts/gsc_query.py \
  --site "sc-domain:example.com" \
  --days 90 \
  --limit 200 \
  --out gsc_data.json
```

Output (`gsc_data.json`) contains:

- **Queries with metrics** — top queries with clicks/impressions/CTR/position, branded flag
- **Pages with metrics** — top URLs with metrics
- Use this data to identify:
  - Low-hanging fruit (positions 5-20 with good impressions)
  - Lost clicks (queries that lost traffic)
  - Branded vs non-branded performance
  - Country/device breakdown for targeting decisions

### 2.2 Site crawler (client + competitors)

Check if `scripts/site_crawler.py` exists. If not, copy from the hotel skill or create it.

Run once per site:

```bash
python scripts/site_crawler.py --domain https://example.com --out client_site.json --max 100
python scripts/site_crawler.py --domain https://competitor1.com --out comp1.json --max 50
```

For each site you get:

- **total_urls** — for the URLs-indexed comparison
- **pages** — title, meta_desc, H1, H2 list, word count, lang, image stats,
  schema types, internal links per URL
- **blog_posts** — list with titles
- **summary** — flags for industry-specific pages (e.g., has_rooms_page for hospitality,
  has_product_pages for e-commerce, has_pricing_page for SaaS)

Use these flags to identify content gaps compared to competitors.

### 2.3 GSC fallback (when no API access)

If the user can't provide credentials, ask them to:

1. Export their last 90 days of "Performance > Queries" from GSC as CSV
2. Export "Performance > Pages" CSV
3. Drop both in the active project's `data/` folder

Then read them with pandas in a small ad-hoc script to convert to JSON format.

### 2.4 Competitor identification

If the user doesn't supply competitors, identify them with `WebSearch` queries
relevant to the industry:
- Hospitality: `[location] hotel [feature]`, `romantic getaway [location]`
- E-commerce: `buy [product category] online`, `best [product type]`
- SaaS: `[software category] tool`, `[feature] software`
- Local: `[service] in [city]`, `best [service provider] [location]`

Pick the top 3-6 organic results (excluding aggregators like Yelp, TripAdvisor,
marketplaces — those are platforms, not direct competitors).

---

## Stage 3 — Synthesis: build the content JSON

The renderer expects a single JSON file with the structure documented at the
top of `scripts/strategy_report_builder.py`. See `examples/example_content.json` for a
fully populated reference.

### Section-by-section synthesis guide

**1. Executive Summary** — Pull the most striking numbers from GSC totals + the
URL count gap vs the largest competitor. The "key_findings" list should be 6-8
bullets, each one combining a metric with a strategic implication. The business
profile paragraph should be factual, dense, finishing with the target audience.

**2. Current Website Analysis** — `sitemap_pages` comes directly from the
client crawler; rate each page using these heuristics:
- title 50-60 chars + has location/product keyword + has differentiator → ✓
- title too short or generic → ⚠
- title duplicates another page or is just "Contact"/"News" → ✗

`blog_articles` is filled from the crawler's `blog_posts` for the client. For
each one, infer a probable target keyword from the title and rate ✓ / ⚠ / ✗
based on whether the title clearly maps to a search intent.

**3. Competition** — Build the `competitors` table. Always put the client business
LAST in the list with a 🚀 emoji and a "OUR BUSINESS" prefix to make it stand
out. Use color circles 🔴 (high) 🟡 (medium) 🟢 (low) for positioning, never
just words. `competitor_insights` is 3-5 bullets of "what's competitor X doing
well that we should learn from".

**4. SWOT** — Each cell is a list of short bullets (5-12 words each). The
opportunities list should foreshadow the recommendations in section 6. Threats
should mention aggregators/platforms and the strongest 1-2 competitors by name.

**5. Keywords & gaps** — `keywords` table mixes:
- Branded keywords from GSC (positions 1-3, just to confirm they're handled)
- Non-branded transactional keywords (industry-specific)
- Seasonal keywords (holidays, events, seasons)
- Informational keywords (guides, how-tos, comparisons)

For each one, set `current_position` based on GSC data if available, else
"Not ranking" if it's a gap. Action column should be specific: "Create landing"
/ "Optimize homepage" / "Create guide" / "Improve position" — not vague.

`gaps` list: 3 critical (level=critical, red box) + 2 important (level=important,
yellow box). Each gap names a specific competitor URL that's winning the gap.

**6. Opportunities** — 8-10 prioritized opportunities. Use 🔴/🟡/🟢 emojis in
the impact column. `brand_opportunities` is the place to highlight the business's
unique differentiator and any adjacent assets. 1-3 boxes total.

**7. Pages to create** — Three tables (adapt to industry):
- `structural_pages`: core service/product pages
- `experience_pages`: thematic packages, use cases, solutions
- `blog_guides`: destination/informational content

For each, write the slug in kebab-case with relevant keywords. The H1 keyword
column should be the literal H1 the page should use — phrased as a search query,
not a marketing slogan.

**8. Editorial Calendar** — Cover all 12 months of `year`. Each month gets a
descriptive label that hooks the seasonal angle. Each month has 2-4 entries
(most months 2; busy months can have 4). Mix "New Page" / "Offer Landing" /
"Blog" types. Always reuse slugs from sections 7.1-7.3 when launching
those pages — the calendar is the launch schedule.

**9. Technical SEO** — `quick_wins` is 8-12 actionable items, sorted by
impact/effort ratio. Mention image alt-text, schema markup (industry-appropriate
types), breadcrumbs, internal linking, Core Web Vitals. The `url_architecture`
field is a multiline tree using `├─` and `└─` characters — preserve indentation
exactly. `reoptimize` is the existing-pages-to-improve list.

**10. Action Plan** — Three phases:
- Phase 1 (months 1-2): foundations — must-have structural pages
- Phase 2 (months 3-6): growth — seasonal landings + content marketing
- Phase 3 (months 7-12): consolidation — scale + optimization

Each task has a clear owner and a measurable KPI. `kpis` table at the end is
the executive scorecard — keep it under 10 metrics.

### Tone and language

The report should be professional but direct. Language-specific guidelines:

**English**:
- "Findings" not "Hallazgos"
- "Ranking" not "Posicionamiento"
- Use percentages and concrete numbers wherever possible
- Use emojis consistently (🔴🟡🟢🚀🌟⚠️✓✗)
- Keep paragraphs short — most bullets are one sentence

**Spanish**:
- "Hallazgos" not "findings"
- "Posicionamiento" not "ranking"
- Maintain professional tone

**Italian**:
- "Risultati" for findings
- "Posizionamento" for ranking
- Maintain professional tone

For seasonal events, adapt to local context:
- English: Easter, Bank Holiday, Summer, Black Friday
- Spanish: Semana Santa, Puente, Verano, Black Friday
- Italian: Pasqua, Ponte, Estate, Black Friday

---

## Stage 4 — Render

Once the content JSON is complete, render the report:

```bash
python scripts/strategy_report_builder.py \
  --content content.json \
  --template skills/seo-strategy-report/assets/template.html \
  --out clients/{client-slug}/{project-slug}/reports/SEO-Strategy-<BusinessName>-<Year>.doc
```

Then use present_files or save to the active project folder.

### Filename convention

`SEO-Strategy-<BusinessKebabCase>-<Year>.doc`

Examples:
- `SEO-Strategy-Example-Business-2026.doc`
- `SEO-Strategy-Acme-Corp-2026.doc`

### Validation

After rendering:

1. Check the file size (should be 25-50 KB for a complete report)
2. Verify no `{{PLACEHOLDER}}` strings remain: `grep "{{" output.doc` should
   return empty
3. Optionally generate a preview: convert to PDF with LibreOffice and
   look at page 1 to confirm the cover page and section 1 look correct

```bash
grep -c "{{" /path/to/output.doc  # must print 0
```

---

## Industry-specific adaptations

### Hospitality (Hotels, Resorts, B&Bs)
- Structural pages: Rooms, Spa, Restaurant, Pool, Common Areas
- Experience pages: Romantic getaway, Wellness, Family, Adults-only, Seasonal packages
- Keywords focus: Location + amenity, seasonal offers, experiential searches

### E-commerce
- Structural pages: Product categories, Collections, Sale pages
- Experience pages: Buying guides, Gift guides, Seasonal collections
- Keywords focus: Product names, "buy X online", comparisons, reviews

### SaaS
- Structural pages: Features, Pricing, Integrations, Use cases
- Experience pages: Industry solutions, Role-based pages, Comparison pages
- Keywords focus: "[category] software", "best tool for X", "vs competitor"

### Local Business
- Structural pages: Services, Locations, Service areas, Team
- Experience pages: Case studies, Testimonials, Emergency services
- Keywords focus: "[service] in [city]", "near me", emergency terms

### Professional Services
- Structural pages: Services, Expertise, Case studies, Team
- Experience pages: Industry-specific services, Guides, Resources
- Keywords focus: "[service] for [industry]", "[problem] solution"

See `references/industry-templates.md` for detailed templates.

---

## Integration with existing skills

This skill integrates with:

- `/seo-project` — saves reports to active project folder
- `/seo-client` — pulls client information
- `scripts/gsc_query.py` — reuses existing GSC data fetching
- `scripts/client_manager.py` — tracks report generation in database

---

## Customization tips

### Different visual style

The template's CSS lives in the `<style>` block at the top of
`assets/template.html`. The corporate color scheme uses `#005580` (dark blue)
and `#1a6fa8` (medium blue). To customize:

- Change `#005580` to the client's primary brand color (h1 borders, table
  headers, cover background)
- Change `#1a6fa8` to a complementary tone (h2 background tint)
- Keep `.alert` red, `.hl` amber, `.ok` green — these are semantic and work
  across all industries

### Different sections

If a business doesn't need certain sections (e.g. no plan to internationalize,
skip section about adding languages), pass an empty list/string for those keys
in the JSON. The template will render the heading with empty content.

### Larger/smaller editorial calendar

Default is 12 months. For shorter engagements (Q1 only), populate
`editorial_calendar` with 3 months. The template auto-adapts.

---

## File map

```
seo-strategy-report/
├── SKILL.md                           # this file
├── assets/
│   └── template.html                  # HTML template with {{PLACEHOLDERS}}
├── references/
│   ├── industry-templates.md          # Industry-specific section templates
│   ├── report-structure.md            # Detailed structure documentation
│   └── synthesis-guide.md             # Step-by-step synthesis guide
├── examples/
│   └── example_content.json           # full reference (Hotel example)
└── (scripts moved to main scripts/ folder)
```

---

## Dependencies

Python packages required (in `requirements.txt`):
- `google-api-python-client` (GSC API)
- `google-auth-httplib2` (GSC auth)
- `google-auth-oauthlib` (GSC OAuth)
- `requests` (site crawling)
- `beautifulsoup4` (HTML parsing)
- `lxml` (XML parsing)

---

## End-to-end example

```bash
# 1. User requests: "Create an SEO strategy report for Acme Corp"
# 2. Skill asks via AskUserQuestion:
#    - Industry? → "E-commerce"
#    - Domain? → "acmecorp.com"
#    - Report language? → "English" (auto-detected)
#    - GSC access? → Yes, using ~/.config/claude-seo/google-api.json

# 3. Fetch GSC data
python scripts/gsc_query.py \
  --site "sc-domain:acmecorp.com" \
  --days 90 --limit 200 \
  --out gsc_data.json

# 4. Crawl client + 3 competitors (detected via WebSearch)
python scripts/site_crawler.py --domain https://acmecorp.com --out client.json --max 100
python scripts/site_crawler.py --domain https://competitor1.com --out c1.json --max 50
python scripts/site_crawler.py --domain https://competitor2.com --out c2.json --max 50
python scripts/site_crawler.py --domain https://competitor3.com --out c3.json --max 50

# 5. Synthesize content (Claude reads all JSON files, industry template,
#    does WebSearch for competitor positioning, writes content.json)

# 6. Render
python scripts/strategy_report_builder.py \
  --content content.json \
  --template skills/seo-strategy-report/assets/template.html \
  --out clients/acme-corp/main-site/reports/SEO-Strategy-Acme-Corp-2026.doc

# 7. Verify and present
grep -c "{{" clients/acme-corp/main-site/reports/SEO-Strategy-Acme-Corp-2026.doc  # must be 0
# present_files or save to project
```

---

## Common pitfalls

- **Don't skip Stage 1.** A report with wrong client name or industry will fail
  sanity checks. Always confirm the basics via AskUserQuestion.
- **Don't invent GSC data.** If the API call fails, say so and ask for a CSV
  export. Never fabricate clicks/impressions numbers.
- **Don't put competitors as bullet text.** They go in the `competitors` table
  with all six columns filled.
- **Don't skip the low-hanging fruit analysis.** Those queries (positions
  5-20, good impressions, non-branded) are the most actionable insights and
  should drive section 5.1 and the Phase 1 action plan.
- **Don't forget the 🚀 prefix on the client business.** It's how the reader
  immediately spots their own business in the competitor table.
- **Don't write the URL architecture inline as bullets.** It must be a
  `<pre>`-formatted ASCII tree using `├─` and `└─` to look like a real
  filesystem hierarchy.
- **Adapt to industry.** Don't use hotel-specific terms (rooms, spa) for
  e-commerce or SaaS reports. Use the industry template as a guide.
