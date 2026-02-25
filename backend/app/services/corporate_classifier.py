"""
Corporate Classifier — determines if a merchant is local, corporate, or needs review.

Extracted from scripts/find_nearby_merchants.py for reuse in bulk seeding pipelines.
"""
import re
from typing import Optional
from urllib.parse import urlparse


def _normalize_name(name: str) -> str:
    """Normalize business name for matching."""
    name = name.lower().strip()
    name = re.sub(
        r'\s*[-\u2013\u2014]\s*[a-z\s]+(mall|center|plaza|square|village|commons|crossing).*$',
        '', name, flags=re.IGNORECASE,
    )
    name = re.sub(r'\s*#\d+.*$', '', name)
    name = re.sub(r'\s+store\s*#?\d+.*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+location\s*#?\d+.*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+at\s+[a-z\s]+$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+(inc|llc|corp|co|ltd)\.?$', '', name, flags=re.IGNORECASE)
    return name.strip()


def _extract_domain(website: str) -> Optional[str]:
    """Extract brand domain from a URL."""
    if not website:
        return None
    try:
        parsed = urlparse(website if "://" in website else f"https://{website}")
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        parts = domain.split(".")
        if len(parts) >= 2:
            return ".".join(parts[-2:])
        return domain
    except Exception:
        return None


# ~100+ known corporate domains
CORPORATE_DOMAINS = {
    # Fast Food
    "mcdonalds.com", "bk.com", "wendys.com", "tacobell.com", "kfc.com",
    "chickfila.com", "popeyes.com", "arbys.com", "sonicdrivein.com",
    "jackinthebox.com", "whataburger.com", "carlsjr.com", "hardees.com",
    "fiveguys.com", "in-n-out.com", "culvers.com", "raisingcanes.com",
    "wingstop.com", "buffalowildwings.com", "zaxbys.com", "shakeshack.com",
    # Fast Casual
    "chipotle.com", "panerabread.com", "qdoba.com", "moes.com",
    "pandaexpress.com", "noodles.com", "firehousesubs.com", "jerseymikes.com",
    "jimmyjohns.com", "subway.com", "potbelly.com", "mcalistersdeli.com",
    "jasonsdeli.com", "tropicalsmoothie.com", "smoothieking.com",
    "blazepizza.com", "modpizza.com", "cava.com", "sweetgreen.com",
    # Coffee
    "starbucks.com", "dunkindonuts.com", "peets.com", "dutchbros.com",
    "timhortons.com", "cariboucoffee.com", "coffeebean.com", "philzcoffee.com",
    # Casual Dining
    "applebees.com", "chilis.com", "tgifridays.com", "olivegarden.com",
    "redlobster.com", "outback.com", "texasroadhouse.com", "longhornsteakhouse.com",
    "crackerbarrel.com", "dennys.com", "ihop.com", "wafflehouse.com",
    "thecheesecakefactory.com", "pfchangs.com", "bjsrestaurants.com",
    "redrobin.com", "bonefishgrill.com", "carrabbas.com",
    # Ice Cream / Dessert
    "baskinrobbins.com", "coldstonecreamery.com", "dairyqueen.com",
    "jamba.com", "insomnia.com", "crumblcookies.com",
    # Retail / Convenience
    "walmart.com", "target.com", "costco.com", "samsclub.com",
    "walgreens.com", "cvs.com", "7-eleven.com", "circlek.com",
    "quiktrip.com", "wawa.com", "sheetz.com", "bucees.com",
    # Fitness
    "planetfitness.com", "lafitness.com", "24hourfitness.com",
    "anytimefitness.com", "orangetheory.com", "equinox.com",
}

# Chain brand names to block (matched against normalized name)
CORPORATE_DENYLIST = [
    "mcdonald", "burger king", "wendy", "taco bell", "kfc",
    "chick-fil-a", "popeyes", "arby", "sonic drive-in",
    "jack in the box", "whataburger", "carl's jr", "hardee",
    "five guys", "in-n-out", "culver", "raising cane",
    "wingstop", "buffalo wild wings", "zaxby", "shake shack",
    "chipotle", "panera", "qdoba", "panda express",
    "firehouse sub", "jersey mike", "jimmy john", "subway",
    "starbucks", "dunkin", "peet's coffee", "dutch bros",
    "tim horton", "caribou coffee",
    "applebee", "chili's", "tgi friday", "olive garden",
    "red lobster", "outback", "texas roadhouse", "longhorn",
    "cracker barrel", "denny's", "ihop", "waffle house",
    "cheesecake factory", "p.f. chang", "red robin",
    "baskin-robbins", "cold stone", "dairy queen", "jamba",
    "walmart", "target", "costco", "sam's club",
    "walgreens", "cvs", "7-eleven", "circle k",
    "planet fitness", "la fitness", "anytime fitness",
    "mcdonald's", "burger king", "chick fil a",
]

FRANCHISE_PATTERNS = [
    re.compile(r"\bno\.\s*\d+", re.IGNORECASE),
    re.compile(r"#\d{3,}"),
    re.compile(r"\bstore\s*#?\d+", re.IGNORECASE),
    re.compile(r"\blocation\s*#?\d+", re.IGNORECASE),
    re.compile(r"\bunit\s*\d+", re.IGNORECASE),
]


class CorporateClassifier:
    """Multi-layer classifier: denylist -> domain -> franchise pattern -> type heuristic."""

    CORPORATE_TYPES = {
        "department_store", "supermarket", "convenience",
        "mall", "gas_station",
    }

    def classify(
        self,
        name: str,
        website: Optional[str] = None,
        place_type: Optional[str] = None,
        brand: Optional[str] = None,
    ) -> str:
        """
        Returns 'local', 'corporate', or 'review'.
        """
        name_lower = name.lower()
        name_norm = _normalize_name(name)

        # Layer 1: Brand tag from OSM (very reliable)
        if brand:
            brand_lower = brand.lower()
            for pattern in CORPORATE_DENYLIST:
                if pattern in brand_lower:
                    return "corporate"

        # Layer 2: Hard denylist match on name
        for pattern in CORPORATE_DENYLIST:
            if pattern in name_lower or pattern in name_norm:
                return "corporate"

        # Layer 3: Domain check
        domain = _extract_domain(website)
        if domain and domain in CORPORATE_DOMAINS:
            return "corporate"

        # Layer 4: Franchise naming patterns
        for regex in FRANCHISE_PATTERNS:
            if regex.search(name):
                return "corporate"

        # Layer 5: Type heuristic
        if place_type and place_type in self.CORPORATE_TYPES:
            return "review"

        return "local"
