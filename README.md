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
- 🔄 **Auto-synced** — weekly scraper keeps items & prices fresh from 7-Eleven Japan

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

| Category | Items | Must-Try |
|----------|-------|----------|
| 🍙 Onigiri | 6 | Salmon, Tuna Mayo, Mentaiko |
| 🍱 Bento | 6 | Oyako-don, Katsudon, Curry |
| 🍗 Hot Foods | 4 | Karaage, Nikuman |
| 🍜 Noodles | 4 | Cup Noodle, Ippudo |
| 🥤 Drinks | 7 | Green Tea, BOSS Coffee, Matcha Latte |
| 🍺 Alcohol | 5 | Strong Zero, Lemon Chu-Hi, Umeshu |
| 🍪 Snacks | 7 | Kaki no Tane, Jagariko, Pocky |
| 🍰 Desserts | 6 | Pudding, Mochi Ice Cream, Dorayaki |
| 📦 Daily Goods | 7 | Umbrella, SIM Card, Toothbrush |
| 🏪 Services | 5 | ATM, Shipping, Ticket Pickup |

## How the Data Stays Fresh

The item database is **auto-synced weekly** from 7-Eleven Japan's official product pages:

1. **`konbini-scraper.py`** — scrapes 246+ live items from sej.co.jp across 17 categories
2. **`konbini-sync.py`** — compares scraped data with the existing database, identifies new items and price changes
3. **Weekly cron job** (Mondays 6AM) — runs the sync pipeline via LLM to translate Japanese names, generate descriptions, and update prices
4. Results are automatically pushed to this repo

No manual data entry needed — new products and price changes are picked up automatically every week.

## Data

The tool exports to `~/.hermes/data/konbini-companion-items.json` with full structured data including all items, categories, store availability, and metadata.

## Project Structure

```
├── konbini-companion.py      # CLI tool — search, browse, explore
├── konbini-scraper.py        # 7-Eleven product scraper
├── konbini-sync.py           # Diff + merge pipeline
├── data/
│   └── konbini-companion-items.json   # Item database
└── .github/workflows/        # (future) manual sync trigger
```

## License

MIT
