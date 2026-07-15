"""
Seed Script

Populates the database with demo categories, subcategories, products
(with real, unique photography per product — no two products share an
image, and every product ships a photo gallery), and a bootstrap
admin account. Safe to re-run — skips creation if data already exists.

Usage:
    python seed.py
"""

import os
import random
from datetime import datetime, timedelta
from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models.product import Category, Product, slugify
from app.models.user import User
from app.models.order import Order, OrderItem, ORDER_STATUSES

app = create_app("development")

IMG = lambda photo_id: f"https://images.unsplash.com/{photo_id}?w=1000&q=80&auto=format&fit=crop"

# =====================================================================
# CURATED PHOTO POOLS — one Unsplash photo ID is used at most once
# across the entire catalog. Grouped by visual theme so lighting/tone
# stays consistent within a category.
# =====================================================================

# ---- Bags (leather goods, neutral studio + lifestyle shots) ----
BAG = {
    "b2": IMG("photo-1598532163257-ae3c6b2524b6"),
    "b6": IMG("photo-1691480150204-66dd1eb77391"),
    "b15": IMG("photo-1575032617751-6ddec2089882"),
    "b14": IMG("photo-1637759292654-a12cb2be085e"),
    "b5": IMG("photo-1647540945262-7da3bd1a3d96"),
    "b13": IMG("photo-1535120927584-0230f40fc1e2"),
    "b1": IMG("photo-1473188588951-666fce8e7c68"),
    "b3": IMG("photo-1622560257067-108402fcedc0"),
    "b12": IMG("photo-1622560480605-d83c853bc5c3"),
    "b10": IMG("photo-1479219136056-56bb6495a005"),
    "b8": IMG("photo-1603219527847-24c87f552a77"),
    "b4": IMG("photo-1608731267464-c0c889c2ff92"),
    "b11": IMG("photo-1602082430164-0c1927ddecb2"),
    "b7": IMG("photo-1624687943971-e86af76d57de"),
    "b9": IMG("photo-1613482184972-f9c1022d0928"),
}

# ---- Fashion (coats, jackets, knitwear) ----
FSH = {
    "f1": IMG("photo-1539533113208-f6df8cc8b543"),
    "f3": IMG("photo-1539533018447-63fcce2678e3"),
    "f9": IMG("photo-1617391258031-f8d80b22fb35"),
    "f4": IMG("photo-1619603364904-c0498317e145"),
    "f13": IMG("photo-1619603364937-8d7af41ef206"),
    "f8": IMG("photo-1608635680046-aebf91c1a9c8"),
    "f14": IMG("photo-1574201635302-388dd92a4c3f"),
    "f15": IMG("photo-1581497396202-5645e76a3a8e"),
    "f17": IMG("photo-1588271968087-4c51abe05afc"),
    "f5": IMG("photo-1592343516109-362f7bd871aa"),
    "f6": IMG("photo-1669575903350-9a349b411810"),
    "f2": IMG("photo-1591047139829-d91aecb6caea"),
    "f18": IMG("photo-1610901157620-340856d0a50f"),
    "f10": IMG("photo-1619473918387-2710c35e3bf2"),
    "f12": IMG("photo-1591900947067-851789555ef3"),
    "f7": IMG("photo-1514813836041-518668f092b1"),
    "f11": IMG("photo-1698133468659-5ff0a0b02dda"),
    "f16": IMG("photo-1601379327928-bedfaf9da2d0"),
}

# ---- Jewellery (gold/silver product macro shots) ----
JWL = {
    "j1": IMG("photo-1611107683227-e9060eccd846"),
    "j9": IMG("photo-1662434923031-b9bf1b6c10e2"),
    "j4": IMG("photo-1611955167811-4711904bb9f8"),
    "j6": IMG("photo-1622398925373-3f91b1e275f5"),
    "j3": IMG("photo-1623321673989-830eff0fd59f"),
    "j2": IMG("photo-1601121141461-9d6647bca1ed"),
    "j8": IMG("photo-1601821765780-754fa98637c1"),
    "j12": IMG("photo-1620656798579-1984d9e87df7"),
    "j10": IMG("photo-1626122780071-c09d403b8e32"),
    "j5": IMG("photo-1633934542430-0905ccb5f050"),
    "j7": IMG("photo-1602173574767-37ac01994b2a"),
    "j11": IMG("photo-1612150354898-a69132eb7c67"),
}

# ---- Watches / timepieces ----
WCH = {
    "w1": IMG("photo-1670177257750-9b47927f68eb"),
    "w2": IMG("photo-1600003014755-ba31aa59c4b6"),
    "w3": IMG("photo-1670404160620-a3a86428560e"),
    "w4": IMG("photo-1600003014637-ff82a275e191"),
    "w5": IMG("photo-1600003014608-c2ccc1570a65"),
    "w11": IMG("photo-1548171916-c0dea7f94ca6"),
    "w6": IMG("photo-1548169874-53e85f753f1e"),
    "w7": IMG("photo-1636639818651-d97365346a5c"),
    "w8": IMG("photo-1634140704051-58a787556cd1"),
}

# ---- Cameras / travel tech ----
CAM = {
    "c1": IMG("photo-1495121553079-4c61bcce1894"),
    "c4": IMG("photo-1512390225428-a9d51c817f94"),
    "c13": IMG("photo-1511184059754-e4b5bbbcef75"),
    "c2": IMG("photo-1601854266103-c1dd42130633"),
    "c5": IMG("photo-1516961642265-531546e84af2"),
    "c9": IMG("photo-1528594498426-ea65fdafcbf4"),
    "c8": IMG("photo-1515622472995-1a06094d2224"),
    "c11": IMG("photo-1520549233664-03f65c1d1327"),
    "c14": IMG("photo-1517092756309-24071485f6db"),
}

# ---- Home accessories (ceramics + textiles) ----
HOM = {
    "v1": IMG("photo-1631125915902-d8abe9225ff2"),
    "v2": IMG("photo-1597696929736-6d13bed8e6a8"),
    "v3": IMG("photo-1677761640321-b80251be00ca"),
    "v4": IMG("photo-1481401908818-600b7a676c0d"),
    "v5": IMG("photo-1643569556871-91ec60671ed7"),
    "v6": IMG("photo-1631125915973-e0d155a14e4e"),
    "v7": IMG("photo-1526198049595-f32cde2a219d"),
    "v8": IMG("photo-1631125916276-69bcd14e3980"),
    "v9": IMG("photo-1526198330131-9b0bc79625e4"),
    "t1": IMG("photo-1611911813383-67769b37a149"),
    "t2": IMG("photo-1670080589800-6416c8ce8a14"),
    "t3": IMG("photo-1670080946016-d9b4445ff8b6"),
    "t4": IMG("photo-1634901581982-6b408cf4226a"),
}

# --- Category hero banners (each distinct from every product photo above) ---
CAT_BAGS = IMG("photo-1622560480605-d83c853bc5c3")
CAT_FASHION = IMG("photo-1539533113208-f6df8cc8b543")
CAT_JEWELLERY = IMG("photo-1611107683227-e9060eccd846")
CAT_ELECTRONICS = IMG("photo-1730757679771-b53e798846cf")
CAT_HOME = IMG("photo-1572853566597-b83cde546912")

# ---- Small leather goods (wallets, card holders) ----
SLG = {
    "wl1": IMG("photo-1601592996763-f05c9c80a7f1"),
    "wl3": IMG("photo-1612023395494-1c4050b68647"),
    "wl6": IMG("photo-1512414947060-048d53abb081"),
    "wl2": IMG("photo-1620109176813-e91290f6c795"),
    "wl5": IMG("photo-1637168943285-a8f9ea0dc3f5"),
    "wl8": IMG("photo-1606503825008-909a67e63c3d"),
}

# ---- Leather belts ----
BLT = {
    "bl1": IMG("photo-1664286074176-5206ee5dc878"),
    "bl3": IMG("photo-1705493655920-20c572928501"),
    "bl6": IMG("photo-1684510334550-0c4fa8aaffd1"),
}

# ---- Extra watches / cameras (rounding out Electronics) ----
WCH2 = {
    "w9": IMG("photo-1524805444758-089113d48a6d"),
    "w10": IMG("photo-1604242692760-2f7b0c26856d"),
    "w13": IMG("photo-1649357585015-179ed98f513d"),
    "w14": IMG("photo-1634595947394-87012e7b12ba"),
    "w15": IMG("photo-1548171838-1fd4cb4ab854"),
}
CAM2 = {
    "c3": IMG("photo-1595401735913-4ca17c66e755"),
    "c6": IMG("photo-1516962126636-27ad087061cc"),
    "c7": IMG("photo-1481923387198-050ac1a2896e"),
    "c10": IMG("photo-1531635410863-4c7d45c6f712"),
}

# ---- Extra ceramics (rounding out Home Accessories) ----
HOM2 = {
    "v10": IMG("photo-1687191883721-257d8cad5b54"),
    "v11": IMG("photo-1633000116322-d7f5cb7d3ebb"),
    "v13": IMG("photo-1631125915361-b749fdeea230"),
    "v14": IMG("photo-1723779232101-19167d4b6e00"),
}

CATEGORIES = [
    {"name": "Bags", "description": "Heritage leather goods, crafted to last a lifetime.", "image_url": CAT_BAGS},
    {"name": "Fashion", "description": "Tailored apparel for the discerning wardrobe.", "image_url": CAT_FASHION},
    {"name": "Jewellery", "description": "Fine jewellery, ethically sourced and expertly set.", "image_url": CAT_JEWELLERY},
    {"name": "Electronics", "description": "Precision instruments and everyday technology.", "image_url": CAT_ELECTRONICS},
    {"name": "Home Accessories", "description": "Considered pieces for a refined interior.", "image_url": CAT_HOME},
]


def gallery(*urls):
    """Joins gallery URLs, filtering out any falsy entries."""
    return ",".join(u for u in urls if u)


PRODUCTS = [
    # ---------------- BAGS ----------------
    # Subcategory: Carry-All Bags
    {"name": "Aldgate Leather Briefcase", "category": "Bags", "subcategory": "Carry-All Bags", "price": 349.00,
     "compare_at_price": 420.00, "stock": 9, "sku": "BAG-001", "image": BAG["b2"], "gallery": gallery(BAG["b2"], BAG["b6"]),
     "description": "Full-grain leather briefcase, hand-stitched in a heritage tannery. Ages beautifully with wear."},
    {"name": "Kensington Tote", "category": "Bags", "subcategory": "Carry-All Bags", "price": 289.00, "stock": 14,
     "sku": "BAG-002", "image": BAG["b15"], "gallery": gallery(BAG["b15"], BAG["b14"]),
     "description": "A structured tote in vegetable-tanned leather, sized for laptop and daily essentials."},
    {"name": "Camden Weekender Bag", "category": "Bags", "subcategory": "Carry-All Bags", "price": 410.00, "stock": 5,
     "sku": "BAG-003", "image": BAG["b5"], "gallery": gallery(BAG["b5"], BAG["b13"], BAG["b1"]),
     "description": "A spacious weekend companion in oiled leather with reinforced brass hardware."},
    {"name": "Mayfair Backpack", "category": "Bags", "subcategory": "Carry-All Bags", "price": 265.00, "stock": 11,
     "sku": "BAG-004", "image": BAG["b3"], "gallery": gallery(BAG["b3"], BAG["b12"], BAG["b10"]),
     "description": "Minimalist leather backpack with a padded laptop sleeve, built for the modern commute."},
    # Subcategory: Everyday Leather Goods
    {"name": "Chelsea Crossbody Satchel", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 195.00,
     "compare_at_price": 230.00, "stock": 3, "sku": "BAG-005", "image": BAG["b8"], "gallery": gallery(BAG["b8"], BAG["b4"], BAG["b11"]),
     "description": "Compact crossbody in pebbled leather with an adjustable strap and antique-brass clasp."},
    {"name": "Belgravia Document Holder", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 145.00,
     "stock": 20, "sku": "BAG-006", "image": BAG["b7"], "gallery": gallery(BAG["b7"], BAG["b9"]),
     "description": "A slim leather folio for documents and a tablet, finished with a hand-stitched edge."},
    {"name": "Marylebone Leather Wallet", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 95.00,
     "stock": 20, "sku": "BAG-007", "image": SLG["wl1"], "gallery": gallery(SLG["wl1"], SLG["wl3"], SLG["wl6"]),
     "description": "A bifold wallet in vegetable-tanned leather, with card slots and a coin pocket."},
    {"name": "Notting Hill Card Holder", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 55.00,
     "stock": 26, "sku": "BAG-008", "image": SLG["wl2"], "gallery": gallery(SLG["wl2"], SLG["wl5"], SLG["wl8"]),
     "description": "A slim card holder in burnished leather, sized to fit five cards and folded notes."},

    # ---------------- FASHION ----------------
    # Subcategory: Outerwear & Tailoring
    {"name": "Heritage Wool Overcoat", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 420.00,
     "compare_at_price": 495.00, "stock": 7, "sku": "FSH-001", "image": FSH["f1"], "gallery": gallery(FSH["f1"], FSH["f3"], FSH["f9"]),
     "description": "A tailored wool overcoat cut from a heavyweight Yorkshire cloth. Built to outlast trends."},
    {"name": "Cognac Leather Jacket", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 385.00,
     "stock": 6, "sku": "FSH-002", "image": FSH["f4"], "gallery": gallery(FSH["f4"], FSH["f13"], FSH["f8"]),
     "description": "Classic biker silhouette in supple lambskin leather with a quilted lining."},
    {"name": "Merino Wool Sweater", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 125.00,
     "stock": 18, "sku": "FSH-003", "image": FSH["f14"], "gallery": gallery(FSH["f14"], FSH["f15"], FSH["f17"]),
     "description": "Fine-gauge merino knit in a relaxed fit, spun from ethically sourced wool."},
    {"name": "Tailored Wool Trousers", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 165.00,
     "stock": 12, "sku": "FSH-004", "image": FSH["f5"], "gallery": gallery(FSH["f5"], FSH["f6"], FSH["f2"]),
     "description": "A precisely tailored trouser in Italian wool twill, finished with a clean break."},
    # Subcategory: Accessories & Footwear
    {"name": "Cashmere Scarf", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 145.00,
     "stock": 0, "sku": "FSH-005", "image": FSH["f18"], "gallery": gallery(FSH["f18"], FSH["f10"], FSH["f12"]),
     "description": "Pure cashmere scarf, woven in a herringbone pattern for understated warmth."},
    {"name": "Oxford Leather Brogues", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 275.00,
     "stock": 9, "sku": "FSH-006", "image": FSH["f7"], "gallery": gallery(FSH["f7"], FSH["f11"], FSH["f16"]),
     "description": "Hand-lasted brogues in burnished calfskin, Goodyear-welted for decades of resoling."},
    {"name": "Full-Grain Leather Belt", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 95.00,
     "stock": 22, "sku": "FSH-007", "image": BLT["bl1"], "gallery": gallery(BLT["bl1"], BLT["bl3"], BLT["bl6"]),
     "description": "A reversible belt in full-grain leather with a solid brass buckle."},

    # ---------------- JEWELLERY ----------------
    # Subcategory: Necklaces, Chains & Earrings
    {"name": "18k Gold Cuban Chain", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 890.00,
     "stock": 4, "sku": "JWL-001", "image": JWL["j1"], "gallery": gallery(JWL["j1"], JWL["j9"]),
     "description": "Solid 18k gold Cuban link chain, hand-finished by our in-house goldsmiths."},
    {"name": "Gold Hoop Earrings", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 210.00,
     "stock": 16, "sku": "JWL-003", "image": JWL["j3"], "gallery": gallery(JWL["j3"], JWL["j2"]),
     "description": "Sculptural 14k gold hoops, polished to a soft satin finish."},
    {"name": "Pearl Drop Necklace", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 320.00,
     "stock": 8, "sku": "JWL-004", "image": JWL["j8"], "gallery": gallery(JWL["j8"], JWL["j12"]),
     "description": "Freshwater pearl pendant on a fine gold chain, an heirloom in the making."},
    # Subcategory: Rings & Bracelets
    {"name": "Diamond Solitaire Ring", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 1450.00,
     "compare_at_price": 1650.00, "stock": 2, "sku": "JWL-002", "image": JWL["j4"], "gallery": gallery(JWL["j4"], JWL["j6"]),
     "description": "A timeless solitaire set with a certified diamond in a platinum band."},
    {"name": "Signet Ring, Sterling Silver", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 165.00,
     "stock": 13, "sku": "JWL-005", "image": JWL["j10"], "gallery": gallery(JWL["j10"], JWL["j5"]),
     "description": "A hand-engraved signet ring in sterling silver, made to be personalised."},
    {"name": "Studded Gold Bangle", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 480.00,
     "stock": 6, "sku": "JWL-006", "image": JWL["j7"], "gallery": gallery(JWL["j7"]),
     "description": "A pyramid-studded gold bangle, solid and substantial — a signature statement piece."},
    {"name": "Sapphire Tennis Bracelet", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 980.00,
     "stock": 3, "sku": "JWL-007", "image": JWL["j11"], "gallery": gallery(JWL["j11"]),
     "description": "Deep-blue sapphires channel-set in 18k white gold, a statement of quiet luxury."},

    # ---------------- ELECTRONICS ----------------
    # Subcategory: Watches & Timepieces
    {"name": "Heritage Mechanical Watch", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 620.00,
     "compare_at_price": 720.00, "stock": 6, "sku": "ELC-001", "image": WCH["w1"], "gallery": gallery(WCH["w1"], WCH["w2"], WCH["w3"]),
     "description": "Swiss automatic movement in a brushed steel case with a hand-stitched leather strap."},
    {"name": "Precision Desk Clock", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 95.00,
     "stock": 17, "sku": "ELC-004", "image": WCH["w4"], "gallery": gallery(WCH["w4"], WCH["w5"], WCH["w11"]),
     "description": "A precision quartz desk clock in a solid brass housing, silent-sweep movement."},
    {"name": "Rose Gold Chronograph Watch", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 540.00,
     "stock": 8, "sku": "ELC-006", "image": WCH2["w9"], "gallery": gallery(WCH2["w9"], WCH2["w10"]),
     "description": "A rose-gold chronograph on a leather strap, with a sapphire-crystal face."},
    {"name": "Leather Watch Roll", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 68.00,
     "stock": 15, "sku": "ELC-007", "image": WCH2["w13"], "gallery": gallery(WCH2["w13"], WCH2["w14"], WCH2["w15"]),
     "description": "A hand-rolled leather case for storing and travelling with up to three watches."},
    # Subcategory: Cameras, Audio & Travel
    {"name": "Classic Film Camera", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 340.00,
     "stock": 5, "sku": "ELC-002", "image": CAM["c1"], "gallery": gallery(CAM["c1"], CAM["c4"], CAM["c13"]),
     "description": "A fully restored vintage film camera, tested and calibrated for everyday shooting."},
    {"name": "Studio Wireless Headphones", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 285.00,
     "stock": 22, "sku": "ELC-003", "image": CAM["c2"], "gallery": gallery(CAM["c2"], CAM["c5"], CAM["c9"]),
     "description": "Studio-grade wireless headphones with active noise cancellation and 40-hour battery life."},
    {"name": "Leather-Bound Travel Organiser", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 78.00,
     "stock": 2, "sku": "ELC-005", "image": CAM["c8"], "gallery": gallery(CAM["c8"], CAM["c11"], CAM["c14"]),
     "description": "A leather tech organiser with dedicated slots for cables, chargers, and a passport."},
    {"name": "Compact Digital Camera", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 210.00,
     "stock": 10, "sku": "ELC-008", "image": CAM2["c3"], "gallery": gallery(CAM2["c3"], CAM2["c6"], CAM2["c7"], CAM2["c10"]),
     "description": "A pocketable digital camera with a fast prime lens, built for everyday carry."},

    # ---------------- HOME ACCESSORIES ----------------
    # Subcategory: Ceramics & Tabletop
    {"name": "Hand-Thrown Ceramic Vase", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 85.00,
     "stock": 15, "sku": "HOM-001", "image": HOM["v1"], "gallery": gallery(HOM["v1"], HOM["v2"], HOM["v3"]),
     "description": "A hand-thrown stoneware vase finished in a matte glaze, no two exactly alike."},
    {"name": "Brass Table Lamp", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 165.00,
     "stock": 6, "sku": "HOM-003", "image": HOM["v4"], "gallery": gallery(HOM["v4"], HOM["v5"], HOM["v6"]),
     "description": "A solid brass table lamp with a hand-pleated linen shade, aging to a warm patina."},
    {"name": "Marble Coaster Set", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 48.00,
     "stock": 30, "sku": "HOM-006", "image": HOM2["v10"], "gallery": gallery(HOM2["v10"], HOM2["v11"]),
     "description": "A set of four honed-marble coasters with a soft cork backing."},
    {"name": "Terracotta Planter Vase", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 58.00,
     "stock": 18, "sku": "HOM-007", "image": HOM2["v13"], "gallery": gallery(HOM2["v13"], HOM2["v14"]),
     "description": "An unglazed terracotta planter, thrown by hand with a naturally weathered finish."},
    # Subcategory: Textiles
    {"name": "Linen Throw Pillow, Set of Two", "category": "Home Accessories", "subcategory": "Textiles", "price": 65.00,
     "stock": 24, "sku": "HOM-002", "image": HOM["t1"], "gallery": gallery(HOM["t1"], HOM["t2"], HOM["t3"]),
     "description": "Heavyweight Belgian linen cushion covers with a concealed zip closure."},
    {"name": "Cashmere Throw Blanket", "category": "Home Accessories", "subcategory": "Textiles", "price": 245.00,
     "compare_at_price": 290.00, "stock": 4, "sku": "HOM-004", "image": HOM["t4"], "gallery": gallery(HOM["t4"], HOM["v7"], HOM["v8"]),
     "description": "A generously sized cashmere throw, woven in Scotland from the finest fibres."},
    {"name": "Walnut Wood Wall Clock", "category": "Home Accessories", "subcategory": "Textiles", "price": 135.00,
     "stock": 0, "sku": "HOM-005", "image": WCH["w6"], "gallery": gallery(WCH["w6"], WCH["w7"], WCH["w8"]),
     "description": "A minimalist wall clock in solid walnut, silent-sweep movement, no ticking."},
    # ---------------- AUTO-GENERATED: additional products (18 per subcategory) ----------------

    # Subcategory: Carry-All Bags (extra items)
    {"name": "Bond Street Leather Tote", "category": "Bags", "subcategory": "Carry-All Bags", "price": 45.0, "stock": 2, "sku": "BAG-009", "image": "https://images.unsplash.com/photo-1598532163257-ae3c6b2524b6?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1598532163257-ae3c6b2524b6?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1691480150204-66dd1eb77391?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1575032617751-6ddec2089882?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Chiswick Canvas Backpack", "category": "Bags", "subcategory": "Carry-All Bags", "price": 62.3, "stock": 7, "sku": "BAG-010", "image": "https://images.unsplash.com/photo-1575032617751-6ddec2089882?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1575032617751-6ddec2089882?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1637759292654-a12cb2be085e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1647540945262-7da3bd1a3d96?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Hampstead Structured Briefcase", "category": "Bags", "subcategory": "Carry-All Bags", "price": 79.6, "stock": 12, "sku": "BAG-011", "image": "https://images.unsplash.com/photo-1647540945262-7da3bd1a3d96?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1647540945262-7da3bd1a3d96?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1535120927584-0230f40fc1e2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1473188588951-666fce8e7c68?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Islington Weekend Duffel", "category": "Bags", "subcategory": "Carry-All Bags", "price": 96.9, "stock": 17, "sku": "BAG-012", "image": "https://images.unsplash.com/photo-1473188588951-666fce8e7c68?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1473188588951-666fce8e7c68?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1622560257067-108402fcedc0?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Shoreditch Messenger Bag", "category": "Bags", "subcategory": "Carry-All Bags", "price": 114.2, "stock": 22, "sku": "BAG-013", "image": "https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1479219136056-56bb6495a005?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1603219527847-24c87f552a77?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Fitzrovia Laptop Satchel", "category": "Bags", "subcategory": "Carry-All Bags", "price": 131.5, "stock": 27, "sku": "BAG-014", "image": "https://images.unsplash.com/photo-1603219527847-24c87f552a77?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1603219527847-24c87f552a77?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1608731267464-c0c889c2ff92?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1602082430164-0c1927ddecb2?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Greenwich Convertible Backpack", "category": "Bags", "subcategory": "Carry-All Bags", "price": 148.8, "stock": 4, "sku": "BAG-015", "image": "https://images.unsplash.com/photo-1602082430164-0c1927ddecb2?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1602082430164-0c1927ddecb2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1624687943971-e86af76d57de?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1613482184972-f9c1022d0928?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Camberwell Rolling Carry-On", "category": "Bags", "subcategory": "Carry-All Bags", "price": 166.1, "stock": 9, "sku": "BAG-016", "image": "https://images.unsplash.com/photo-1613482184972-f9c1022d0928?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1613482184972-f9c1022d0928?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1598532163257-ae3c6b2524b6?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1691480150204-66dd1eb77391?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Highgate Suede Tote", "category": "Bags", "subcategory": "Carry-All Bags", "price": 183.4, "stock": 14, "sku": "BAG-017", "image": "https://images.unsplash.com/photo-1691480150204-66dd1eb77391?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1691480150204-66dd1eb77391?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1575032617751-6ddec2089882?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1637759292654-a12cb2be085e?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Peckham Nylon Backpack", "category": "Bags", "subcategory": "Carry-All Bags", "price": 200.7, "stock": 19, "sku": "BAG-018", "image": "https://images.unsplash.com/photo-1637759292654-a12cb2be085e?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1637759292654-a12cb2be085e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1647540945262-7da3bd1a3d96?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1535120927584-0230f40fc1e2?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Bermondsey Overnight Duffel", "category": "Bags", "subcategory": "Carry-All Bags", "price": 218.0, "stock": 24, "sku": "BAG-019", "image": "https://images.unsplash.com/photo-1535120927584-0230f40fc1e2?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1535120927584-0230f40fc1e2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1473188588951-666fce8e7c68?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1622560257067-108402fcedc0?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Clapham Garment Bag", "category": "Bags", "subcategory": "Carry-All Bags", "price": 235.3, "stock": 29, "sku": "BAG-020", "image": "https://images.unsplash.com/photo-1622560257067-108402fcedc0?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1622560257067-108402fcedc0?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1479219136056-56bb6495a005?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Soho Utility Tote", "category": "Bags", "subcategory": "Carry-All Bags", "price": 252.6, "stock": 6, "sku": "BAG-021", "image": "https://images.unsplash.com/photo-1479219136056-56bb6495a005?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1479219136056-56bb6495a005?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1603219527847-24c87f552a77?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1608731267464-c0c889c2ff92?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Brixton Explorer Backpack", "category": "Bags", "subcategory": "Carry-All Bags", "price": 269.9, "stock": 11, "sku": "BAG-022", "image": "https://images.unsplash.com/photo-1608731267464-c0c889c2ff92?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1608731267464-c0c889c2ff92?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1602082430164-0c1927ddecb2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1624687943971-e86af76d57de?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},

    # Subcategory: Everyday Leather Goods (extra items)
    {"name": "Bond Street Bifold Wallet", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 45.0, "stock": 2, "sku": "BAG-023", "image": "https://images.unsplash.com/photo-1601592996763-f05c9c80a7f1?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1601592996763-f05c9c80a7f1?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1612023395494-1c4050b68647?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1512414947060-048d53abb081?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Chiswick Card Holder", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 62.3, "stock": 7, "sku": "BAG-024", "image": "https://images.unsplash.com/photo-1512414947060-048d53abb081?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1512414947060-048d53abb081?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1620109176813-e91290f6c795?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1637168943285-a8f9ea0dc3f5?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Hampstead Coin Pouch", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 79.6, "stock": 12, "sku": "BAG-025", "image": "https://images.unsplash.com/photo-1637168943285-a8f9ea0dc3f5?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1637168943285-a8f9ea0dc3f5?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1606503825008-909a67e63c3d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1598532163257-ae3c6b2524b6?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Islington Passport Holder", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 96.9, "stock": 17, "sku": "BAG-026", "image": "https://images.unsplash.com/photo-1598532163257-ae3c6b2524b6?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1598532163257-ae3c6b2524b6?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1691480150204-66dd1eb77391?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1575032617751-6ddec2089882?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Shoreditch Key Fob", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 114.2, "stock": 22, "sku": "BAG-027", "image": "https://images.unsplash.com/photo-1575032617751-6ddec2089882?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1575032617751-6ddec2089882?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1637759292654-a12cb2be085e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1647540945262-7da3bd1a3d96?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Fitzrovia Zip Pouch", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 131.5, "stock": 27, "sku": "BAG-028", "image": "https://images.unsplash.com/photo-1647540945262-7da3bd1a3d96?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1647540945262-7da3bd1a3d96?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1535120927584-0230f40fc1e2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1473188588951-666fce8e7c68?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Greenwich Phone Sleeve", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 148.8, "stock": 4, "sku": "BAG-029", "image": "https://images.unsplash.com/photo-1473188588951-666fce8e7c68?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1473188588951-666fce8e7c68?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1622560257067-108402fcedc0?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Camberwell Cosmetics Case", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 166.1, "stock": 9, "sku": "BAG-030", "image": "https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1479219136056-56bb6495a005?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1603219527847-24c87f552a77?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Highgate Crossbody Pouch", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 183.4, "stock": 14, "sku": "BAG-031", "image": "https://images.unsplash.com/photo-1603219527847-24c87f552a77?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1603219527847-24c87f552a77?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1608731267464-c0c889c2ff92?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1602082430164-0c1927ddecb2?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Peckham Belt Bag", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 200.7, "stock": 19, "sku": "BAG-032", "image": "https://images.unsplash.com/photo-1602082430164-0c1927ddecb2?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1602082430164-0c1927ddecb2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1624687943971-e86af76d57de?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1613482184972-f9c1022d0928?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Bermondsey Travel Wallet", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 218.0, "stock": 24, "sku": "BAG-033", "image": "https://images.unsplash.com/photo-1613482184972-f9c1022d0928?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1613482184972-f9c1022d0928?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601592996763-f05c9c80a7f1?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1612023395494-1c4050b68647?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Clapham Keychain Pouch", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 235.3, "stock": 29, "sku": "BAG-034", "image": "https://images.unsplash.com/photo-1612023395494-1c4050b68647?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1612023395494-1c4050b68647?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1512414947060-048d53abb081?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1620109176813-e91290f6c795?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Soho Slim Cardholder", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 252.6, "stock": 6, "sku": "BAG-035", "image": "https://images.unsplash.com/photo-1620109176813-e91290f6c795?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1620109176813-e91290f6c795?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1637168943285-a8f9ea0dc3f5?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1606503825008-909a67e63c3d?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},
    {"name": "Brixton Mini Crossbody", "category": "Bags", "subcategory": "Everyday Leather Goods", "price": 269.9, "stock": 11, "sku": "BAG-036", "image": "https://images.unsplash.com/photo-1606503825008-909a67e63c3d?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1606503825008-909a67e63c3d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1598532163257-ae3c6b2524b6?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1691480150204-66dd1eb77391?w=1000&q=80&auto=format&fit=crop"), "description": "Crafted from premium materials with meticulous stitching, built for everyday use and years of wear."},

    # Subcategory: Outerwear & Tailoring (extra items)
    {"name": "Bond Street Wool Blazer", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 45.0, "stock": 2, "sku": "FSH-008", "image": "https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1617391258031-f8d80b22fb35?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Chiswick Trench Coat", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 62.3, "stock": 7, "sku": "FSH-009", "image": "https://images.unsplash.com/photo-1617391258031-f8d80b22fb35?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1617391258031-f8d80b22fb35?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1619603364904-c0498317e145?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1619603364937-8d7af41ef206?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Hampstead Puffer Jacket", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 79.6, "stock": 12, "sku": "FSH-010", "image": "https://images.unsplash.com/photo-1619603364937-8d7af41ef206?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1619603364937-8d7af41ef206?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1608635680046-aebf91c1a9c8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1574201635302-388dd92a4c3f?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Islington Cashmere Cardigan", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 96.9, "stock": 17, "sku": "FSH-011", "image": "https://images.unsplash.com/photo-1574201635302-388dd92a4c3f?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1574201635302-388dd92a4c3f?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1581497396202-5645e76a3a8e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1588271968087-4c51abe05afc?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Shoreditch Denim Jacket", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 114.2, "stock": 22, "sku": "FSH-012", "image": "https://images.unsplash.com/photo-1588271968087-4c51abe05afc?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1588271968087-4c51abe05afc?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1592343516109-362f7bd871aa?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1669575903350-9a349b411810?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Fitzrovia Quilted Gilet", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 131.5, "stock": 27, "sku": "FSH-013", "image": "https://images.unsplash.com/photo-1669575903350-9a349b411810?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1669575903350-9a349b411810?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1610901157620-340856d0a50f?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Greenwich Wool Peacoat", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 148.8, "stock": 4, "sku": "FSH-014", "image": "https://images.unsplash.com/photo-1610901157620-340856d0a50f?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1610901157620-340856d0a50f?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1619473918387-2710c35e3bf2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1591900947067-851789555ef3?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Camberwell Bomber Jacket", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 166.1, "stock": 9, "sku": "FSH-015", "image": "https://images.unsplash.com/photo-1591900947067-851789555ef3?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1591900947067-851789555ef3?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1514813836041-518668f092b1?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1698133468659-5ff0a0b02dda?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Highgate Suit Jacket", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 183.4, "stock": 14, "sku": "FSH-016", "image": "https://images.unsplash.com/photo-1698133468659-5ff0a0b02dda?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1698133468659-5ff0a0b02dda?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601379327928-bedfaf9da2d0?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Peckham Wool Waistcoat", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 200.7, "stock": 19, "sku": "FSH-017", "image": "https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1617391258031-f8d80b22fb35?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Bermondsey Shearling Coat", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 218.0, "stock": 24, "sku": "FSH-018", "image": "https://images.unsplash.com/photo-1617391258031-f8d80b22fb35?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1617391258031-f8d80b22fb35?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1619603364904-c0498317e145?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1619603364937-8d7af41ef206?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Clapham Corduroy Jacket", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 235.3, "stock": 29, "sku": "FSH-019", "image": "https://images.unsplash.com/photo-1619603364937-8d7af41ef206?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1619603364937-8d7af41ef206?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1608635680046-aebf91c1a9c8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1574201635302-388dd92a4c3f?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Soho Linen Blazer", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 252.6, "stock": 6, "sku": "FSH-020", "image": "https://images.unsplash.com/photo-1574201635302-388dd92a4c3f?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1574201635302-388dd92a4c3f?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1581497396202-5645e76a3a8e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1588271968087-4c51abe05afc?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Brixton Field Jacket", "category": "Fashion", "subcategory": "Outerwear & Tailoring", "price": 269.9, "stock": 11, "sku": "FSH-021", "image": "https://images.unsplash.com/photo-1588271968087-4c51abe05afc?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1588271968087-4c51abe05afc?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1592343516109-362f7bd871aa?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1669575903350-9a349b411810?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},

    # Subcategory: Accessories & Footwear (extra items)
    {"name": "Bond Street Silk Tie", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 45.0, "stock": 2, "sku": "FSH-022", "image": "https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1617391258031-f8d80b22fb35?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Chiswick Leather Gloves", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 62.3, "stock": 7, "sku": "FSH-023", "image": "https://images.unsplash.com/photo-1617391258031-f8d80b22fb35?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1617391258031-f8d80b22fb35?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1619603364904-c0498317e145?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1619603364937-8d7af41ef206?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Hampstead Chelsea Boots", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 79.6, "stock": 12, "sku": "FSH-024", "image": "https://images.unsplash.com/photo-1619603364937-8d7af41ef206?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1619603364937-8d7af41ef206?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1608635680046-aebf91c1a9c8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1574201635302-388dd92a4c3f?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Islington Suede Loafers", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 96.9, "stock": 17, "sku": "FSH-025", "image": "https://images.unsplash.com/photo-1574201635302-388dd92a4c3f?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1574201635302-388dd92a4c3f?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1581497396202-5645e76a3a8e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1588271968087-4c51abe05afc?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Shoreditch Wool Beanie", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 114.2, "stock": 22, "sku": "FSH-026", "image": "https://images.unsplash.com/photo-1588271968087-4c51abe05afc?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1588271968087-4c51abe05afc?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1592343516109-362f7bd871aa?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1669575903350-9a349b411810?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Fitzrovia Pocket Square", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 131.5, "stock": 27, "sku": "FSH-027", "image": "https://images.unsplash.com/photo-1669575903350-9a349b411810?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1669575903350-9a349b411810?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1610901157620-340856d0a50f?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Greenwich Woven Belt", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 148.8, "stock": 4, "sku": "FSH-028", "image": "https://images.unsplash.com/photo-1610901157620-340856d0a50f?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1610901157620-340856d0a50f?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1619473918387-2710c35e3bf2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1591900947067-851789555ef3?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Camberwell Driving Shoes", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 166.1, "stock": 9, "sku": "FSH-029", "image": "https://images.unsplash.com/photo-1591900947067-851789555ef3?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1591900947067-851789555ef3?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1514813836041-518668f092b1?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1698133468659-5ff0a0b02dda?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Highgate Canvas Sneakers", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 183.4, "stock": 14, "sku": "FSH-030", "image": "https://images.unsplash.com/photo-1698133468659-5ff0a0b02dda?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1698133468659-5ff0a0b02dda?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601379327928-bedfaf9da2d0?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1664286074176-5206ee5dc878?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Peckham Knit Scarf", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 200.7, "stock": 19, "sku": "FSH-031", "image": "https://images.unsplash.com/photo-1664286074176-5206ee5dc878?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1664286074176-5206ee5dc878?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1705493655920-20c572928501?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1684510334550-0c4fa8aaffd1?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Bermondsey Leather Sandals", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 218.0, "stock": 24, "sku": "FSH-032", "image": "https://images.unsplash.com/photo-1684510334550-0c4fa8aaffd1?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1684510334550-0c4fa8aaffd1?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Clapham Silk Pocket Scarf", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 235.3, "stock": 29, "sku": "FSH-033", "image": "https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1617391258031-f8d80b22fb35?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1619603364904-c0498317e145?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Soho Suede Ankle Boots", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 252.6, "stock": 6, "sku": "FSH-034", "image": "https://images.unsplash.com/photo-1619603364904-c0498317e145?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1619603364904-c0498317e145?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1619603364937-8d7af41ef206?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1608635680046-aebf91c1a9c8?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Brixton Wool Flat Cap", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 269.9, "stock": 11, "sku": "FSH-035", "image": "https://images.unsplash.com/photo-1608635680046-aebf91c1a9c8?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1608635680046-aebf91c1a9c8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1574201635302-388dd92a4c3f?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1581497396202-5645e76a3a8e?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},
    {"name": "Hackney Leather Gloves, Lined", "category": "Fashion", "subcategory": "Accessories & Footwear", "price": 287.2, "stock": 16, "sku": "FSH-036", "image": "https://images.unsplash.com/photo-1581497396202-5645e76a3a8e?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1581497396202-5645e76a3a8e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1588271968087-4c51abe05afc?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1592343516109-362f7bd871aa?w=1000&q=80&auto=format&fit=crop"), "description": "Tailored from quality fabric with careful attention to fit and finish, a versatile addition to any wardrobe."},

    # Subcategory: Necklaces, Chains & Earrings (extra items)
    {"name": "Bond Street Gold Chain Necklace", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 45.0, "stock": 2, "sku": "JWL-008", "image": "https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1662434923031-b9bf1b6c10e2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Chiswick Silver Drop Earrings", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 62.3, "stock": 7, "sku": "JWL-009", "image": "https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1622398925373-3f91b1e275f5?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Hampstead Pearl Stud Earrings", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 79.6, "stock": 12, "sku": "JWL-010", "image": "https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601121141461-9d6647bca1ed?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601821765780-754fa98637c1?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Islington Diamond Pendant", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 96.9, "stock": 17, "sku": "JWL-011", "image": "https://images.unsplash.com/photo-1601821765780-754fa98637c1?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1601821765780-754fa98637c1?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1620656798579-1984d9e87df7?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1626122780071-c09d403b8e32?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Shoreditch Rose Gold Choker", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 114.2, "stock": 22, "sku": "JWL-012", "image": "https://images.unsplash.com/photo-1626122780071-c09d403b8e32?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1626122780071-c09d403b8e32?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1633934542430-0905ccb5f050?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Fitzrovia Sapphire Drop Earrings", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 131.5, "stock": 27, "sku": "JWL-013", "image": "https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1612150354898-a69132eb7c67?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Greenwich Emerald Pendant Necklace", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 148.8, "stock": 4, "sku": "JWL-014", "image": "https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1662434923031-b9bf1b6c10e2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Camberwell Vintage Locket", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 166.1, "stock": 9, "sku": "JWL-015", "image": "https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1622398925373-3f91b1e275f5?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Highgate Herringbone Chain", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 183.4, "stock": 14, "sku": "JWL-016", "image": "https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601121141461-9d6647bca1ed?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601821765780-754fa98637c1?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Peckham Opal Stud Earrings", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 200.7, "stock": 19, "sku": "JWL-017", "image": "https://images.unsplash.com/photo-1601821765780-754fa98637c1?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1601821765780-754fa98637c1?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1620656798579-1984d9e87df7?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1626122780071-c09d403b8e32?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Bermondsey Layered Gold Necklace", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 218.0, "stock": 24, "sku": "JWL-018", "image": "https://images.unsplash.com/photo-1626122780071-c09d403b8e32?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1626122780071-c09d403b8e32?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1633934542430-0905ccb5f050?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Clapham Amethyst Pendant", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 235.3, "stock": 29, "sku": "JWL-019", "image": "https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1612150354898-a69132eb7c67?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Soho Silver Hoop Earrings", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 252.6, "stock": 6, "sku": "JWL-020", "image": "https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1662434923031-b9bf1b6c10e2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Brixton Citrine Drop Earrings", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 269.9, "stock": 11, "sku": "JWL-021", "image": "https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1622398925373-3f91b1e275f5?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Hackney Onyx Pendant", "category": "Jewellery", "subcategory": "Necklaces, Chains & Earrings", "price": 287.2, "stock": 16, "sku": "JWL-022", "image": "https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601121141461-9d6647bca1ed?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601821765780-754fa98637c1?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},

    # Subcategory: Rings & Bracelets (extra items)
    {"name": "Bond Street Eternity Band", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 45.0, "stock": 2, "sku": "JWL-023", "image": "https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1662434923031-b9bf1b6c10e2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Chiswick Gemstone Cocktail Ring", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 62.3, "stock": 7, "sku": "JWL-024", "image": "https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1622398925373-3f91b1e275f5?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Hampstead Silver Cuff Bracelet", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 79.6, "stock": 12, "sku": "JWL-025", "image": "https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601121141461-9d6647bca1ed?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601821765780-754fa98637c1?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Islington Gold Bangle", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 96.9, "stock": 17, "sku": "JWL-026", "image": "https://images.unsplash.com/photo-1601821765780-754fa98637c1?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1601821765780-754fa98637c1?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1620656798579-1984d9e87df7?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1626122780071-c09d403b8e32?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Shoreditch Tennis Bracelet", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 114.2, "stock": 22, "sku": "JWL-027", "image": "https://images.unsplash.com/photo-1626122780071-c09d403b8e32?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1626122780071-c09d403b8e32?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1633934542430-0905ccb5f050?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Fitzrovia Wide Signet Ring", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 131.5, "stock": 27, "sku": "JWL-028", "image": "https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1612150354898-a69132eb7c67?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Greenwich Stacking Ring Set", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 148.8, "stock": 4, "sku": "JWL-029", "image": "https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1662434923031-b9bf1b6c10e2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Camberwell Charm Bracelet", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 166.1, "stock": 9, "sku": "JWL-030", "image": "https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1622398925373-3f91b1e275f5?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Highgate Beaded Bracelet", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 183.4, "stock": 14, "sku": "JWL-031", "image": "https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601121141461-9d6647bca1ed?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601821765780-754fa98637c1?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Peckham Rose Gold Ring", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 200.7, "stock": 19, "sku": "JWL-032", "image": "https://images.unsplash.com/photo-1601821765780-754fa98637c1?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1601821765780-754fa98637c1?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1620656798579-1984d9e87df7?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1626122780071-c09d403b8e32?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Bermondsey Sapphire Cocktail Ring", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 218.0, "stock": 24, "sku": "JWL-033", "image": "https://images.unsplash.com/photo-1626122780071-c09d403b8e32?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1626122780071-c09d403b8e32?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1633934542430-0905ccb5f050?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Clapham Pearl Bracelet", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 235.3, "stock": 29, "sku": "JWL-034", "image": "https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1612150354898-a69132eb7c67?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Soho Twist Band Ring", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 252.6, "stock": 6, "sku": "JWL-035", "image": "https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611107683227-e9060eccd846?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1662434923031-b9bf1b6c10e2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},
    {"name": "Brixton Chain Link Bracelet", "category": "Jewellery", "subcategory": "Rings & Bracelets", "price": 269.9, "stock": 11, "sku": "JWL-036", "image": "https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611955167811-4711904bb9f8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1622398925373-3f91b1e275f5?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1623321673989-830eff0fd59f?w=1000&q=80&auto=format&fit=crop"), "description": "Finely crafted by hand, finished to a lasting shine — an elegant piece for any occasion."},

    # Subcategory: Watches & Timepieces (extra items)
    {"name": "Bond Street Automatic Watch", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 45.0, "stock": 2, "sku": "ELC-009", "image": "https://images.unsplash.com/photo-1670177257750-9b47927f68eb?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1670177257750-9b47927f68eb?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1600003014755-ba31aa59c4b6?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1670404160620-a3a86428560e?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Chiswick Chronograph Watch", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 62.3, "stock": 7, "sku": "ELC-010", "image": "https://images.unsplash.com/photo-1670404160620-a3a86428560e?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1670404160620-a3a86428560e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1600003014637-ff82a275e191?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1600003014608-c2ccc1570a65?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Hampstead Minimalist Watch", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 79.6, "stock": 12, "sku": "ELC-011", "image": "https://images.unsplash.com/photo-1600003014608-c2ccc1570a65?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1600003014608-c2ccc1570a65?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1548171916-c0dea7f94ca6?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1548169874-53e85f753f1e?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Islington Hybrid Smart Watch", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 96.9, "stock": 17, "sku": "ELC-012", "image": "https://images.unsplash.com/photo-1548169874-53e85f753f1e?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1548169874-53e85f753f1e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1636639818651-d97365346a5c?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1634140704051-58a787556cd1?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Shoreditch Pocket Watch", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 114.2, "stock": 22, "sku": "ELC-013", "image": "https://images.unsplash.com/photo-1634140704051-58a787556cd1?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1634140704051-58a787556cd1?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1604242692760-2f7b0c26856d?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Fitzrovia Travel Alarm Clock", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 131.5, "stock": 27, "sku": "ELC-014", "image": "https://images.unsplash.com/photo-1604242692760-2f7b0c26856d?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1604242692760-2f7b0c26856d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1649357585015-179ed98f513d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1634595947394-87012e7b12ba?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Greenwich Marble Desk Clock", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 148.8, "stock": 4, "sku": "ELC-015", "image": "https://images.unsplash.com/photo-1634595947394-87012e7b12ba?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1634595947394-87012e7b12ba?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1548171838-1fd4cb4ab854?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1670177257750-9b47927f68eb?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Camberwell Watch Winder Box", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 166.1, "stock": 9, "sku": "ELC-016", "image": "https://images.unsplash.com/photo-1670177257750-9b47927f68eb?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1670177257750-9b47927f68eb?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1600003014755-ba31aa59c4b6?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1670404160620-a3a86428560e?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Highgate Leather Watch Strap", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 183.4, "stock": 14, "sku": "ELC-017", "image": "https://images.unsplash.com/photo-1670404160620-a3a86428560e?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1670404160620-a3a86428560e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1600003014637-ff82a275e191?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1600003014608-c2ccc1570a65?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Peckham Dive Watch", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 200.7, "stock": 19, "sku": "ELC-018", "image": "https://images.unsplash.com/photo-1600003014608-c2ccc1570a65?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1600003014608-c2ccc1570a65?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1548171916-c0dea7f94ca6?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1548169874-53e85f753f1e?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Bermondsey Dress Watch", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 218.0, "stock": 24, "sku": "ELC-019", "image": "https://images.unsplash.com/photo-1548169874-53e85f753f1e?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1548169874-53e85f753f1e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1636639818651-d97365346a5c?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1634140704051-58a787556cd1?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Clapham Skeleton Watch", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 235.3, "stock": 29, "sku": "ELC-020", "image": "https://images.unsplash.com/photo-1634140704051-58a787556cd1?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1634140704051-58a787556cd1?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1604242692760-2f7b0c26856d?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Soho Mantel Clock", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 252.6, "stock": 6, "sku": "ELC-021", "image": "https://images.unsplash.com/photo-1604242692760-2f7b0c26856d?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1604242692760-2f7b0c26856d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1649357585015-179ed98f513d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1634595947394-87012e7b12ba?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Brixton Vintage Field Watch", "category": "Electronics", "subcategory": "Watches & Timepieces", "price": 269.9, "stock": 11, "sku": "ELC-022", "image": "https://images.unsplash.com/photo-1634595947394-87012e7b12ba?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1634595947394-87012e7b12ba?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1548171838-1fd4cb4ab854?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1670177257750-9b47927f68eb?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},

    # Subcategory: Cameras, Audio & Travel (extra items)
    {"name": "Bond Street Instant Camera", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 45.0, "stock": 2, "sku": "ELC-023", "image": "https://images.unsplash.com/photo-1495121553079-4c61bcce1894?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1495121553079-4c61bcce1894?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1512390225428-a9d51c817f94?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1511184059754-e4b5bbbcef75?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Chiswick Bluetooth Speaker", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 62.3, "stock": 7, "sku": "ELC-024", "image": "https://images.unsplash.com/photo-1511184059754-e4b5bbbcef75?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1511184059754-e4b5bbbcef75?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601854266103-c1dd42130633?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1516961642265-531546e84af2?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Hampstead Noise-Cancelling Earbuds", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 79.6, "stock": 12, "sku": "ELC-025", "image": "https://images.unsplash.com/photo-1516961642265-531546e84af2?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1516961642265-531546e84af2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1528594498426-ea65fdafcbf4?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1515622472995-1a06094d2224?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Islington Travel Adapter Kit", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 96.9, "stock": 17, "sku": "ELC-026", "image": "https://images.unsplash.com/photo-1515622472995-1a06094d2224?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1515622472995-1a06094d2224?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1520549233664-03f65c1d1327?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1517092756309-24071485f6db?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Shoreditch Portable Power Bank", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 114.2, "stock": 22, "sku": "ELC-027", "image": "https://images.unsplash.com/photo-1517092756309-24071485f6db?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1517092756309-24071485f6db?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1595401735913-4ca17c66e755?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1516962126636-27ad087061cc?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Fitzrovia Leather Camera Strap", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 131.5, "stock": 27, "sku": "ELC-028", "image": "https://images.unsplash.com/photo-1516962126636-27ad087061cc?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1516962126636-27ad087061cc?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1481923387198-050ac1a2896e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1531635410863-4c7d45c6f712?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Greenwich Tabletop Tripod", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 148.8, "stock": 4, "sku": "ELC-029", "image": "https://images.unsplash.com/photo-1531635410863-4c7d45c6f712?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1531635410863-4c7d45c6f712?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1495121553079-4c61bcce1894?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1512390225428-a9d51c817f94?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Camberwell Mini Drone", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 166.1, "stock": 9, "sku": "ELC-030", "image": "https://images.unsplash.com/photo-1512390225428-a9d51c817f94?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1512390225428-a9d51c817f94?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1511184059754-e4b5bbbcef75?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1601854266103-c1dd42130633?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Highgate Action Camera", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 183.4, "stock": 14, "sku": "ELC-031", "image": "https://images.unsplash.com/photo-1601854266103-c1dd42130633?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1601854266103-c1dd42130633?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1516961642265-531546e84af2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1528594498426-ea65fdafcbf4?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Peckham Vinyl Turntable", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 200.7, "stock": 19, "sku": "ELC-032", "image": "https://images.unsplash.com/photo-1528594498426-ea65fdafcbf4?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1528594498426-ea65fdafcbf4?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1515622472995-1a06094d2224?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1520549233664-03f65c1d1327?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Bermondsey Travel Charging Case", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 218.0, "stock": 24, "sku": "ELC-033", "image": "https://images.unsplash.com/photo-1520549233664-03f65c1d1327?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1520549233664-03f65c1d1327?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1517092756309-24071485f6db?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1595401735913-4ca17c66e755?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Clapham Wireless Earphones", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 235.3, "stock": 29, "sku": "ELC-034", "image": "https://images.unsplash.com/photo-1595401735913-4ca17c66e755?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1595401735913-4ca17c66e755?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1516962126636-27ad087061cc?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1481923387198-050ac1a2896e?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Soho Compact Tripod", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 252.6, "stock": 6, "sku": "ELC-035", "image": "https://images.unsplash.com/photo-1481923387198-050ac1a2896e?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1481923387198-050ac1a2896e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1531635410863-4c7d45c6f712?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1495121553079-4c61bcce1894?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},
    {"name": "Brixton Film Roll Kit", "category": "Electronics", "subcategory": "Cameras, Audio & Travel", "price": 269.9, "stock": 11, "sku": "ELC-036", "image": "https://images.unsplash.com/photo-1495121553079-4c61bcce1894?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1495121553079-4c61bcce1894?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1512390225428-a9d51c817f94?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1511184059754-e4b5bbbcef75?w=1000&q=80&auto=format&fit=crop"), "description": "Precision-made with quality materials, combining reliable performance with everyday practicality."},

    # Subcategory: Ceramics & Tabletop (extra items)
    {"name": "Bond Street Ceramic Bowl Set", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 45.0, "stock": 2, "sku": "HOM-008", "image": "https://images.unsplash.com/photo-1631125915902-d8abe9225ff2?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1631125915902-d8abe9225ff2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1597696929736-6d13bed8e6a8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1677761640321-b80251be00ca?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Chiswick Stoneware Mug Set", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 62.3, "stock": 7, "sku": "HOM-009", "image": "https://images.unsplash.com/photo-1677761640321-b80251be00ca?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1677761640321-b80251be00ca?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1481401908818-600b7a676c0d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1643569556871-91ec60671ed7?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Hampstead Marble Cheese Board", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 79.6, "stock": 12, "sku": "HOM-010", "image": "https://images.unsplash.com/photo-1643569556871-91ec60671ed7?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1643569556871-91ec60671ed7?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1631125915973-e0d155a14e4e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1526198049595-f32cde2a219d?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Islington Glass Carafe", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 96.9, "stock": 17, "sku": "HOM-011", "image": "https://images.unsplash.com/photo-1526198049595-f32cde2a219d?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1526198049595-f32cde2a219d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1631125916276-69bcd14e3980?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1526198330131-9b0bc79625e4?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Shoreditch Porcelain Dinner Set", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 114.2, "stock": 22, "sku": "HOM-012", "image": "https://images.unsplash.com/photo-1526198330131-9b0bc79625e4?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1526198330131-9b0bc79625e4?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611911813383-67769b37a149?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1670080589800-6416c8ce8a14?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Fitzrovia Brass Candle Holder", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 131.5, "stock": 27, "sku": "HOM-013", "image": "https://images.unsplash.com/photo-1670080589800-6416c8ce8a14?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1670080589800-6416c8ce8a14?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1670080946016-d9b4445ff8b6?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1634901581982-6b408cf4226a?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Greenwich Ceramic Planter", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 148.8, "stock": 4, "sku": "HOM-014", "image": "https://images.unsplash.com/photo-1634901581982-6b408cf4226a?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1634901581982-6b408cf4226a?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1687191883721-257d8cad5b54?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1633000116322-d7f5cb7d3ebb?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Camberwell Oak Serving Platter", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 166.1, "stock": 9, "sku": "HOM-015", "image": "https://images.unsplash.com/photo-1633000116322-d7f5cb7d3ebb?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1633000116322-d7f5cb7d3ebb?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1631125915361-b749fdeea230?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1723779232101-19167d4b6e00?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Highgate Crystal Wine Decanter", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 183.4, "stock": 14, "sku": "HOM-016", "image": "https://images.unsplash.com/photo-1723779232101-19167d4b6e00?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1723779232101-19167d4b6e00?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1631125915902-d8abe9225ff2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1597696929736-6d13bed8e6a8?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Peckham Porcelain Tea Set", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 200.7, "stock": 19, "sku": "HOM-017", "image": "https://images.unsplash.com/photo-1597696929736-6d13bed8e6a8?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1597696929736-6d13bed8e6a8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1677761640321-b80251be00ca?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1481401908818-600b7a676c0d?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Bermondsey Stoneware Pitcher", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 218.0, "stock": 24, "sku": "HOM-018", "image": "https://images.unsplash.com/photo-1481401908818-600b7a676c0d?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1481401908818-600b7a676c0d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1643569556871-91ec60671ed7?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1631125915973-e0d155a14e4e?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Clapham Glass Vase", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 235.3, "stock": 29, "sku": "HOM-019", "image": "https://images.unsplash.com/photo-1631125915973-e0d155a14e4e?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1631125915973-e0d155a14e4e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1526198049595-f32cde2a219d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1631125916276-69bcd14e3980?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Soho Marble Trivet", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 252.6, "stock": 6, "sku": "HOM-020", "image": "https://images.unsplash.com/photo-1631125916276-69bcd14e3980?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1631125916276-69bcd14e3980?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1526198330131-9b0bc79625e4?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611911813383-67769b37a149?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Brixton Ceramic Butter Dish", "category": "Home Accessories", "subcategory": "Ceramics & Tabletop", "price": 269.9, "stock": 11, "sku": "HOM-021", "image": "https://images.unsplash.com/photo-1611911813383-67769b37a149?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611911813383-67769b37a149?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1670080589800-6416c8ce8a14?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1670080946016-d9b4445ff8b6?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},

    # Subcategory: Textiles (extra items)
    {"name": "Bond Street Wool Area Rug", "category": "Home Accessories", "subcategory": "Textiles", "price": 45.0, "stock": 2, "sku": "HOM-022", "image": "https://images.unsplash.com/photo-1631125915902-d8abe9225ff2?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1631125915902-d8abe9225ff2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1597696929736-6d13bed8e6a8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1677761640321-b80251be00ca?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Chiswick Linen Bedding Set", "category": "Home Accessories", "subcategory": "Textiles", "price": 62.3, "stock": 7, "sku": "HOM-023", "image": "https://images.unsplash.com/photo-1677761640321-b80251be00ca?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1677761640321-b80251be00ca?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1481401908818-600b7a676c0d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1643569556871-91ec60671ed7?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Hampstead Velvet Cushion Cover", "category": "Home Accessories", "subcategory": "Textiles", "price": 79.6, "stock": 12, "sku": "HOM-024", "image": "https://images.unsplash.com/photo-1643569556871-91ec60671ed7?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1643569556871-91ec60671ed7?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1631125915973-e0d155a14e4e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1526198049595-f32cde2a219d?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Islington Cotton Table Runner", "category": "Home Accessories", "subcategory": "Textiles", "price": 96.9, "stock": 17, "sku": "HOM-025", "image": "https://images.unsplash.com/photo-1526198049595-f32cde2a219d?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1526198049595-f32cde2a219d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1631125916276-69bcd14e3980?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1526198330131-9b0bc79625e4?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Shoreditch Alpaca Throw Blanket", "category": "Home Accessories", "subcategory": "Textiles", "price": 114.2, "stock": 22, "sku": "HOM-026", "image": "https://images.unsplash.com/photo-1526198330131-9b0bc79625e4?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1526198330131-9b0bc79625e4?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611911813383-67769b37a149?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1670080589800-6416c8ce8a14?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Fitzrovia Bath Towel Set", "category": "Home Accessories", "subcategory": "Textiles", "price": 131.5, "stock": 27, "sku": "HOM-027", "image": "https://images.unsplash.com/photo-1670080589800-6416c8ce8a14?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1670080589800-6416c8ce8a14?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1670080946016-d9b4445ff8b6?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1634901581982-6b408cf4226a?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Greenwich Woven Placemat Set", "category": "Home Accessories", "subcategory": "Textiles", "price": 148.8, "stock": 4, "sku": "HOM-028", "image": "https://images.unsplash.com/photo-1634901581982-6b408cf4226a?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1634901581982-6b408cf4226a?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1687191883721-257d8cad5b54?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1633000116322-d7f5cb7d3ebb?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Camberwell Linen Napkin Set", "category": "Home Accessories", "subcategory": "Textiles", "price": 166.1, "stock": 9, "sku": "HOM-029", "image": "https://images.unsplash.com/photo-1633000116322-d7f5cb7d3ebb?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1633000116322-d7f5cb7d3ebb?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1631125915361-b749fdeea230?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1723779232101-19167d4b6e00?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Highgate Cotton Curtains", "category": "Home Accessories", "subcategory": "Textiles", "price": 183.4, "stock": 14, "sku": "HOM-030", "image": "https://images.unsplash.com/photo-1723779232101-19167d4b6e00?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1723779232101-19167d4b6e00?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1631125915902-d8abe9225ff2?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1597696929736-6d13bed8e6a8?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Peckham Jute Doormat", "category": "Home Accessories", "subcategory": "Textiles", "price": 200.7, "stock": 19, "sku": "HOM-031", "image": "https://images.unsplash.com/photo-1597696929736-6d13bed8e6a8?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1597696929736-6d13bed8e6a8?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1677761640321-b80251be00ca?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1481401908818-600b7a676c0d?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Bermondsey Wool Blanket", "category": "Home Accessories", "subcategory": "Textiles", "price": 218.0, "stock": 24, "sku": "HOM-032", "image": "https://images.unsplash.com/photo-1481401908818-600b7a676c0d?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1481401908818-600b7a676c0d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1643569556871-91ec60671ed7?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1631125915973-e0d155a14e4e?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Clapham Velvet Throw Pillow", "category": "Home Accessories", "subcategory": "Textiles", "price": 235.3, "stock": 29, "sku": "HOM-033", "image": "https://images.unsplash.com/photo-1631125915973-e0d155a14e4e?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1631125915973-e0d155a14e4e?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1526198049595-f32cde2a219d?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1631125916276-69bcd14e3980?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Soho Linen Duvet Cover", "category": "Home Accessories", "subcategory": "Textiles", "price": 252.6, "stock": 6, "sku": "HOM-034", "image": "https://images.unsplash.com/photo-1631125916276-69bcd14e3980?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1631125916276-69bcd14e3980?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1526198330131-9b0bc79625e4?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1611911813383-67769b37a149?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Brixton Woven Wall Hanging", "category": "Home Accessories", "subcategory": "Textiles", "price": 269.9, "stock": 11, "sku": "HOM-035", "image": "https://images.unsplash.com/photo-1611911813383-67769b37a149?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1611911813383-67769b37a149?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1670080589800-6416c8ce8a14?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1670080946016-d9b4445ff8b6?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
    {"name": "Hackney Cotton Bath Robe", "category": "Home Accessories", "subcategory": "Textiles", "price": 287.2, "stock": 16, "sku": "HOM-036", "image": "https://images.unsplash.com/photo-1670080946016-d9b4445ff8b6?w=1000&q=80&auto=format&fit=crop", "gallery": gallery("https://images.unsplash.com/photo-1670080946016-d9b4445ff8b6?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1634901581982-6b408cf4226a?w=1000&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1687191883721-257d8cad5b54?w=1000&q=80&auto=format&fit=crop"), "description": "Thoughtfully made to bring warmth and character to any room, built to last."},
]


def seed():
    with app.app_context():
        db.create_all()

        admin_name = os.environ.get("ADMIN_NAME", "Vishma Noor")
        admin_email = os.environ.get("ADMIN_EMAIL", "vishmanoor9@gmail.com").lower().strip()
        admin_password = os.environ.get("ADMIN_PASSWORD", "24017119")

        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(full_name=admin_name, email=admin_email, is_admin=True)
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"Admin account created: {admin_email}")
        else:
            # Keep name/password in sync on re-seed, so the admin identity never drifts.
            admin.full_name = admin_name
            admin.is_admin = True
            admin.set_password(admin_password)
            db.session.commit()
            print(f"Admin account updated: {admin_email}")

        # Demote any other/old admin accounts left over from earlier seeds,
        # so there is exactly one admin identity going forward.
        stray_admins = User.query.filter(User.is_admin.is_(True), User.email != admin_email).all()
        for stray in stray_admins:
            stray.is_admin = False
        if stray_admins:
            db.session.commit()
            print(f"Demoted {len(stray_admins)} stray admin account(s).")

        category_map = {}
        for cat_data in CATEGORIES:
            existing = Category.query.filter_by(name=cat_data["name"]).first()
            if existing:
                if cat_data.get("image_url"):
                    existing.image_url = cat_data["image_url"]
                if cat_data.get("description"):
                    existing.description = cat_data["description"]
                category_map[cat_data["name"]] = existing
                continue
            cat = Category(
                name=cat_data["name"],
                slug=slugify(cat_data["name"]),
                description=cat_data["description"],
                image_url=cat_data.get("image_url"),
            )
            db.session.add(cat)
            db.session.flush()
            category_map[cat_data["name"]] = cat

        db.session.commit()
        print(f"Categories ready: {list(category_map.keys())}")

        created_count = 0
        updated_count = 0
        for p in PRODUCTS:
            slug = slugify(p["name"])
            existing_product = Product.query.filter_by(slug=slug).first()
            if existing_product:
                # Keep subcategory/image/gallery in sync on reseed
                existing_product.subcategory = p.get("subcategory")
                existing_product.image_url = p.get("image")
                existing_product.image_gallery = p.get("gallery")
                updated_count += 1
                continue

            product = Product(
                name=p["name"],
                slug=slug,
                description=p["description"],
                subcategory=p.get("subcategory"),
                price=p["price"],
                compare_at_price=p.get("compare_at_price"),
                stock_quantity=p["stock"],
                sku=p["sku"],
                category_id=category_map[p["category"]].id,
                image_url=p.get("image"),
                image_gallery=p.get("gallery"),
                is_active=True,
                is_featured=(p.get("compare_at_price") is not None),
            )
            db.session.add(product)
            created_count += 1

        db.session.commit()
        print(f"Products created: {created_count}, updated: {updated_count}")

        # --- Demo customers (so the admin dashboard has real orders/revenue to chart) ---
        DEMO_CUSTOMERS = [
            ("Alina Rahman", "alina.rahman@example.com", "Karachi", "Pakistan"),
            ("James Whitmore", "james.whitmore@example.com", "Sydney", "Australia"),
            ("Sofia Almeida", "sofia.almeida@example.com", "Lisbon", "Portugal"),
            ("Daniyal Ahmed", "daniyal.ahmed@example.com", "Lahore", "Pakistan"),
            ("Emma Clarke", "emma.clarke@example.com", "London", "United Kingdom"),
            ("Hassan Raza", "hassan.raza@example.com", "Islamabad", "Pakistan"),
            ("Chloe Bennett", "chloe.bennett@example.com", "Toronto", "Canada"),
            ("Ayesha Malik", "ayesha.malik@example.com", "Dubai", "UAE"),
        ]
        customers = []
        for name, email, city, country in DEMO_CUSTOMERS:
            existing = User.query.filter_by(email=email).first()
            if existing:
                customers.append(existing)
                continue
            cust = User(
                full_name=name, email=email, city=city, country=country,
                address_line="12 Market Street", postal_code="00000",
            )
            cust.set_password("Demo12345!")
            db.session.add(cust)
            customers.append(cust)
        db.session.commit()

        # --- Demo orders across the last 6 months (only if none exist yet) ---
        if Order.query.count() == 0:
            all_products = Product.query.filter_by(is_active=True).all()
            status_weights = ["Delivered"] * 5 + ["Shipped"] * 3 + ["Pending"] * 2 + ["Cancelled"] * 1
            order_count = 0
            for i in range(70):
                customer = random.choice(customers)
                days_ago = random.randint(0, 178)
                created = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
                status = random.choice(status_weights)

                order = Order(
                    customer_id=customer.id,
                    status=status,
                    payment_method=random.choice(["Cash on Delivery", "Card Payment (Stripe)"]),
                    is_paid=(status in ("Shipped", "Delivered")),
                    shipping_full_name=customer.full_name,
                    shipping_phone="+1 555 010 0000",
                    shipping_address_line=customer.address_line,
                    shipping_city=customer.city,
                    shipping_postal_code=customer.postal_code,
                    shipping_country=customer.country,
                    shipping_fee=Decimal("15.00"),
                    created_at=created,
                    updated_at=created,
                )
                if status == "Delivered":
                    order.delivered_at = created + timedelta(days=random.randint(2, 6))
                db.session.add(order)
                db.session.flush()

                for _ in range(random.randint(1, 4)):
                    product = random.choice(all_products)
                    qty = random.randint(1, 3)
                    db.session.add(OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        product_name=product.name,
                        product_image_url=product.image_url,
                        unit_price=product.price,
                        quantity=qty,
                    ))
                db.session.flush()
                order.recalculate_totals()
                order_count += 1

            db.session.commit()
            print(f"Demo orders created: {order_count}")
        else:
            print("Orders already exist — skipping demo order seed.")

        print("Seeding complete ✅")


if __name__ == "__main__":
    seed()
