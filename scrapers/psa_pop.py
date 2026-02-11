"""PSA Population Report scraper for graded card data.

Scrapes population data from GemRate (aggregates PSA, BGS, SGC, CGC)
and PSA directly to help identify low-pop investment opportunities.
"""

import re
import time
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from db.models import get_connection


# Rate limiting
RATE_LIMIT_SECONDS = 3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def init_pop_table():
    """Create the population data table if it doesn't exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS card_populations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            card_name TEXT NOT NULL,
            year INTEGER,
            set_name TEXT,
            grader TEXT DEFAULT 'PSA',
            grade_10 INTEGER DEFAULT 0,
            grade_9 INTEGER DEFAULT 0,
            grade_8 INTEGER DEFAULT 0,
            grade_7 INTEGER DEFAULT 0,
            grade_lower INTEGER DEFAULT 0,
            total_graded INTEGER DEFAULT 0,
            gem_rate REAL,
            source_url TEXT,
            last_updated TEXT,
            UNIQUE(player_name, card_name, grader)
        )
    """)
    conn.commit()


def search_gemrate(player_name):
    """Search GemRate for player population data.

    GemRate aggregates PSA, BGS, SGC, CGC data.
    Returns list of card population records.
    """
    time.sleep(RATE_LIMIT_SECONDS)

    # GemRate uses a search API endpoint
    search_url = "https://www.gemrate.com/api/search"

    try:
        # Try the search endpoint
        resp = requests.get(
            search_url,
            params={"q": player_name, "limit": 50},
            headers=HEADERS,
            timeout=30
        )

        if resp.status_code == 200:
            data = resp.json()
            return parse_gemrate_results(data, player_name)
    except Exception as e:
        print(f"  GemRate API error: {e}")

    # Fallback: try scraping the page directly
    return search_gemrate_scrape(player_name)


def search_gemrate_scrape(player_name):
    """Scrape GemRate search results page."""
    from playwright.sync_api import sync_playwright

    time.sleep(RATE_LIMIT_SECONDS)

    search_term = player_name.replace(" ", "+")
    url = f"https://www.gemrate.com/universal-search?q={search_term}"

    print(f"  Fetching GemRate: {url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers(HEADERS)
            page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for results to load
            page.wait_for_timeout(2000)

            html = page.content()
            browser.close()

        return parse_gemrate_html(html, player_name)
    except Exception as e:
        print(f"  GemRate scrape error: {e}")
        return []


def parse_gemrate_results(data, player_name):
    """Parse GemRate API response."""
    results = []

    if not data or not isinstance(data, list):
        return results

    for item in data:
        try:
            results.append({
                "player_name": player_name,
                "card_name": item.get("name", "Unknown"),
                "year": item.get("year"),
                "set_name": item.get("set"),
                "grader": item.get("grader", "PSA"),
                "grade_10": item.get("psa10", 0) or item.get("gem", 0),
                "grade_9": item.get("psa9", 0) or item.get("mint", 0),
                "grade_8": item.get("psa8", 0),
                "grade_7": item.get("psa7", 0),
                "total_graded": item.get("total", 0),
                "gem_rate": item.get("gem_rate"),
                "source_url": item.get("url", ""),
            })
        except Exception:
            continue

    return results


def parse_gemrate_html(html, player_name):
    """Parse GemRate HTML search results."""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # Look for card result rows
    for row in soup.select(".card-row, .search-result, tr[data-card]"):
        try:
            card_name = row.select_one(".card-name, .name, td:nth-child(2)")
            if card_name:
                card_name = card_name.get_text(strip=True)
            else:
                continue

            # Extract population numbers
            pop_data = {
                "player_name": player_name,
                "card_name": card_name,
                "grader": "PSA",
                "grade_10": 0,
                "grade_9": 0,
                "grade_8": 0,
                "total_graded": 0,
            }

            # Try to find grade columns
            for cell in row.select("td, .grade-cell"):
                text = cell.get_text(strip=True)
                if text.isdigit():
                    num = int(text)
                    # Assign based on column position or class
                    cell_class = cell.get("class", [])
                    if "psa10" in str(cell_class) or "gem" in str(cell_class):
                        pop_data["grade_10"] = num
                    elif "psa9" in str(cell_class):
                        pop_data["grade_9"] = num

            results.append(pop_data)
        except Exception:
            continue

    return results


def search_psa_player(player_name):
    """Search PSA population report by player name.

    Uses Playwright since PSA requires JavaScript rendering.
    """
    from playwright.sync_api import sync_playwright

    time.sleep(RATE_LIMIT_SECONDS)

    search_term = player_name.replace(" ", "%20")
    url = f"https://www.psacard.com/pop/playersearch?name={search_term}"

    print(f"  Fetching PSA: {url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers(HEADERS)
            page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for results
            page.wait_for_timeout(3000)

            html = page.content()
            browser.close()

        return parse_psa_player_results(html, player_name)
    except Exception as e:
        print(f"  PSA player search error: {e}")
        return []


def parse_psa_player_results(html, player_name):
    """Parse PSA player search results page."""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # PSA shows a table of cards for the player
    for row in soup.select("table tr"):
        cells = row.select("td")
        if len(cells) < 5:
            continue

        try:
            # Typical PSA layout: Set | Card# | Card Name | Grades...
            card_name = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            set_name = cells[0].get_text(strip=True) if len(cells) > 0 else ""

            # Grade columns are usually the last several columns
            # PSA 10, 9, 8, 7, etc.
            grades = []
            for cell in cells[3:]:
                text = cell.get_text(strip=True).replace(",", "")
                if text.isdigit():
                    grades.append(int(text))
                else:
                    grades.append(0)

            # Calculate total
            total = sum(grades)

            results.append({
                "player_name": player_name,
                "card_name": card_name,
                "set_name": set_name,
                "grader": "PSA",
                "grade_10": grades[0] if len(grades) > 0 else 0,
                "grade_9": grades[1] if len(grades) > 1 else 0,
                "grade_8": grades[2] if len(grades) > 2 else 0,
                "grade_7": grades[3] if len(grades) > 3 else 0,
                "grade_lower": sum(grades[4:]) if len(grades) > 4 else 0,
                "total_graded": total,
                "gem_rate": (grades[0] / total * 100) if total > 0 else 0,
                "source_url": f"https://www.psacard.com/pop/playersearch?name={player_name.replace(' ', '%20')}",
            })
        except Exception:
            continue

    return results


def search_psa_with_llm(player_name):
    """Use LLM to parse PSA population data from scraped HTML."""
    import anthropic
    from playwright.sync_api import sync_playwright

    time.sleep(RATE_LIMIT_SECONDS)

    search_term = player_name.replace(" ", "%20")
    url = f"https://www.psacard.com/pop/playersearch?name={search_term}"

    print(f"  Fetching PSA with LLM parsing: {url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers(HEADERS)
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            html = page.content()
            browser.close()
    except Exception as e:
        print(f"  PSA fetch error: {e}")
        return []

    # Clean HTML for LLM
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "svg", "link", "meta"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.find(id="content") or soup
    text_content = main.get_text(separator="\n")

    # Clean whitespace
    lines = [line.strip() for line in text_content.split("\n") if line.strip()]
    text_content = "\n".join(lines)

    if len(text_content) > 25000:
        text_content = text_content[:25000]

    client = anthropic.Anthropic()

    prompt = f"""Extract PSA population report data for {player_name} from this page content.

I need a JSON array of cards with these fields:
- "card_name": full card description (e.g., "2024 Panini Prizm #123 Lauren Betts RC")
- "year": card year as integer
- "set_name": set name (e.g., "Panini Prizm")
- "grade_10": PSA 10 population count (integer)
- "grade_9": PSA 9 population count (integer)
- "grade_8": PSA 8 population count (integer)
- "grade_7": PSA 7 population count (integer)
- "total_graded": total cards graded (integer)

Return ONLY a valid JSON array, no markdown, no explanation. Just the raw JSON starting with [ and ending with ].
If you can't find population data, return: []

Page content:
{text_content}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()

        # Clean response
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            text = text[start:end + 1]

        data = json.loads(text)

        results = []
        for item in data:
            grade_10 = item.get("grade_10", 0) or 0
            total = item.get("total_graded", 0) or 0

            results.append({
                "player_name": player_name,
                "card_name": item.get("card_name", "Unknown"),
                "year": item.get("year"),
                "set_name": item.get("set_name"),
                "grader": "PSA",
                "grade_10": grade_10,
                "grade_9": item.get("grade_9", 0) or 0,
                "grade_8": item.get("grade_8", 0) or 0,
                "grade_7": item.get("grade_7", 0) or 0,
                "total_graded": total,
                "gem_rate": (grade_10 / total * 100) if total > 0 else 0,
                "source_url": url,
            })

        return results
    except Exception as e:
        print(f"  LLM parsing error: {e}")
        return []


def save_population_data(records):
    """Save population records to database."""
    init_pop_table()
    conn = get_connection()

    now = datetime.now().isoformat()
    saved = 0

    for r in records:
        try:
            conn.execute("""
                INSERT INTO card_populations
                (player_name, card_name, year, set_name, grader,
                 grade_10, grade_9, grade_8, grade_7, grade_lower,
                 total_graded, gem_rate, source_url, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(player_name, card_name, grader) DO UPDATE SET
                    grade_10 = excluded.grade_10,
                    grade_9 = excluded.grade_9,
                    grade_8 = excluded.grade_8,
                    grade_7 = excluded.grade_7,
                    grade_lower = excluded.grade_lower,
                    total_graded = excluded.total_graded,
                    gem_rate = excluded.gem_rate,
                    last_updated = excluded.last_updated
            """, (
                r.get("player_name"),
                r.get("card_name"),
                r.get("year"),
                r.get("set_name"),
                r.get("grader", "PSA"),
                r.get("grade_10", 0),
                r.get("grade_9", 0),
                r.get("grade_8", 0),
                r.get("grade_7", 0),
                r.get("grade_lower", 0),
                r.get("total_graded", 0),
                r.get("gem_rate"),
                r.get("source_url"),
                now,
            ))
            saved += 1
        except Exception as e:
            print(f"  Error saving {r.get('card_name')}: {e}")

    conn.commit()
    return saved


def get_player_population(player_name):
    """Get cached population data for a player."""
    init_pop_table()
    conn = get_connection()

    rows = conn.execute("""
        SELECT * FROM card_populations
        WHERE player_name LIKE ?
        ORDER BY grade_10 DESC, total_graded DESC
    """, (f"%{player_name}%",)).fetchall()

    return [dict(row) for row in rows]


def get_low_pop_gems(max_pop=50, min_total=10):
    """Find cards with low PSA 10 population but decent grading volume.

    These are potential investment opportunities -
    cards that are hard to get in gem mint condition.
    """
    init_pop_table()
    conn = get_connection()

    rows = conn.execute("""
        SELECT * FROM card_populations
        WHERE grade_10 <= ? AND total_graded >= ?
        ORDER BY gem_rate ASC, grade_10 ASC
        LIMIT 100
    """, (max_pop, min_total)).fetchall()

    return [dict(row) for row in rows]


def lookup_player_pop(player_name, use_llm=True):
    """Main entry point: look up population data for a player.

    Tries GemRate first (aggregates multiple graders),
    then falls back to PSA directly.
    """
    print(f"Looking up population data for: {player_name}")

    results = []

    # Try GemRate first (aggregates PSA, BGS, SGC, CGC)
    print("  Trying GemRate...")
    results = search_gemrate(player_name)

    if not results:
        # Fall back to PSA with LLM parsing
        if use_llm:
            print("  Trying PSA with LLM parsing...")
            results = search_psa_with_llm(player_name)
        else:
            print("  Trying PSA direct parsing...")
            results = search_psa_player(player_name)

    if results:
        saved = save_population_data(results)
        print(f"  Found {len(results)} cards, saved {saved} records")
    else:
        print("  No population data found")

    return results


def lookup_all_watchlist():
    """Look up population data for all players on the watchlist."""
    conn = get_connection()

    # Get watchlist players
    rows = conn.execute("""
        SELECT DISTINCT player_name FROM watchlist
        ORDER BY player_name
    """).fetchall()

    if not rows:
        print("No players in watchlist")
        return

    print(f"Looking up population for {len(rows)} watchlist players...")

    for row in rows:
        player_name = row["player_name"]
        lookup_player_pop(player_name)
        time.sleep(2)  # Extra rate limiting between players


def get_pop_buy_signals(draft_year=None):
    """Identify buy signals based on population + rising rankings.

    Low pop PSA 10 + rising in mock drafts = potential buy
    """
    from analysis.movers import get_movers

    init_pop_table()
    conn = get_connection()

    # Get rising players
    movers = get_movers(draft_year=draft_year, days_back=30)
    risers = [m for m in movers if m.get("direction") == "up"]

    signals = []

    for riser in risers:
        player_name = riser.get("name", "")

        # Check if we have population data
        pops = conn.execute("""
            SELECT * FROM card_populations
            WHERE player_name LIKE ?
            ORDER BY grade_10 ASC
            LIMIT 5
        """, (f"%{player_name}%",)).fetchall()

        for pop in pops:
            pop = dict(pop)
            grade_10 = pop.get("grade_10", 0)
            total = pop.get("total_graded", 0)

            # Low pop 10s are interesting
            if grade_10 <= 100 and total >= 5:
                gem_rate = (grade_10 / total * 100) if total > 0 else 0

                signals.append({
                    "player_name": player_name,
                    "card_name": pop.get("card_name"),
                    "set_name": pop.get("set_name"),
                    "grader": pop.get("grader"),
                    "psa_10_pop": grade_10,
                    "total_graded": total,
                    "gem_rate": round(gem_rate, 1),
                    "rank_change": riser.get("change"),
                    "current_rank": riser.get("current_rank"),
                    "signal_strength": "STRONG" if grade_10 <= 25 else "MODERATE",
                    "reason": f"Rising prospect (+{abs(riser.get('change', 0))} spots) with low PSA 10 pop ({grade_10})",
                })

    # Sort by signal strength and pop
    signals.sort(key=lambda x: (x["signal_strength"] != "STRONG", x["psa_10_pop"]))

    return signals
