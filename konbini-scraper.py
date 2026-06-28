#!/usr/bin/env python3
"""Konbini product scraper — fetches live item data from Japanese convenience store websites.

Currently scrapes:
  - 7-Eleven Japan (sej.co.jp): server-rendered HTML, all categories
  - Lawson (lawson.co.jp): best-effort
  - FamilyMart (family.co.jp): best-effort

Outputs a JSON array of scraped items to stdout, one per line (JSONL format).
Run with --all to scrape every source.
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

# ─── 7-Eleven ─────────────────────────────────────────────────────────────

# Category mapping: 7-Eleven category slugs → our konbini categories
SEJ_CATEGORY_MAP = {
    "onigiri": "onigiri",
    "bento": "bento",
    "sushi": "bento",
    "sandwich": "bento",
    "men": "noodles",
    "hotsnack": "hot_foods",
    "sweets": "desserts",
    "ice_cream": "desserts",
    "bread": "snacks",
    "donut": "desserts",
    "chukaman": "hot_foods",
    "oden": "hot_foods",
    "salad": "daily_goods",
    "dailydish": "bento",
    "pasta": "noodles",
    "gratin": "bento",
    "frozen_foods": "daily_goods",
}

SEJ_EMOJI_MAP = {
    "onigiri": "🍙",
    "bento": "🍱",
    "hot_foods": "🍗",
    "noodles": "🍜",
    "drinks": "🥤",
    "alcohol": "🍺",
    "snacks": "🍪",
    "desserts": "🍰",
    "daily_goods": "📦",
    "services": "🏪",
}

# Categories to skip (not food/travel relevant)
SEJ_SKIP_CATEGORIES = {"7premium", "sevencafe"}

# Regions to scrape (kanto has the most products)
DEFAULT_REGION = "kanto"


def fetch_url(url, retries=2):
    """Fetch a URL with retry logic."""
    for attempt in range(retries + 1):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except (HTTPError, URLError, OSError) as e:
            if attempt < retries:
                time.sleep(1)
                continue
            return None


def parse_list_inner_blocks(html):
    """Parse product listing blocks from a category page.
    
    Returns list of dicts with product_code and raw HTML for each item.
    """
    items = []
    # Each product is in a div with class "list_inner" plus "-item-code-XXXXXX"
    pattern = r'<div class="list_inner[^"]*-item-code-(\d+)[^"]*">(.*?)</div>\s*<!-- list_inner -->'
    for match in re.finditer(pattern, html, re.DOTALL):
        code = match.group(1)
        block = match.group(2)
        items.append({"product_code": code, "html": block})
    return items


def scrape_sej_category(category_slug, region=DEFAULT_REGION):
    """Scrape a single 7-Eleven category page and return parsed items."""
    url = f"https://www.sej.co.jp/products/a/{category_slug}/{region}/"
    html = fetch_url(url)
    if not html:
        return []
    
    items = parse_list_inner_blocks(html)
    results = []
    
    for item in items:
        code = item["product_code"]
        block = item["html"]
        
        # Extract name
        name_match = re.search(
            r'class="item_ttl"[^>]*>.*?<p><a[^>]*>(.*?)</a></p>',
            block, re.DOTALL
        )
        name_jp = name_match.group(1).strip() if name_match else ""
        
        # Extract price
        price_match = re.search(
            r'class="item_price"[^>]*>.*?<p>\s*(\d+)[^\d]*',
            block, re.DOTALL
        )
        price_yen = int(price_match.group(1)) if price_match else 0
        
        # Extract region info
        region_match = re.search(
            r'class="item_region"[^>]*>.*?<p>(?:<span>[^<]*</span>)?\s*(.*?)</p>',
            block, re.DOTALL
        )
        regions = region_match.group(1).strip() if region_match else ""
        
        # Extract launch date
        launch_match = re.search(
            r'class="item_launch"[^>]*>.*?<p>(.*?)</p>',
            block, re.DOTALL
        )
        launch_date = launch_match.group(1).strip() if launch_match else ""
        
        # Extract image URL
        img_match = re.search(
            r'<img[^>]*data-original="([^"]+)"',
            block, re.DOTALL
        )
        img_url = img_match.group(1) if img_match else ""
        
        # Map to our category
        our_cat = SEJ_CATEGORY_MAP.get(category_slug, "daily_goods")
        
        results.append({
            "source": "7-Eleven",
            "source_url": f"https://www.sej.co.jp/products/a/item/{code}/{region}/",
            "product_code": code,
            "jp": name_jp,
            "price_yen": price_yen,
            "category_slug": category_slug,
            "category": our_cat,
            "emoji": SEJ_EMOJI_MAP.get(our_cat, "📦"),
            "regions": regions,
            "launch_date": launch_date,
            "image_url": img_url,
        })
    
    return results


def scrape_sej_item_detail(product_code, region=DEFAULT_REGION):
    """Scrape a single 7-Eleven item detail page for additional info (description, etc.)"""
    url = f"https://www.sej.co.jp/products/a/item/{product_code}/{region}/"
    html = fetch_url(url)
    if not html:
        return {}
    
    detail = {}
    
    # Description
    desc_match = re.search(
        r'class="item_text"[^>]*>.*?<p>(.*?)</p>',
        html, re.DOTALL
    )
    if desc_match:
        detail["description_jp"] = desc_match.group(1).strip()
    
    # Price (with tax)
    price_match = re.search(
        r'class="item_price"[^>]*>.*?<p>\s*(\d+)円（税込[\d,.]+円）',
        html, re.DOTALL
    )
    if price_match:
        detail["price_yen"] = int(price_match.group(1))
    
    # Full-size image URL
    img_match = re.search(
        r'<li><img\s+src="([^"]+)"',
        html, re.DOTALL
    )
    if img_match:
        detail["image_url"] = img_match.group(1)
    
    return detail


def scrape_sej_all(region=DEFAULT_REGION, include_details=False, rate_limit=0.5):
    """Scrape all 7-Eleven categories."""
    all_items = []
    cat_list = [c for c in SEJ_CATEGORY_MAP if c not in SEJ_SKIP_CATEGORIES]
    cat_list = sorted(set(cat_list))
    
    for slug in cat_list:
        items = scrape_sej_category(slug, region)
        print(f"  [{slug}] {len(items)} items", file=sys.stderr)
        
        if include_details:
            for item in items:
                detail = scrape_sej_item_detail(item["product_code"], region)
                item.update(detail)
                time.sleep(rate_limit)
        
        all_items.extend(items)
    
    return all_items


# ─── Lawson (best-effort) ──────────────────────────────────────────────

def scrape_lawson():
    """Scrape Lawson product listings (JS-heavy, limited data)."""
    url = "https://www.lawson.co.jp/recommend/original/"
    html = fetch_url(url)
    if not html:
        return []
    # Lawson uses JS rendering — limited data from raw HTML
    # Try to find product links in the static content
    results = []
    pattern = r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*item[^"]*"[^>]*>'
    for match in re.finditer(pattern, html):
        href = match.group(1)
        if "/product/" in href or "/recommend/" in href:
            full_url = "https://www.lawson.co.jp" + href if href.startswith("/") else href
            results.append({"source": "Lawson", "source_url": full_url})
    return results


# ─── FamilyMart (best-effort) ──────────────────────────────────────────

def scrape_familymart():
    """Scrape FamilyMart product listings (AEM-based, limited data from raw HTML)."""
    url = "https://www.family.co.jp/goods/"
    html = fetch_url(url)
    if not html:
        return []
    # FamilyMart uses Adobe AEM with JS rendering
    # Try to find static product data
    results = []
    # Check for any embedded JSON-LD or product data
    jsonld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
    for match in re.finditer(jsonld_pattern, html, re.DOTALL):
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict) and data.get("@type") == "Product":
                results.append({
                    "source": "FamilyMart",
                    "jp": data.get("name", ""),
                })
        except json.JSONDecodeError:
            pass
    return results


# ─── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Konbini product scraper")
    parser.add_argument("--all", action="store_true", help="Scrape all sources")
    parser.add_argument("--sej", action="store_true", help="Scrape 7-Eleven Japan")
    parser.add_argument("--lawson", action="store_true", help="Scrape Lawson")
    parser.add_argument("--familymart", action="store_true", help="Scrape FamilyMart")
    parser.add_argument("--details", action="store_true", help="Fetch item detail pages (slower)")
    parser.add_argument("--region", default=DEFAULT_REGION, help=f"7-Eleven region (default: {DEFAULT_REGION})")
    parser.add_argument("--category", help="Scrape a single 7-Eleven category slug only")
    args = parser.parse_args()
    
    # Default: scrape everything
    do_all = args.all or not (args.sej or args.lawson or args.familymart or args.category)
    
    all_items = []
    
    if (do_all or args.sej) or args.category:
        print("Scraping 7-Eleven Japan...", file=sys.stderr)
        if args.category:
            items = scrape_sej_category(args.category, args.region)
            if args.details:
                for item in items:
                    detail = scrape_sej_item_detail(item["product_code"], args.region)
                    item.update(detail)
                    time.sleep(0.3)
            all_items.extend(items)
        else:
            items = scrape_sej_all(region=args.region, include_details=args.details)
            all_items.extend(items)
    
    if do_all or args.lawson:
        print("Scraping Lawson...", file=sys.stderr)
        items = scrape_lawson()
        all_items.extend(items)
    
    if do_all or args.familymart:
        print("Scraping FamilyMart...", file=sys.stderr)
        items = scrape_familymart()
        all_items.extend(items)
    
    # Output as JSON lines (one item per line for streaming)
    for item in all_items:
        print(json.dumps(item, ensure_ascii=False))
    
    print(f"\nTotal: {len(all_items)} items", file=sys.stderr)


if __name__ == "__main__":
    main()
