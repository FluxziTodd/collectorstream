"""Player photo scraper — fetch headshots from university athletics roster pages."""

import os
import time
import requests
from pathlib import Path
from urllib.parse import urljoin

import yaml
from bs4 import BeautifulSoup

from db.models import (
    init_db, get_players_by_draft_year, update_player_photo,
    get_connection,
)

CONFIG_PATH = Path(__file__).parent.parent / "config" / "schools.yaml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
}

# Placeholder image generator URL
PLACEHOLDER_URL = "https://ui-avatars.com/api/?name={name}&background=1a1a1a&color=ff6b35&size=200"

# Wikipedia API endpoints
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


def _search_wikipedia_photo(player_name, sport="basketball"):
    """Search Wikipedia for player photo.

    Uses Wikipedia API to:
    1. Search for the player's page
    2. Get the page's main image (infobox image)

    Args:
        player_name: The player's name
        sport: The sport context (basketball, football, baseball, hockey)
    """
    # Map sport codes to search terms
    sport_terms = {
        "wnba": "basketball",
        "nba": "basketball",
        "nfl": "american football",
        "mlb": "baseball",
        "nhl": "ice hockey",
        "basketball": "basketball",
        "football": "american football",
        "baseball": "baseball",
        "hockey": "ice hockey",
    }
    sport_keyword = sport_terms.get(sport.lower(), sport)

    try:
        # Step 1: Search for the player's Wikipedia page
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{player_name} {sport_keyword}",
            "format": "json",
            "srlimit": 5,
        }
        resp = requests.get(WIKIPEDIA_API, params=search_params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        search_data = resp.json()

        results = search_data.get("query", {}).get("search", [])
        if not results:
            return None

        # Get the first matching page
        page_title = None
        last_name = player_name.lower().split()[-1]
        for result in results:
            title = result.get("title", "").lower()
            # Verify it's likely the right person
            if sport_keyword.split()[0] in title or last_name in title:
                page_title = result.get("title")
                break

        if not page_title:
            page_title = results[0].get("title")  # Fall back to first result

        # Step 2: Get the page images
        images_params = {
            "action": "query",
            "titles": page_title,
            "prop": "pageimages",
            "pithumbsize": 500,  # Request 500px thumbnail
            "format": "json",
        }
        resp = requests.get(WIKIPEDIA_API, params=images_params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        images_data = resp.json()

        pages = images_data.get("query", {}).get("pages", {})
        for page_id, page_info in pages.items():
            if page_id == "-1":  # Page not found
                continue
            thumbnail = page_info.get("thumbnail", {})
            source = thumbnail.get("source")
            if source:
                print(f"    Found Wikipedia photo for {player_name}")
                return source

        return None

    except Exception as e:
        print(f"    Wikipedia search error: {e}")
        return None


def _load_school_config():
    """Load school URL config."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f) or {}
    return config.get("schools", {})


def _get_roster_url(school_config, school_name):
    """Get roster URL for a school, deriving from stats_url if needed."""
    if "roster_url" in school_config:
        return school_config["roster_url"]

    # Derive roster URL from stats URL by replacing /stats with /roster
    stats_url = school_config.get("stats_url", "")
    if "/stats" in stats_url:
        return stats_url.replace("/stats", "/roster")

    return None


def _fetch_page(url):
    """Fetch page content, trying requests first, then Playwright for JS sites."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        html = resp.text

        # Check if content seems minimal (JS-rendered site)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ").strip()
        if len(text) < 500:
            return _fetch_with_playwright(url)
        return html
    except Exception:
        return _fetch_with_playwright(url)


def _fetch_with_playwright(url):
    """Fetch JS-rendered page with Playwright."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers(HEADERS)
            page.goto(url, wait_until="networkidle", timeout=30000)
            html = page.content()
            browser.close()
        return html
    except Exception as e:
        print(f"    Playwright error: {e}")
        return None


def _extract_photo_with_llm(html, player_name, base_url):
    """Use Claude to extract player photo URL from roster page."""
    import anthropic

    soup = BeautifulSoup(html, "html.parser")

    # Remove scripts and styles
    for tag in soup(["script", "style", "nav", "footer", "header", "svg", "link", "meta"]):
        tag.decompose()

    # Get main content
    main = soup.find("main") or soup.find("article") or soup.find(id="content") or soup

    # Find all images and their surrounding text
    img_data = []
    for img in main.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        alt = img.get("alt", "")

        # Get nearby text context
        parent = img.parent
        context = ""
        for _ in range(3):  # Go up 3 levels to find text context
            if parent:
                context = parent.get_text(separator=" ", strip=True)[:200]
                parent = parent.parent
                if len(context) > 30:
                    break

        if src:
            img_data.append(f"IMG: {src} | ALT: {alt} | CONTEXT: {context}")

    if not img_data:
        return None

    img_text = "\n".join(img_data[:50])  # Limit to 50 images

    client = anthropic.Anthropic()
    prompt = f"""Find the headshot photo URL for the basketball player "{player_name}" from this roster page data.

IMAGES ON PAGE:
{img_text}

Return a JSON object with:
- "photo_url": the full or relative URL of the player's headshot (or null if not found)
- "confidence": "high", "medium", or "low" based on how certain you are this is the right player

Rules:
- Look for the player's name in the ALT text or CONTEXT
- Prefer larger/higher quality images (look for roster-, headshot-, or player- in the URL)
- Exclude logos, team photos, or thumbnails
- If the URL is relative, that's OK - we'll make it absolute

Return ONLY the JSON, no other text."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()

        # Clean up response
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]

        import json
        result = json.loads(text)

        photo_url = result.get("photo_url")
        confidence = result.get("confidence", "low")

        if photo_url and confidence in ("high", "medium"):
            # Make URL absolute if relative
            if photo_url.startswith("/"):
                photo_url = urljoin(base_url, photo_url)
            elif not photo_url.startswith("http"):
                photo_url = urljoin(base_url, photo_url)
            return photo_url

    except Exception as e:
        print(f"    LLM extraction error: {e}")

    return None


def _get_placeholder_url(player_name):
    """Generate a placeholder avatar URL for a player."""
    # URL-encode the name for the avatar service
    name_encoded = player_name.replace(" ", "+")
    return PLACEHOLDER_URL.format(name=name_encoded)


def scrape_player_photo(player_id, player_name, school, sport="basketball"):
    """Fetch and store photo URL for a single player.

    Args:
        player_id: Database ID of the player
        player_name: Full name of the player
        school: School/college name
        sport: Sport code (wnba, nba, nfl, mlb, nhl) for Wikipedia search context
    """
    schools_config = _load_school_config()

    # Find school config
    school_config = schools_config.get(school)
    if not school_config:
        # Try case-insensitive match
        for s, conf in schools_config.items():
            if s.lower() == school.lower():
                school_config = conf
                break

    if not school_config:
        print(f"  No config found for school: {school}")
        # Try Wikipedia first
        wiki_photo = _search_wikipedia_photo(player_name, sport=sport)
        if wiki_photo:
            print(f"  Found Wikipedia photo: {wiki_photo[:60]}...")
            update_player_photo(player_id, wiki_photo)
            return wiki_photo
        # Use placeholder as fallback
        placeholder = _get_placeholder_url(player_name)
        update_player_photo(player_id, placeholder)
        return placeholder

    roster_url = _get_roster_url(school_config, school)
    if not roster_url:
        print(f"  No roster URL for school: {school}")
        # Try Wikipedia first
        wiki_photo = _search_wikipedia_photo(player_name, sport=sport)
        if wiki_photo:
            print(f"  Found Wikipedia photo: {wiki_photo[:60]}...")
            update_player_photo(player_id, wiki_photo)
            return wiki_photo
        placeholder = _get_placeholder_url(player_name)
        update_player_photo(player_id, placeholder)
        return placeholder

    print(f"  Fetching roster: {roster_url}")
    html = _fetch_page(roster_url)
    if not html:
        print(f"  Failed to fetch roster page")
        # Try Wikipedia first
        wiki_photo = _search_wikipedia_photo(player_name, sport=sport)
        if wiki_photo:
            print(f"  Found Wikipedia photo: {wiki_photo[:60]}...")
            update_player_photo(player_id, wiki_photo)
            return wiki_photo
        placeholder = _get_placeholder_url(player_name)
        update_player_photo(player_id, placeholder)
        return placeholder

    # Extract photo URL using LLM
    photo_url = _extract_photo_with_llm(html, player_name, roster_url)

    if photo_url:
        print(f"  Found photo: {photo_url[:60]}...")
        update_player_photo(player_id, photo_url)
        return photo_url

    # Try Wikipedia as fallback
    print(f"  Trying Wikipedia...")
    wiki_photo = _search_wikipedia_photo(player_name, sport=sport)
    if wiki_photo:
        print(f"  Found Wikipedia photo: {wiki_photo[:60]}...")
        update_player_photo(player_id, wiki_photo)
        return wiki_photo

    # Use placeholder as last resort
    print(f"  No photo found, using placeholder")
    placeholder = _get_placeholder_url(player_name)
    update_player_photo(player_id, placeholder)
    return placeholder


def scrape_all_photos(draft_year=None, sport=None):
    """Scrape photos for all players missing photos.

    Args:
        draft_year: Optional year filter
        sport: Optional sport filter (wnba, nba, nfl, mlb, nhl)
    """
    conn = get_connection()

    # Get players without photos
    query = """
        SELECT id, name, school, draft_year, sport
        FROM players
        WHERE (photo_url IS NULL OR photo_url = '')
    """
    params = []

    if draft_year:
        query += " AND draft_year = ?"
        params.append(draft_year)

    if sport:
        query += " AND LOWER(sport) = ?"
        params.append(sport.lower())

    query += " ORDER BY sport, draft_year, name"

    players = conn.execute(query, params).fetchall()
    conn.close()

    print(f"Found {len(players)} players without photos")

    # Group by school to minimize roster page fetches
    by_school = {}
    for p in players:
        school = p['school'] or 'Unknown'
        if school not in by_school:
            by_school[school] = []
        by_school[school].append(dict(p))

    total_found = 0
    total_placeholder = 0

    for school, school_players in by_school.items():
        print(f"\n{school} ({len(school_players)} players):")

        for player in school_players:
            player_sport = player.get('sport', 'WNBA')
            print(f"  {player['name']} ({player_sport})...")
            result = scrape_player_photo(
                player['id'],
                player['name'],
                school,
                sport=player_sport
            )

            if result and "ui-avatars.com" not in result:
                total_found += 1
            else:
                total_placeholder += 1

            time.sleep(1)  # Rate limit

    print(f"\n\nSummary:")
    print(f"  Photos found: {total_found}")
    print(f"  Placeholders: {total_placeholder}")


def scrape_player_photo_by_name(player_name):
    """Scrape photo for a specific player by name."""
    conn = get_connection()
    player = conn.execute(
        "SELECT id, name, school FROM players WHERE name LIKE ? LIMIT 1",
        (f"%{player_name}%",)
    ).fetchone()
    conn.close()

    if not player:
        print(f"Player not found: {player_name}")
        return None

    print(f"Scraping photo for {player['name']} ({player['school']})")
    return scrape_player_photo(player['id'], player['name'], player['school'] or 'Unknown')
