"""Build the Shopwise catalog and historical order data from UCI Online Retail II.

The raw workbook contains ~1.07M transaction lines from a UK online gift retailer.
We keep a clean, sellable catalog of 1,000 products and derive a customer/order
history that is loaded into the shop. The recommender is trained on exactly this
history, so the demo, the API and the report all tell the same story.

Run from the repository root:
    python -m backend.app.ml.build_dataset
or:
    python backend/app/ml/build_dataset.py
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "online_retail_ii"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_XLSX = RAW_DIR / "online_retail_II.xlsx"

N_PRODUCTS = 1000
N_CUSTOMERS = 750
MAX_ORDERS_PER_CUSTOMER = 30
RANDOM_SEED = 42

CATEGORY_RULES: list[tuple[str, str]] = [
    ("Bags & Accessories", r"\b(BAGS?|PURSES?|WALLETS?|SHOPPERS?|TOTES?|BACKPACKS?|RUCKSACKS?|LUGGAGE|UMBRELLAS?|KEYRING|KEY RING|KEY FOB|JEWELLERY|JEWELRY|NECKLACES?|BRACELETS?|EARRINGS?|BROOCH|HAIR|CLIP|BELT|SCARF|GLOVES?|HATS?|SUNGLASSES|PONCHO|MOBILE)\b"),
    ("Bath & Beauty", r"\b(SOAP|BATH|BEAUTY|CREAM|LOTION|PERFUME|SACHET|SPONGE|WASH|NAIL|COSMETIC|VANITY|TOOTH|BRUSH|MASSAGE|SALTS)\b"),
    ("Christmas", r"\b(CHRISTMAS|XMAS|ADVENT|SANTA|REINDEER|SNOWMAN|BAUBLE|STOCKING|NATIVITY|MISTLETOE|HOLLY|NOEL|ELVES|ELF|SNOWFLAKE)\b"),
    ("Festive & Gifts", r"\b(GIFT|PARTY|BIRTHDAY|WEDDING|VALENTINE|EASTER|HALLOWEEN|BUNTING|BALLOON|GARLAND|CONFETTI|CELEBRATION|ANNIVERSARY)\b"),
    ("Lighting", r"\b(LIGHTS?|LAMPS?|LANTERNS?|CANDLES?|CANDLEHOLDERS?|CANDLE HOLDERS?|T-LIGHTS?|TEALIGHTS?|CHANDELIERS?|NIGHTLIGHTS?|BULBS?)\b"),
    ("Textiles", r"\b(HAND WARMERS?|HOT WATER BOTTLES?|CUSHIONS?|THROWS?|BLANKETS?|QUILTS?|PILLOWS?|TOWELS?|TABLECLOTHS?|TEA TOWELS?|FABRICS?|KNITTED|DUVETS?|BEDSPREADS?|TEXTILES?)\b"),
    ("Kitchen & Dining", r"\b(MUGS?|CUPS?|PLATES?|BOWLS?|JUGS?|TEAPOTS?|CAKE STAND|CAKESTAND|CAKE CASES?|CAKE TINS?|JAM|JARS?|BOTTLES?|GLASSES?|CUTLERY|SPOONS?|FORK|KNIFE|NAPKINS?|TABLE|TEA|COFFEE|EGG|MILK|SUGAR|BAKING|PAN|COOK|DISH|SAUCE|SALT|PEPPER|OIL|VINEGAR|CORKSCREW|OPENER|ICE CUBE|APRONS?|OVEN|KITCHEN|CULINARY|PICNIC|LUNCH|BREAKFAST|PITCHERS?|TRAYS?|COASTERS?|STRAWS?|SNACK)\b"),
    ("Stationery", r"\b(CARDS?|NOTEBOOKS?|NOTE BOOK|PENS?|PENCILS?|PAPER|ENVELOPES?|WRAP|RIBBONS?|TAPE|STICKERS?|CHALK|BOARD|DIARIES|DIARY|JOURNALS?|CALENDARS?|BOOKMARKS?|STAMPS?|INK|STATIONERY|MEMOBOARD|MAGNETS?|CALCULATOR|WRITING SET|MATCHES?)\b"),
    ("Textiles", r"\b(CUSHION|COVER|THROW|BLANKET|QUILT|BED|PILLOW|TOWEL|TABLECLOTH|RUNNER|TEA TOWEL|FABRIC|COTTON|LINEN|KNITTED|HOTTIE|HOT WATER BOTTLE|SOCKS|SOCKS|TEXTILE|DUVET)\b"),
    ("Storage", r"\b(BOX|TIN|CONTAINER|BASKET|CRATE|CHEST|DRAWER|ORGANISER|STORAGE|SUITCASE|TRUNK|TROLLEY|CADDY|HOLDER)\b"),
    ("Kids & Toys", r"\b(TOYS?|GAMES?|PUZZLES?|DOLLS?|TEDDY|BEAR|SKIPPING|PLAY|KITE|BALL|MARBLES|JIGSAW|DOMINOES?|CHESS|BINGO|KALEIDOSCOPE|YO-YO|SPINNING|BABY|CHILD|KIDS|GIRL|BOY|NURSERY|PUSHCHAIR|BIB|RATTLE|SNAKES|LADDERS|BUILDING BLOCK|GLOBES?|NAUGHTS|CROSSES|PLAYHOUSE)\b"),
    ("Garden & Outdoor", r"\b(GARDEN|PLANTS?|WATERING|SEEDS?|BIRD|OUTDOOR|GREENHOUSE|HERBS?|POTS?|PLANTERS?|WINDMILL|WIND CHIME|PARASOL|BARBECUE|BBQ|CAMPING|FISHING|DOORMAT|WELLINGTON|SPADE|SANDFLAGS?|HAMMOCK|TWINE)\b"),
    ("Home Decor", r"\b(HEART|FRAME|PHOTO|MIRROR|VASE|ORNAMENT|DECORATION|SIGN|CLOCK|HOOK|HANGER|WALL|DOORSTOP|BIRD|BUTTERFLY|FLOWER|ROSE|SKULL|PARIS|LONDON|STAR|MOON|SUN|CLOUD|CROWN|ANGEL|FAIRY|DRAGONFLY|HANGING)\b"),
]

MATERIALS = [
    "ceramic", "glass", "powder-coated metal", "natural wood", "cotton",
    "stoneware", "brass", "frosted glass", "woven rattan", "enamel",
]
COLOURS = ["cream", "sage", "terracotta", "ink", "ochre", "blush", "ivory", "charcoal"]
CATEGORY_DETAILS = {
    "Home Decor": "A quietly expressive piece for shelves, mantels and tablescapes.",
    "Kitchen & Dining": "Made for slow breakfasts, generous dinners and everything between.",
    "Lighting": "A warm pool of light that turns an ordinary corner into a moment.",
    "Textiles": "Soft to the touch and easy to layer, it brings warmth without fuss.",
    "Storage": "Everyday order, beautifully kept.",
    "Stationery": "For lists, letters and small, important ideas.",
    "Bags & Accessories": "A considered finishing touch for the everyday.",
    "Christmas": "A little festive tradition to bring out year after year.",
    "Festive & Gifts": "A celebration-ready piece, made to be given and kept.",
    "Garden & Outdoor": "A little more life for windowsills, gardens and open air.",
    "Bath & Beauty": "Small rituals for slower mornings and softer evenings.",
    "Kids & Toys": "Made for curious hands and long afternoons of play.",
    "Everyday Finds": "The useful, the charming and the quietly indispensable.",
}

NAME_OVERRIDES = {
    "T-LIGHT": "T-Light",
    "T-Light": "T-Light",
    "Led": "LED",
    "Pvc": "PVC",
    "Diy": "DIY",
    "Xmas": "Xmas",
    "Uk": "UK",
    "Nye": "NYE",
}


def slugify_code(code: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", code.lower()).strip("-")


def titleise(text: str) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip().strip('"').replace("&amp;", "&")
    text = text.title()
    for old, new in NAME_OVERRIDES.items():
        text = re.sub(rf"\b{re.escape(old)}\b", new, text)
    text = re.sub(r"\b(\d+)T\b", r"\1 T", text)
    return text


def classify(name: str) -> str:
    upper = name.upper()
    for category, pattern in CATEGORY_RULES:
        if re.search(pattern, upper):
            return category
    return "Everyday Finds"


def material_and_colour(code: str, name: str) -> tuple[str, str]:
    upper = name.upper()
    material = next((m for m in ["CERAMIC", "GLASS", "WOOD", "METAL", "COTTON", "LINEN", "BRASS", "RATTAN", "ENAMEL", "STONEWARE"] if m in upper), None)
    colour = next((c for c in ["RED", "PINK", "BLUE", "GREEN", "WHITE", "CREAM", "BLACK", "SILVER", "GOLD", "PURPLE", "YELLOW", "ORANGE", "GREY", "BROWN"] if c in upper), None)
    h = int(hashlib.sha1(code.encode()).hexdigest(), 16)
    material = (material or MATERIALS[h % len(MATERIALS)]).lower()
    colour = (colour or COLOURS[(h // 7) % len(COLOURS)]).lower()
    return material, colour


def make_description(name: str, category: str, code: str) -> tuple[str, str, str]:
    material, colour = material_and_colour(code, name)
    detail = CATEGORY_DETAILS.get(category, CATEGORY_DETAILS["Home Decor"])
    description = (
        f"{name} is an easy favourite from the Shopwise {category.lower()} collection. "
        f"Finished in {colour} with a {material} feel, it brings a considered touch to everyday living. "
        f"{detail}"
    )
    return description, material, colour


def sha_float(key: str, salt: str = "") -> float:
    digest = hashlib.sha1(f"{key}:{salt}".encode()).hexdigest()
    return int(digest[:12], 16) / float(16**12)


def load_transactions() -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cache = PROCESSED_DIR / "transactions.parquet"
    if cache.exists():
        print(f"[data] using cached transactions: {cache}")
        cached = pd.read_parquet(cache)
        if "Country" in cached.columns:
            cached = cached.rename(columns={"Country": "country"})
        return cached

    if not RAW_XLSX.exists():
        raise FileNotFoundError(
            f"Dataset not found at {RAW_XLSX}. Download the UCI Online Retail II zip "
            "and extract online_retail_II.xlsx into backend/data/raw/online_retail_ii/."
        )

    print("[data] reading both sheets from Online Retail II (this takes a moment)...")
    sheets = pd.read_excel(RAW_XLSX, sheet_name=None, engine="openpyxl")
    frames = []
    for sheet_name, frame in sheets.items():
        frame = frame.copy()
        frame["Sheet"] = sheet_name
        frames.append(frame)
    raw = pd.concat(frames, ignore_index=True)

    raw.columns = [str(c).strip() for c in raw.columns]
    raw = raw.rename(
        columns={
            "Customer ID": "customer_id",
            "StockCode": "stock_code",
            "InvoiceDate": "invoice_date",
            "Description": "description",
            "Quantity": "quantity",
            "Price": "price",
            "Invoice": "invoice",
        }
    )

    # Clean, sellable product lines only.
    raw = raw[raw["customer_id"].notna()]
    raw = raw[~raw["invoice"].astype(str).str.upper().str.startswith("C")]
    raw = raw[(raw["quantity"] > 0) & (raw["price"] > 0) & (raw["price"] < 500)]
    raw["stock_code"] = raw["stock_code"].astype(str).str.strip().str.upper()
    raw["description"] = raw["description"].astype(str).str.strip()
    raw = raw[raw["stock_code"].str.match(r"^[0-9]{5}[A-Z]{0,2}$", na=False)]
    raw = raw[raw["description"].str.len().between(4, 80)]
    raw = raw[
        ~raw["description"].str.upper().str.contains(
            r"POSTAGE|CARRIAGE|DISCOUNT|MANUAL|BANK CHARGE|AMAZON|SAMPLES?|ADJUST|DAMAGED|WRONG|CRUSHED|MISSING|CHECK|FOUND|TEST",
            regex=True,
        )
    ]
    raw["customer_id"] = raw["customer_id"].astype(int)
    raw["invoice"] = raw["invoice"].astype(str)
    raw["invoice_date"] = pd.to_datetime(raw["invoice_date"])
    raw = raw.drop_duplicates(subset=["invoice", "stock_code", "quantity", "price", "invoice_date"])
    raw.to_parquet(cache, index=False)
    print(f"[data] cleaned {len(raw):,} transaction lines -> {cache}")
    return raw


def build_catalog(raw: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        raw.groupby("stock_code")
        .agg(
            raw_name=("description", lambda s: s.value_counts().index[0]),
            price=("price", "median"),
            popularity=("invoice", "nunique"),
            quantity_sold=("quantity", "sum"),
            last_sold=("invoice_date", "max"),
        )
        .reset_index()
    )
    grouped = grouped[(grouped["popularity"] >= 3) & (grouped["price"] >= 0.5)]
    # Favour products with broad appeal, but keep small press-worthy pieces too.
    grouped = grouped.sort_values(["popularity", "quantity_sold"], ascending=False).head(N_PRODUCTS).copy()
    grouped = grouped.sort_values("stock_code").reset_index(drop=True)

    rows = []
    for i, row in grouped.iterrows():
        code = row["stock_code"]
        name = titleise(row["raw_name"])
        category = classify(name)
        description, material, colour = make_description(name, category, code)
        rating = round(3.7 + 1.2 * sha_float(code, "rating"), 2)
        review_count = int(3 + 40 * sha_float(code, "reviews") * min(1, row["popularity"] / 80))
        stock = int(min(260, max(12, 12 + row["popularity"] * 0.25 + 50 * sha_float(code, "stock"))))
        rows.append(
            {
                "code": code,
                "name": name,
                "description": description,
                "category": category,
                "price": round(max(3.99, float(row["price"]) * 2.8), 2),  # wholesale GBP -> retail USD
                "stock": stock,
                "rating": rating,
                "review_count": review_count,
                "popularity": int(row["popularity"]),
                "quantity_sold": int(row["quantity_sold"]),
                "material": material,
                "colour": colour,
                "image": f"/static/products/{slugify_code(code)}.svg",
            }
        )
    catalog = pd.DataFrame(rows)
    print(f"[data] catalog: {len(catalog)} products, {catalog['category'].nunique()} categories")
    print(catalog["category"].value_counts().to_string())
    return catalog


def build_users_and_orders(raw: pd.DataFrame, catalog: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Select customers and build a compact, recent order history."""
    selected = raw[raw["stock_code"].isin(catalog["code"])].copy()
    selected["line_total"] = selected["quantity"] * selected["price"]

    customer_stats = (
        selected.groupby("customer_id")
        .agg(
            n_lines=("stock_code", "size"),
            n_products=("stock_code", "nunique"),
            n_invoices=("invoice", "nunique"),
            total_spent=("line_total", "sum"),
            last_purchase=("invoice_date", "max"),
            country=("country", lambda s: s.value_counts().index[0]),
        )
        .reset_index()
    )
    eligible = customer_stats[(customer_stats["n_products"] >= 5) & (customer_stats["n_invoices"] >= 3)].copy()
    print(f"[data] eligible customers: {len(eligible):,} of {len(customer_stats):,}")

    rng = np.random.default_rng(RANDOM_SEED)
    eligible = eligible.sort_values("customer_id").reset_index(drop=True)
    if len(eligible) > N_CUSTOMERS:
        # Keep a deterministic cross-section, with a slight preference for engaged customers.
        weights = np.sqrt(eligible["n_products"].to_numpy())
        weights = weights / weights.sum()
        chosen = rng.choice(eligible.index.to_numpy(), size=N_CUSTOMERS, replace=False, p=weights)
        sample = eligible.loc[chosen].copy()
    else:
        sample = eligible.copy()

    # The demo account gets a rich but not extreme history that spans many categories.
    rich_candidates = sample[(sample["n_products"] >= 18) & (sample["n_products"] <= 75)]
    demo_customer = int((rich_candidates if len(rich_candidates) else sample).sort_values("n_products", ascending=False).iloc[0]["customer_id"])

    sample = sample.sort_values("customer_id").reset_index(drop=True)
    sample["user_id"] = np.arange(1, len(sample) + 1)
    demo_row = sample[sample["customer_id"] == demo_customer].index[0]
    if demo_row != 0:
        first = sample.loc[0].copy()
        sample.loc[0] = sample.loc[demo_row]
        sample.loc[demo_row] = first
        sample["user_id"] = np.arange(1, len(sample) + 1)

    first_names = [
        "Alice", "Maya", "Oliver", "Sofia", "Theo", "Isla", "Noah", "Amelia", "Leo", "Grace",
        "Ethan", "Nora", "Milo", "Freya", "Hugo", "Elena", "Arthur", "Cleo", "Finn", "Iris",
        "Jasper", "Luna", "Oscar", "Zoe", "Rory", "Ada", "Max", "Clara", "Sam", "Eva",
        "Arjun", "Meera", "Ravi", "Anika", "Kabir", "Sana", "Dev", "Priya", "Neel", "Tara",
        "Ben", "Chloe", "Daniel", "Ella", "Felix", "Georgia", "Harry", "Imogen", "Jack", "Keira",
    ]
    last_names = [
        "Hart", "Bennett", "Carter", "Collins", "Diaz", "Ellis", "Fischer", "Grant", "Hayes", "Ibrahim",
        "Jensen", "Kaur", "Lopez", "Miller", "Nair", "Owen", "Patel", "Quinn", "Reed", "Shaw",
        "Singh", "Taylor", "Underwood", "Vale", "Walker", "Young", "Kapoor", "Rao", "Brooks", "Foster",
    ]
    used_names = set()
    customers = []
    for i, row in sample.iterrows():
        if i == 0:
            name = "Sofia Hart"
            email = "demo@shopwise.com"
        else:
            attempt = 0
            while True:
                name = f"{first_names[(i * 7 + attempt) % len(first_names)]} {last_names[(i * 11 + attempt) % len(last_names)]}"
                attempt += 1
                if name not in used_names or attempt > 100:
                    break
            email = f"{name.lower().replace(' ', '.')}{i + 1}@example.com"
        used_names.add(name)
        customers.append(
            {
                "user_id": int(row["user_id"]),
                "customer_key": int(row["customer_id"]),
                "name": name,
                "email": email,
                "country": row["country"],
                "n_products": int(row["n_products"]),
                "n_invoices": int(row["n_invoices"]),
                "total_spent": round(float(row["total_spent"]) * 2.8, 2),
                "is_demo": i == 0,
            }
        )
    users = pd.DataFrame(customers)

    # Recent historical window: map the dataset timeline into the last ~20 months.
    selected = selected[selected["customer_id"].isin(sample["customer_id"])].copy()
    # Cap very long histories to the most recent invoices per customer.
    selected["invoice_date"] = pd.to_datetime(selected["invoice_date"])
    invoice_dates = selected[["customer_id", "invoice", "invoice_date"]].drop_duplicates()
    invoice_dates = invoice_dates.sort_values(["customer_id", "invoice_date"])
    invoice_dates["rank"] = invoice_dates.groupby("customer_id").cumcount(ascending=False)
    keep_invoices = set(invoice_dates[invoice_dates["rank"] < MAX_ORDERS_PER_CUSTOMER]["invoice"])
    selected = selected[selected["invoice"].isin(keep_invoices)].copy()

    span_start = selected["invoice_date"].min()
    span_end = selected["invoice_date"].max()
    window_end = date.today() - timedelta(days=8)
    window_start = window_end - timedelta(days=590)
    total_seconds = max(1.0, (span_end - span_start).total_seconds())
    selected["invoice_date"] = selected["invoice_date"].apply(
        lambda d: pd.Timestamp(window_start)
        + pd.Timedelta(seconds=(d - span_start).total_seconds() / total_seconds * (window_end - window_start).days * 86400)
    )
    # Spread each invoice's time to daytime hours deterministically.
    selected["invoice_date"] = selected["invoice_date"] + pd.to_timedelta(
        selected["invoice"].apply(lambda inv: int(hashlib.md5(inv.encode()).hexdigest()[:4], 16) % 36000), unit="s"
    )

    cust_to_user = dict(zip(sample["customer_id"], sample["user_id"]))
    invoices = (
        selected.groupby(["customer_id", "invoice"])
        .agg(invoice_date=("invoice_date", "min"), total=("line_total", "sum"))
        .reset_index()
        .sort_values("invoice_date")
    )
    invoices["order_id"] = np.arange(1, len(invoices) + 1)
    invoices["user_id"] = invoices["customer_id"].map(cust_to_user)
    invoices["total"] = (invoices["total"] * 1.25).round(2)

    items = selected.merge(invoices[["invoice", "customer_id", "order_id"]], on=["invoice", "customer_id"], how="inner")
    # The source is a wholesaler; normalise bulk quantities into retail-sized
    # baskets while retaining the real product co-purchase structure.
    items["quantity"] = np.where(items["quantity"] <= 2, 1, np.where(items["quantity"] <= 9, 2, 3))
    items["unit_price"] = (items["price"] * 2.8).round(2)
    items["line_total"] = (items["quantity"] * items["unit_price"]).round(2)
    # Align the order total exactly with its line items.
    totals = items.groupby("order_id")["line_total"].sum()
    invoices["total"] = invoices["order_id"].map(totals).round(2)
    users["total_spent"] = users["user_id"].map(
        invoices.groupby("user_id")["total"].sum()
    ).round(2)

    orders = invoices.rename(columns={"customer_id": "customer_key"})[
        ["order_id", "user_id", "customer_key", "invoice", "invoice_date", "total"]
    ].copy()
    order_items = items.rename(columns={"customer_id": "customer_key"})[
        ["order_id", "stock_code", "quantity", "unit_price", "line_total"]
    ].copy()
    order_items = order_items.merge(catalog[["code", "name"]], left_on="stock_code", right_on="code", how="left")
    order_items = order_items.rename(columns={"name": "product_name"})[
        ["order_id", "stock_code", "product_name", "quantity", "unit_price", "line_total"]
    ]

    print(f"[data] users: {len(users)}, orders: {len(orders)}, order lines: {len(order_items):,}")
    print(f"[data] demo customer: {demo_customer}, orders: {(orders['customer_key'] == demo_customer).sum()}")
    return users, orders, order_items


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_transactions()
    catalog = build_catalog(raw)
    users, orders, order_items = build_users_and_orders(raw, catalog)

    catalog.to_csv(DATA_DIR / "catalog.csv", index=False)
    users.to_csv(DATA_DIR / "customers.csv", index=False)
    orders.to_csv(DATA_DIR / "orders.csv", index=False)
    order_items.to_csv(DATA_DIR / "order_items.csv", index=False)

    stats = {
        "source": "UCI Machine Learning Repository - Online Retail II (ID 502)",
        "source_url": "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
        "raw_transaction_lines": int(len(raw)),
        "raw_customers": int(raw["customer_id"].nunique()),
        "raw_products": int(raw["stock_code"].nunique()),
        "catalog_products": int(len(catalog)),
        "categories": int(catalog["category"].nunique()),
        "seeded_customers": int(len(users)),
        "historical_orders": int(len(orders)),
        "historical_order_lines": int(len(order_items)),
        "historical_revenue": round(float(orders["total"].sum()), 2),
        "date_range": [str(orders["invoice_date"].min()), str(orders["invoice_date"].max())],
        "generated_at": pd.Timestamp.now().isoformat(timespec="seconds"),
    }
    (DATA_DIR / "dataset_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
