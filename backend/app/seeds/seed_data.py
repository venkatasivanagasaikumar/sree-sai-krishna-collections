from datetime import datetime, timezone, timedelta
from app.database import get_db, db_manager
from app.core.security import get_password_hash
from app.core.permissions import Role
from app.core.logging import logger

def run_seed():
    db = get_db()
    logger.info("Initializing database seeds...")

    # 1. Seed Users (Super Admin, Staff, Customer)
    users_to_seed = [
        {
            "email": "admin@sskcollections.com",
            "full_name": "Sree Sai Krishna Admin",
            "phone": "+91 98480 22338",
            "role": Role.SUPER_ADMIN,
            "hashed_password": get_password_hash("Admin@SSK2026!"),
            "addresses": [
                {
                    "id": "addr-ssk-hq",
                    "name": "SSK Flagship Center",
                    "phone": "+91 98480 22338",
                    "address_line1": "Shop #12, Sri Krishna Temple Street",
                    "address_line2": "Near Clock Tower",
                    "landmark": "Temple Square",
                    "city": "Secunderabad",
                    "state": "Telangana",
                    "pincode": "500003",
                    "is_default": True,
                    "type": "Work"
                }
            ],
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "email": "orders@sskcollections.com",
            "full_name": "Ravi Teja (Order Manager)",
            "phone": "+91 98480 22339",
            "role": Role.ORDER_MANAGER,
            "hashed_password": get_password_hash("Staff@SSK2026!"),
            "addresses": [],
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "email": "inventory@sskcollections.com",
            "full_name": "Sunita Rao (Inventory Manager)",
            "phone": "+91 98480 22340",
            "role": Role.INVENTORY_MANAGER,
            "hashed_password": get_password_hash("Staff@SSK2026!"),
            "addresses": [],
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "email": "priya.sharma@example.com",
            "full_name": "Priya Sharma",
            "phone": "+91 98765 43210",
            "role": Role.CUSTOMER,
            "hashed_password": get_password_hash("Customer@123"),
            "addresses": [
                {
                    "id": "addr-priya-home",
                    "name": "Priya Sharma",
                    "phone": "+91 98765 43210",
                    "address_line1": "Flat 402, Sai Balaji Residency",
                    "address_line2": "Road No. 3, Banjara Hills",
                    "landmark": "Opposite KBR Park",
                    "city": "Hyderabad",
                    "state": "Telangana",
                    "pincode": "500034",
                    "is_default": True,
                    "type": "Home"
                }
            ],
            "is_active": True,
            "created_at": datetime.now(timezone.utc) - timedelta(days=20)
        }
    ]

    for u in users_to_seed:
        db.users.update_one(
            {"email": u["email"]},
            {"$set": u},
            upsert=True
        )

    # 2. Seed Categories
    categories = [
        {
            "name": "1-Gram Gold Jewellery",
            "slug": "1-gram-gold-jewellery",
            "parent_category": "Jewellery",
            "description": "Premium micro gold-plated traditional jewellery with authentic south-Indian craftsmanship.",
            "image_url": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=600&q=80",
            "display_order": 1,
            "is_active": True
        },
        {
            "name": "Earrings & Jhumkas",
            "slug": "earrings-and-jhumkas",
            "parent_category": "Jewellery",
            "description": "Antique temple jhumkas, chandelier drops, studs, and pearl danglers.",
            "image_url": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=600&q=80",
            "display_order": 2,
            "is_active": True
        },
        {
            "name": "Necklaces & Chains",
            "slug": "necklaces-and-chains",
            "parent_category": "Jewellery",
            "description": "Royal chokers, layered haaram necklaces, and elegant daily wear chains.",
            "image_url": "https://images.unsplash.com/photo-1611591475870-be7c427db9fa?auto=format&fit=crop&w=600&q=80",
            "display_order": 3,
            "is_active": True
        },
        {
            "name": "Bangles & Bracelets",
            "slug": "bangles-and-bracelets",
            "parent_category": "Jewellery",
            "description": "Kada bangles, temple design openable bracelets, and festive sets.",
            "image_url": "https://images.unsplash.com/photo-1611591475878-be7c427db9fb?auto=format&fit=crop&w=600&q=80",
            "display_order": 4,
            "is_active": True
        },
        {
            "name": "Temple Jewellery Sets",
            "slug": "temple-jewellery-sets",
            "parent_category": "Jewellery",
            "description": "Complete bridal sets with Lakshmi motif, matte gold finish, and kemp stones.",
            "image_url": "https://images.unsplash.com/photo-1601121141461-9d6647bca1ed?auto=format&fit=crop&w=600&q=80",
            "display_order": 5,
            "is_active": True
        },
        {
            "name": "Hair Clips & Pins",
            "slug": "hair-clips-and-pins",
            "parent_category": "Hair Accessories",
            "description": "Korean pearl hair clips, metal bobby pins, and stone-studded hair accessories.",
            "image_url": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=600&q=80",
            "display_order": 6,
            "is_active": True
        },
        {
            "name": "Claw Clips",
            "slug": "claw-clips",
            "parent_category": "Hair Accessories",
            "description": "Matte pastel claw clips, oversized French hair claws, and metallic clips.",
            "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=600&q=80",
            "display_order": 7,
            "is_active": True
        },
        {
            "name": "Scrunchies & Hair Bands",
            "slug": "scrunchies-and-hair-bands",
            "parent_category": "Hair Accessories",
            "description": "Mulberry silk scrunchies, organza hair ties, and velvet padded headbands.",
            "image_url": "https://images.unsplash.com/photo-1607083206869-4c7672e72a8a?auto=format&fit=crop&w=600&q=80",
            "display_order": 8,
            "is_active": True
        },
        {
            "name": "Traditional Accessories",
            "slug": "traditional-accessories",
            "parent_category": "Women's Accessories",
            "description": "Bridal waist belts (Vaddanam), payal / anklets, and ornate brooch pins.",
            "image_url": "https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=600&q=80",
            "display_order": 9,
            "is_active": True
        }
    ]

    for cat in categories:
        db.categories.update_one(
            {"slug": cat["slug"]},
            {"$set": cat},
            upsert=True
        )

    # 3. Seed Products
    products = [
        {
            "sku": "SSK-JWL-101",
            "name": "Royal Lakshmi Matte Finish 1-Gram Gold Choker Set",
            "category": "1-Gram Gold Jewellery",
            "subcategory": "Necklaces & Chains",
            "description": "Exquisite handcrafted South Indian choker necklace featuring Goddess Lakshmi motifs, fine ruby and emerald kemp stone embellishments, and dangling South Sea pearls. Finished with durable 1-gram gold-finish electroplating.",
            "short_description": "Traditional Lakshmi motif choker with earrings in high-grade 1-gram gold finish.",
            "mrp": 3499.0,
            "price": 1899.0,
            "stock": 28,
            "low_stock_threshold": 5,
            "images": [
                "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1601121141461-9d6647bca1ed?auto=format&fit=crop&w=800&q=80"
            ],
            "materials_and_finish": "High-durability brass copper alloy with 24k micron 1-gram gold-tone electroplate.",
            "jewelry_type": "1-Gram Gold Finish",
            "genuine_gold_disclaimer": "This is a premium imitation 1-gram gold-finish fashion piece and contains no precious gold metal or BIS hallmark certification.",
            "colors": ["Gold with Ruby Red", "Gold with Green Kemp"],
            "sizes": ["Free Size (Adjustable Dori)"],
            "variants": [
                {
                    "variant_id": "v101-ruby",
                    "name": "Ruby Red Accents",
                    "sku": "SSK-JWL-101-RUBY",
                    "price": 1899.0,
                    "mrp": 3499.0,
                    "stock": 16,
                    "color": "Ruby Red",
                    "size": "Free Size"
                },
                {
                    "variant_id": "v101-green",
                    "name": "Emerald Green Accents",
                    "sku": "SSK-JWL-101-GRN",
                    "price": 1899.0,
                    "mrp": 3499.0,
                    "stock": 12,
                    "color": "Emerald Green",
                    "size": "Free Size"
                }
            ],
            "care_instructions": "Store in the supplied air-tight velvet pouch. Avoid direct contact with deodorant, perfumes, soap water, and sweat.",
            "shipping_estimate_days": "2-4 Business Days",
            "return_eligible": True,
            "return_window_days": 7,
            "status": "active",
            "tags": ["1-gram gold", "choker", "temple", "bridal", "lakshmi", "bestseller"],
            "is_featured": True,
            "is_bestseller": True,
            "is_trending": True,
            "rating": 4.9,
            "rating_count": 34,
            "sales_count": 89,
            "weight_grams": 75.0,
            "created_at": datetime.now(timezone.utc) - timedelta(days=25)
        },
        {
            "sku": "SSK-JWL-102",
            "name": "Heritage Peacock Filigree Antique Jhumkas",
            "category": "Earrings & Jhumkas",
            "subcategory": "Earrings & Jhumkas",
            "description": "Grand two-tier temple jhumkas inspired by regal royal court treasures. Adorned with delicate peacock carvings, micro pearls, and lightweight hollow dome craft for comfortable all-day wear.",
            "short_description": "Antique gold finish lightweight heritage peacock dome jhumkas.",
            "mrp": 1599.0,
            "price": 799.0,
            "stock": 45,
            "low_stock_threshold": 8,
            "images": [
                "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1630019852942-f89202989a59?auto=format&fit=crop&w=800&q=80"
            ],
            "materials_and_finish": "Skin-friendly lead-free brass with antique gold matte polish.",
            "jewelry_type": "Imitation Jewellery",
            "genuine_gold_disclaimer": "This is high-finish fashion costume jewellery and contains no genuine precious metals.",
            "colors": ["Antique Gold", "Dual Tone"],
            "sizes": ["Standard (Length 6.5 cm)"],
            "variants": [],
            "care_instructions": "Wipe gently with a soft cotton cloth after wearing before storing.",
            "shipping_estimate_days": "2-3 Business Days",
            "return_eligible": True,
            "return_window_days": 7,
            "status": "active",
            "tags": ["jhumka", "peacock", "antique", "earrings", "temple"],
            "is_featured": True,
            "is_bestseller": True,
            "is_trending": False,
            "rating": 4.8,
            "rating_count": 52,
            "sales_count": 142,
            "weight_grams": 28.0,
            "created_at": datetime.now(timezone.utc) - timedelta(days=18)
        },
        {
            "sku": "SSK-JWL-103",
            "name": "Classic Micro-Plated Gold Kada Bangles (Set of 2)",
            "category": "Bangles & Bracelets",
            "subcategory": "Bangles & Bracelets",
            "description": "Stunning pair of screw-openable kada bangles finished with a radiant 1-gram gold look. Subtle floral engraving provides timeless sophistication for weddings, festivals, and pujas.",
            "short_description": "Set of 2 screw-openable floral kada bangles with 1-gram gold tone.",
            "mrp": 2199.0,
            "price": 1199.0,
            "stock": 19,
            "low_stock_threshold": 4,
            "images": [
                "https://images.unsplash.com/photo-1611591475878-be7c427db9fb?auto=format&fit=crop&w=800&q=80"
            ],
            "materials_and_finish": "Non-tarnish brass core with double-coated micro gold plating.",
            "jewelry_type": "1-Gram Gold Finish",
            "genuine_gold_disclaimer": "Fashion imitation jewellery item without real gold bullion content.",
            "colors": ["Radiant Gold"],
            "sizes": ["Size 2.4", "Size 2.6", "Size 2.8"],
            "variants": [
                {
                    "variant_id": "v103-24",
                    "name": "Size 2.4",
                    "sku": "SSK-JWL-103-24",
                    "price": 1199.0,
                    "mrp": 2199.0,
                    "stock": 6,
                    "size": "2.4"
                },
                {
                    "variant_id": "v103-26",
                    "name": "Size 2.6",
                    "sku": "SSK-JWL-103-26",
                    "price": 1199.0,
                    "mrp": 2199.0,
                    "stock": 8,
                    "size": "2.6"
                },
                {
                    "variant_id": "v103-28",
                    "name": "Size 2.8",
                    "sku": "SSK-JWL-103-28",
                    "price": 1199.0,
                    "mrp": 2199.0,
                    "stock": 5,
                    "size": "2.8"
                }
            ],
            "care_instructions": "Keep away from perfumes and hand sanitizers. Do not immerse in water.",
            "shipping_estimate_days": "2-4 Business Days",
            "return_eligible": True,
            "return_window_days": 7,
            "status": "active",
            "tags": ["bangles", "kada", "gold plated", "wedding"],
            "is_featured": False,
            "is_bestseller": True,
            "is_trending": True,
            "rating": 4.7,
            "rating_count": 21,
            "sales_count": 64,
            "weight_grams": 45.0,
            "created_at": datetime.now(timezone.utc) - timedelta(days=12)
        },
        {
            "sku": "SSK-JWL-104",
            "name": "Navratna Multistrand Bridal Haar & Pendant Set",
            "category": "1-Gram Gold Jewellery",
            "subcategory": "Necklaces & Chains",
            "description": "Grand 9-gem replica Navratna long necklace (Haaram) with detailed gold filigree mesh beads and matching stud earrings. Ideal centerpiece for bridal sarees and festive lehengas.",
            "short_description": "Grand multi-stone Navratna long haaram with matching earrings.",
            "mrp": 4999.0,
            "price": 2799.0,
            "stock": 9,
            "low_stock_threshold": 3,
            "images": [
                "https://images.unsplash.com/photo-1611591475870-be7c427db9fa?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1601121141461-9d6647bca1ed?auto=format&fit=crop&w=800&q=80"
            ],
            "materials_and_finish": "Copper brass alloy with micro gold rhodium coating and synthetic faceted navratna stones.",
            "jewelry_type": "1-Gram Gold Finish",
            "genuine_gold_disclaimer": "This is premium synthetic/fashion imitation jewellery with gold finish.",
            "colors": ["Multi-Color Navratna"],
            "sizes": ["Free Size"],
            "variants": [],
            "care_instructions": "Store in velvet lined box. Polish gently with a dry lint-free cloth.",
            "shipping_estimate_days": "3-5 Business Days",
            "return_eligible": True,
            "return_window_days": 7,
            "status": "active",
            "tags": ["navratna", "haaram", "bridal", "long necklace"],
            "is_featured": True,
            "is_bestseller": False,
            "is_trending": True,
            "rating": 4.9,
            "rating_count": 18,
            "sales_count": 39,
            "weight_grams": 95.0,
            "created_at": datetime.now(timezone.utc) - timedelta(days=10)
        },
        {
            "sku": "SSK-HAIR-201",
            "name": "Luxury French Matte Pastel Hair Claw Clip (Pack of 3)",
            "category": "Claw Clips",
            "subcategory": "Claw Clips",
            "description": "Set of 3 heavy-duty non-slip French claw clips in stylish muted tones (Navy Blue, Cream White, and Blush Rose). Engineered with durable rust-free steel springs to firmly hold thick and fine hair comfortably.",
            "short_description": "Pack of 3 aesthetic matte finish sturdy claw clips.",
            "mrp": 699.0,
            "price": 349.0,
            "stock": 65,
            "low_stock_threshold": 10,
            "images": [
                "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=800&q=80"
            ],
            "materials_and_finish": "Shatterproof acrylic resin with soft rubberized matte coating.",
            "jewelry_type": "Hair Accessory",
            "genuine_gold_disclaimer": "Accessory product.",
            "colors": ["Pastel Trio (Navy, Cream, Blush)"],
            "sizes": ["Medium (10.5 cm)"],
            "variants": [],
            "care_instructions": "Clean with damp cloth. Store dry.",
            "shipping_estimate_days": "2-3 Business Days",
            "return_eligible": True,
            "return_window_days": 7,
            "status": "active",
            "tags": ["claw clip", "hair accessory", "matte", "korean fashion"],
            "is_featured": False,
            "is_bestseller": True,
            "is_trending": True,
            "rating": 4.8,
            "rating_count": 68,
            "sales_count": 210,
            "weight_grams": 60.0,
            "created_at": datetime.now(timezone.utc) - timedelta(days=30)
        },
        {
            "sku": "SSK-HAIR-202",
            "name": "Pure Mulberry Silk Hair Scrunchies (Pack of 4)",
            "category": "Scrunchies & Hair Bands",
            "subcategory": "Scrunchies & Hair Bands",
            "description": "Zero-frizz, anti-breakage 100% grade 6A silk hair ties. Protects your hair follicles from split ends and crease lines while adding understated elegance to your wrist or ponytail.",
            "short_description": "Pack of 4 pure silk scrunchies in Royal Navy, Champagne Gold, Pearl White & Rose.",
            "mrp": 999.0,
            "price": 549.0,
            "stock": 38,
            "low_stock_threshold": 8,
            "images": [
                "https://images.unsplash.com/photo-1607083206869-4c7672e72a8a?auto=format&fit=crop&w=800&q=80"
            ],
            "materials_and_finish": "100% Mulberry Silk with flexible high-rebound elastic.",
            "jewelry_type": "Hair Accessory",
            "genuine_gold_disclaimer": "Hair accessory product.",
            "colors": ["Royal Navy & Gold Palette"],
            "sizes": ["Classic Medium"],
            "variants": [],
            "care_instructions": "Hand wash with cold water and mild silk shampoo. Air dry in shade.",
            "shipping_estimate_days": "2-3 Business Days",
            "return_eligible": True,
            "return_window_days": 7,
            "status": "active",
            "tags": ["scrunchies", "silk", "hair care", "accessories"],
            "is_featured": True,
            "is_bestseller": False,
            "is_trending": True,
            "rating": 4.9,
            "rating_count": 41,
            "sales_count": 135,
            "weight_grams": 40.0,
            "created_at": datetime.now(timezone.utc) - timedelta(days=22)
        },
        {
            "sku": "SSK-ACC-301",
            "name": "Traditional Temple Kundan Bridal Waist Belt (Vaddanam)",
            "category": "Traditional Accessories",
            "subcategory": "Traditional Accessories",
            "description": "Royal south-Indian bridal Kamarbandh / Vaddanam featuring embossed Peacock & Lakshmi carving with hanging gold bead ghungroos. Adjustable chain link fits waist sizes 26 to 40 inches.",
            "short_description": "Antique gold finish bridal waistbelt (Vaddanam) with kundan work.",
            "mrp": 2999.0,
            "price": 1499.0,
            "stock": 14,
            "low_stock_threshold": 4,
            "images": [
                "https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=800&q=80"
            ],
            "materials_and_finish": "Sturdy zinc brass alloy with matte 1-gram gold tone and synthetic kundan stones.",
            "jewelry_type": "Imitation Jewellery",
            "genuine_gold_disclaimer": "This is traditional bridal imitation jewellery and contains no genuine gold.",
            "colors": ["Antique Matte Gold"],
            "sizes": ["Adjustable (26 to 40 inches)"],
            "variants": [],
            "care_instructions": "Keep wrapped in plastic or soft cloth when not in use.",
            "shipping_estimate_days": "2-5 Business Days",
            "return_eligible": True,
            "return_window_days": 7,
            "status": "active",
            "tags": ["vaddanam", "waistbelt", "kamarbandh", "bridal", "traditional"],
            "is_featured": True,
            "is_bestseller": True,
            "is_trending": False,
            "rating": 4.8,
            "rating_count": 19,
            "sales_count": 48,
            "weight_grams": 120.0,
            "created_at": datetime.now(timezone.utc) - timedelta(days=15)
        },
        {
            "sku": "SSK-HAIR-203",
            "name": "Handmade Pearl & Crystal Bridal Hair Pins (Set of 6)",
            "category": "Hair Clips & Pins",
            "subcategory": "Hair Clips & Pins",
            "description": "Handmade floral hair pins woven with silver and gold-tone copper wire, faux South Sea pearls, and light-catching Austrian crystals. Flexible branches can be styled into wedding buns, braids, or half-up hairstyles.",
            "short_description": "Set of 6 flexible pearl and crystal wedding hair pins.",
            "mrp": 899.0,
            "price": 449.0,
            "stock": 3, # Low stock demo!
            "low_stock_threshold": 5,
            "images": [
                "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=800&q=80"
            ],
            "materials_and_finish": "Pliable copper wire with acrylic pearls and crystal glass beads.",
            "jewelry_type": "Hair Accessory",
            "genuine_gold_disclaimer": "Hair accessory product.",
            "colors": ["Pearl & Gold"],
            "sizes": ["Free Size (Set of 6)"],
            "variants": [],
            "care_instructions": "Do not spray hairspray directly on the pins.",
            "shipping_estimate_days": "2-3 Business Days",
            "return_eligible": True,
            "return_window_days": 7,
            "status": "active",
            "tags": ["hair pin", "bridal hair", "pearl", "wedding"],
            "is_featured": False,
            "is_bestseller": False,
            "is_trending": True,
            "rating": 4.7,
            "rating_count": 15,
            "sales_count": 32,
            "weight_grams": 25.0,
            "created_at": datetime.now(timezone.utc) - timedelta(days=8)
        }
    ]

    for p in products:
        # Calculate discount
        mrp = p.get("mrp", p["price"])
        p["discount_percent"] = round(((mrp - p["price"]) / mrp) * 100) if mrp > p["price"] else 0
        p["discount_amount"] = round(mrp - p["price"], 2)
        p["updated_at"] = datetime.now(timezone.utc)
        
        db.products.update_one(
            {"sku": p["sku"]},
            {"$set": p},
            upsert=True
        )

    # 4. Seed Coupons
    coupons = [
        {
            "code": "SSKFIRST10",
            "description": "10% Instant Discount on your first SSK collection purchase",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "min_order_value": 499.0,
            "max_discount_amount": 300.0,
            "usage_limit_total": 1000,
            "usage_limit_per_user": 1,
            "times_used": 14,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "code": "FESTIVE250",
            "description": "Flat ₹250 Discount on festive orders above ₹1,499",
            "discount_type": "fixed",
            "discount_value": 250.0,
            "min_order_value": 1499.0,
            "max_discount_amount": 250.0,
            "usage_limit_total": 500,
            "usage_limit_per_user": 2,
            "times_used": 8,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "code": "ROYALGOLD",
            "description": "15% OFF on exclusive 1-Gram Gold Collection",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "min_order_value": 1999.0,
            "max_discount_amount": 600.0,
            "usage_limit_total": 200,
            "usage_limit_per_user": 1,
            "times_used": 3,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
    ]

    for c in coupons:
        db.coupons.update_one(
            {"code": c["code"]},
            {"$set": c},
            upsert=True
        )

    # 5. Seed Sample Orders with Timeline (for realistic Meesho panel & customer tracking)
    customer_user = db.users.find_one({"email": "priya.sharma@example.com"})
    customer_id = str(customer_user["_id"]) if customer_user else "cust-1"

    sample_orders = [
        {
            "order_id": "SSK-20261025-8831",
            "user_id": customer_id,
            "customer_name": "Priya Sharma",
            "customer_email": "priya.sharma@example.com",
            "customer_phone": "+91 98765 43210",
            "items": [
                {
                    "product_id": "SSK-JWL-101",
                    "variant_id": "v101-ruby",
                    "name": "Royal Lakshmi Matte Finish 1-Gram Gold Choker Set",
                    "sku": "SSK-JWL-101-RUBY",
                    "image": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=800&q=80",
                    "unit_price": 1899.0,
                    "mrp": 3499.0,
                    "quantity": 1,
                    "total_price": 1899.0
                }
            ],
            "subtotal": 1899.0,
            "discount_amount": 189.9,
            "coupon_code": "SSKFIRST10",
            "shipping_fee": 0.0,
            "final_amount": 1709.1,
            "currency": "INR",
            "shipping_address": {
                "name": "Priya Sharma",
                "phone": "+91 98765 43210",
                "address_line1": "Flat 402, Sai Balaji Residency",
                "address_line2": "Road No. 3, Banjara Hills",
                "landmark": "Opposite KBR Park",
                "city": "Hyderabad",
                "state": "Telangana",
                "pincode": "500034",
                "is_default": True,
                "type": "Home"
            },
            "payment_method": "Razorpay",
            "payment_status": "PAID",
            "order_status": "DELIVERED",
            "fulfilment_status": "DELIVERED",
            "carrier_name": "Delhivery Express",
            "tracking_number": "DEL-SSK-99218274",
            "timeline": [
                {
                    "status": "ORDER_PLACED",
                    "message": "Order SSK-20261025-8831 placed successfully",
                    "timestamp": datetime.now(timezone.utc) - timedelta(days=4),
                    "performed_by": "Priya Sharma"
                },
                {
                    "status": "PAYMENT_CONFIRMED",
                    "message": "Payment of ₹1709.10 confirmed via Razorpay (pay_Rzp9931)",
                    "timestamp": datetime.now(timezone.utc) - timedelta(days=4, hours=1),
                    "performed_by": "Razorpay Gateway"
                },
                {
                    "status": "PACKED",
                    "message": "Items quality-inspected and sealed in tamper-proof bubble container",
                    "timestamp": datetime.now(timezone.utc) - timedelta(days=3),
                    "performed_by": "Sunita Rao (Inventory)"
                },
                {
                    "status": "SHIPPED",
                    "message": "Order handed over to Delhivery Express. AWB: DEL-SSK-99218274",
                    "timestamp": datetime.now(timezone.utc) - timedelta(days=2),
                    "performed_by": "Ravi Teja (Orders)"
                },
                {
                    "status": "DELIVERED",
                    "message": "Package delivered successfully to customer at Banjara Hills, Hyderabad.",
                    "timestamp": datetime.now(timezone.utc) - timedelta(days=1),
                    "performed_by": "Delhivery Courier Partner"
                }
            ],
            "created_at": datetime.now(timezone.utc) - timedelta(days=4),
            "updated_at": datetime.now(timezone.utc) - timedelta(days=1)
        },
        {
            "order_id": "SSK-20261028-4412",
            "user_id": customer_id,
            "customer_name": "Priya Sharma",
            "customer_email": "priya.sharma@example.com",
            "customer_phone": "+91 98765 43210",
            "items": [
                {
                    "product_id": "SSK-HAIR-201",
                    "variant_id": None,
                    "name": "Luxury French Matte Pastel Hair Claw Clip (Pack of 3)",
                    "sku": "SSK-HAIR-201",
                    "image": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=800&q=80",
                    "unit_price": 349.0,
                    "mrp": 699.0,
                    "quantity": 2,
                    "total_price": 698.0
                },
                {
                    "product_id": "SSK-JWL-102",
                    "variant_id": None,
                    "name": "Heritage Peacock Filigree Antique Jhumkas",
                    "sku": "SSK-JWL-102",
                    "image": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=800&q=80",
                    "unit_price": 799.0,
                    "mrp": 1599.0,
                    "quantity": 1,
                    "total_price": 799.0
                }
            ],
            "subtotal": 1497.0,
            "discount_amount": 250.0,
            "coupon_code": "FESTIVE250",
            "shipping_fee": 0.0,
            "final_amount": 1247.0,
            "currency": "INR",
            "shipping_address": {
                "name": "Priya Sharma",
                "phone": "+91 98765 43210",
                "address_line1": "Flat 402, Sai Balaji Residency",
                "address_line2": "Road No. 3, Banjara Hills",
                "landmark": "Opposite KBR Park",
                "city": "Hyderabad",
                "state": "Telangana",
                "pincode": "500034",
                "is_default": True,
                "type": "Home"
            },
            "payment_method": "COD",
            "payment_status": "PENDING_COD",
            "order_status": "PROCESSING",
            "fulfilment_status": "UNFULFILLED",
            "timeline": [
                {
                    "status": "ORDER_PLACED",
                    "message": "Order SSK-20261028-4412 placed with Cash on Delivery",
                    "timestamp": datetime.now(timezone.utc) - timedelta(hours=14),
                    "performed_by": "Priya Sharma"
                },
                {
                    "status": "PROCESSING",
                    "message": "Order verification confirmed with customer. Sent to packaging line.",
                    "timestamp": datetime.now(timezone.utc) - timedelta(hours=8),
                    "performed_by": "Ravi Teja (Orders)"
                }
            ],
            "created_at": datetime.now(timezone.utc) - timedelta(hours=14),
            "updated_at": datetime.now(timezone.utc) - timedelta(hours=8)
        }
    ]

    for ord_doc in sample_orders:
        db.orders.update_one(
            {"order_id": ord_doc["order_id"]},
            {"$set": ord_doc},
            upsert=True
        )

    # 6. Seed Product Reviews
    sample_reviews = [
        {
            "product_id": "SSK-JWL-101",
            "reviewer_name": "Ananya Reddy",
            "rating": 5,
            "title": "Stunning bridal look, looks exactly like real 22k gold!",
            "comment": "Wore this for my cousin's wedding reception with a Kanjeevaram silk saree. Everyone thought it was authentic gold jewellery. The finish is supreme, no tarnishing or skin irritation.",
            "images": ["https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=400&q=80"],
            "is_verified_purchase": True,
            "is_approved": True,
            "created_at": datetime.now(timezone.utc) - timedelta(days=6)
        },
        {
            "product_id": "SSK-JWL-102",
            "reviewer_name": "Kavitha M.",
            "rating": 5,
            "title": "Lightweight and gorgeous peacock details",
            "comment": "Normally heavy jhumkas hurt my ears, but SSK made these so comfortable. The peacock filigree is mesmerizing. Very fast shipping to Bangalore!",
            "images": [],
            "is_verified_purchase": True,
            "is_approved": True,
            "created_at": datetime.now(timezone.utc) - timedelta(days=3)
        }
    ]

    for r in sample_reviews:
        db.reviews.update_one(
            {"product_id": r["product_id"], "reviewer_name": r["reviewer_name"]},
            {"$set": r},
            upsert=True
        )

    db_manager.persist_to_disk()
    logger.info("Database seeds completed successfully.")

if __name__ == "__main__":
    run_seed()
