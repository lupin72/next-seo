"""
site_crawler.py
Analyzes a site's sitemap.xml and extracts key meta tags from each URL.

Usage:
    python site_crawler.py --domain https://example.com --out client_site.json
    python site_crawler.py --domain https://competitor.com --out competitor1.json --max 50

Output (JSON):
    {
        "domain": "...",
        "sitemap_urls": [...],
        "total_urls": 17,
        "pages": [
            {
                "url": "...",
                "status": 200,
                "title": "...",
                "meta_description": "...",
                "h1": "...",
                "h2_list": [...],
                "word_count": 850,
                "lang": "es",
                "images_total": 12,
                "images_without_alt": 4,
                "internal_links": 15,
                "schema_types": ["Organization", "FAQPage"]
            }
        ],
        "blog_posts": [ { "url", "title", "date_guess" } ],
        "summary": {
            "languages": ["es", "en", "fr"],
            "has_blog": true,
            "blog_post_count": 10,
            "has_product_pages": false,
            "has_pricing_page": false,
            "has_services_page": false
        }
    }

Requirements:
    pip install requests beautifulsoup4 lxml
"""

import argparse
import json
import re
import sys
import time
from urllib.parse import urlparse, urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: install dependencies with:")
    print("  pip install requests beautifulsoup4 lxml --break-system-packages")
    sys.exit(1)


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; SEOAnalyzer/1.0; +https://example.com/bot)'
}


def fetch_sitemap(domain: str) -> list[str]:
    """Download sitemap.xml (includes sitemap-index recursion) and return URLs."""
    base = domain.rstrip('/')
    candidates = [
        f"{base}/sitemap_index.xml",
        f"{base}/sitemap.xml",
        f"{base}/sitemap-index.xml",
        f"{base}/wp-sitemap.xml",
    ]
    sitemap_xml = None
    for url in candidates:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200 and ('<urlset' in r.text or '<sitemapindex' in r.text):
                print(f"[crawler] Sitemap found: {url}", file=sys.stderr)
                sitemap_xml = (url, r.text)
                break
        except Exception as exc:
            print(f"[crawler] {url} → error: {exc}", file=sys.stderr)

    if not sitemap_xml:
        # Fallback: try robots.txt
        try:
            r = requests.get(f"{base}/robots.txt", headers=HEADERS, timeout=10)
            for line in r.text.splitlines():
                if line.lower().startswith('sitemap:'):
                    sm_url = line.split(':', 1)[1].strip()
                    rs = requests.get(sm_url, headers=HEADERS, timeout=15)
                    if rs.status_code == 200:
                        sitemap_xml = (sm_url, rs.text)
                        break
        except Exception:
            pass

    if not sitemap_xml:
        print("[crawler] No sitemap found. Returning empty list.", file=sys.stderr)
        return []

    return parse_sitemap(sitemap_xml[1])


def parse_sitemap(xml: str, depth: int = 0) -> list[str]:
    """Parse sitemap.xml. If it's an index, download sub-sitemaps."""
    if depth > 3:
        return []
    urls = []
    soup = BeautifulSoup(xml, 'xml')

    # Sitemap index
    for sm in soup.find_all('sitemap'):
        loc = sm.find('loc')
        if loc:
            try:
                r = requests.get(loc.text.strip(), headers=HEADERS, timeout=15)
                if r.status_code == 200:
                    urls.extend(parse_sitemap(r.text, depth + 1))
            except Exception as exc:
                print(f"[crawler] sub-sitemap error: {exc}", file=sys.stderr)

    # Urlset
    for url_tag in soup.find_all('url'):
        loc = url_tag.find('loc')
        if loc:
            urls.append(loc.text.strip())

    return urls


def analyze_page(url: str, domain: str) -> dict:
    """Download a page and extract key SEO info."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        status = r.status_code
        if status != 200:
            return {'url': url, 'status': status, 'error': f'HTTP {status}'}
    except Exception as exc:
        return {'url': url, 'status': 0, 'error': str(exc)}

    soup = BeautifulSoup(r.text, 'lxml')

    title = (soup.title.string.strip() if soup.title and soup.title.string else '').strip()

    meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
    meta_desc = meta_desc_tag.get('content', '').strip() if meta_desc_tag else ''

    h1 = ''
    h1_tag = soup.find('h1')
    if h1_tag:
        h1 = h1_tag.get_text(strip=True)

    h2_list = [h.get_text(strip=True) for h in soup.find_all('h2')[:20]]

    # Language
    html_tag = soup.find('html')
    lang = html_tag.get('lang', '') if html_tag else ''

    # Images and alts
    imgs = soup.find_all('img')
    images_total = len(imgs)
    images_without_alt = sum(1 for img in imgs if not img.get('alt', '').strip())
    bad_alt_examples = [
        img.get('src', '')[:80]
        for img in imgs
        if not img.get('alt', '').strip()
        or re.match(r'^(untitled|image|img|dsc|photo)[-_0-9]*$',
                    img.get('alt', ''), re.I)
    ][:5]

    # Internal links
    parsed_domain = urlparse(domain).netloc.replace('www.', '')
    internal = 0
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/') or parsed_domain in href:
            internal += 1

    # Schema markup
    schema_types = []
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '{}')
            if isinstance(data, dict):
                t = data.get('@type')
                if t:
                    schema_types.append(t if isinstance(t, str) else ','.join(t))
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get('@type'):
                        t = item['@type']
                        schema_types.append(t if isinstance(t, str) else ','.join(t))
        except Exception:
            pass

    # Word count (visible text)
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    word_count = len(text.split())

    return {
        'url': url,
        'status': status,
        'title': title,
        'title_length': len(title),
        'meta_description': meta_desc,
        'meta_description_length': len(meta_desc),
        'h1': h1,
        'h2_list': h2_list,
        'word_count': word_count,
        'lang': lang,
        'images_total': images_total,
        'images_without_alt': images_without_alt,
        'bad_alt_examples': bad_alt_examples,
        'internal_links': internal,
        'schema_types': schema_types,
    }


def categorize_pages(pages: list[dict]) -> dict:
    """Heuristic to detect what types of pages the site has."""
    urls = [p['url'].lower() for p in pages]
    summary = {
        # E-commerce
        'has_product_pages': any(re.search(r'/(product|productos?|produit)s?/', u) for u in urls),
        'has_cart_page': any(re.search(r'/(cart|carrito|panier|warenkorb)', u) for u in urls),
        'has_checkout_page': any(re.search(r'/(checkout|pago|commande)', u) for u in urls),

        # SaaS
        'has_pricing_page': any(re.search(r'/(pricing|precios?|tarif)', u) for u in urls),
        'has_features_page': any(re.search(r'/(features?|caracteristicas?|fonctionnalites?)', u) for u in urls),

        # Hospitality
        'has_rooms_page': any(re.search(r'/(habitacion|rooms?|chambres?|zimmer)', u) for u in urls),
        'has_spa_page': any(re.search(r'/(spa|wellness|bienestar)', u) for u in urls),
        'has_restaurant_page': any(re.search(r'/(restaurante|restaurant|gastronom)', u) for u in urls),

        # Professional Services
        'has_services_page': any(re.search(r'/(servic|services?|dienstleistung)', u) for u in urls),
        'has_case_studies': any(re.search(r'/(case-stud|casos?-exito|portfolio)', u) for u in urls),

        # General
        'has_blog': any(re.search(r'/(blog|noticias|news|actualidad|posts?)', u) for u in urls),
        'has_contact_page': any(re.search(r'/(contacto|contact|kontakt)', u) for u in urls),
    }

    # Languages (heuristic by prefix /xx/)
    langs = set()
    for u in urls:
        m = re.search(r'/(es|en|fr|de|it|pt|ru|nl)/', u)
        if m:
            langs.add(m.group(1))
    if not langs:
        # Try to detect from lang attribute
        for p in pages:
            if p.get('lang'):
                lang_code = p['lang'].split('-')[0].lower()
                if lang_code in ('es', 'en', 'fr', 'de', 'it', 'pt', 'ru', 'nl'):
                    langs.add(lang_code)
    if not langs:
        langs.add('en')  # assume default
    summary['languages'] = sorted(langs)

    # Blog posts
    blog_posts = [p for p in pages if re.search(r'/(blog|noticias|news|posts?)/', p['url'].lower())
                  and not p['url'].rstrip('/').endswith(('blog', 'noticias', 'news'))]
    summary['blog_post_count'] = len(blog_posts)

    return summary


def main():
    """CLI entry point for site crawler."""
    parser = argparse.ArgumentParser(description='Analyze a website for SEO.')
    parser.add_argument('--domain', required=True, help='Base URL (https://example.com)')
    parser.add_argument('--out', default='site_analysis.json', help='Output JSON')
    parser.add_argument('--max', type=int, default=100, help='Max URLs to analyze')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests (s)')
    args = parser.parse_args()

    domain = args.domain.rstrip('/')

    print(f"[crawler] Domain: {domain}", file=sys.stderr)
    sitemap_urls = fetch_sitemap(domain)
    print(f"[crawler] {len(sitemap_urls)} URLs in sitemap", file=sys.stderr)

    if not sitemap_urls:
        # If no sitemap, at least analyze the homepage
        sitemap_urls = [domain + '/']

    sitemap_urls = sitemap_urls[:args.max]

    pages = []
    for i, url in enumerate(sitemap_urls, 1):
        print(f"[crawler] ({i}/{len(sitemap_urls)}) {url}", file=sys.stderr)
        pages.append(analyze_page(url, domain))
        time.sleep(args.delay)

    # Filter pages with errors for stats
    valid_pages = [p for p in pages if p.get('status') == 200]

    summary = categorize_pages(valid_pages)
    blog_posts = [
        {'url': p['url'], 'title': p.get('title', ''), 'h1': p.get('h1', '')}
        for p in valid_pages
        if re.search(r'/(blog|noticias|news|posts?)/', p['url'].lower())
        and not p['url'].rstrip('/').endswith(('blog', 'noticias', 'news'))
    ]

    result = {
        'domain': domain,
        'total_urls': len(valid_pages),
        'sitemap_url_count': len(sitemap_urls),
        'pages': pages,
        'blog_posts': blog_posts,
        'summary': summary,
    }

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Analysis saved to {args.out}", file=sys.stderr)
    print(f"  URLs analyzed: {len(valid_pages)}", file=sys.stderr)
    print(f"  Blog posts: {summary['blog_post_count']}", file=sys.stderr)
    print(f"  Languages: {summary['languages']}", file=sys.stderr)
    print(f"  Structural pages detected:", file=sys.stderr)
    for k in ('has_product_pages', 'has_pricing_page', 'has_services_page', 'has_rooms_page'):
        if k in summary:
            print(f"    {k}: {summary[k]}", file=sys.stderr)


if __name__ == '__main__':
    main()
