#!/usr/bin/env python3
"""Konbini Companion — data sync script.

Runs the scraper, identifies new items, and updates the database.
Outputs structured JSON to stdout for consumption by the cron agent.

Output format (to stdout):
  {
    "action": "sync",
    "timestamp": "...",
    "stats": { "total_scraped": 246, "new_items": 5, "prices_updated": 12 },
    "new_items": [ { "product_code": "...", "jp": "...", "price_yen": 198, ... } ],
    "price_changes": [ { "product_code": "...", "old_price": 180, "new_price": 198 } ]
  }
"""

import json
import os
import sys
from datetime import datetime

# Import the scraper module
SCRIPTS_DIR = os.path.expanduser("~/.hermes/scripts")
sys.path.insert(0, SCRIPTS_DIR)
import importlib
scraper = importlib.import_module("konbini-scraper")
scrape_sej_all = scraper.scrape_sej_all
SEJ_CATEGORY_MAP = scraper.SEJ_CATEGORY_MAP

DATA_FILE = os.path.expanduser("~/.hermes/data/konbini-companion-items.json")


def load_existing_data():
    """Load current database, return dict of items keyed by product_code."""
    if not os.path.exists(DATA_FILE):
        return {}, []
    
    with open(DATA_FILE) as f:
        data = json.load(f)
    
    items_by_code = {}
    existing_items = []
    
    for item in data.get("items", []):
        # Items with product_code are from scraping
        if item.get("product_code"):
            items_by_code[item["product_code"]] = item
        existing_items.append(item)
    
    return items_by_code, existing_items


def get_category_items_from_scraper():
    """Run scraper and return dict of items keyed by product_code."""
    scraped_items = scrape_sej_all()
    return {item["product_code"]: item for item in scraped_items}


def compute_diff(scraped, existing):
    """Compare scraped data with existing, return new items and price changes."""
    new_items = []
    price_changes = []
    
    for code, s_item in scraped.items():
        if code not in existing:
            new_items.append(s_item)
        else:
            e_item = existing[code]
            old_price = e_item.get("price_yen", 0)
            new_price = s_item.get("price_yen", 0)
            if old_price and new_price and old_price != new_price:
                price_changes.append({
                    "product_code": code,
                    "jp": s_item.get("jp", ""),
                    "old_price": old_price,
                    "new_price": new_price,
                })
    
    return new_items, price_changes


def main():
    print("Loading existing data...", file=sys.stderr)
    items_by_code, existing_items = load_existing_data()
    print(f"  {len(items_by_code)} items with product codes in database", file=sys.stderr)
    
    print("Running scraper...", file=sys.stderr)
    scraped = get_category_items_from_scraper()
    print(f"  {len(scraped)} items scraped from 7-Eleven", file=sys.stderr)
    
    new_items, price_changes = compute_diff(scraped, items_by_code)
    
    result = {
        "action": "sync",
        "timestamp": datetime.now().isoformat(),
        "stats": {
            "total_scraped": len(scraped),
            "existing_matched": len(scraped) - len(new_items),
            "new_items": len(new_items),
            "prices_updated": len(price_changes),
        },
        "new_items": new_items[:10],  # Keep context manageable
        "price_changes": price_changes[:10],
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Save compact summary for cron efficiency
    diff_path = os.path.expanduser("~/.hermes/data/konbini-sync-last.json")
    compact = {
        "timestamp": result["timestamp"],
        "stats": result["stats"],
        "new_items_count": len(new_items),
        "prices_updated_count": len(price_changes),
        "has_changes": len(new_items) > 0 or len(price_changes) > 0,
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
