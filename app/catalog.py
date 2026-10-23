from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    slug: str
    name: str
    price_cents: int
    category: str
    blurb: str
    emoji: str


PRODUCTS: list[Product] = [
    Product("hedgehog-plush", "Hedgehog plush", 2400, "merch", "A soft hedgehog that judges your dashboards quietly.", "🦔"),
    Product("ship-it-mug", "Ship it mug", 1800, "merch", "Holds 400 ml of coffee and one strong opinion about release trains.", "☕"),
    Product("flag-flipper-tee", "Flag flipper tee", 2900, "apparel", "For people who roll out to 1% first and brag later.", "👕"),
    Product("replay-hoodie", "Replay hoodie", 6500, "apparel", "Warm enough to watch session recordings until 2 a.m.", "🧥"),
    Product("funnel-poster", "Funnel poster", 1500, "prints", "A2 print of a conversion funnel that finally converts.", "🖼️"),
    Product("sticker-pack", "Sticker pack", 700, "merch", "Twelve stickers, zero tracking pixels.", "✨"),
    Product("desk-mat", "Query desk mat", 3500, "merch", "A desk mat with a SQL cheat sheet you will pretend not to need.", "⌨️"),
    Product("cold-brew-kit", "Cold brew kit", 4200, "kitchen", "Everything needed to over-engineer coffee.", "🧊"),
]

BY_SLUG = {p.slug: p for p in PRODUCTS}


def search(query: str) -> list[Product]:
    q = query.lower().strip()
    if not q:
        return PRODUCTS
    return [p for p in PRODUCTS if q in p.name.lower() or q in p.blurb.lower() or q in p.category.lower()]


def format_price(cents: int) -> str:
    return f"${cents / 100:,.2f}"
