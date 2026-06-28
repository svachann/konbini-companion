# Konbini Companion 🏪

Decode Japanese convenience stores like a local.

Search, browse, and translate items across 10 categories from Japan's major konbini chains (7-Eleven, Lawson, FamilyMart). Perfect companion for any Japan trip.

## Features

- 🔍 **Search** items by Japanese or English name
- 📂 **Browse** 10 categories (onigiri, bento, drinks, snacks, etc.)
- 🎲 **Random pick** for spontaneous discoveries
- 🏪 **Store browser** — see what's available at each chain
- 💡 **Cultural notes** — understand what you're buying
- 💾 **JSON export** for data pipelines
- 🔄 **Auto-synced weekly** — prices and items updated from 7-Eleven Japan

## Quick Start

```bash
# Requires Python 3.10+
python konbini-companion.py --help

# Search for something
python konbini-companion.py --search ramen

# Browse a category
python konbini-companion.py --category alcohol

# Random discovery
python konbini-companion.py --random
```

## Categories

The database covers 10 categories across all major konbini chains. Item counts update automatically every week from live 7-Eleven Japan product data.

| Category | Must-Try Picks |
|----------|----------------|
| 🍙 Onigiri | Salmon, Tuna Mayo, Mentaiko |
| 🍱 Bento & Meals | Oyako-don, Katsudon, Curry |
| 🍗 Hot Foods / Fried | Karaage, Nikuman, Famichiki |
| 🍜 Noodles & Cup Noodles | Cup Noodle, Ippudo, Yakisoba |
| 🥤 Drinks | Green Tea, BOSS Coffee, Matcha Latte |
| 🍺 Alcohol | Strong Zero, Lemon Chu-Hi, Umeshu |
| 🍪 Snacks | Kaki no Tane, Jagariko, Pocky |
| 🍰 Desserts & Sweets | Pudding, Mochi Ice Cream, Dorayaki |
| 📦 Daily Goods & Essentials | Umbrella, SIM Card, Toothbrush |
| 🏪 Konbini Services | ATM, Shipping, Ticket Pickup |

## How the Data Stays Fresh

The item database is **auto-synced weekly** (Mondays 6AM) from 7-Eleven Japan's official product pages:

1. **`konbini-scraper.py`** — scrapes 246+ live products from sej.co.jp. Gets Japanese names, prices, regions, and launch dates. 7-Eleven's product pages are server-rendered HTML (no JS needed), so this is reliable and fast.

2. **`konbini-sync.py`** — compares scraped data against the existing database, identifies new items and price changes, outputs a compact diff.

3. **Weekly enrichment** — the scraper output is fed to an LLM which translates Japanese names to English, generates descriptions, assigns tier ratings (★★★ must-try / ★★ good / ★ standard), and adds cultural notes. New items get merged into the database; existing items get price updates.

4. **Auto-push** — changes are automatically committed and pushed to this repo.

## Project Structure

```
├── konbini-companion.py      # CLI tool — loads data from JSON, search/browse/explore
├── konbini-scraper.py        # 7-Eleven product scraper
├── konbini-sync.py           # Diff + merge pipeline
├── data/
│   └── konbini-companion-items.json   # Item database (auto-updated weekly)
└── .gitignore
```

## Data

The database file at `data/konbini-companion-items.json` contains all items with:
- Japanese and English names
- Romaji readings
- Price ranges
- Tier ratings
- Cultural notes
- Store availability
- Source URLs and product codes (for scraped items)

## License

MIT
