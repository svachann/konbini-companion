#!/usr/bin/env python3
"""
Konbini Companion — Japan Convenience Store Item Translator & Guide

A CLI tool that helps travelers decode the overwhelming aisles of Japanese
convenience stores (7-Eleven, Lawson, FamilyMart). Search items by Japanese
or English name, browse by category, get cultural notes, and generate
structured JSON data for other tools.

Usage:
    python konbini-companion.py                    # Interactive menu mode
    python konbini-companion.py --search onigiri   # Search items
    python konbini-companion.py --category snacks  # Browse category
    python konbini-companion.py --random           # Random item
    python konbini-companion.py --list-categories  # List all categories
    python konbini-companion.py --export-json      # Export all data as JSON
    python konbini-companion.py --help             # This help
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime

# ─── Data File ────────────────────────────────────────────────────────────
DATA_FILE = os.path.expanduser("~/.hermes/data/konbini-companion-items.json")


def load_items():
    """Load items from the JSON database file.
    Falls back to generating an empty dataset if the file doesn't exist.
    """
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("items", [])
        except (json.JSONDecodeError, KeyError):
            pass
    print(f"⚠️  Data file not found at {DATA_FILE}", file=sys.stderr)
    print(f"   Run the scraper first or place a valid JSON file there.", file=sys.stderr)
    return []





CATEGORIES = {
    "onigiri": "🍙 Rice Balls (Onigiri)",
    "bento": "🍱 Bento & Meals",
    "hot_foods": "🍗 Hot Foods / Fried",
    "noodles": "🍜 Noodles & Cup Noodles",
    "drinks": "🥤 Drinks (Tea, Coffee, Soda)",
    "alcohol": "🍺 Alcoholic Drinks",
    "snacks": "🍪 Snacks & Chips",
    "desserts": "🍰 Desserts & Sweets",
    "daily_goods": "📦 Daily Goods & Essentials",
    "services": "🏪 Konbini Services",
}

CATEGORY_IDS = list(CATEGORIES.keys())

TIER_ORDER = {"★★★": 0, "★★": 1, "★": 2}

# Store names and their distinctive facts
STORES = {
    "7-Eleven": {"color": "🟢🟢🟢", "nickname": "Seven", "tagline": "Green stripe, red logo. Open 24/7. The OG konbini."},
    "Lawson": {"color": "🔵🔵🔵", "nickname": "Lawson", "tagline": "Blue & white. L-kara fried chicken. Famous for Loppi terminal."},
    "FamilyMart": {"color": "🟢🔵🟢", "nickname": "Famima", "tagline": "Green & blue. Famichiki chicken. Best crepe cakes."},
}


def build_index(items):
    """Build search indices."""
    jp_index = {}
    en_index = {}
    romaji_index = {}
    for item in items:
        for word in item["jp"].replace("(", "").replace(")", "").replace("（", "").replace("）", "").split():
            clean = word.strip("（）()、。").lower()
            jp_index.setdefault(clean, []).append(item["id"])
        for word in item["en"].lower().split():
            en_index.setdefault(word.strip("(),./").lower(), []).append(item["id"])
        for word in item.get("jp_romaji", item["jp"]).lower().split():
            romaji_index.setdefault(word.strip("(),./").lower(), []).append(item["id"])
        # Also index cultural note and category
        if "category" in item:
            en_index.setdefault(item["category"].lower(), []).append(item["id"])
    return {"jp": jp_index, "en": en_index, "romaji": romaji_index}


def search_items(items, query, indices):
    """Search items by Japanese or English keyword."""
    q = query.lower().strip()
    results = {}
    seen = set()

    # Search by exact id
    if q in [i["id"] for i in items]:
        return [i for i in items if i["id"] == q]

    # Search indices
    for lang, index in indices.items():
        for word, ids in index.items():
            if q in word or word in q:
                for iid in ids:
                    if iid not in seen:
                        seen.add(iid)

    # Also search full text fields
    for item in items:
        if item["id"] in seen:
            continue
        for field in ["jp", "en", "jp_romaji", "description", "cultural_note"]:
            if q in item.get(field, "").lower():
                seen.add(item["id"])
                break

    return [i for i in items if i["id"] in seen]


def get_items_by_category(items, category):
    """Filter items by category."""
    return [i for i in items if i["category"] == category]


def get_random_item(items):
    """Return a random item."""
    return random.choice(items)


def format_item(item, index=None):
    """Format a single item for display."""
    lines = []
    lines.append(f"━━━ {item['emoji']} {item['en']} ━━━")
    lines.append(f"   Japanese: {item['jp']}  ({item['jp_romaji']})")
    lines.append(f"   Category: {CATEGORIES.get(item['category'], item['category'])}")
    lines.append(f"   Sub:      {item['subcategory']}")
    lines.append(f"   Price:    {item['price_range']}")
    lines.append(f"   Rating:   {item['tier']}")
    lines.append(f"   Found at: {', '.join(item['common_at'])}")
    lines.append(f"")
    lines.append(f"   {item['description']}")
    lines.append(f"")
    lines.append(f"   💡 {item['cultural_note']}")
    lines.append("")
    return "\n".join(lines)


def json_export(items):
    """Export items as structured JSON."""
    return json.dumps({
        "meta": {
            "name": "Konbini Companion Database",
            "description": "Japan convenience store item translator & guide",
            "version": "1.0.0",
            "generated": datetime.now().isoformat(),
            "total_items": len(items),
            "stores": [
                {"name": k, "nickname": v["nickname"], "tagline": v["tagline"]}
                for k, v in STORES.items()
            ],
        },
        "categories": [
            {
                "id": cid,
                "name": CATEGORIES[cid],
                "item_count": len(get_items_by_category(items, cid)),
            }
            for cid in CATEGORY_IDS
        ],
        "items": items,
    }, ensure_ascii=False, indent=2)


def print_help(items):
    """Print detailed help."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║            🏪 KONBINI COMPANION - Japan Travel Tool         ║
║   Decode Japanese convenience stores like a local           ║
╚══════════════════════════════════════════════════════════════╝

ITEMS DATABASE: {len(items)} items across {len(CATEGORIES)} categories

USAGE:
  python konbini-companion.py                      
      → Interactive menu mode

  python konbini-companion.py --search <keyword>   
      → Search items by name (JP/EN/romaji)
      Example: --search onigiri, --search おにぎり, --search ramen

  python konbini-companion.py --category <cat_id>  
      → Browse all items in a category
      Example: --category drinks, --category snacks

  python konbini-companion.py --random             
      → Discover a random konbini item

  python konbini-companion.py --list-categories    
      → List all available categories

  python konbini-companion.py --export-json [path] 
      → Export full database as JSON

  python konbini-companion.py --store <name>       
      → Show store info and items available there
      Example: --store 7-Eleven

  python konbini-companion.py --stats              
      → Show database statistics

CATEGORIES:
""")
    for cid, cname in CATEGORIES.items():
        count = len(get_items_by_category(items, cid))
        print(f"  {cid:<15} {cname:<25} ({count} items)")
    print("")


def show_stats(items):
    """Print database statistics."""
    print("📊 Konbini Companion - Database Statistics")
    print("━" * 45)
    print(f"  Total items:      {len(items)}")
    print(f"  Categories:       {len(CATEGORIES)}")
    for cid, cname in CATEGORIES.items():
        count = len(get_items_by_category(items, cid))
        print(f"    {cname:<25} {count} items")
    print()
    tier_counts = {"★★★": 0, "★★": 0, "★": 0}
    for item in items:
        t = item["tier"]
        if t in tier_counts:
            tier_counts[t] += 1
    print(f"  ★★★ Must-try:     {tier_counts['★★★']} items")
    print(f"  ★★  Good:         {tier_counts['★★']} items")
    print(f"  ★   Standard:     {tier_counts['★']} items")
    print()
    store_counts = {}
    for item in items:
        for s in item["common_at"]:
            store_counts[s] = store_counts.get(s, 0) + 1
    print("  Items per store:")
    for store, count in sorted(store_counts.items()):
        info = STORES.get(store, {})
        nick = info.get("nickname", "")
        print(f"    {store:<15} {count:>3} items  {info.get('tagline', '')}")


def show_store(items, store_name):
    """Show items available at a given store."""
    store_key = None
    for s in STORES:
        if store_name.lower() in s.lower():
            store_key = s
            break
    if not store_key:
        print(f"Unknown store: {store_name}")
        print(f"Available: {', '.join(STORES.keys())}")
        return
    store = STORES[store_key]
    store_items = [i for i in items if store_key in i["common_at"]]
    print(f"{store['color']} {store_key} ({store['nickname']})")
    print(f"  {store['tagline']}")
    print(f"  Items available: {len(store_items)}")
    # Group by category
    by_cat = {}
    for item in store_items:
        by_cat.setdefault(item["category"], []).append(item)
    for cid in CATEGORY_IDS:
        if cid in by_cat:
            print(f"\n  {CATEGORIES[cid]}:")
            for item in by_cat[cid]:
                print(f"    {item['emoji']} {item['en']:35s} {item['price_range']:>10s}  {item['tier']}")
    print("")


def interactive_mode(items, indices):
    """Interactive menu loop."""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║            🏪 KONBINI COMPANION - Japan Travel Tool         ║")
    print("║   Decode Japanese convenience stores like a local           ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"   {len(items)} items · {len(CATEGORIES)} categories · 3 stores\n")

    while True:
        print("━━━ Menu ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("  1) 🔍 Search items   2) 📂 Browse category")
        print("  3) 🎲 Random pick    4) 📋 List categories")
        print("  5) 🏪 Store browser  6) 📊 Stats")
        print("  7) 💾 Export JSON    8) ❌ Quit")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        choice = input("  Choose (1-8): ").strip()

        if choice == "1":
            q = input("  Search keyword (JP/EN): ").strip()
            if q:
                results = search_items(items, q, indices)
                if results:
                    print(f"\n  Found {len(results)} item(s):\n")
                    for r in results:
                        print(format_item(r))
                        print()
                else:
                    print("  ❌ No results.\n")

        elif choice == "2":
            print("\n  Categories:")
            for i, cid in enumerate(CATEGORY_IDS, 1):
                count = len(get_items_by_category(items, cid))
                print(f"  {i}) {CATEGORIES[cid]} ({count} items)")
            try:
                cat_choice = int(input("\n  Choose category: ").strip())
                if 1 <= cat_choice <= len(CATEGORY_IDS):
                    cid = CATEGORY_IDS[cat_choice - 1]
                    cat_items = get_items_by_category(items, cid)
                    print(f"\n  {CATEGORIES[cid]}\n")
                    for item in cat_items:
                        print(format_item(item))
                        print()
            except ValueError:
                print("  Invalid choice.\n")

        elif choice == "3":
            item = get_random_item(items)
            print("\n" + format_item(item))

        elif choice == "4":
            print("\n  Available categories:\n")
            for cid, cname in CATEGORIES.items():
                count = len(get_items_by_category(items, cid))
                print(f"    {cid:<15} {cname:<30} ({count} items)")

        elif choice == "5":
            print("\n  Available stores:")
            for s in STORES:
                print(f"    {s}")
            store_input = input("\n  Store name: ").strip()
            if store_input:
                show_store(items, store_input)

        elif choice == "6":
            print()
            show_stats(items)

        elif choice == "7":
            path = input("  Export path (default: ./konbini-data.json): ").strip() or "./konbini-data.json"
            data = json_export(items)
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
            real_path = os.path.abspath(path)
            print(f"  ✅ Exported {len(items)} items to {real_path}")

        elif choice == "8":
            print("  👋 Sayonara! Enjoy the konbini adventure!")
            break

        else:
            print("  Invalid choice.\n")


def main():
    # Load items from JSON data file (not hardcoded)
    items = load_items()
    if not items:
        print("❌ No items loaded from database.")
        print(f"   Expected at: {DATA_FILE}")
        print("   Run the scraper first: python konbini-scraper.py")
        return

    parser = argparse.ArgumentParser(
        description="Konbini Companion — Japan Convenience Store Translator & Guide",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument("--search", "-s", type=str, help="Search items by keyword (JP/EN/romaji)")
    parser.add_argument("--category", "-c", type=str, help="Browse items by category")
    parser.add_argument("--random", "-r", action="store_true", help="Show a random item")
    parser.add_argument("--list-categories", "-l", action="store_true", help="List all categories")
    parser.add_argument("--export-json", "-e", type=str, nargs="?", const="auto", help="Export data as JSON (optional path)")
    parser.add_argument("--store", type=str, help="Show items at a specific store")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--help", "-h", action="help", help="Show this help message")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        indices = build_index(items)
        interactive_mode(items, indices)
        return

    indices = build_index(items)

    if args.list_categories:
        print("Available categories:\n")
        for cid, cname in CATEGORIES.items():
            count = len(get_items_by_category(items, cid))
            print(f"  {cid:<15} {cname:<30} ({count} items)")

    elif args.search:
        results = search_items(items, args.search, indices)
        if results:
            print(f"Found {len(results)} item(s) matching '{args.search}':\n")
            for r in results:
                print(format_item(r))
                print()
        else:
            print(f"No items found matching '{args.search}'.")

    elif args.category:
        if args.category in CATEGORIES:
            cat_items = get_items_by_category(items, args.category)
            print(f"{CATEGORIES[args.category]} ({len(cat_items)} items):\n")
            for item in cat_items:
                print(format_item(item))
                print()
        else:
            print(f"Unknown category: '{args.category}'")
            print(f"Available: {', '.join(CATEGORIES.keys())}")

    elif args.random:
        item = get_random_item(items)
        print(format_item(item))

    elif args.export_json:
        data = json_export(items)
        if args.export_json == "auto":
            data_dir = os.path.expanduser("~/.hermes/data")
            os.makedirs(data_dir, exist_ok=True)
            path = os.path.join(data_dir, "konbini-companion-items.json")
        else:
            path = args.export_json
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"✅ Exported {len(items)} items to {os.path.abspath(path)}")

    elif args.store:
        show_store(items, args.store)

    elif args.stats:
        show_stats(items)


if __name__ == "__main__":
    main()
