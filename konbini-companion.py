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

# ─── Konbini Item Database ────────────────────────────────────────────────
# Tiers: ★★★ = must-try, ★★ = good, ★ = standard
ITEMS = [
    # ── Onigiri (Rice Balls) ──
    {
        "id": "onigiri-salmon",
        "jp": "鮭おにぎり",
        "jp_romaji": "sake onigiri",
        "en": "Salmon Rice Ball",
        "category": "onigiri",
        "subcategory": "filled",
        "price_range": "¥100-180",
        "emoji": "🍙",
        "tier": "★★★",
        "description": "Grilled salmon flakes wrapped in seasoned rice with nori seaweed. The classic choice.",
        "cultural_note": "Onigiri is the original Japanese fast food. The nori seaweed wrapper is usually separated from the rice by a plastic layer — peel it off just before eating to keep it crispy.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "onigiri-tuna-mayo",
        "jp": "ツナマヨおにぎり",
        "jp_romaji": "tsuna mayo onigiri",
        "en": "Tuna Mayo Rice Ball",
        "category": "onigiri",
        "subcategory": "filled",
        "price_range": "¥100-180",
        "emoji": "🍙",
        "tier": "★★★",
        "description": "Canned tuna mixed with Japanese mayonnaise wrapped in rice. Comfort food perfection.",
        "cultural_note": "Japan's mayo (Kewpie) is richer and tangier than Western mayo — made with egg yolks only, no whites. This combo is a national obsession.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "onigiri-ume",
        "jp": "梅おにぎり",
        "jp_romaji": "ume onigiri",
        "en": "Pickled Plum Rice Ball",
        "category": "onigiri",
        "subcategory": "filled",
        "price_range": "¥100-180",
        "emoji": "🍙",
        "tier": "★★",
        "description": "Sour-salty pickled plum (umeboshi) center. Polarizing — you either love it or hate it.",
        "cultural_note": "Umeboshi is a traditional preservative — samurai would carry it in battle. The extreme sourness is an acquired taste but aids digestion.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "onigiri-kombu",
        "jp": "昆布おにぎり",
        "jp_romaji": "kombu onigiri",
        "en": "Seaweed Simmered Rice Ball",
        "category": "onigiri",
        "subcategory": "filled",
        "price_range": "¥100-180",
        "emoji": "🍙",
        "tier": "★★",
        "description": "Simmered kelp in sweet soy sauce. Umami bomb, less common outside Japan.",
        "cultural_note": "Kombu is a foundational ingredient in dashi (Japanese soup stock). Eating it directly like this shows how deeply umami runs in the cuisine.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "onigiri-mentaiko",
        "jp": "明太子おにぎり",
        "jp_romaji": "mentaiko onigiri",
        "en": "Spicy Cod Roe Rice Ball",
        "category": "onigiri",
        "subcategory": "filled",
        "price_range": "¥120-200",
        "emoji": "🍙",
        "tier": "★★★",
        "description": "Spicy seasoned cod roe — bright orange, slightly spicy, intensely savory.",
        "cultural_note": "Mentaiko is a Fukuoka specialty. The \"spicy\" level is mild by international standards — more of a pleasant tingle.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "onigiri-ebi-mayo",
        "jp": "えびマヨおにぎり",
        "jp_romaji": "ebi mayo onigiri",
        "en": "Shrimp Mayo Rice Ball",
        "category": "onigiri",
        "subcategory": "filled",
        "price_range": "¥120-200",
        "emoji": "🍙",
        "tier": "★★★",
        "description": "Small shrimp with mayo. Sweet, creamy, and satisfying — a konbini classic.",
        "cultural_note": "7-Eleven's version is particularly beloved. Limited editions (sakura shrimp, garlic shrimp) appear seasonally.",
        "common_at": ["7-Eleven", "Lawson"]
    },

    # ── Bento / Meals ──
    {
        "id": "bento-oyako",
        "jp": "親子丼",
        "jp_romaji": "oyakodon",
        "en": "Chicken & Egg Rice Bowl",
        "category": "bento",
        "subcategory": "rice bowls",
        "price_range": "¥350-550",
        "emoji": "🍚",
        "tier": "★★★",
        "description": "Chicken and egg simmered in sweet soy broth over rice. 'Parent and child' (chicken + egg).",
        "cultural_note": "The name is a pun — both the chicken (parent) and egg (child) are in the dish. Don't overthink it, just enjoy.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "bento-katsu",
        "jp": "カツ丼",
        "jp_romaji": "katsudon",
        "en": "Pork Cutlet Rice Bowl",
        "category": "bento",
        "subcategory": "rice bowls",
        "price_range": "¥400-600",
        "emoji": "🍚",
        "tier": "★★★",
        "description": "Breaded deep-fried pork cutlet with egg and onion sauce over rice. Students eat this before exams for luck.",
        "cultural_note": "Katsu sounds like 'winning' (勝つ) — eating katsudon before a test or competition is a tradition. 'Katsu!' is also a common cheer.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "bento-pasta",
        "jp": "パスタ",
        "jp_romaji": "pasuta",
        "en": "Japanese Pasta (Various)",
        "category": "bento",
        "subcategory": "pasta",
        "price_range": "¥300-500",
        "emoji": "🍝",
        "tier": "★★",
        "description": "Japanese-style pasta — often with mentaiko (cod roe) cream sauce, or Japanese-style meat sauce (napolitan).",
        "cultural_note": "Japanese 'napolitan' pasta is a retro Western dish with ketchup-based sauce, sausage, and veggies. Very昭和 (Showa-era) comfort food.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "bento-curry",
        "jp": "カレーライス",
        "jp_romaji": "kare raisu",
        "en": "Curry Rice",
        "category": "bento",
        "subcategory": "curry",
        "price_range": "¥350-550",
        "emoji": "🍛",
        "tier": "★★★",
        "description": "Thick Japanese curry roux with beef/chicken and vegetables over rice. Japanese soul food.",
        "cultural_note": "Japanese curry is a 'Western' dish — introduced by the British Navy in the Meiji era. It's thicker, sweeter, and milder than Indian curry. The JMSDF still serves curry every Friday.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "bento-yakiniku",
        "jp": "焼肉弁当",
        "jp_romaji": "yakiniku bento",
        "en": "Grilled Meat Bento",
        "category": "bento",
        "subcategory": "meat",
        "price_range": "¥400-600",
        "emoji": "🥩",
        "tier": "★★★",
        "description": "Grilled beef or pork with sweet soy glaze, served with rice and pickled veggies.",
        "cultural_note": "Yakiniku ('grilled meat') is Korean-influenced Japanese BBQ. The sweet-tangy tare sauce is the key — each konbini chain has its own recipe.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "bento-sushi",
        "jp": "お寿司",
        "jp_romaji": "osushi",
        "en": "Pre-made Sushi / Sashimi Pack",
        "category": "bento",
        "subcategory": "sushi",
        "price_range": "¥300-700",
        "emoji": "🍣",
        "tier": "★★★",
        "description": "Fresh sushi rolls or sashimi platters. Surprisingly good quality for konbini food.",
        "cultural_note": "Conbini sushi is a marvel of supply chain logistics — it's made fresh daily and often discounted (半額, hangaku) after 7 PM. Not Japan's best sushi, but better than most 'sushi' abroad.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },

    # ── Fried / Hot Foods ──
    {
        "id": "karaage",
        "jp": "唐揚げ",
        "jp_romaji": "karaage",
        "en": "Japanese Fried Chicken",
        "category": "hot_foods",
        "subcategory": "fried",
        "price_range": "¥150-300",
        "emoji": "🍗",
        "tier": "★★★",
        "description": "Marinated bite-sized chicken, double-fried for maximum crispiness. Famima's is legendary.",
        "cultural_note": "Lawson's 'L-kara' (Lチキ) and FamilyMart's 'Famichiki' (ファミチキ) have cult followings. Each chain guards their recipe like a state secret. The pre-battered frozen ones you buy are just the beginning — they're fried fresh in-store.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "nikuman",
        "jp": "肉まん",
        "jp_romaji": "nikuman",
        "en": "Steamed Pork Bun",
        "category": "hot_foods",
        "subcategory": "steamed",
        "price_range": "¥100-200",
        "emoji": "🥟",
        "tier": "★★★",
        "description": "Fluffy steamed bun filled with savory pork. The quintessential winter konbini snack.",
        "cultural_note": "The steamers sit by the register in cold months. Variations include pizza-man, curry-man, and sweet an-man (red bean). Ask for 'nikuman hitotsu kudasai' (肉まん一つください).",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "korokke",
        "jp": "コロッケ",
        "jp_romaji": "korokke",
        "en": "Croquette",
        "category": "hot_foods",
        "subcategory": "fried",
        "price_range": "¥80-150",
        "emoji": "🥔",
        "tier": "★★",
        "description": "Potato and meat cream croquette, breaded and deep-fried. Crispy outside, creamy inside.",
        "cultural_note": "Korokke is a yoshoku (Western-style) dish from the Meiji era — adapted from French croquettes. Cream corn korokke is a beloved seasonal variant.",
        "common_at": ["7-Eleven", "Lawson"]
    },
    {
        "id": "hot-dog",
        "jp": "ホットドッグ",
        "jp_romaji": "hotto doggu",
        "en": "Hot Dog",
        "category": "hot_foods",
        "subcategory": "grilled",
        "price_range": "¥100-200",
        "emoji": "🌭",
        "tier": "★★",
        "description": "Self-serve hot dog with squirty ketchup and mustard. Pure nostalgia.",
        "cultural_note": "7-Eleven's hot dogs are a beloved snack — the bun is steamed soft and fluffy, not toasted. A relic of 80s Japan's fascination with American culture.",
        "common_at": ["7-Eleven", "FamilyMart"]
    },

    # ── Noodles ──
    {
        "id": "cup-noodle-standard",
        "jp": "カップヌードル",
        "jp_romaji": "kappu nudoru",
        "en": "Cup Noodle (Original)",
        "category": "noodles",
        "subcategory": "instant",
        "price_range": "¥180-250",
        "emoji": "🍜",
        "tier": "★★★",
        "description": "Nissin Cup Noodle — the OG. Shrimp, egg, pork in soy broth. A cultural icon.",
        "cultural_note": "Invented by Momofuku Ando in 1971. Japan has hundreds of regional and limited-edition flavors. The foil lid isn't just sealing — it's a cooking timer (3 min). Just add hot water from the store's dispenser.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "cup-noodle-seafood",
        "jp": "シーフードヌードル",
        "jp_romaji": "shiifuudo nudoru",
        "en": "Cup Noodle (Seafood)",
        "category": "noodles",
        "subcategory": "instant",
        "price_range": "¥180-250",
        "emoji": "🍜",
        "tier": "★★★",
        "description": "Creamy seafood broth with crab, scallop, and squid bits. Many say it's the best Cup Noodle flavor.",
        "cultural_note": "Seafood flavor is Japan-exclusive and has a devoted following. The 'real crab' bits are tiny but the flavor is unmistakable.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "ippudo-ramen",
        "jp": "一風堂カップ麺",
        "jp_romaji": "ippuudo kappumen",
        "en": "Ippudo Tonkotsu Ramen Cup",
        "category": "noodles",
        "subcategory": "premium instant",
        "price_range": "¥250-350",
        "emoji": "🍜",
        "tier": "★★★",
        "description": "Premium tonkotsu (pork bone broth) ramen from famous Ippudo brand. Restaurant quality at home.",
        "cultural_note": "Premium cup ramen (¥300+) is a whole different experience — real soup base, better noodles, generous toppings. Look for brands like Ippudo, Afuri, or Nakiryu.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "yakisoba",
        "jp": "焼きそば",
        "jp_romaji": "yakisoba",
        "en": "Pan-Fried Noodles (Bowl)",
        "category": "noodles",
        "subcategory": "instant",
        "price_range": "¥150-250",
        "emoji": "🍝",
        "tier": "★★",
        "description": "Thick stir-fried noodles with Worcestershire-style sauce. Add the included sachets of aonori (seaweed) and benishoga (pickled ginger).",
        "cultural_note": "Not actually soba — yakisoba uses wheat-flour noodles (chuuka-men). The brown sauce is a thick, tangy Worcestershire variant unique to Japan.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },

    # ── Drinks: Tea & Coffee ──
    {
        "id": "green-tea-bottle",
        "jp": "緑茶 (ペットボトル)",
        "jp_romaji": "ryokucha",
        "en": "Bottled Green Tea (Unsweetened)",
        "category": "drinks",
        "subcategory": "tea",
        "price_range": "¥100-160",
        "emoji": "🍵",
        "tier": "★★★",
        "description": "Authentic Japanese green tea in a bottle, no sugar. Ito En Oi Ocha is the gold standard.",
        "cultural_note": "Japan drinks more green tea from plastic bottles than brewed at home. Ito En's Oi Ocha (伊藤園 お〜いお茶) is the #1 brand. Unlike 'green tea' abroad, this is unsweetened — real tea flavor.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "mugicha",
        "jp": "麦茶",
        "jp_romaji": "mugicha",
        "en": "Roasted Barley Tea",
        "category": "drinks",
        "subcategory": "tea",
        "price_range": "¥90-150",
        "emoji": "🫖",
        "tier": "★★",
        "description": "Toasty, nutty, caffeine-free roasted barley tea. Perfect in summer. Usually served cold.",
        "cultural_note": "The default summer drink in Japanese homes — many fridges always have a pitcher. It's caffeine-free so kids drink it too. The roasted aroma is pure summer nostalgia for Japanese people.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "boss-coffee",
        "jp": "BOSSコーヒー",
        "jp_romaji": "BOSS koohii",
        "en": "BOSS Canned Coffee",
        "category": "drinks",
        "subcategory": "coffee",
        "price_range": "¥100-180",
        "emoji": "☕",
        "tier": "★★★",
        "description": "Suntory's iconic canned coffee — available hot (from vending machine) or cold. Milk, black, or micro-sugar variants.",
        "cultural_note": "BOSS is Japan's #1 canned coffee. The famous ad campaign featured Tommy Lee Jones as 'Alien BOSS'. Hot cans are a winter staple from heated vending machines — press the red button for hot, blue for cold.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "georgia-coffee",
        "jp": "GEORGIAコーヒー",
        "jp_romaji": "GEORGIA koohii",
        "en": "Georgia Canned Coffee (Coca-Cola)",
        "category": "drinks",
        "subcategory": "coffee",
        "price_range": "¥100-170",
        "emoji": "☕",
        "tier": "★★★",
        "description": "Coca-Cola Japan's premium coffee brand. The 'Georgia Max' series is notably good.",
        "cultural_note": "Japan's canned coffee market is fiercely competitive (BOSS vs Georgia vs Fire vs Roots). Each has 10+ variants. 'Black' (unsweetened) is the health-conscious choice.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "calpis",
        "jp": "カルピス",
        "jp_romaji": "karupisu",
        "en": "Calpis (Calpico) Drink",
        "category": "drinks",
        "subcategory": "soft drinks",
        "price_range": "¥100-160",
        "emoji": "🥛",
        "tier": "★★",
        "description": "Milky, slightly tart yogurt-based soft drink. An iconic Japanese taste since 1919.",
        "cultural_note": "The name sounds like 'cow piss' to English ears, hence the 'Calpico' branding abroad. It's actually from 'calcium' + 'sap' (sanskrit for taste). Dilute concentrate 3:1 with water (or milk for 'Calpis Soda').",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "ramune",
        "jp": "ラムネ",
        "jp_romaji": "ramune",
        "en": "Ramune Soda",
        "category": "drinks",
        "subcategory": "soda",
        "price_range": "¥120-180",
        "emoji": "🥤",
        "tier": "★★",
        "description": "Japanese lemon-lime soda in a Codd-neck bottle with a marble. The summer festival drink.",
        "cultural_note": "The marble stopper is a gimmick — you push it down into the bottle to open. Don't lose the plastic ring! Try original or yuzu flavor. Not usually at konbini but at festivals (matsuri) and souvenir shops. In konbini, buy the plastic bottle version.",
        "common_at": ["7-Eleven", "Lawson"]
    },
    {
        "id": "matcha-latte",
        "jp": "抹茶ラテ",
        "jp_romaji": "matcha rate",
        "en": "Matcha Latte (Bottled)",
        "category": "drinks",
        "subcategory": "specialty",
        "price_range": "¥120-200",
        "emoji": "🟢",
        "tier": "★★★",
        "description": "Creamy sweet matcha and milk blend. The canned/bottle versions from konbini are surprisingly good.",
        "cultural_note": "Matcha lattes became a global phenomenon, but in Japan they're a konbini staple. Brands like Kirin's 'Gogo no Koucha' and Suntory's 'Iyemon' make excellent versions.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },

    # ── Alcoholic Drinks ──
    {
        "id": "strong-zero",
        "jp": "ストロングゼロ",
        "jp_romaji": "sutorongu zero",
        "en": "Strong Zero (Chu-Hi)",
        "category": "alcohol",
        "subcategory": "chuhai",
        "price_range": "¥150-250",
        "emoji": "🥫",
        "tier": "★★★",
        "description": "9% ABV canned citrus cocktail. The legendary drink that sneaks up on you. Double Lemon is the classic.",
        "cultural_note": "Strong Zero is a rite of passage. At 9% ABV (double a typical beer) in a tall can, it's dangerously smooth. The 'zero' means zero sugar, not zero alcohol. Popularized by street drinkers in Shibuya and park gatherings. Respect the can — it's stronger than it tastes.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "chuhai-lemon",
        "jp": "レモンチューハイ",
        "jp_romaji": "remon chuuhai",
        "en": "Lemon Chu-Hi (Standard)",
        "category": "alcohol",
        "subcategory": "chuhai",
        "price_range": "¥150-250",
        "emoji": "🍋",
        "tier": "★★★",
        "description": "Lemon-flavored shochu highball. Refreshing, lower alcohol (3-5%), perfect with food.",
        "cultural_note": "Chu-Hi = shochu + highball. The standard lemon flavor is the baseline — every izakaya has their own take. Konbini versions by Kirin and Suntory are excellent.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "sapporo-beer",
        "jp": "サッポロビール",
        "jp_romaji": "sapporo biiru",
        "en": "Sapporo Premium Beer (Can)",
        "category": "alcohol",
        "subcategory": "beer",
        "price_range": "¥200-300",
        "emoji": "🍺",
        "tier": "★★★",
        "description": "Japan's oldest beer brand (1876). Crisp, clean lager. The gold standard of Japanese beer.",
        "cultural_note": "Sapporo is the 'original'. Look for 'Sapporo Premium' (black label with red star) or 'Ebisu' (Yebisu) — the premium version. 'Happoshu' (発泡酒) and 'Dai-san no biiru' (第三のビール) are cheaper malt alternatives if you're on a budget.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "umeshu",
        "jp": "梅酒",
        "jp_romaji": "umeshu",
        "en": "Plum Wine (Shochu-based)",
        "category": "alcohol",
        "subcategory": "liqueur",
        "price_range": "¥200-400",
        "emoji": "🍑",
        "tier": "★★★",
        "description": "Sweet, fragrant Japanese plum liqueur. Sip over ice (roku) or with soda (soda-wari).",
        "cultural_note": "Umeshu is made by steeping ume (Japanese plums) in shochu and sugar. Home-brewing is common — families often have a jar steeping. Konbini sells cute single-serve cans perfect for hotel room sipping.",
        "common_at": ["7-Eleven", "Lawson"]
    },
    {
        "id": "happoshu",
        "jp": "発泡酒",
        "jp_romaji": "happoushu",
        "en": "Low-Malt Beer (Budget Beer)",
        "category": "alcohol",
        "subcategory": "beer",
        "price_range": "¥120-200",
        "emoji": "🍺",
        "tier": "★",
        "description": "Cheaper beer alternative with less malt. Lighter taste, lighter wallet impact.",
        "cultural_note": "Happoshu was invented to dodge Japan's high malt tax. The 'third beer' (第三のビール) category uses soy protein or pea protein instead of malt — even cheaper and surprisingly not terrible. Popular brands: Hon Kirin, Tanrei.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },

    # ── Snacks ──
    {
        "id": "kaki-no-tane",
        "jp": "柿の種",
        "jp_romaji": "kaki no tane",
        "en": "Spicy Rice Crackers (Kaki Pai)",
        "category": "snacks",
        "subcategory": "savory",
        "price_range": "¥100-200",
        "emoji": "🍘",
        "tier": "★★★",
        "description": "Crunchy crescent-shaped rice crackers with a spicy kick. Often mixed with peanuts.",
        "cultural_note": "The name means 'persimmon seeds' (they look like seeds). The spicy-savory combo is addictive. Mixed with peanuts it's called 'kaki-pi' — THE classic beer snack.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "wasabi-beef-jerky",
        "jp": "わさびビーフジャーキー",
        "jp_romaji": "wasabi biifu jaakii",
        "en": "Wasabi Beef Jerky",
        "category": "snacks",
        "subcategory": "jerky",
        "price_range": "¥200-400",
        "emoji": "🥩",
        "tier": "★★★",
        "description": "Beef jerky with real wasabi kick. Surprisingly high quality, excellent with beer.",
        "cultural_note": "Lawson's wasabi beef jerky has a cult following. The wasabi is real — the heat hits your nose, not your tongue. A fantastic omiyage (souvenir) to bring home.",
        "common_at": ["Lawson", "FamilyMart"]
    },
    {
        "id": "jagarico",
        "jp": "じゃがりこ",
        "jp_romaji": "jagariko",
        "en": "Jagariko (Crispy Potato Sticks)",
        "category": "snacks",
        "subcategory": "potato",
        "price_range": "¥120-180",
        "emoji": "🥔",
        "tier": "★★★",
        "description": "Crunchy, thick potato sticks in a cup — salad (green) and cheese (yellow) are classics.",
        "cultural_note": "Jagariko has a distinctive trapezoid cup shape and comes with a tiny fork. Limited edition flavors (consomme, teriyaki, butter soy sauce) drop regularly and sell out fast.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "pocky",
        "jp": "ポッキー",
        "jp_romaji": "pokkii",
        "en": "Pocky (Chocolate Stick)",
        "category": "snacks",
        "subcategory": "sweet",
        "price_range": "¥100-200",
        "emoji": "🥢",
        "tier": "★★★",
        "description": "Pretzel sticks dipped in chocolate. Japan's most famous exported snack. Try matcha or strawberry limited editions.",
        "cultural_note": "Pocky Day (11/11) is a real Japanese holiday — the sticks look like 1s. Glico releases special flavors just for this day. Pocky has dozens of Japan-exclusive flavors: purple sweet potato, mango, crème brûlée.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "kitkat-japan",
        "jp": "キットカット",
        "jp_romanji": "kittokatto",
        "en": "KitKat (Japan Exclusives)",
        "category": "snacks",
        "subcategory": "sweet",
        "price_range": "¥150-400",
        "emoji": "🍫",
        "tier": "★★★",
        "description": "Japan has 300+ KitKat flavors — matcha, sake, sweet potato, melon, cheesecake, and more.",
        "cultural_note": "KitKat in Japan is associated with good luck — 'Kitto Katsu' (きっと勝つ = 'surely win') sounds like the brand name. Students eat them before exams. Regional exclusives (Shinshu apple, Kyushu sweet potato) are popular omiyage.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "konbu-chips",
        "jp": "昆布チップス",
        "jp_romaji": "konbu chippusu",
        "en": "Seaweed Chips",
        "category": "snacks",
        "subcategory": "savory",
        "price_range": "¥100-200",
        "emoji": "🟤",
        "tier": "★★",
        "description": "Crispy fried kelp chips — umami-rich and surprisingly light. Healthy-ish by snack standards.",
        "cultural_note": "These are often found in the 'otokuyouhin' (value bin) section. They're a Hokkaido specialty but available nationwide at most konbini.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "umaibo",
        "jp": "うまい棒",
        "jp_romaji": "umaibou",
        "en": "Umaibo (Cheese Puff Stick)",
        "category": "snacks",
        "subcategory": "savory",
        "price_range": "¥10-20",
        "emoji": "🌽",
        "tier": "★★",
        "description": "Cylindrical puffed corn snack, cheese flavor. Iconic cheap snack at ¥10 each. Mental note: price is rising to ¥12 in 2025.",
        "cultural_note": "Umaibo has held the ¥10 price point since 1979 — a miracle of Japanese deflation economics. The recent price hike to ¥12 (2025) made national news. There's even a Umaibo museum in Tochigi.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },

    # ── Desserts ──
    {
        "id": "pudding",
        "jp": "プリン",
        "jp_romaji": "purin",
        "en": "Japanese Custard Pudding",
        "category": "desserts",
        "subcategory": "custard",
        "price_range": "¥100-200",
        "emoji": "🍮",
        "tier": "★★★",
        "description": "Silky egg custard with caramel sauce. A konbini staple that beats most restaurant versions.",
        "cultural_note": "Japanese pudding is closer to French crème caramel than American pudding. The caramel is usually a liquid layer on top. Tofu-like texture when done right. 7-Eleven's is considered the gold standard among budget purins.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "crepe-cake",
        "jp": "クレープケーキ",
        "jp_romaji": "kureepu keeki",
        "en": "Crepe Cake Slice",
        "category": "desserts",
        "subcategory": "cake",
        "price_range": "¥200-400",
        "emoji": "🥞",
        "tier": "★★★",
        "description": "Layers of thin crepes with whipped cream and fruit. Light, elegant, dangerously good.",
        "cultural_note": "FamilyMart's crepe cakes are particularly good. The strawberry shortcake crepe is a seasonal highlight during spring. This is the kind of thing that convinces people Japanese konbini food is unmatched.",
        "common_at": ["FamilyMart", "7-Eleven"]
    },
    {
        "id": "mochi-ice-cream",
        "jp": "もちアイス",
        "jp_romaji": "mochi aisu",
        "en": "Mochi Ice Cream",
        "category": "desserts",
        "subcategory": "ice cream",
        "price_range": "¥100-200",
        "emoji": "🍡",
        "tier": "★★★",
        "description": "Chewy rice dough wrapping vanilla/matcha ice cream. Bite-sized bliss.",
        "cultural_note": "Lotte's Yukimi Daifuku (雪見だいふく) is the OG — 'snow-viewing daifuku'. The mochi skin stays chewy even frozen. Don't microwave (it melts the ice cream inside) — let it sit 2-3 min at room temp.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "anmitsu",
        "jp": "あんみつ",
        "jp_romaji": "anmitsu",
        "en": "Anmitsu (Bean Paste Jelly Dessert)",
        "category": "desserts",
        "subcategory": "traditional",
        "price_range": "¥200-350",
        "emoji": "🫘",
        "tier": "★★",
        "description": "Traditional Japanese dessert with agar jelly, sweet bean paste, fruit, and black sugar syrup.",
        "cultural_note": "Anmitsu is a Meiji-era creation. The black sugar syrup (kuromitsu) is the key — pour it over everything. Konbini versions come in cute compartmented cups.",
        "common_at": ["7-Eleven", "FamilyMart"]
    },
    {
        "id": "ice-cream-cone",
        "jp": "アイスクリーム",
        "jp_romaji": "aisu kuriimu",
        "en": "Soft Serve / Ice Cream Cone",
        "category": "desserts",
        "subcategory": "ice cream",
        "price_range": "¥100-200",
        "emoji": "🍦",
        "tier": "★★★",
        "description": "Creamy soft-serve with chocolate dip. Always hits the spot on a humid day.",
        "cultural_note": "7-Eleven's soft serve machine is legendary. The 'cremia' (クレミア) soft serve — available at some konbini — has 12.5% butterfat content, making it incredibly rich.",
        "common_at": ["7-Eleven", "FamilyMart"]
    },
    {
        "id": "dorayaki",
        "jp": "どら焼き",
        "jp_romaji": "dorayaki",
        "en": "Dorayaki (Red Bean Pancake)",
        "category": "desserts",
        "subcategory": "traditional",
        "price_range": "¥100-200",
        "emoji": "🥞",
        "tier": "★★★",
        "description": "Two small pancake-like patties sandwiching sweet red bean paste. Doraemon's favorite food.",
        "cultural_note": "Dorayaki is famous worldwide as Doraemon's favorite snack. The best version has a thin layer of mochi-like texture. Try the 'shiro-an' (white bean) variant if you see it.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },

    # ── Daily Goods ──
    {
        "id": "umbrella",
        "jp": "傘",
        "jp_romaji": "kasa",
        "en": "Transparent Plastic Umbrella",
        "category": "daily_goods",
        "subcategory": "essentials",
        "price_range": "¥300-700",
        "emoji": "🌂",
        "tier": "★★★",
        "description": "Clear plastic umbrella — the savior when sudden rain catches you. Sold at every konbini worldwide, but in Japan they're practically a uniform.",
        "cultural_note": "Clear umbrellas are the Japanese default because they don't obscure vision on crowded streets. When it rains in Tokyo, every konbini puts a basket of them by the entrance. You'll see the city transformed into a sea of clear domes.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "business-shirt",
        "jp": "ワイシャツ",
        "jp_romaji": "wai shatsu",
        "en": "Dress Shirt (Laundry-Fresh)",
        "category": "daily_goods",
        "subcategory": "clothing",
        "price_range": "¥1,500-3,000",
        "emoji": "👔",
        "tier": "★★",
        "description": "Individually packaged dress shirts in your size — laundry-fresh. Yes, really, at a convenience store.",
        "cultural_note": "A uniquely Japanese konbini service — salarymen who had a long night and need a fresh shirt for the morning grab these. They come laundered, starched, and individually packaged.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "toothbrush-set",
        "jp": "歯ブラシセット",
        "jp_romaji": "haburashi setto",
        "en": "Travel Toothbrush Set",
        "category": "daily_goods",
        "subcategory": "toiletries",
        "price_range": "¥100-300",
        "emoji": "🪥",
        "tier": "★★★",
        "description": "Compact toothbrush + mini toothpaste. What to grab when your hotel doesn't provide one (or you forgot yours).",
        "cultural_note": "Many Japanese hotels don't provide toiletries by default (eco policy). The toothbrush sets near the konbini register are a traveler's lifeline. They also sell travel-sized everything — shampoo, razor, contact lens solution.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "facial-tissues",
        "jp": "ティッシュ",
        "jp_romaji": "tisshu",
        "en": "Pocket Tissues",
        "category": "daily_goods",
        "subcategory": "essentials",
        "price_range": "¥30-100",
        "emoji": "🧻",
        "tier": "★★",
        "description": "Small pocket pack of tissues. Often given away for free by advertisers, but konbini sells them too.",
        "cultural_note": "Free tissue packs are a classic Japanese advertising medium — handed out in front of stations by people in costumes. They're used ONCE here (blow, fold, discard) because they're practically free.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "sim-card",
        "jp": "SIMカード",
        "jp_romaji": "shimu kaado",
        "en": "Prepaid SIM Card / eSIM",
        "category": "daily_goods",
        "subcategory": "electronics",
        "price_range": "¥1,500-5,000",
        "emoji": "📱",
        "tier": "★★★",
        "description": "Prepaid data SIM for tourists. Available at bigger konbini (especially near airports and stations).",
        "cultural_note": "Look for 'Japan Travel SIM' by NTT Docomo or Softbank. 7-Eleven also sells their own '7-11 Talk & Data SIM'. You'll need to show your passport to buy — it's for tourist use only.",
        "common_at": ["7-Eleven", "Lawson"]
    },
    {
        "id": "stamps",
        "jp": "切手",
        "jp_romaji": "kitte",
        "en": "Postage Stamps",
        "category": "daily_goods",
        "subcategory": "postal",
        "price_range": "¥10-200+",
        "emoji": "✉️",
        "tier": "★",
        "description": "Postage stamps for sending postcards and letters. Standard postcard rate to overseas is ¥70.",
        "cultural_note": "The konbini clerk can weigh your mail and sell you the correct stamps. Postcards to overseas: ¥70 (air). Letters start at ¥120 for up to 25g. Also sell cute character-themed washi tapes and stationery.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "shampoo-travel",
        "jp": "トラベルシャンプー",
        "jp_romaji": "toraberu shanpuu",
        "en": "Travel Shampoo / Conditioner",
        "category": "daily_goods",
        "subcategory": "toiletries",
        "price_range": "¥50-200",
        "emoji": "🧴",
        "tier": "★★",
        "description": "Single-use packs of shampoo, conditioner, body soap. Perfect for capsule hotels or hostels.",
        "cultural_note": "These tiny sachets are a lifesaver at shared showers. Tsubaki (椿) and Pantene are the most common brands. The konbini also sells 'dryers' (coin-operated in some locations).",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },

    # ── Services / Cultural ──
    {
        "id": "atm-service",
        "jp": "ATM",
        "jp_romaji": "ATM",
        "en": "ATM (Cash Withdrawal)",
        "category": "services",
        "subcategory": "financial",
        "price_range": "¥0-220 (fee)",
        "emoji": "🏧",
        "tier": "★★★",
        "description": "International ATM accepting foreign cards (Visa, Mastercard, etc.) for cash withdrawal.",
        "cultural_note": "7-Eleven ATMs are the best for international cards — lower fees, English UI, and available 24/7 at 21,000+ stores. Lawson ATMs (beyond) and FamilyMart ATMs (E-net) also work but may charge higher fees. Japan is still VERY cash-based.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "copier-printer",
        "jp": "コピー機",
        "jp_romaji": "kopii ki",
        "en": "Multi-Function Copier/Printer",
        "category": "services",
        "subcategory": "business",
        "price_range": "¥10-50 per copy",
        "emoji": "🖨️",
        "tier": "★★",
        "description": "Full color copier/printer/scanner. Accepts USB, SD card, and smartphone transfer (app or QR).",
        "cultural_note": "A lifesaver for printing tickets, boarding passes, or documents. The interface is available in English (press 'English' at the top). You can also print photos from your phone — great for instant Shutterstock-type souvenir prints.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "concert-ticket",
        "jp": "チケット発券",
        "jp_romaji": "chiketto hakken",
        "en": "Ticket Pickup (Loppi / Fami Port)",
        "category": "services",
        "subcategory": "ticketing",
        "price_range": "varies",
        "emoji": "🎫",
        "tier": "★★★",
        "description": "Pick up pre-booked event tickets (concerts, films, Shinkansen, theme parks) at the terminal.",
        "cultural_note": "Lawson's 'Loppi' (ロッピー) and FamilyMart's 'Fami Port' (ファミポート) are essential for buying/reserving event tickets, concert tickets (Ticket Pia), Ghibli Museum passes, and highway bus seats. Many online orders in Japan require konbini payment/pickup.",
        "common_at": ["Lawson", "FamilyMart"]
    },
    {
        "id": "bill-payment",
        "jp": "支払い",
        "jp_romaji": "shiharai",
        "en": "Bill Payment Service",
        "category": "services",
        "subcategory": "financial",
        "price_range": "¥0 (bill amount)",
        "emoji": "🧾",
        "tier": "★★",
        "description": "Pay utility bills, taxes, insurance, and online shopping invoices at the register.",
        "cultural_note": "Paying bills at konbini is still common practice in Japan — young people do it more than you'd expect. Just take the barcode slip to the register and they'll scan and collect payment. Receipt is your proof of payment.",
        "common_at": ["7-Eleven", "Lawson", "FamilyMart"]
    },
    {
        "id": "shipping",
        "jp": "宅配便",
        "jp_romaji": "takkyuubin",
        "en": "Package Shipping (Yamato / Sagawa)",
        "category": "services",
        "subcategory": "shipping",
        "price_range": "¥500-2,000+",
        "emoji": "📦",
        "tier": "★★★",
        "description": "Ship luggage to your next hotel or the airport. A game-changer for traveling Japan.",
        "cultural_note": "Konbini takkyuubin (宅配便) is a game-changer. Drop your luggage at 7-Eleven (Yamato/Kuroneko) or FamilyMart and it arrives at your next hotel the next day. You travel hands-free. Fill out the form at the counter, pay, and done. Omiyato (souvenir shipping home) also available.",
        "common_at": ["7-Eleven", "FamilyMart"]
    },
]


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


def print_help():
    """Print detailed help."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║            🏪 KONBINI COMPANION - Japan Travel Tool         ║
║   Decode Japanese convenience stores like a local           ║
╚══════════════════════════════════════════════════════════════╝

ITEMS DATABASE: {count} items across {cat_count} categories

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
""".format(count=len(ITEMS), cat_count=len(CATEGORIES)))
    for cid, cname in CATEGORIES.items():
        count = len(get_items_by_category(ITEMS, cid))
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
        indices = build_index(ITEMS)
        interactive_mode(ITEMS, indices)
        return

    indices = build_index(ITEMS)

    if args.list_categories:
        print("Available categories:\n")
        for cid, cname in CATEGORIES.items():
            count = len(get_items_by_category(ITEMS, cid))
            print(f"  {cid:<15} {cname:<30} ({count} items)")

    elif args.search:
        results = search_items(ITEMS, args.search, indices)
        if results:
            print(f"Found {len(results)} item(s) matching '{args.search}':\n")
            for r in results:
                print(format_item(r))
                print()
        else:
            print(f"No items found matching '{args.search}'.")

    elif args.category:
        if args.category in CATEGORIES:
            cat_items = get_items_by_category(ITEMS, args.category)
            print(f"{CATEGORIES[args.category]} ({len(cat_items)} items):\n")
            for item in cat_items:
                print(format_item(item))
                print()
        else:
            print(f"Unknown category: '{args.category}'")
            print(f"Available: {', '.join(CATEGORIES.keys())}")

    elif args.random:
        item = get_random_item(ITEMS)
        print(format_item(item))

    elif args.export_json:
        data = json_export(ITEMS)
        if args.export_json == "auto":
            data_dir = os.path.expanduser("~/.hermes/data")
            os.makedirs(data_dir, exist_ok=True)
            path = os.path.join(data_dir, "konbini-companion-items.json")
        else:
            path = args.export_json
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"✅ Exported {len(ITEMS)} items to {os.path.abspath(path)}")

    elif args.store:
        show_store(ITEMS, args.store)

    elif args.stats:
        show_stats(ITEMS)


if __name__ == "__main__":
    main()
