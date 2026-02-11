"""Deep photo hunt — super aggressive search for player photos."""

import os
import sys
import time
import json
import re
import requests
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup

sys.path.insert(0, '.')
from db.models import get_connection, update_player_photo

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
}

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


def search_wikipedia_deep(player_name, school=None):
    """Deep Wikipedia search with multiple strategies."""
    # More search variations
    last_name = player_name.split()[-1] if player_name else ""
    first_name = player_name.split()[0] if player_name else ""

    strategies = [
        f"{player_name} basketball",
        f"{player_name} women's basketball",
        f"{player_name} WNBA",
        f"{player_name} college basketball",
        f"{player_name}",
    ]

    if school and school != "None":
        strategies.insert(0, f"{player_name} {school}")
        strategies.insert(1, f"{player_name} {school} basketball")

    for search_term in strategies:
        try:
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": search_term,
                "format": "json",
                "srlimit": 10,
            }
            resp = requests.get(WIKIPEDIA_API, params=search_params, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue

            results = resp.json().get("query", {}).get("search", [])

            for result in results:
                title = result.get("title", "")
                snippet = result.get("snippet", "").lower()

                # Check if result is likely about this player
                if last_name.lower() not in title.lower() and last_name.lower() not in snippet:
                    continue

                # Skip disambiguation pages
                if "disambiguation" in title.lower() or "may refer to" in snippet:
                    continue

                # Get page images
                images_params = {
                    "action": "query",
                    "titles": title,
                    "prop": "pageimages|images",
                    "pithumbsize": 500,
                    "format": "json",
                }
                img_resp = requests.get(WIKIPEDIA_API, params=images_params, headers=HEADERS, timeout=10)
                if img_resp.status_code != 200:
                    continue

                pages = img_resp.json().get("query", {}).get("pages", {})
                for page_id, page_info in pages.items():
                    if page_id == "-1":
                        continue

                    # Try thumbnail first
                    thumbnail = page_info.get("thumbnail", {})
                    source = thumbnail.get("source")
                    if source:
                        return source

                    # Try to find any images that might be the person
                    images = page_info.get("images", [])
                    for img in images:
                        img_title = img.get("title", "")
                        # Skip common non-photo images
                        if any(x in img_title.lower() for x in ["logo", "icon", "flag", "map", "seal", "coat", "jersey"]):
                            continue
                        if first_name.lower() in img_title.lower() or last_name.lower() in img_title.lower():
                            # Get image URL
                            img_info_params = {
                                "action": "query",
                                "titles": img_title,
                                "prop": "imageinfo",
                                "iiprop": "url",
                                "iiurlwidth": 500,
                                "format": "json",
                            }
                            img_info_resp = requests.get(WIKIPEDIA_API, params=img_info_params, headers=HEADERS, timeout=10)
                            if img_info_resp.status_code == 200:
                                img_pages = img_info_resp.json().get("query", {}).get("pages", {})
                                for img_page in img_pages.values():
                                    img_info = img_page.get("imageinfo", [{}])[0]
                                    thumb_url = img_info.get("thumburl") or img_info.get("url")
                                    if thumb_url:
                                        return thumb_url

        except Exception as e:
            continue

    return None


def search_school_roster(player_name, school):
    """Search university athletics roster for player photo."""
    if not school or school == "None":
        return None

    # Map school names to domains
    school_domains = {
        "USC": "usctrojans.com",
        "UCLA": "uclabruins.com",
        "UConn": "uconnhuskies.com",
        "Stanford": "gostanford.com",
        "Duke": "goduke.com",
        "South Carolina": "gamecocksonline.com",
        "LSU": "lsusports.net",
        "Tennessee": "utsports.com",
        "Texas": "texassports.com",
        "Oklahoma": "soonersports.com",
        "Iowa": "hawkeyesports.com",
        "NC State": "gopack.com",
        "North Carolina": "goheels.com",
        "Michigan": "mgoblue.com",
        "Michigan State": "msuspartans.com",
        "Ohio State": "ohiostatebuckeyes.com",
        "Florida": "floridagators.com",
        "Kentucky": "ukathletics.com",
        "Ole Miss": "olemisssports.com",
        "Vanderbilt": "vucommodores.com",
        "Colorado": "cubuffs.com",
        "Oregon": "goducks.com",
        "Rutgers": "scarletknights.com",
        "BYU": "byucougars.com",
        "Virginia": "virginiasports.com",
        "Virginia Tech": "hokiesports.com",
        "TCU": "gofrogs.com",
        "Nebraska": "huskers.com",
        "Louisville": "gocards.com",
        "Maryland": "umterps.com",
        "Indiana": "iuhoosiers.com",
        "Purdue": "purduesports.com",
        "Penn State": "gopsusports.com",
        "Houston": "uhcougars.com",
        "Syracuse": "cuse.com",
        "UNLV": "unlvrebels.com",
        "Arizona": "arizonawildcats.com",
        "Arizona State": "thesundevils.com",
        "Creighton": "gocreighton.com",
        "Gonzaga": "gozags.com",
        "Marquette": "gomarquette.com",
        "Villanova": "villanova.com",
        "Seton Hall": "shupirates.com",
        "Baylor": "baylorbears.com",
        "Kansas": "kuathletics.com",
        "Notre Dame": "und.com",
        "Georgia": "georgiadogs.com",
        "Georgia Tech": "ramblinwreck.com",
        "Auburn": "auburntigers.com",
        "Alabama": "rolltide.com",
        "Mississippi State": "hailstate.com",
        "Arkansas": "arkansasrazorbacks.com",
        "Texas Tech": "texastech.com",
        "Oklahoma State": "okstate.com",
        "UCF": "ucfknights.com",
        "Utah": "utahutes.com",
    }

    domain = school_domains.get(school)
    if not domain:
        return None

    roster_url = f"https://{domain}/sports/womens-basketball/roster"

    try:
        resp = requests.get(roster_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Normalize player name for matching
        name_parts = player_name.lower().split()

        # Find player in roster
        for link in soup.find_all("a"):
            text = link.get_text().lower()
            if all(part in text for part in name_parts):
                # Found player link, look for nearby image
                parent = link.parent
                for _ in range(5):  # Go up 5 levels
                    if parent:
                        img = parent.find("img")
                        if img:
                            src = img.get("src") or img.get("data-src")
                            if src:
                                if src.startswith("/"):
                                    src = f"https://{domain}{src}"
                                if "placeholder" not in src.lower() and "logo" not in src.lower():
                                    return src
                        parent = parent.parent

    except Exception as e:
        pass

    return None


def search_espn_college(player_name, school=None):
    """Search ESPN for women's college basketball player."""
    try:
        search_url = f"https://site.web.api.espn.com/apis/common/v3/search"
        params = {
            "query": player_name,
            "limit": 10,
            "type": "player",
            "sport": "basketball",
        }
        resp = requests.get(search_url, params=params, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            for r in results:
                if r.get("type") == "player":
                    display_name = r.get("displayName", "").lower()
                    # Check if name matches
                    if player_name.lower() in display_name or display_name in player_name.lower():
                        player_id = r.get("id")
                        if player_id:
                            # Try women's college basketball endpoint
                            for league in ["womens-college-basketball", "wnba"]:
                                detail_url = f"https://site.api.espn.com/apis/common/v3/sports/basketball/{league}/athletes/{player_id}"
                                try:
                                    detail_resp = requests.get(detail_url, headers=HEADERS, timeout=10)
                                    if detail_resp.status_code == 200:
                                        player_data = detail_resp.json().get("athlete", {})
                                        headshot = player_data.get("headshot", {}).get("href")
                                        if headshot:
                                            return headshot
                                except:
                                    continue
    except Exception as e:
        pass
    return None


def search_maxpreps(player_name):
    """Search MaxPreps for high school player photo."""
    try:
        search_url = f"https://www.maxpreps.com/search/default.aspx?search={quote_plus(player_name)}&type=athlete"
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for card in soup.find_all("div", class_="athlete-card"):
                name = card.find(class_="athlete-name")
                if name and player_name.lower() in name.get_text().lower():
                    img = card.find("img")
                    if img:
                        src = img.get("src")
                        if src and "default" not in src.lower():
                            return src
    except Exception:
        pass
    return None


def search_commons_category(player_name, school=None):
    """Search Wikimedia Commons for player photos."""
    try:
        # Search in Commons
        search_url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{player_name} basketball",
            "srnamespace": "6",  # File namespace
            "format": "json",
            "srlimit": 10,
        }
        resp = requests.get(search_url, params=params, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            results = resp.json().get("query", {}).get("search", [])
            for result in results:
                title = result.get("title", "")
                if any(part.lower() in title.lower() for part in player_name.split()):
                    # Get image URL
                    info_params = {
                        "action": "query",
                        "titles": title,
                        "prop": "imageinfo",
                        "iiprop": "url",
                        "iiurlwidth": 500,
                        "format": "json",
                    }
                    info_resp = requests.get(search_url, params=info_params, headers=HEADERS, timeout=10)
                    if info_resp.status_code == 200:
                        pages = info_resp.json().get("query", {}).get("pages", {})
                        for page in pages.values():
                            img_info = page.get("imageinfo", [{}])[0]
                            thumb_url = img_info.get("thumburl")
                            if thumb_url:
                                return thumb_url
    except Exception:
        pass
    return None


def find_player_photo_deep(player_name, school=None):
    """Try all sources aggressively to find a player photo."""
    sources = [
        ("Wikipedia Deep", lambda: search_wikipedia_deep(player_name, school)),
        ("School Roster", lambda: search_school_roster(player_name, school)),
        ("ESPN College", lambda: search_espn_college(player_name, school)),
        ("Wikimedia Commons", lambda: search_commons_category(player_name, school)),
    ]

    for source_name, search_func in sources:
        try:
            result = search_func()
            if result:
                print(f"    Found on {source_name}")
                return result
        except Exception as e:
            continue
        time.sleep(0.3)

    return None


def hunt_remaining_photos():
    """Find photos for players still missing them."""
    conn = get_connection()

    query = """
        SELECT id, name, school, photo_url
        FROM players
        WHERE photo_url IS NULL
           OR photo_url = ''
           OR photo_url LIKE '%ui-avatars.com%'
        ORDER BY draft_year, name
    """

    players = conn.execute(query).fetchall()
    conn.close()

    print(f"Deep hunting photos for {len(players)} players...")

    found = 0
    not_found = []

    for p in players:
        player_id = p["id"]
        name = p["name"]
        school = p["school"]

        print(f"\n{name} ({school}):")

        photo_url = find_player_photo_deep(name, school)

        if photo_url:
            update_player_photo(player_id, photo_url)
            found += 1
            print(f"    SUCCESS: {photo_url[:70]}...")
        else:
            print(f"    NOT FOUND")
            not_found.append(f"{name} ({school})")

        time.sleep(0.5)

    print(f"\n\n{'='*60}")
    print(f"RESULTS:")
    print(f"  Found: {found}")
    print(f"  Not found: {len(not_found)}")
    print(f"\nStill missing:")
    for p in not_found:
        print(f"  - {p}")

    return found, not_found


if __name__ == "__main__":
    hunt_remaining_photos()
