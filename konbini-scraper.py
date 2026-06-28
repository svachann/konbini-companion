#!/usr/bin/env python3
"""Konbini product scraper — fetches live item data from Japanese convenience store websites.

Scrapes:
  - 7-Eleven Japan (sej.co.jp): category grid pages + paginated search for drinks & alcohol
  - Lawson + FamilyMart: not directly scrapable (JS-rendered), but their common items
    are enriched by the LLM during the weekly cron sync.

Strategy:
  1. Category grid pages (/products/a/{slug}/kanto/) — fast, 1 request per category.
     Covers: onigiri, bento, sushi, sandwiches, bread, noodles, hot foods, desserts, etc.
  2. Paginated search (/products/a/itemresult/?key={term}&p={n}) — covers categories
     that don't have dedicated grid pages (drinks, alcohol).
  3. All results are deduplicated by product_code.

Outputs JSONL to stdout.
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
SEJ_BASE = "https://www.sej.co.jp"
DEFAULT_REGION = "kanto"

# ─── 7-Eleven: Category grid slugs → our categories ─────────────────────

SEJ_CATEGORY_MAP = {
    "onigiri":   ("onigiri", "🍙"),
    "bento":     ("bento", "🍱"),
    "sushi":     ("bento", "🍱"),
    "sandwich":  ("bento", "🍱"),
    "bread":     ("snacks", "🍪"),
    "donut":     ("desserts", "🍰"),
    "men":       ("noodles", "🍜"),
    "pasta":     ("noodles", "🍜"),
    "gratin":    ("bento", "🍱"),
    "dailydish": ("bento", "🍱"),
    "salad":     ("daily_goods", "📦"),
    "hotsnack":  ("hot_foods", "🍗"),
    "oden":      ("hot_foods", "🍗"),
    "chukaman":  ("hot_foods", "🍗"),
    "sweets":    ("desserts", "🍰"),
    "ice_cream": ("desserts", "🍰"),
    "sevencafe": ("drinks", "🥤"),  # coffee & bakery → drinks
}

# 7-Eleven slugs we skip (not product listings we can parse)
SEJ_SKIP_SLUGS = {"7premium"}

# ─── 7-Eleven: Search terms for missing categories ───────────────────────
# These categories DON'T have dedicated grid pages, so we use the search
# endpoint which supports pagination (up to 20+ pages × 15 items).

SEJ_SEARCH_TERMS = {
    "drinks": "飲料",
    "alcohol": "酒",
}


# ─── HTTP helpers ─────────────────────────────────────────────────────────

def _clean_jp_name(name):
    """Remove HTML tags, extra whitespace, and fullwidth spaces from Japanese names."""
    # Strip HTML tags first (search results have <span class="highlight">)
    name = re.sub(r'<[^>]+>', '', name)
    return re.sub(r'\s+', ' ', name).replace('\u3000', ' ').strip()


def fetch_url(url, retries=2):
    """Fetch a URL with retry and timeout."""
    for attempt in range(retries + 1):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except (HTTPError, URLError, OSError) as e:
            if attempt < retries:
                time.sleep(1 * (attempt + 1))
                continue
            return None


def parse_product_blocks(html):
    """Parse product listing blocks from a 7-Eleven page (category or search result).
    
    Returns list of dicts with product_code and parsed fields.
    """
    items = []
    # Each product lives in a div like: <div class="list_inner -item-code-XXXXXX">
    pattern = r'<div class="list_inner[^"]*-item-code-(\d+)[^"]*">(.*?)</div>\s*<!--\s*list_inner\s*-->'
    for match in re.finditer(pattern, html, re.DOTALL):
        code = match.group(1)
        block = match.group(2)

        # Japanese name
        name_match = re.search(
            r'class="item_ttl"[^>]*>.*?<p><a[^>]*>(.*?)</a></p>',
            block, re.DOTALL
        )
        name_jp = _clean_jp_name(name_match.group(1)) if name_match else ""

        # Price (integer yen, no tax)
        price_match = re.search(
            r'class="item_price"[^>]*>.*?<p>\s*(\d+)[^\d]*',
            block, re.DOTALL
        )
        price_yen = int(price_match.group(1)) if price_match else 0

        # Region availability
        region_match = re.search(
            r'class="item_region"[^>]*>.*?<p>(?:<span>[^<]*</span>)?\s*(.*?)</p>',
            block, re.DOTALL
        )
        regions = region_match.group(1).strip() if region_match else ""

        # Launch date
        launch_match = re.search(
            r'class="item_launch"[^>]*>.*?<p>(.*?)</p>',
            block, re.DOTALL
        )
        launch_date = launch_match.group(1).strip() if launch_match else ""

        # Image URL (data-original for lazy-load, or src)
        img_match = re.search(
            r'<img[^>]*(?:data-original|src)="([^"]+)"',
            block, re.DOTALL
        )
        img_url = img_match.group(1) if img_match else ""

        items.append({
            "product_code": code,
            "jp": name_jp,
            "price_yen": price_yen,
            "regions": regions,
            "launch_date": launch_date,
            "image_url": img_url,
        })

    return items


# ─── Category grid scraping ──────────────────────────────────────────────

def scrape_sej_category(slug, region=DEFAULT_REGION):
    """Scrape a single 7-Eleven category grid page."""
    url = f"{SEJ_BASE}/products/a/{slug}/{region}/"
    html = fetch_url(url)
    if not html:
        return []

    blocks = parse_product_blocks(html)
    mapped_cat, emoji = SEJ_CATEGORY_MAP.get(slug, ("daily_goods", "📦"))

    results = []
    for b in blocks:
        results.append({
            "source": "7-Eleven",
            "source_url": f"{SEJ_BASE}/products/a/item/{b['product_code']}/{region}/",
            "product_code": b["product_code"],
            "jp": b["jp"],
            "price_yen": b["price_yen"],
            "category_slug": slug,
            "category": mapped_cat,
            "emoji": emoji,
            "regions": b["regions"],
            "launch_date": b["launch_date"],
            "image_url": b["image_url"],
        })

    return results


# ─── Search-based scraping ────────────────────────────────────────────────

def get_search_total_pages(html):
    """Parse total item count from search results to estimate pages.
    Falls back to following pagination links."""
    # Parse the counter: e.g. "375件中 1-15件表示" = 375 items
    count_match = re.search(r'(\d+)件中', html)
    if count_match:
        total = int(count_match.group(1))
        pages = (total + 14) // 15  # ceil division, 15 items per page
        return max(pages, 1)
    # Fallback: find max page number from links
    pages = re.findall(r'[?&;]p=(\d+)(?:&|$)', html)
    if pages:
        return max(int(p) for p in pages)
    # Single page
    if parse_product_blocks(html):
        return 1
    return 0


def scrape_sej_search(term_jp, our_category, emoji, region=DEFAULT_REGION, rate_limit=0.3):
    """Scrape all pages of a 7-Eleven search result.

    Args:
        term_jp: Japanese search term (URL-encoded or raw)
        our_category: Our category name (e.g. "drinks", "alcohol")
        emoji: Emoji for the category
        
    Returns list of items.
    """
    from urllib.parse import quote
    
    encoded = quote(term_jp) if not '%' in term_jp else term_jp
    page1_url = f"{SEJ_BASE}/products/a/itemresult/?key={encoded}&limit=15"
    
    html = fetch_url(page1_url)
    if not html:
        return []
    
    total_pages = get_search_total_pages(html)
    if total_pages == 0:
        return []
    
    # Collect all items from all pages
    all_items = {}
    
    # Parse page 1
    blocks = parse_product_blocks(html)
    for b in blocks:
        code = b["product_code"]
        if code not in all_items:
            all_items[code] = {
                "source": "7-Eleven",
                "source_url": f"{SEJ_BASE}/products/a/item/{code}/{region}/",
                "product_code": code,
                "jp": b["jp"],
                "price_yen": b["price_yen"],
                "category_slug": f"search:{term_jp}",
                "category": our_category,
                "emoji": emoji,
                "regions": b["regions"],
                "launch_date": b["launch_date"],
                "image_url": b["image_url"],
            }
    
    # Pages 2+
    for page in range(2, total_pages + 1):
        url = f"{SEJ_BASE}/products/a/itemresult/?key={encoded}&p={page}&limit=15"
        html = fetch_url(url)
        if not html:
            continue
        
        blocks = parse_product_blocks(html)
        for b in blocks:
            code = b["product_code"]
            if code not in all_items:
                all_items[code] = {
                    "source": "7-Eleven",
                    "source_url": f"{SEJ_BASE}/products/a/item/{code}/{region}/",
                    "product_code": code,
                    "jp": b["jp"],
                    "price_yen": b["price_yen"],
                    "category_slug": f"search:{term_jp}",
                    "category": our_category,
                    "emoji": emoji,
                    "regions": b["regions"],
                    "launch_date": b["launch_date"],
                    "image_url": b["image_url"],
                }
        
        time.sleep(rate_limit)
        
        print(f"    Search '{term_jp}' page {page}/{total_pages}: {len(blocks)} blocks, {len(all_items)} unique", file=sys.stderr)
    
    return list(all_items.values())


# ─── High-level functions ────────────────────────────────────────────────

def scrape_sej_all(region=DEFAULT_REGION, rate_limit=0.3):
    """Scrape all available 7-Eleven data."""
    all_items = {}
    
    # 1. Category grid pages
    print("Scraping 7-Eleven category pages...", file=sys.stderr)
    for slug in sorted(SEJ_CATEGORY_MAP):
        if slug in SEJ_SKIP_SLUGS:
            continue
        items = scrape_sej_category(slug, region)
        for item in items:
            all_items[item["product_code"]] = item
        print(f"  [{slug:12s}] {len(items):>3} items (total unique: {len(all_items):>3})", file=sys.stderr)
        time.sleep(rate_limit)
    
    # 2. Search-based categories (drinks, alcohol)
    print("\nScraping 7-Eleven search results...", file=sys.stderr)
    for our_cat, term_jp in SEJ_SEARCH_TERMS.items():
        emoji = {"drinks": "🥤", "alcohol": "🍺"}.get(our_cat, "📦")
        before = len(all_items)
        items = scrape_sej_search(term_jp, our_cat, emoji, region, rate_limit)
        for item in items:
            all_items[item["product_code"]] = item
        new_count = len(all_items) - before
        print(f"  [{our_cat:12s}] {len(items):>3} from search ({new_count} new, {len(items) - new_count} already in grid)", file=sys.stderr)
    
    return list(all_items.values())


# ─── Main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Konbini product scraper")
    parser.add_argument("--sej", action="store_true", help="Scrape 7-Eleven Japan (default)")
    parser.add_argument("--region", default=DEFAULT_REGION, help=f"Region (default: {DEFAULT_REGION})")
    parser.add_argument("--category", help="Scrape a single category slug only (grid page)")
    parser.add_argument("--search", help="Scrape a single search term only")
    parser.add_argument("--search-cat", default="drinks", help="Category name for --search (default: drinks)")
    parser.add_argument("--slow", action="store_true", help="Slower rate (higher quality, avoid bot detection)")
    args = parser.parse_args()
    
    rate = 0.5 if args.slow else 0.3
    
    all_items = []
    
    if args.category:
        items = scrape_sej_category(args.category, args.region)
        all_items.extend(items)
    elif args.search:
        emoji = {"drinks": "🥤", "alcohol": "🍺"}.get(args.search_cat, "📦")
        items = scrape_sej_search(args.search, args.search_cat, emoji, args.region, rate)
        all_items.extend(items)
    else:
        items = scrape_sej_all(region=args.region, rate_limit=rate)
        all_items.extend(items)
    
    # Output as JSONL
    for item in all_items:
        print(json.dumps(item, ensure_ascii=False))
    
    print(f"\nTotal: {len(all_items)} unique items across {len(set(i['category'] for i in all_items))} categories", file=sys.stderr)


if __name__ == "__main__":
    main()
