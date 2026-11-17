import os
import re
import sqlite3
import urllib.request
import pandas as pd

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_PHOTOS = os.path.join(ROOT_DIR, "backend", "static", "products", "photos")
os.makedirs(STATIC_PHOTOS, exist_ok=True)

# Curated library of high-resolution commercial product photos on Unsplash
PHOTO_LIBRARY = {
    # Kitchen & Tableware
    "ceramic_bowl": "https://images.unsplash.com/photo-1610701596007-11502861dcfa?auto=format&fit=crop&w=600&h=600&q=80",
    "salad_bowl": "https://images.unsplash.com/photo-1543339308-43e59d6b73a6?auto=format&fit=crop&w=600&h=600&q=80",
    "ceramic_plate": "https://images.unsplash.com/photo-1584269600519-112d071b35e6?auto=format&fit=crop&w=600&h=600&q=80",
    "coffee_mug": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=600&h=600&q=80",
    "ceramic_cup": "https://images.unsplash.com/photo-1577937927133-66ef06acdf18?auto=format&fit=crop&w=600&h=600&q=80",
    "teapot": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=600&h=600&q=80",
    "tea_set": "https://images.unsplash.com/photo-1594631252845-29fc4cc8cde9?auto=format&fit=crop&w=600&h=600&q=80",
    "water_bottle": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=600&h=600&q=80",
    "cutlery_fork": "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?auto=format&fit=crop&w=600&h=600&q=80",
    "baking_dish": "https://images.unsplash.com/photo-1590736969955-71cc94801759?auto=format&fit=crop&w=600&h=600&q=80",
    "glassware": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=600&h=600&q=80",

    # Candles & Lighting
    "scented_candle": "https://images.unsplash.com/photo-1603006905003-be475563bc59?auto=format&fit=crop&w=600&h=600&q=80",
    "tlight_holder": "https://images.unsplash.com/photo-1508746829417-e6f548d8d6ed?auto=format&fit=crop&w=600&h=600&q=80",
    "brass_lantern": "https://images.unsplash.com/photo-1517411032315-54ef2cb783bb?auto=format&fit=crop&w=600&h=600&q=80",
    "table_lamp": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=600&h=600&q=80",
    "fairy_lights": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=600&h=600&q=80",

    # Bags & Accessories
    "tote_bag": "https://images.unsplash.com/photo-1544816155-12df9643f363?auto=format&fit=crop&w=600&h=600&q=80",
    "canvas_shopper": "https://images.unsplash.com/photo-1597484662317-9bd7bdda2907?auto=format&fit=crop&w=600&h=600&q=80",
    "leather_purse": "https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=600&h=600&q=80",
    "luggage_case": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=600&h=600&q=80",
    "lunch_bag": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=600&h=600&q=80",
    "cosmetic_pouch": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=600&h=600&q=80",
    "umbrella": "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?auto=format&fit=crop&w=600&h=600&q=80",

    # Stationery & Craft
    "colouring_pencils": "https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?auto=format&fit=crop&w=600&h=600&q=80",
    "notebook_journal": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&h=600&q=80",
    "greeting_cards": "https://images.unsplash.com/photo-1586075010923-2dd4570fb338?auto=format&fit=crop&w=600&h=600&q=80",
    "craft_paper": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&h=600&q=80",
    "desk_accessories": "https://images.unsplash.com/photo-1456735190829-80ab072ac175?auto=format&fit=crop&w=600&h=600&q=80",

    # Storage & Tins
    "vintage_tin": "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=600&h=600&q=80",
    "wooden_box": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=600&h=600&q=80",
    "woven_basket": "https://images.unsplash.com/photo-1595341888016-a392ef81b7de?auto=format&fit=crop&w=600&h=600&q=80",
    "glass_storage_jar": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=600&h=600&q=80",
    "trinket_box": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=600&h=600&q=80",

    # Home Decor
    "ceramic_vase": "https://images.unsplash.com/photo-1581783342308-f792dbdd27c5?auto=format&fit=crop&w=600&h=600&q=80",
    "photo_frame": "https://images.unsplash.com/photo-1582053433979-22c0fe1a21ab?auto=format&fit=crop&w=600&h=600&q=80",
    "vintage_clock": "https://images.unsplash.com/photo-1563861826100-9cb868fdbe1c?auto=format&fit=crop&w=600&h=600&q=80",
    "wall_mirror": "https://images.unsplash.com/photo-1618220179428-22790b461013?auto=format&fit=crop&w=600&h=600&q=80",
    "heart_decoration": "https://images.unsplash.com/photo-1518199266791-5375a83190b7?auto=format&fit=crop&w=600&h=600&q=80",
    "cushion_pillow": "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?auto=format&fit=crop&w=600&h=600&q=80",
    "tea_towel": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=600&h=600&q=80",
    "doormat": "https://images.unsplash.com/photo-1584589167171-541ce45f1eea?auto=format&fit=crop&w=600&h=600&q=80",

    # Garden & Outdoor
    "terracotta_planter": "https://images.unsplash.com/photo-1485955900006-10f4d324d411?auto=format&fit=crop&w=600&h=600&q=80",
    "watering_can": "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&w=600&h=600&q=80",
    "garden_lantern": "https://images.unsplash.com/photo-1598880940371-c756e015fea1?auto=format&fit=crop&w=600&h=600&q=80",

    # Kids & Toys
    "globe_classic": "https://images.unsplash.com/photo-1521295121783-8a321d551ad2?auto=format&fit=crop&w=600&h=600&q=80",
    "wooden_toy": "https://images.unsplash.com/photo-1558060370-d644479cb6f7?auto=format&fit=crop&w=600&h=600&q=80",
    "plush_bear": "https://images.unsplash.com/photo-1559454403-b8fb88521f11?auto=format&fit=crop&w=600&h=600&q=80",
    "jigsaw_puzzle": "https://images.unsplash.com/photo-1618842676087-c1f48a40dd6e?auto=format&fit=crop&w=600&h=600&q=80",

    # Bath & Beauty
    "natural_soap": "https://images.unsplash.com/photo-1607006310488-82a176885b51?auto=format&fit=crop&w=600&h=600&q=80",
    "bath_sponge": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=600&h=600&q=80",
    "apothecary_jar": "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=600&h=600&q=80",
    "spa_towel": "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?auto=format&fit=crop&w=600&h=600&q=80",

    # Christmas & Festive
    "christmas_ornament": "https://images.unsplash.com/photo-1543257580-7269da773bf5?auto=format&fit=crop&w=600&h=600&q=80",
    "holiday_wreath": "https://images.unsplash.com/photo-1512389142860-9c449e58a543?auto=format&fit=crop&w=600&h=600&q=80",
    "gift_ribbon": "https://images.unsplash.com/photo-1513885535751-8b9238bd345a?auto=format&fit=crop&w=600&h=600&q=80",
    "party_bunting": "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?auto=format&fit=crop&w=600&h=600&q=80",
    "party_candles": "https://images.unsplash.com/photo-1531747056595-07f6cbbe10ad?auto=format&fit=crop&w=600&h=600&q=80",
}

def download_photos():
    print(f"Downloading {len(PHOTO_LIBRARY)} curated product photos...")
    headers = {"User-Agent": "Mozilla/5.0"}
    success = 0
    for name, url in PHOTO_LIBRARY.items():
        fp = os.path.join(STATIC_PHOTOS, f"{name}.jpg")
        if os.path.exists(fp) and os.path.getsize(fp) > 5000:
            success += 1
            continue
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read()
                with open(fp, "wb") as f:
                    f.write(content)
            success += 1
            print(f"  Downloaded: {name}.jpg ({len(content)} bytes)")
        except Exception as e:
            print(f"  Failed {name}: {e}")
    print(f"Total downloaded photos: {success}/{len(PHOTO_LIBRARY)}")

def choose_photo(name: str, category: str) -> str:
    n = name.lower()
    c = category.lower()

    # Highly specific keyword matching
    if "globe" in n:
        return "globe_classic"
    if "bowl" in n:
        return "ceramic_bowl" if "salad" not in n else "salad_bowl"
    if "mug" in n or "cup" in n:
        return "coffee_mug" if "tea" not in n else "ceramic_cup"
    if "teapot" in n or "tea set" in n:
        return "teapot"
    if "pencil" in n or "pen" in n:
        return "colouring_pencils"
    if "notebook" in n or "journal" in n:
        return "notebook_journal"
    if "candle" in n:
        return "scented_candle"
    if "t-light" in n or "tealight" in n or "holder" in n and "light" in n:
        return "tlight_holder"
    if "lantern" in n:
        return "brass_lantern"
    if "lamp" in n or "light" in n:
        return "table_lamp"
    if "tote" in n or "shopper" in n:
        return "tote_bag"
    if "purse" in n or "wallet" in n:
        return "leather_purse"
    if "luggage" in n or "cases" in n or "suitcase" in n:
        return "luggage_case"
    if "lunch bag" in n or "lunch" in n:
        return "lunch_bag"
    if "bag" in n:
        return "canvas_shopper"
    if "umbrella" in n or "parasol" in n:
        return "umbrella"
    if "tin" in n or "biscuit" in n:
        return "vintage_tin"
    if "box" in n:
        return "wooden_box" if "trinket" not in n else "trinket_box"
    if "basket" in n or "hamper" in n:
        return "woven_basket"
    if "jar" in n or "bottle" in n:
        return "glass_storage_jar"
    if "vase" in n:
        return "ceramic_vase"
    if "frame" in n:
        return "photo_frame"
    if "clock" in n:
        return "vintage_clock"
    if "mirror" in n:
        return "wall_mirror"
    if "heart" in n:
        return "heart_decoration"
    if "cushion" in n or "pillow" in n:
        return "cushion_pillow"
    if "towel" in n:
        return "tea_towel"
    if "doormat" in n or "mat" in n:
        return "doormat"
    if "planter" in n or "pot" in n:
        return "terracotta_planter"
    if "watering can" in n:
        return "watering_can"
    if "soap" in n:
        return "natural_soap"
    if "sponge" in n:
        return "bath_sponge"
    if "toy" in n or "puzzle" in n:
        return "wooden_toy" if "puzzle" not in n else "jigsaw_puzzle"
    if "bear" in n or "doll" in n:
        return "plush_bear"
    if "christmas" in n or "bauble" in n or "xmas" in n:
        return "christmas_ornament"
    if "party" in n or "bunting" in n or "garland" in n:
        return "party_bunting"
    if "ribbon" in n or "gift" in n:
        return "gift_ribbon"

    # Category fallbacks
    cat_fallbacks = {
        "kitchen & dining": "ceramic_plate",
        "home decor": "ceramic_vase",
        "lighting": "table_lamp",
        "stationery": "notebook_journal",
        "bags & accessories": "tote_bag",
        "storage": "vintage_tin",
        "christmas": "christmas_ornament",
        "garden & outdoor": "terracotta_planter",
        "textiles": "cushion_pillow",
        "festive & gifts": "gift_ribbon",
        "kids & toys": "wooden_toy",
        "bath & beauty": "natural_soap",
        "everyday finds": "ceramic_bowl",
    }
    return cat_fallbacks.get(c, "ceramic_bowl")

def update_database_and_catalog():
    print("Mapping 1,000 products to real photos...")
    db_path = os.path.join(ROOT_DIR, "backend", "shopwise.db")
    catalog_path = os.path.join(ROOT_DIR, "backend", "data", "catalog.csv")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, name, category, code FROM products")
    products = cur.fetchall()

    updates = []
    for pid, name, category, code in products:
        photo_key = choose_photo(name, category)
        photo_path = f"/static/products/photos/{photo_key}.jpg"
        updates.append((photo_path, pid))

    cur.executemany("UPDATE products SET image = ? WHERE id = ?", updates)
    conn.commit()
    conn.close()
    print(f"Updated {len(updates)} products in shopwise.db!")

    # Also update catalog.csv
    if os.path.exists(catalog_path):
        df = pd.read_csv(catalog_path)
        df["image"] = df.apply(lambda row: f"/static/products/photos/{choose_photo(str(row['name']), str(row['category']))}.jpg", axis=1)
        df.to_csv(catalog_path, index=False)
        print("Updated catalog.csv with photo paths!")

if __name__ == "__main__":
    download_photos()
    update_database_and_catalog()
    print("Photo update completed successfully!")
