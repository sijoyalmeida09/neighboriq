"""niche_classifier.py — maps raw business category strings to normalized niches."""
from __future__ import annotations

from dataclasses import dataclass

_FOOD_NICHES = {
    "indian_restaurant", "chinese_restaurant", "mexican_restaurant",
    "pizza_restaurant", "coffee_shop", "cafe", "bakery", "bar",
    "sushi_restaurant", "thai_restaurant", "mediterranean_restaurant",
    "ethiopian_restaurant", "vietnamese_restaurant", "halal_restaurant",
    "restaurant",
}

# (niche, parent_category, typical_capital_usd)
# Longer/more specific patterns must come before shorter ones to win on substring match
NICHE_MAP: dict[str, tuple[str, str, int]] = {
    # Food & Beverage — specific ethnic first
    "indian restaurant": ("indian_restaurant", "food_beverage", 150_000),
    "chinese restaurant": ("chinese_restaurant", "food_beverage", 120_000),
    "mexican restaurant": ("mexican_restaurant", "food_beverage", 130_000),
    "mediterranean restaurant": ("mediterranean_restaurant", "food_beverage", 160_000),
    "ethiopian restaurant": ("ethiopian_restaurant", "food_beverage", 120_000),
    "vietnamese restaurant": ("vietnamese_restaurant", "food_beverage", 110_000),
    "thai restaurant": ("thai_restaurant", "food_beverage", 140_000),
    "sushi restaurant": ("sushi_restaurant", "food_beverage", 180_000),
    "halal restaurant": ("halal_restaurant", "food_beverage", 130_000),
    # ethnic keywords without "restaurant"
    "indian": ("indian_restaurant", "food_beverage", 150_000),
    "chinese": ("chinese_restaurant", "food_beverage", 120_000),
    "mexican": ("mexican_restaurant", "food_beverage", 130_000),
    "mediterranean": ("mediterranean_restaurant", "food_beverage", 160_000),
    "ethiopian": ("ethiopian_restaurant", "food_beverage", 120_000),
    "vietnamese": ("vietnamese_restaurant", "food_beverage", 110_000),
    "thai": ("thai_restaurant", "food_beverage", 140_000),
    "sushi": ("sushi_restaurant", "food_beverage", 180_000),
    "halal": ("halal_restaurant", "food_beverage", 130_000),
    # Generic food
    "pizza": ("pizza_restaurant", "food_beverage", 100_000),
    "coffee": ("coffee_shop", "food_beverage", 80_000),
    "cafe": ("cafe", "food_beverage", 60_000),
    "bakery": ("bakery", "food_beverage", 70_000),
    "restaurant": ("restaurant", "food_beverage", 250_000),
    "bar ": ("bar", "food_beverage", 200_000),
    "brewery": ("bar", "food_beverage", 500_000),
    "diner": ("restaurant", "food_beverage", 200_000),
    "deli": ("cafe", "food_beverage", 80_000),
    # Personal Services
    "nail salon": ("nail_salon", "personal_services", 50_000),
    "hair salon": ("hair_salon", "personal_services", 60_000),
    "barbershop": ("barbershop", "personal_services", 30_000),
    "barber shop": ("barbershop", "personal_services", 30_000),
    "laundromat": ("laundromat", "personal_services", 200_000),
    "dry clean": ("dry_cleaning", "personal_services", 80_000),
    "nail": ("nail_salon", "personal_services", 50_000),
    "hair": ("hair_salon", "personal_services", 60_000),
    "barber": ("barbershop", "personal_services", 30_000),
    "laundry": ("laundromat", "personal_services", 200_000),
    "spa": ("hair_salon", "personal_services", 100_000),
    # Fitness & Wellness
    "yoga studio": ("yoga_studio", "fitness_wellness", 50_000),
    "fitness center": ("gym", "fitness_wellness", 200_000),
    "gym": ("gym", "fitness_wellness", 200_000),
    "yoga": ("yoga_studio", "fitness_wellness", 50_000),
    "fitness": ("gym", "fitness_wellness", 200_000),
    "pilates": ("yoga_studio", "fitness_wellness", 60_000),
    # Retail
    "grocery store": ("grocery_store", "retail", 500_000),
    "convenience store": ("convenience_store", "retail", 100_000),
    "hardware store": ("hardware_store", "retail", 500_000),
    "pet store": ("pet_store", "retail", 200_000),
    "shoe store": ("shoe_store", "retail", 100_000),
    "clothing store": ("clothing_store", "retail", 150_000),
    "liquor store": ("liquor_store", "retail", 150_000),
    "grocery": ("grocery_store", "retail", 500_000),
    "pharmacy": ("pharmacy", "retail", 1_000_000),
    "liquor": ("liquor_store", "retail", 150_000),
    "convenience": ("convenience_store", "retail", 100_000),
    "bookstore": ("bookstore", "retail", 100_000),
    "book store": ("bookstore", "retail", 100_000),
    "clothing": ("clothing_store", "retail", 150_000),
    "apparel": ("clothing_store", "retail", 150_000),
    "shoe": ("shoe_store", "retail", 100_000),
    "hardware": ("hardware_store", "retail", 500_000),
    "electronics": ("electronics_store", "retail", 200_000),
    "furniture": ("furniture_store", "retail", 300_000),
    "florist": ("florist", "retail", 50_000),
    "flower": ("florist", "retail", 50_000),
    "jewelry": ("jewelry_store", "retail", 150_000),
    "gift shop": ("gift_shop", "retail", 80_000),
    "supermarket": ("grocery_store", "retail", 1_000_000),
    # Healthcare
    "dentist": ("dentist", "healthcare", 500_000),
    "dental": ("dentist", "healthcare", 500_000),
    "doctor": ("doctor", "healthcare", 300_000),
    "clinic": ("doctor", "healthcare", 300_000),
    "optometrist": ("doctor", "healthcare", 200_000),
    "chiropractor": ("doctor", "healthcare", 150_000),
    # Professional Services
    "real estate": ("real_estate", "professional_services", 30_000),
    "law office": ("law_office", "professional_services", 50_000),
    "law firm": ("law_office", "professional_services", 50_000),
    "accounting": ("accounting", "professional_services", 30_000),
    "insurance": ("insurance", "professional_services", 30_000),
    "attorney": ("law_office", "professional_services", 50_000),
    "lawyer": ("law_office", "professional_services", 50_000),
    "cpa": ("accounting", "professional_services", 30_000),
    # Financial
    "bank": ("bank", "financial", 2_000_000),
    "credit union": ("credit_union", "financial", 1_000_000),
    "check cash": ("check_cashing", "financial", 80_000),
    "check cashing": ("check_cashing", "financial", 80_000),
    "atm": ("bank", "financial", 10_000),
    # Education
    "daycare": ("daycare", "education", 150_000),
    "day care": ("daycare", "education", 150_000),
    "tutoring": ("tutoring_center", "education", 30_000),
    "tutor": ("tutoring_center", "education", 30_000),
    "preschool": ("daycare", "education", 200_000),
    # Automotive
    "auto repair": ("auto_repair", "automotive", 200_000),
    "auto body": ("auto_repair", "automotive", 300_000),
    "gas station": ("gas_station", "automotive", 1_000_000),
    "car wash": ("auto_repair", "automotive", 150_000),
    "mechanic": ("auto_repair", "automotive", 200_000),
}

_SORTED_KEYS = sorted(NICHE_MAP.keys(), key=len, reverse=True)


@dataclass(frozen=True)
class NicheClassification:
    niche: str
    parent_category: str
    typical_capital_req: int
    is_food: bool


_OTHER = NicheClassification(
    niche="other",
    parent_category="uncategorized",
    typical_capital_req=100_000,
    is_food=False,
)


def classify(raw_category: str) -> NicheClassification:
    """Case-insensitive substring match; longest key wins."""
    lower = raw_category.lower().strip()
    for key in _SORTED_KEYS:
        if key in lower:
            niche, parent, capital = NICHE_MAP[key]
            return NicheClassification(
                niche=niche,
                parent_category=parent,
                typical_capital_req=capital,
                is_food=niche in _FOOD_NICHES,
            )
    return _OTHER


def classify_businesses(businesses: list[dict]) -> list[dict]:
    """
    Returns a new list of dicts with niche, parent_category, typical_capital_req added.
    Does not mutate input dicts.
    """
    result = []
    for biz in businesses:
        raw = biz.get("raw_category", "") or biz.get("category", "")
        nc = classify(raw)
        result.append(
            {
                **biz,
                "niche": nc.niche,
                "parent_category": nc.parent_category,
                "typical_capital_req": nc.typical_capital_req,
                "is_food": nc.is_food,
            }
        )
    return result
