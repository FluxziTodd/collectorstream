"""Card fingerprinting — identify, search, and match specific card variants."""

import re
from difflib import SequenceMatcher

# Known card properties for regex-based title parsing
MANUFACTURERS = [
    "panini", "topps", "leaf", "donruss", "bowman", "upper deck", "hoops",
    "fleer", "sage", "press pass", "sp authentic", "immaculate", "national treasures",
]

SETS = [
    "prizm", "contenders", "crown royale", "mosaic", "select", "optic",
    "chronicles", "donruss", "elite", "absolute", "spectra", "flawless",
    "immaculate", "national treasures", "noir", "one and one", "court kings",
    "revolution", "status", "recon", "origins", "obsidian", "certified",
    "hoops", "prestige", "score", "playoff", "luminance", "illusions",
    "flux", "zenith", "clearly donruss", "clearly rated",
]

PARALLELS = [
    "base", "silver", "gold", "red", "blue", "green", "orange", "purple",
    "pink", "black", "white", "yellow", "bronze", "platinum", "emerald",
    "ruby", "sapphire", "teal", "neon green", "neon orange", "neon pink",
    "pink shimmer", "cracked ice", "mojo", "hyper", "holo",
    "ice", "camo", "tie-dye", "tiger stripe", "snakeskin", "peacock",
    "disco", "fast break", "choice", "scope", "wave", "laser",
    "no huddle", "press proof", "rated rookie", "downtown",
]

GRADE_PATTERNS = [
    (r"psa\s*10", "PSA 10"), (r"psa\s*9", "PSA 9"), (r"psa\s*8", "PSA 8"),
    (r"psa\s*7", "PSA 7"), (r"bgs\s*10", "BGS 10"), (r"bgs\s*9\.?5", "BGS 9.5"),
    (r"bgs\s*9(?!\.)", "BGS 9"), (r"sgc\s*10", "SGC 10"), (r"sgc\s*9\.?5", "SGC 9.5"),
    (r"sgc\s*9(?!\.)", "SGC 9"), (r"gem\s*mint", "PSA 10"),
]

AUTO_KEYWORDS = ["auto", "autograph", "autographed", "on card auto", "on-card auto"]
ROOKIE_KEYWORDS = ["rc", "rookie", "rookie card"]
NUMBERED_RE = re.compile(r"(?:/|#|numbered\s*)(\d+)", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(20\d{2})(?:-\d{2})?\b")


def build_fingerprint(card):
    """Build a canonical fingerprint dict from a portfolio_cards row or dict."""
    return {
        "player": card.get("player_name", ""),
        "year": card.get("card_year"),
        "manufacturer": card.get("manufacturer", ""),
        "set": card.get("set_name", ""),
        "parallel": card.get("parallel", "Base"),
        "numbered": card.get("numbered_to"),
        "auto": bool(card.get("is_autograph")),
        "rookie": bool(card.get("is_rookie")),
        "grade": card.get("grade", "Raw"),
    }


def build_ebay_query(fingerprint, level=1):
    """Build eBay search query from fingerprint.

    level=1: most precise (all details)
    level=2: set-level (drop grade, numbered)
    level=3: broad (player + year + set)
    """
    parts = [fingerprint["player"]]

    if fingerprint["year"]:
        parts.append(str(fingerprint["year"]))

    if level <= 3 and fingerprint["set"]:
        parts.append(fingerprint["set"])

    if level <= 2 and fingerprint["parallel"] and fingerprint["parallel"] != "Base":
        parts.append(fingerprint["parallel"])

    if level <= 1:
        if fingerprint["auto"]:
            parts.append("auto")
        if fingerprint["grade"] and fingerprint["grade"] != "Raw":
            parts.append(fingerprint["grade"])
        if fingerprint["numbered"]:
            parts.append(f"/{fingerprint['numbered']}")

    return " ".join(parts)


def build_cardladder_query(fingerprint):
    """Card Ladder searches by player name only; filtering is done post-search."""
    return fingerprint["player"]


def _fuzzy_match(needle, haystack):
    """Check if needle is present in haystack (case-insensitive fuzzy)."""
    needle_lower = needle.lower().strip()
    haystack_lower = haystack.lower()
    if needle_lower in haystack_lower:
        return 1.0
    # Try each word
    words = needle_lower.split()
    if len(words) > 1 and all(w in haystack_lower for w in words):
        return 0.9
    # Partial match
    ratio = SequenceMatcher(None, needle_lower, haystack_lower).ratio()
    return ratio if ratio > 0.6 else 0.0


def score_title_match(title, fingerprint):
    """Score 0.0-1.0 how well a listing title matches a card fingerprint.

    Weighted components check for presence of each fingerprint attribute
    in the title text.
    """
    if not title:
        return 0.0

    title_lower = title.lower()
    score = 0.0

    weights = {
        "player": 0.30,
        "year": 0.15,
        "set": 0.20,
        "parallel": 0.15,
        "auto": 0.10,
        "grade": 0.05,
        "numbered": 0.05,
    }

    # Player name
    player = fingerprint.get("player", "")
    if player:
        player_score = _fuzzy_match(player, title)
        score += weights["player"] * player_score

    # Year
    year = fingerprint.get("year")
    if year and str(year) in title:
        score += weights["year"]
    elif year:
        # Check for year range like "2024-25"
        short_year = str(year)[-2:]
        if re.search(rf"\b\d{{4}}-{short_year}\b", title):
            score += weights["year"]

    # Set name
    set_name = fingerprint.get("set", "")
    if set_name:
        set_score = _fuzzy_match(set_name, title)
        score += weights["set"] * set_score

    # Parallel
    parallel = fingerprint.get("parallel", "Base")
    if parallel and parallel != "Base":
        par_score = _fuzzy_match(parallel, title)
        score += weights["parallel"] * par_score
    elif parallel == "Base":
        # If looking for base and no parallel keywords found, partial match
        has_parallel = any(p in title_lower for p in PARALLELS if p != "base")
        if not has_parallel:
            score += weights["parallel"] * 0.5

    # Autograph
    if fingerprint.get("auto"):
        if any(kw in title_lower for kw in AUTO_KEYWORDS):
            score += weights["auto"]
    else:
        # Not looking for auto — penalize if title has auto
        if any(kw in title_lower for kw in AUTO_KEYWORDS):
            score -= weights["auto"] * 0.5

    # Grade
    grade = fingerprint.get("grade", "Raw")
    if grade and grade != "Raw":
        grade_lower = grade.lower()
        if grade_lower in title_lower:
            score += weights["grade"]
        elif grade_lower.replace(" ", "") in title_lower.replace(" ", ""):
            score += weights["grade"] * 0.8

    # Numbered
    numbered = fingerprint.get("numbered")
    if numbered:
        if f"/{numbered}" in title or f"#{numbered}" in title:
            score += weights["numbered"]
        elif str(numbered) in title:
            score += weights["numbered"] * 0.5

    return max(0.0, min(1.0, score))


def parse_title(title, player_name=None):
    """Extract structured card metadata from a listing title.

    Returns dict with extracted fields. Fields that can't be determined
    are set to None.
    """
    if not title:
        return {}

    title_lower = title.lower()
    result = {
        "player_name": player_name,
        "card_year": None,
        "manufacturer": None,
        "set_name": None,
        "parallel": None,
        "is_numbered": 0,
        "numbered_to": None,
        "is_autograph": 0,
        "is_rookie": 0,
        "grade": None,
    }

    # Year
    year_match = YEAR_RE.search(title)
    if year_match:
        result["card_year"] = int(year_match.group(1))

    # Manufacturer
    for mfr in MANUFACTURERS:
        if mfr in title_lower:
            result["manufacturer"] = mfr.title()
            break

    # Set name — check longest matches first to avoid partial matches
    sorted_sets = sorted(SETS, key=len, reverse=True)
    for s in sorted_sets:
        if s in title_lower:
            result["set_name"] = s.title()
            break

    # Parallel — check longest first
    sorted_parallels = sorted(PARALLELS, key=len, reverse=True)
    for p in sorted_parallels:
        if p != "base" and p in title_lower:
            result["parallel"] = p.title()
            break

    # Numbered
    numbered_match = NUMBERED_RE.search(title)
    if numbered_match:
        result["is_numbered"] = 1
        result["numbered_to"] = int(numbered_match.group(1))

    # Autograph
    if any(kw in title_lower for kw in AUTO_KEYWORDS):
        result["is_autograph"] = 1

    # Rookie
    if any(kw in title_lower for kw in ROOKIE_KEYWORDS):
        result["is_rookie"] = 1

    # Grade
    for pattern, grade_name in GRADE_PATTERNS:
        if re.search(pattern, title_lower):
            result["grade"] = grade_name
            break

    return result


def card_description(card):
    """Build a human-readable card description from a portfolio_cards dict."""
    parts = []
    if card.get("card_year"):
        parts.append(str(card["card_year"]))
    if card.get("manufacturer"):
        parts.append(card["manufacturer"])
    if card.get("set_name"):
        parts.append(card["set_name"])
    if card.get("parallel") and card["parallel"] != "Base":
        parts.append(card["parallel"])
    if card.get("card_number"):
        parts.append(f"#{card['card_number']}")
    if card.get("is_numbered") and card.get("numbered_to"):
        serial = card.get("serial_number", "?")
        parts.append(f"{serial}/{card['numbered_to']}")
    if card.get("is_autograph"):
        parts.append("Auto")
    if card.get("is_rookie"):
        parts.append("RC")
    if card.get("grade") and card["grade"] != "Raw":
        parts.append(card["grade"])
    return " ".join(parts) if parts else "Unknown Card"
