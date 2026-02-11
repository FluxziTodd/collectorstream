"""NCAA stats scraper — fetch player stats from university athletics websites."""

import os
import json
import time
import requests
from datetime import date
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

from db.models import (
    init_db, get_players_by_draft_year, add_player_stats,
    get_player_stats, add_player_status, get_player_latest_status,
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


def _load_school_config():
    """Load school URL config."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f) or {}
    return config.get("schools", {})


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
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers(HEADERS)
        page.goto(url, wait_until="networkidle", timeout=30000)
        html = page.content()
        browser.close()
    return html


def _extract_stats_with_llm(html, player_name, school):
    """Use Claude to extract player stats from a university athletics page."""
    import anthropic

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "svg", "link", "meta"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.find(id="content") or soup
    text = main.get_text(separator="\n")
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    text = "\n".join(lines)

    if len(text) > 30_000:
        text = text[:30_000]

    client = anthropic.Anthropic()
    prompt = f"""Extract basketball statistics for the player "{player_name}" from {school} from this page.

I need a JSON object with these fields (use null if not found):
- "season": current season string (e.g. "2025-26")
- "games_played": total games played (integer)
- "points_per_game": points per game (float)
- "rebounds_per_game": rebounds per game (float)
- "assists_per_game": assists per game (float)
- "steals_per_game": steals per game (float)
- "blocks_per_game": blocks per game (float)
- "fg_pct": field goal percentage as decimal (e.g. 0.485 for 48.5%)
- "three_pct": three-point percentage as decimal
- "ft_pct": free throw percentage as decimal
- "minutes_per_game": minutes per game (float)

Also extract recent game logs if available as a JSON array "recent_games":
- "game_date": date string (YYYY-MM-DD or as shown)
- "opponent": team played against
- "points": points scored in that game
- "rebounds": rebounds in that game
- "assists": assists in that game

Return ONLY valid JSON, no markdown, no code fences. Start with {{ and end with }}.
If player stats are not found on this page, return: {{"error": "not found"}}

Page content:
{text}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    # Clean up response
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"    LLM response was not valid JSON: {text[:200]}...")
        return None


def scrape_player_stats(player_name, school=None):
    """Scrape stats for a single player."""
    init_db()
    schools_config = _load_school_config()

    # Find player in DB
    conn = get_connection()
    if school:
        row = conn.execute(
            "SELECT id, name, school, draft_year FROM players WHERE name LIKE ? AND school LIKE ?",
            (f"%{player_name}%", f"%{school}%"),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id, name, school, draft_year FROM players WHERE name LIKE ?",
            (f"%{player_name}%",),
        ).fetchone()
    conn.close()

    if not row:
        print(f"Player '{player_name}' not found in database.")
        return

    player_school = row["school"]
    if not player_school:
        print(f"  No school listed for {row['name']}.")
        return

    # Find stats URL
    school_config = schools_config.get(player_school, {})
    stats_url = school_config.get("stats_url")

    if not stats_url:
        print(f"  No stats URL configured for {player_school}. Add to config/schools.yaml")
        return

    print(f"  Scraping stats for {row['name']} ({player_school})...", end=" ", flush=True)

    try:
        html = _fetch_page(stats_url)
        stats = _extract_stats_with_llm(html, row["name"], player_school)

        if not stats or stats.get("error"):
            print("not found on page")
            return

        # Store season averages
        season = stats.get("season", f"{date.today().year - 1}-{str(date.today().year)[-2:]}")
        add_player_stats(
            player_id=row["id"],
            season=season,
            stat_type="season_avg",
            games_played=stats.get("games_played"),
            points_per_game=stats.get("points_per_game"),
            rebounds_per_game=stats.get("rebounds_per_game"),
            assists_per_game=stats.get("assists_per_game"),
            steals_per_game=stats.get("steals_per_game"),
            blocks_per_game=stats.get("blocks_per_game"),
            fg_pct=stats.get("fg_pct"),
            three_pct=stats.get("three_pct"),
            ft_pct=stats.get("ft_pct"),
            minutes_per_game=stats.get("minutes_per_game"),
            source_url=stats_url,
        )

        ppg = stats.get("points_per_game")
        rpg = stats.get("rebounds_per_game")
        print(f"{ppg or '?'} PPG, {rpg or '?'} RPG, {stats.get('games_played', '?')} GP")

        # Store recent game logs if available
        for game in stats.get("recent_games", []):
            add_player_stats(
                player_id=row["id"],
                season=season,
                stat_type="game",
                game_date=game.get("game_date"),
                opponent=game.get("opponent"),
                points_per_game=game.get("points"),
                rebounds_per_game=game.get("rebounds"),
                assists_per_game=game.get("assists"),
                source_url=stats_url,
            )

    except Exception as e:
        print(f"ERROR: {e}")


def scrape_all_stats():
    """Scrape stats for all tracked players with configured schools."""
    init_db()
    schools_config = _load_school_config()

    if not schools_config:
        print("No schools configured in config/schools.yaml")
        return

    conn = get_connection()
    players = conn.execute(
        "SELECT DISTINCT id, name, school, draft_year FROM players WHERE school IS NOT NULL ORDER BY draft_year, name"
    ).fetchall()
    conn.close()

    print(f"Checking stats for {len(players)} players...")
    scraped_schools = set()

    for p in players:
        school = p["school"]
        if school not in schools_config:
            continue

        # Only fetch each school's page once per run
        if school in scraped_schools:
            # Still try to extract from cached page
            pass

        scrape_player_stats(p["name"], school=school)
        scraped_schools.add(school)
        time.sleep(2)  # Rate limit

    print(f"\nDone. Scraped stats from {len(scraped_schools)} school(s).")


def detect_hot_cold():
    """Analyze player performance and flag hot/cold streaks."""
    init_db()

    conn = get_connection()
    # Get players with stats
    players = conn.execute("""
        SELECT DISTINCT p.id, p.name, p.school, p.draft_year
        FROM players p
        JOIN player_stats ps ON p.id = ps.player_id
        ORDER BY p.draft_year, p.name
    """).fetchall()
    conn.close()

    if not players:
        print("No player stats available for detection.")
        return

    print(f"Analyzing performance for {len(players)} player(s)...")

    for p in players:
        # Get season averages
        season_stats = get_player_stats(p["id"])
        season_avg = [s for s in season_stats if s["stat_type"] == "season_avg"]
        game_logs = [s for s in season_stats if s["stat_type"] == "game"]

        if not season_avg:
            continue

        latest_avg = season_avg[0]  # Most recent
        ppg = latest_avg.get("points_per_game") or 0

        if not ppg:
            continue

        # Check recent games if available
        recent_games = sorted(game_logs, key=lambda g: g.get("game_date") or "", reverse=True)[:3]

        if recent_games:
            recent_ppg = sum(g.get("points_per_game") or 0 for g in recent_games) / len(recent_games)

            if ppg > 0:
                pct_diff = (recent_ppg - ppg) / ppg

                current_status = get_player_latest_status(p["id"])
                current = current_status.get("status") if current_status else "normal"

                if pct_diff >= 0.15 and current != "hot":
                    add_player_status(
                        p["id"], "hot",
                        f"Recent 3-game avg ({recent_ppg:.1f} PPG) up {pct_diff*100:.0f}% vs season ({ppg:.1f} PPG)"
                    )
                    print(f"  {p['name']}: HOT - {recent_ppg:.1f} PPG recent vs {ppg:.1f} season avg")
                elif pct_diff <= -0.20 and current != "cold":
                    add_player_status(
                        p["id"], "cold",
                        f"Recent 3-game avg ({recent_ppg:.1f} PPG) down {abs(pct_diff)*100:.0f}% vs season ({ppg:.1f} PPG)"
                    )
                    print(f"  {p['name']}: COLD - {recent_ppg:.1f} PPG recent vs {ppg:.1f} season avg")
                elif abs(pct_diff) < 0.10 and current in ("hot", "cold"):
                    add_player_status(
                        p["id"], "normal",
                        f"Performance stabilized at {recent_ppg:.1f} PPG (season avg {ppg:.1f})"
                    )
                    print(f"  {p['name']}: NORMAL - stabilized at {recent_ppg:.1f} PPG")
        else:
            # No game logs, check if games_played stalled
            prev_stats = [s for s in season_avg if s != latest_avg]
            if prev_stats:
                prev_gp = prev_stats[0].get("games_played") or 0
                curr_gp = latest_avg.get("games_played") or 0
                if curr_gp > 0 and curr_gp == prev_gp:
                    current_status = get_player_latest_status(p["id"])
                    current = current_status.get("status") if current_status else "normal"
                    if current != "cold":
                        add_player_status(
                            p["id"], "cold",
                            f"Games played unchanged at {curr_gp} — possible injury/DNP"
                        )
                        print(f"  {p['name']}: COLD - games played stalled at {curr_gp}")

    print("\nDetection complete.")
