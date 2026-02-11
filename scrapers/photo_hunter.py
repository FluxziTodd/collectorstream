"""Aggressive photo hunter — find player photos from multiple sources."""

import os
import time
import json
import requests
from urllib.parse import quote_plus

from db.models import get_connection, update_player_photo

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
}

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


def search_wikipedia(player_name, sport="basketball"):
    """Search Wikipedia for player photo using multiple strategies."""
    strategies = [
        f"{player_name} {sport}",
        f"{player_name} basketball player",
        f"{player_name} WNBA",
        f"{player_name} college basketball",
        player_name,
    ]

    for search_term in strategies:
        try:
            # Search for pages
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": search_term,
                "format": "json",
                "srlimit": 5,
            }
            resp = requests.get(WIKIPEDIA_API, params=search_params, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            results = resp.json().get("query", {}).get("search", [])

            if not results:
                continue

            # Try each result
            for result in results:
                title = result.get("title", "")

                # Get page images
                images_params = {
                    "action": "query",
                    "titles": title,
                    "prop": "pageimages",
                    "pithumbsize": 500,
                    "format": "json",
                }
                resp = requests.get(WIKIPEDIA_API, params=images_params, headers=HEADERS, timeout=10)
                resp.raise_for_status()
                pages = resp.json().get("query", {}).get("pages", {})

                for page_id, page_info in pages.items():
                    if page_id == "-1":
                        continue
                    thumbnail = page_info.get("thumbnail", {})
                    source = thumbnail.get("source")
                    if source:
                        return source
        except Exception as e:
            continue

    return None


def search_espn(player_name):
    """Search ESPN for player headshot."""
    try:
        # ESPN search
        search_url = f"https://site.web.api.espn.com/apis/common/v3/search?query={quote_plus(player_name)}&limit=5&type=player"
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            for r in results:
                if r.get("type") == "player":
                    # Get player details
                    player_id = r.get("id")
                    if player_id:
                        # Try WNBA endpoint
                        detail_url = f"https://site.api.espn.com/apis/common/v3/sports/basketball/wnba/athletes/{player_id}"
                        detail_resp = requests.get(detail_url, headers=HEADERS, timeout=10)
                        if detail_resp.status_code == 200:
                            player_data = detail_resp.json().get("athlete", {})
                            headshot = player_data.get("headshot", {}).get("href")
                            if headshot:
                                return headshot

                        # Try women's college basketball endpoint
                        detail_url = f"https://site.api.espn.com/apis/common/v3/sports/basketball/womens-college-basketball/athletes/{player_id}"
                        detail_resp = requests.get(detail_url, headers=HEADERS, timeout=10)
                        if detail_resp.status_code == 200:
                            player_data = detail_resp.json().get("athlete", {})
                            headshot = player_data.get("headshot", {}).get("href")
                            if headshot:
                                return headshot
    except Exception as e:
        pass
    return None


def search_ncaa(player_name, school=None):
    """Search NCAA for player headshot."""
    try:
        search_term = f"{player_name} {school}" if school else player_name
        search_url = f"https://www.ncaa.com/search/field_name/{quote_plus(search_term)}"
        # NCAA search is complex, skip for now
    except Exception:
        pass
    return None


def search_her_hoop_stats(player_name):
    """Search Her Hoop Stats for player photo."""
    try:
        # Try direct URL pattern
        name_slug = player_name.lower().replace(" ", "-").replace("'", "")
        url = f"https://herhoopstats.com/stats/player/{name_slug}/"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            img = soup.find("img", class_="player-image") or soup.find("img", alt=lambda x: x and player_name.lower() in x.lower())
            if img:
                src = img.get("src")
                if src and not "placeholder" in src.lower():
                    if src.startswith("/"):
                        src = "https://herhoopstats.com" + src
                    return src
    except Exception:
        pass
    return None


def search_prospectsnation(player_name):
    """Search ProspectsNation for player photo."""
    try:
        search_url = f"https://www.prospectsnation.com/search/?q={quote_plus(player_name)}"
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            # Find player card with matching name
            for card in soup.find_all("div", class_="player-card"):
                name_el = card.find(class_="player-name")
                if name_el and player_name.lower() in name_el.get_text().lower():
                    img = card.find("img")
                    if img:
                        src = img.get("src") or img.get("data-src")
                        if src:
                            return src
    except Exception:
        pass
    return None


def search_just_womens_sports(player_name):
    """Search Just Women's Sports for player photo."""
    try:
        search_url = f"https://justwomenssports.com/search/?q={quote_plus(player_name)}"
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            for article in soup.find_all("article"):
                if player_name.lower() in article.get_text().lower():
                    img = article.find("img")
                    if img:
                        src = img.get("src")
                        if src:
                            return src
    except Exception:
        pass
    return None


def search_wikidata(player_name):
    """Search Wikidata for player image."""
    try:
        # Search Wikidata
        search_url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbsearchentities",
            "search": player_name,
            "language": "en",
            "format": "json",
            "limit": 5,
        }
        resp = requests.get(search_url, params=params, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for result in data.get("search", []):
                entity_id = result.get("id")
                desc = result.get("description", "").lower()
                if "basketball" in desc or "athlete" in desc or "player" in desc:
                    # Get entity details
                    entity_url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
                    entity_resp = requests.get(entity_url, headers=HEADERS, timeout=10)
                    if entity_resp.status_code == 200:
                        entity_data = entity_resp.json()
                        claims = entity_data.get("entities", {}).get(entity_id, {}).get("claims", {})
                        # P18 is the image property
                        if "P18" in claims:
                            image_claim = claims["P18"][0]
                            image_name = image_claim.get("mainsnak", {}).get("datavalue", {}).get("value")
                            if image_name:
                                # Convert to Commons URL
                                image_name = image_name.replace(" ", "_")
                                import hashlib
                                md5 = hashlib.md5(image_name.encode()).hexdigest()
                                image_url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{md5[0]}/{md5[0:2]}/{quote_plus(image_name)}/500px-{quote_plus(image_name)}"
                                return image_url
    except Exception:
        pass
    return None


def find_player_photo(player_name, school=None):
    """Try all sources to find a player photo."""
    sources = [
        ("Wikipedia", lambda: search_wikipedia(player_name)),
        ("Wikidata", lambda: search_wikidata(player_name)),
        ("ESPN", lambda: search_espn(player_name)),
        ("Her Hoop Stats", lambda: search_her_hoop_stats(player_name)),
    ]

    for source_name, search_func in sources:
        try:
            result = search_func()
            if result:
                print(f"    Found on {source_name}: {result[:60]}...")
                return result
        except Exception as e:
            continue
        time.sleep(0.5)  # Rate limit between sources

    return None


def hunt_all_photos(limit=None):
    """Find photos for all players missing them."""
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

    if limit:
        players = players[:limit]

    print(f"Hunting photos for {len(players)} players...")

    found = 0
    not_found = 0

    for p in players:
        player_id = p["id"]
        name = p["name"]
        school = p["school"]

        print(f"\n{name} ({school}):")

        photo_url = find_player_photo(name, school)

        if photo_url:
            update_player_photo(player_id, photo_url)
            found += 1
        else:
            print(f"    No photo found")
            not_found += 1

        time.sleep(1)  # Rate limit

    print(f"\n\nResults:")
    print(f"  Found: {found}")
    print(f"  Not found: {not_found}")

    return found, not_found


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    hunt_all_photos(limit)
