"""
strategy_report_builder.py
Takes a JSON file with all report content and fills the HTML template.

The content JSON has the following structure (all fields optional except marked required):

{
    "report_title": "SEO Strategy 2026",       # required
    "business_name": "Business X",             # required
    "business_tagline": "Industry | Location",
    "year": "2026",
    "report_subtitle": "Analysis based on GSC + competition",
    "report_date": "June 2026",
    "business_domain": "businessx.com",
    "client_group": "Parent Company Y",
    "business_profile": "Profile text...",
    "key_findings": ["point 1", "point 2", ...],
    "sitemap_pages": [
        {"url": "/", "title": "...", "rating": "✓ Well optimized"}
    ],
    "critical_gap_summary": "No product pages, no pricing page.",
    "blog_articles": [
        {"title": "...", "section": "...", "keyword": "...", "seo": "✓"}
    ],
    "competitors": [
        {"name": "Business A", "positioning": "...", "urls": "308+",
         "rating": "4.1★", "price_from": "49€", "audience": "Family"}
    ],
    "competitor_insights": ["bullet 1", "bullet 2"],
    "swot": {
        "strengths": ["..."], "weaknesses": ["..."],
        "opportunities": ["..."], "threats": ["..."]
    },
    "keywords": [
        {"keyword": "...", "type": "Transactional", "volume": "High",
         "difficulty": "High", "current_position": "Maps pack", "action": "..."}
    ],
    "gaps": [
        {"level": "critical|important", "title": "Gap 1", "text": "..."}
    ],
    "opportunities": [
        {"opportunity": "...", "keywords": "...", "impact": "Very high", "difficulty": "Medium"}
    ],
    "brand_opportunities": [
        {"type": "ok|hl|alert", "title": "🌟 ...", "text": "..."}
    ],
    "structural_pages": [
        {"page": "...", "slug": "/x/", "h1_keyword": "...", "content": "..."}
    ],
    "experience_pages": [...],
    "blog_guides": [...],
    "editorial_calendar": [
        {
            "month_label": "January 2026 — Launch...",
            "rows": [
                {"week": "W1", "type": "New Page", "title": "...",
                 "slug": "/x/", "keyword": "..."}
            ]
        }
    ],
    "quick_wins": [
        {"action": "...", "where": "...", "impact": "...", "effort": "..."}
    ],
    "url_architecture": "multiline string with tree",
    "reoptimize": [
        {"page": "/services/", "problem": "...", "solution": "..."}
    ],
    "phase1_period": "January — February 2026",
    "phase1_tasks": [
        {"task": "...", "responsible": "...", "deadline": "...", "kpi": "..."}
    ],
    "phase2_period": "...",
    "phase2_tasks": [...],
    "phase3_period": "...",
    "phase3_tasks": [...],
    "kpis": [
        {"metric": "...", "tool": "...", "frequency": "...", "target": "..."}
    ]
}

Usage:
    python strategy_report_builder.py --content content.json --template template.html --out report.doc
"""

import argparse
import html
import json
import sys
from pathlib import Path


def esc(s) -> str:
    """Escape HTML but keep content readable."""
    if s is None:
        return ''
    if not isinstance(s, str):
        s = str(s)
    return html.escape(s, quote=False)


def render_list(items: list[str]) -> str:
    """Render a list of strings as multiple <li> elements."""
    if not items:
        return ''
    return '\n'.join(f'<li>{esc(item)}</li>' for item in items)


def render_table_rows(rows: list[dict], columns: list[str]) -> str:
    """Render table rows from list of dicts and column order."""
    if not rows:
        return ''
    out = []
    for row in rows:
        cells = ''.join(f'<td>{esc(row.get(col, ""))}</td>' for col in columns)
        out.append(f'<tr>{cells}</tr>')
    return '\n'.join(out)


def render_swot_cell(items: list[str]) -> str:
    """Render SWOT cell as bulleted list."""
    if not items:
        return ''
    return '<ul>' + ''.join(f'<li>{esc(it)}</li>' for it in items) + '</ul>'


def render_gap_blocks(gaps: list[dict]) -> str:
    """Each gap is an alert block (critical) or hl block (important)."""
    if not gaps:
        return ''
    blocks = []
    for g in gaps:
        cls = 'alert' if g.get('level', 'critical') == 'critical' else 'hl'
        title = esc(g.get('title', ''))
        text = esc(g.get('text', ''))
        blocks.append(
            f'<div class="{cls}"><p><strong>{title}</strong> {text}</p></div>'
        )
    return '\n'.join(blocks)


def render_brand_opportunity_blocks(blocks: list[dict]) -> str:
    """Render brand opportunity highlight blocks."""
    if not blocks:
        return ''
    out = []
    for b in blocks:
        cls = b.get('type', 'ok')
        title = esc(b.get('title', ''))
        text = esc(b.get('text', ''))
        out.append(f'<h2>{title}</h2><div class="{cls}"><p>{text}</p></div>')
    return '\n'.join(out)


def render_editorial_calendar(months: list[dict]) -> str:
    """Each month is an h2 + table."""
    if not months:
        return ''
    parts = []
    for m in months:
        label = esc(m.get('month_label', ''))
        rows = render_table_rows(
            m.get('rows', []),
            ['week', 'type', 'title', 'slug', 'keyword']
        )
        parts.append(f"""<h2>{label}</h2>
<table>
<thead><tr><th>Week</th><th>Type</th><th>Proposed Title</th><th>Slug</th><th>Target Keyword</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>""")
    return '\n'.join(parts)


def render_sitemap_rows(pages: list[dict]) -> str:
    """Render sitemap table with URL in slug format."""
    if not pages:
        return ''
    out = []
    for p in pages:
        url = esc(p.get('url', ''))
        title = esc(p.get('title', ''))
        rating = esc(p.get('rating', ''))
        out.append(
            f'<tr><td><span class="slug">{url}</span></td>'
            f'<td>{title}</td><td>{rating}</td></tr>'
        )
    return '\n'.join(out)


def render_structural_pages(pages: list[dict]) -> str:
    """Tables with slug formatting."""
    if not pages:
        return ''
    out = []
    for p in pages:
        page = esc(p.get('page', ''))
        slug = esc(p.get('slug', ''))
        kw = esc(p.get('h1_keyword', ''))
        content = esc(p.get('content', ''))
        out.append(
            f'<tr><td>{page}</td>'
            f'<td><span class="slug">{slug}</span></td>'
            f'<td>{kw}</td><td>{content}</td></tr>'
        )
    return '\n'.join(out)


def render_blog_guides(guides: list[dict]) -> str:
    """Render blog guide table rows."""
    if not guides:
        return ''
    out = []
    for p in guides:
        out.append(
            f'<tr><td>{esc(p.get("article", ""))}</td>'
            f'<td><span class="slug">{esc(p.get("slug", ""))}</span></td>'
            f'<td>{esc(p.get("h1_keyword", ""))}</td>'
            f'<td>{esc(p.get("intent", ""))}</td></tr>'
        )
    return '\n'.join(out)


def render_calendar_rows(rows: list[dict]) -> str:
    """Render calendar rows with slug formatting."""
    out = []
    for r in rows:
        out.append(
            f'<tr><td>{esc(r.get("week", ""))}</td>'
            f'<td>{esc(r.get("type", ""))}</td>'
            f'<td>{esc(r.get("title", ""))}</td>'
            f'<td><span class="slug">{esc(r.get("slug", ""))}</span></td>'
            f'<td>{esc(r.get("keyword", ""))}</td></tr>'
        )
    return '\n'.join(out)


def render_editorial_calendar_with_slugs(months: list[dict]) -> str:
    """Override simple version to show styled slugs."""
    if not months:
        return ''
    parts = []
    for m in months:
        label = esc(m.get('month_label', ''))
        rows = render_calendar_rows(m.get('rows', []))
        parts.append(f"""<h2>{label}</h2>
<table>
<thead><tr><th>Week</th><th>Type</th><th>Proposed Title</th><th>Slug</th><th>Target Keyword</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>""")
    return '\n'.join(parts)


def render_quick_wins_rows(rows: list[dict]) -> str:
    """Render quick wins table with numbering."""
    out = []
    for i, r in enumerate(rows, 1):
        out.append(
            f'<tr><td>{i}</td>'
            f'<td>{esc(r.get("action", ""))}</td>'
            f'<td>{esc(r.get("where", ""))}</td>'
            f'<td>{esc(r.get("impact", ""))}</td>'
            f'<td>{esc(r.get("effort", ""))}</td></tr>'
        )
    return '\n'.join(out)


def render_opportunities_rows(rows: list[dict]) -> str:
    """Render opportunities table with numbering."""
    out = []
    for i, r in enumerate(rows, 1):
        out.append(
            f'<tr><td>{i}</td>'
            f'<td>{esc(r.get("opportunity", ""))}</td>'
            f'<td>{esc(r.get("keywords", ""))}</td>'
            f'<td>{esc(r.get("impact", ""))}</td>'
            f'<td>{esc(r.get("difficulty", ""))}</td></tr>'
        )
    return '\n'.join(out)


def build(data: dict, template_path: str) -> str:
    """Build the HTML report from data and template."""
    template = Path(template_path).read_text(encoding='utf-8')

    swot = data.get('swot', {})
    branded = data.get('brand_opportunities', [])

    replacements = {
        '{{REPORT_TITLE}}': esc(data.get('report_title', 'SEO Strategy')),
        '{{BUSINESS_NAME}}': esc(data.get('business_name', '')),
        '{{BUSINESS_TAGLINE}}': esc(data.get('business_tagline', '')),
        '{{YEAR}}': esc(data.get('year', '')),
        '{{REPORT_SUBTITLE}}': esc(data.get('report_subtitle', '')),
        '{{REPORT_DATE}}': esc(data.get('report_date', '')),
        '{{BUSINESS_DOMAIN}}': esc(data.get('business_domain', '')),
        '{{CLIENT_GROUP}}': esc(data.get('client_group', '')),
        '{{BUSINESS_PROFILE}}': esc(data.get('business_profile', '')),
        '{{KEY_FINDINGS}}': render_list(data.get('key_findings', [])),
        '{{SITEMAP_ROWS}}': render_sitemap_rows(data.get('sitemap_pages', [])),
        '{{CRITICAL_GAP_SUMMARY}}': esc(data.get('critical_gap_summary', '')),
        '{{BLOG_ROWS}}': render_table_rows(
            data.get('blog_articles', []),
            ['title', 'section', 'keyword', 'seo']
        ),
        '{{COMPETITORS_ROWS}}': render_table_rows(
            data.get('competitors', []),
            ['name', 'positioning', 'urls', 'rating', 'price_from', 'audience']
        ),
        '{{COMPETITORS_INSIGHTS}}': render_list(data.get('competitor_insights', [])),
        '{{SWOT_STRENGTHS}}': render_swot_cell(swot.get('strengths', [])),
        '{{SWOT_WEAKNESSES}}': render_swot_cell(swot.get('weaknesses', [])),
        '{{SWOT_OPPORTUNITIES}}': render_swot_cell(swot.get('opportunities', [])),
        '{{SWOT_THREATS}}': render_swot_cell(swot.get('threats', [])),
        '{{KEYWORDS_ROWS}}': render_table_rows(
            data.get('keywords', []),
            ['keyword', 'type', 'volume', 'difficulty', 'current_position', 'action']
        ),
        '{{GAPS_BLOCKS}}': render_gap_blocks(data.get('gaps', [])),
        '{{OPPORTUNITIES_ROWS}}': render_opportunities_rows(data.get('opportunities', [])),
        '{{BRAND_OPPORTUNITY_BLOCKS}}': render_brand_opportunity_blocks(branded),
        '{{STRUCTURAL_PAGES_ROWS}}': render_structural_pages(data.get('structural_pages', [])),
        '{{EXPERIENCE_PAGES_ROWS}}': render_structural_pages(data.get('experience_pages', [])),
        '{{BLOG_GUIDES_ROWS}}': render_blog_guides(data.get('blog_guides', [])),
        '{{EDITORIAL_CALENDAR}}': render_editorial_calendar_with_slugs(
            data.get('editorial_calendar', [])
        ),
        '{{QUICK_WINS_ROWS}}': render_quick_wins_rows(data.get('quick_wins', [])),
        '{{URL_ARCHITECTURE}}': esc(data.get('url_architecture', '')),
        '{{REOPTIMIZE_ROWS}}': render_table_rows(
            data.get('reoptimize', []),
            ['page', 'problem', 'solution']
        ),
        '{{PHASE1_PERIOD}}': esc(data.get('phase1_period', '')),
        '{{PHASE1_ROWS}}': render_table_rows(
            data.get('phase1_tasks', []),
            ['task', 'responsible', 'deadline', 'kpi']
        ),
        '{{PHASE2_PERIOD}}': esc(data.get('phase2_period', '')),
        '{{PHASE2_ROWS}}': render_table_rows(
            data.get('phase2_tasks', []),
            ['task', 'responsible', 'deadline', 'kpi']
        ),
        '{{PHASE3_PERIOD}}': esc(data.get('phase3_period', '')),
        '{{PHASE3_ROWS}}': render_table_rows(
            data.get('phase3_tasks', []),
            ['task', 'responsible', 'deadline', 'kpi']
        ),
        '{{KPIS_ROWS}}': render_table_rows(
            data.get('kpis', []),
            ['metric', 'tool', 'frequency', 'target']
        ),
    }

    out = template
    for placeholder, value in replacements.items():
        out = out.replace(placeholder, value)
    return out


def main():
    """CLI entry point for building SEO strategy reports."""
    parser = argparse.ArgumentParser(description='Build SEO strategy report HTML.')
    parser.add_argument('--content', required=True, help='JSON with report content')
    parser.add_argument('--template', required=True, help='HTML template (template.html)')
    parser.add_argument('--out', required=True, help='Output file (.doc)')
    args = parser.parse_args()

    data = json.loads(Path(args.content).read_text(encoding='utf-8'))
    html_out = build(data, args.template)
    Path(args.out).write_text(html_out, encoding='utf-8')

    print(f"✓ Report generated: {args.out}", file=sys.stderr)
    print(f"  Size: {Path(args.out).stat().st_size:,} bytes", file=sys.stderr)


if __name__ == '__main__':
    main()
