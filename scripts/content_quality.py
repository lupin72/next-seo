#!/usr/bin/env python3
"""
Analyze content quality for SEO: E-E-A-T signals, readability, word count, thin content.

Usage:
    python content_quality.py https://example.com
    python content_quality.py --file page.html
"""

import argparse
import json
import re
import sys
from collections import Counter
from typing import Dict, List, Tuple

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 required. Install with: pip install beautifulsoup4")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)


def fetch_page(url: str) -> str:
    """Fetch page content."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def extract_text_content(soup: BeautifulSoup) -> Dict[str, any]:
    """Extract all text content from the page."""
    # Remove script and style elements
    for script in soup(["script", "style", "noscript"]):
        script.decompose()

    # Get main content
    main_content = soup.find("main") or soup.find("article") or soup.find("body")

    # Extract headings
    headings = {
        "h1": [h.get_text(strip=True) for h in soup.find_all("h1")],
        "h2": [h.get_text(strip=True) for h in soup.find_all("h2")],
        "h3": [h.get_text(strip=True) for h in soup.find_all("h3")],
        "h4": [h.get_text(strip=True) for h in soup.find_all("h4")],
    }

    # Extract paragraphs
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]

    # Full body text
    body_text = main_content.get_text(separator=" ", strip=True) if main_content else ""

    return {
        "headings": headings,
        "paragraphs": paragraphs,
        "body_text": body_text,
    }


def calculate_word_count(text: str) -> int:
    """Calculate word count."""
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def calculate_readability(text: str) -> Dict[str, float]:
    """Calculate readability metrics (Flesch Reading Ease approximation)."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    words = re.findall(r'\b\w+\b', text)

    if not sentences or not words:
        return {
            "avg_sentence_length": 0,
            "avg_word_length": 0,
            "flesch_reading_ease": 0,
            "grade_level": "N/A"
        }

    # Count syllables (rough approximation)
    syllables = sum(count_syllables(word) for word in words)

    avg_sentence_length = len(words) / len(sentences)
    avg_syllables_per_word = syllables / len(words) if words else 0
    avg_word_length = sum(len(w) for w in words) / len(words)

    # Flesch Reading Ease: 206.835 - 1.015(total words/total sentences) - 84.6(total syllables/total words)
    flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    flesch_score = max(0, min(100, flesch_score))  # Clamp between 0-100

    # Grade level approximation
    if flesch_score >= 90:
        grade_level = "5th grade (Very easy)"
    elif flesch_score >= 80:
        grade_level = "6th grade (Easy)"
    elif flesch_score >= 70:
        grade_level = "7th grade (Fairly easy)"
    elif flesch_score >= 60:
        grade_level = "8-9th grade (Standard)"
    elif flesch_score >= 50:
        grade_level = "10-12th grade (Fairly difficult)"
    elif flesch_score >= 30:
        grade_level = "College (Difficult)"
    else:
        grade_level = "College graduate (Very difficult)"

    return {
        "avg_sentence_length": round(avg_sentence_length, 1),
        "avg_word_length": round(avg_word_length, 1),
        "flesch_reading_ease": round(flesch_score, 1),
        "grade_level": grade_level
    }


def count_syllables(word: str) -> int:
    """Count syllables in a word (rough approximation)."""
    word = word.lower()
    vowels = "aeiouy"
    syllable_count = 0
    previous_was_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            syllable_count += 1
        previous_was_vowel = is_vowel

    # Adjust for silent e
    if word.endswith('e'):
        syllable_count -= 1

    # Every word has at least one syllable
    if syllable_count == 0:
        syllable_count = 1

    return syllable_count


def assess_eeat(soup: BeautifulSoup, content: Dict) -> Dict[str, any]:
    """Assess E-E-A-T signals."""
    signals = {
        "experience": [],
        "expertise": [],
        "authoritativeness": [],
        "trustworthiness": []
    }

    # Experience signals
    experience_indicators = [
        "our experience", "we have", "years of", "established in",
        "since 19", "since 20", "founded", "family-owned", "family-run",
        "nuestro hotel", "desde 19", "desde 20", "años de experiencia"
    ]

    text_lower = content["body_text"].lower()
    for indicator in experience_indicators:
        if indicator in text_lower:
            signals["experience"].append(f"Found: '{indicator}'")

    # Expertise signals (industry-specific for hospitality)
    expertise_indicators = [
        "certified", "award", "star rating", "★", "review", "testimonial",
        "certificado", "premio", "estrellas", "opiniones", "reseñas"
    ]

    for indicator in expertise_indicators:
        if indicator in text_lower:
            signals["expertise"].append(f"Found: '{indicator}'")

    # Check for author bio/about section
    author_section = soup.find(["section", "div"], class_=re.compile(r"author|about|bio", re.I))
    if author_section:
        signals["expertise"].append("Author/About section present")

    # Authoritativeness signals
    # Check for schema.org markup
    schema_scripts = soup.find_all("script", type="application/ld+json")
    if schema_scripts:
        signals["authoritativeness"].append(f"Found {len(schema_scripts)} schema.org markup(s)")
        for script in schema_scripts:
            try:
                schema_data = json.loads(script.string)
                schema_type = schema_data.get("@type", "Unknown")
                signals["authoritativeness"].append(f"Schema type: {schema_type}")
            except:
                pass

    # Check for external links to authoritative sources
    external_links = soup.find_all("a", href=re.compile(r"^https?://(?!example\.com)"))
    if external_links:
        signals["authoritativeness"].append(f"Found {len(external_links)} external links")

    # Trustworthiness signals
    trust_indicators = {
        "contact": soup.find(["section", "div", "footer"], class_=re.compile(r"contact", re.I)),
        "privacy": soup.find("a", href=re.compile(r"privacy|privacidad", re.I)),
        "terms": soup.find("a", href=re.compile(r"terms|condiciones|legal", re.I)),
        "ssl": True,  # Assume HTTPS from URL
        "address": soup.find(["address", "div"], class_=re.compile(r"address|direccion", re.I)),
        "phone": soup.find("a", href=re.compile(r"^tel:")),
        "email": soup.find("a", href=re.compile(r"^mailto:"))
    }

    for indicator, present in trust_indicators.items():
        if present:
            signals["trustworthiness"].append(f"{indicator.title()} information present")

    return signals


def calculate_eeat_scores(signals: Dict) -> Dict[str, int]:
    """Calculate E-E-A-T scores (0-100)."""
    scores = {}
    weights = {
        "experience": 20,
        "expertise": 25,
        "authoritativeness": 25,
        "trustworthiness": 30
    }

    # Score based on number of signals found
    max_signals = {
        "experience": 5,
        "expertise": 8,
        "authoritativeness": 10,
        "trustworthiness": 7
    }

    for factor, signal_list in signals.items():
        signal_count = len(signal_list)
        max_count = max_signals[factor]
        score = min(100, int((signal_count / max_count) * 100))
        scores[factor] = score

    # Calculate overall E-E-A-T score
    overall = sum(scores[f] * (weights[f] / 100) for f in scores.keys())
    scores["overall"] = int(overall)

    return scores


def detect_thin_content(content: Dict, word_count: int) -> Dict[str, any]:
    """Detect thin content issues."""
    issues = []

    # Minimum word count thresholds by page type
    MIN_HOMEPAGE = 500
    MIN_SERVICE = 800
    MIN_BLOG = 1500
    MIN_PRODUCT = 300

    # Detect page type (simplified)
    page_type = "homepage"  # Default assumption

    if word_count < MIN_HOMEPAGE:
        issues.append(f"Word count ({word_count}) below homepage minimum ({MIN_HOMEPAGE})")

    # Check for duplicate content patterns
    paragraphs = content["paragraphs"]
    if len(paragraphs) > 1:
        para_lengths = [len(p) for p in paragraphs]
        avg_para_length = sum(para_lengths) / len(para_lengths)

        if avg_para_length < 50:
            issues.append(f"Short paragraphs (avg {int(avg_para_length)} chars)")

    # Check heading structure
    h1_count = len(content["headings"]["h1"])
    if h1_count == 0:
        issues.append("Missing H1 heading")
    elif h1_count > 1:
        issues.append(f"Multiple H1 headings ({h1_count})")

    h2_count = len(content["headings"]["h2"])
    if h2_count < 2:
        issues.append("Insufficient H2 subheadings for structure")

    return {
        "is_thin": len(issues) > 0,
        "issues": issues,
        "page_type": page_type,
        "word_count": word_count,
        "min_recommended": MIN_HOMEPAGE
    }


def assess_ai_citation_readiness(soup: BeautifulSoup, content: Dict) -> Dict[str, any]:
    """Assess content for AI citation readiness (GEO/AIO optimization)."""
    scores = {
        "quotable_facts": 0,
        "structured_data": 0,
        "clear_hierarchy": 0,
        "overall": 0
    }

    signals = []

    # Quotable facts (lists, stats, specific claims)
    lists = soup.find_all(["ul", "ol"])
    if lists:
        scores["quotable_facts"] += min(30, len(lists) * 10)
        signals.append(f"Found {len(lists)} lists (quotable content)")

    # Look for statistics/numbers
    numbers = re.findall(r'\b\d+\s*(?:%|percent|years|km|stars?|★)\b', content["body_text"])
    if numbers:
        scores["quotable_facts"] += min(20, len(numbers) * 5)
        signals.append(f"Found {len(numbers)} statistics/numbers")

    # Structured data
    schema_scripts = soup.find_all("script", type="application/ld+json")
    if schema_scripts:
        scores["structured_data"] += min(50, len(schema_scripts) * 25)
        signals.append(f"Found {len(schema_scripts)} schema.org markup(s)")

    # Tables (structured data)
    tables = soup.find_all("table")
    if tables:
        scores["structured_data"] += min(20, len(tables) * 10)
        signals.append(f"Found {len(tables)} tables")

    # Clear hierarchy (proper heading structure)
    h1_count = len(content["headings"]["h1"])
    h2_count = len(content["headings"]["h2"])
    h3_count = len(content["headings"]["h3"])

    if h1_count == 1:
        scores["clear_hierarchy"] += 30
        signals.append("Single H1 (good hierarchy)")

    if h2_count >= 3:
        scores["clear_hierarchy"] += 40
        signals.append(f"{h2_count} H2 headings (clear sections)")

    if h3_count >= 2:
        scores["clear_hierarchy"] += 30
        signals.append(f"{h3_count} H3 headings (detailed structure)")

    # Calculate overall score (average of components, capped at 100)
    scores["overall"] = min(100, int((scores["quotable_facts"] + scores["structured_data"] + scores["clear_hierarchy"]) / 3))

    return {
        "scores": scores,
        "signals": signals
    }


def analyze_content_quality(html: str, url: str = None) -> Dict:
    """Main content quality analysis."""
    soup = BeautifulSoup(html, "html.parser")

    # Extract content
    content = extract_text_content(soup)
    word_count = calculate_word_count(content["body_text"])

    # Readability
    readability = calculate_readability(content["body_text"])

    # E-E-A-T analysis
    eeat_signals = assess_eeat(soup, content)
    eeat_scores = calculate_eeat_scores(eeat_signals)

    # Thin content detection
    thin_content = detect_thin_content(content, word_count)

    # AI citation readiness
    ai_citation = assess_ai_citation_readiness(soup, content)

    # Overall content quality score
    # Weighted: E-E-A-T (40%), Word count adequacy (20%), Readability (20%), AI readiness (20%)
    word_count_score = min(100, int((word_count / thin_content["min_recommended"]) * 100))
    readability_score = int(readability["flesch_reading_ease"])

    overall_quality_score = int(
        eeat_scores["overall"] * 0.4 +
        word_count_score * 0.2 +
        readability_score * 0.2 +
        ai_citation["scores"]["overall"] * 0.2
    )

    return {
        "url": url,
        "content_quality_score": overall_quality_score,
        "word_count": word_count,
        "readability": readability,
        "eeat": {
            "scores": eeat_scores,
            "signals": eeat_signals
        },
        "thin_content": thin_content,
        "ai_citation_readiness": ai_citation,
        "headings": content["headings"],
        "paragraph_count": len(content["paragraphs"])
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze content quality for SEO")
    parser.add_argument("url", nargs="?", help="URL to analyze")
    parser.add_argument("--file", help="HTML file to analyze")
    parser.add_argument("--output", "-o", help="Output JSON file")

    args = parser.parse_args()

    if not args.url and not args.file:
        parser.error("Either URL or --file required")

    # Get HTML content
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            html = f.read()
        url = args.file
    else:
        html = fetch_page(args.url)
        url = args.url

    # Analyze
    result = analyze_content_quality(html, url)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
