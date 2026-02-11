"""Base scraper with common functionality for all mock draft sources.

Supports multiple sports via the SPORT class attribute.
"""

import os
import re
import time
import json
import requests
from datetime import date
from abc import ABC

from bs4 import BeautifulSoup
from db.models import upsert_player, add_ranking, log_scrape


class BaseScraper(ABC):
    """Base class for all mock draft scrapers.

    Subclasses should override:
    - SOURCE_NAME: Name of the source (e.g., "ESPN", "Bleacher Report")
    - SPORT: Sport code (WNBA, NBA, NFL, NHL, MLB)
    """

    SOURCE_NAME = "unknown"
    SPORT = "WNBA"  # Default for backward compatibility
    RATE_LIMIT_SECONDS = 10
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    def fetch_html(self, url):
        """Fetch HTML from a URL with rate limiting."""
        time.sleep(self.RATE_LIMIT_SECONDS)
        resp = requests.get(url, headers=self.HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text

    def fetch_with_playwright(self, url):
        """Fetch HTML from a JS-rendered page using Playwright."""
        from playwright.sync_api import sync_playwright

        time.sleep(self.RATE_LIMIT_SECONDS)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers(self.HEADERS)
            page.goto(url, wait_until="networkidle", timeout=30000)
            html = page.content()
            browser.close()
        return html

    def parse_with_llm(self, html, draft_year, url):
        """Use Claude to extract structured mock draft data from raw HTML."""
        import anthropic

        # Strip to text content to reduce token usage and avoid HTML noise
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "svg", "link", "meta"]):
            tag.decompose()

        # Try to isolate the main content area
        main = soup.find("main") or soup.find("article") or soup.find(id="content") or soup
        text_content = main.get_text(separator="\n")

        # Clean up excessive whitespace
        lines = [line.strip() for line in text_content.split("\n") if line.strip()]
        text_content = "\n".join(lines)

        # Truncate if still too long
        if len(text_content) > 30_000:
            text_content = text_content[:30_000]

        client = anthropic.Anthropic()

        # Sport-specific position hints
        position_hints = {
            "WNBA": "G (guard), F (forward), C (center)",
            "NBA": "PG, SG, SF, PF, C",
            "NFL": "QB, RB, WR, TE, OL, DL, LB, CB, S",
            "NHL": "C (center), W (wing), D (defense), G (goalie)",
            "MLB": "P, C, IF, OF, DH",
        }
        pos_hint = position_hints.get(self.SPORT, "position abbreviation")

        prompt = f"""Extract {self.SPORT} mock draft or prospect ranking data from this page content.

I need a JSON array of players with these fields:
- "name": player's full name (string)
- "rank": their ranking/position in the mock draft (integer)
- "projected_pick": overall draft pick number if mentioned (integer or null)
- "projected_round": draft round if mentioned (integer or null)
- "school": college/university name if mentioned (string or null)
- "position": playing position if mentioned like {pos_hint} (string or null)
- "notes": any brief scouting notes mentioned (string or null)

This is for the {draft_year} {self.SPORT} Draft.

Return ONLY a valid JSON array, no markdown formatting, no code fences, no explanation. Just the raw JSON array starting with [ and ending with ].
If you can't find mock draft data, return: []

Page content:
{text_content}"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()

        # Handle various response formats
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        # Find the JSON array in the response
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            text = text[start:end + 1]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"    LLM response was not valid JSON: {text[:200]}...")
            return []

    def parse_with_beautifulsoup(self, html, draft_year, url):
        """Fallback parser using BeautifulSoup pattern matching.

        Looks for common mock draft patterns: numbered lists, tables,
        and heading+paragraph structures with player names.
        """
        soup = BeautifulSoup(html, "html.parser")
        players = []

        # Remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Pattern: "1. Player Name" or "Pick 1: Player Name" or "#1 Player Name"
        pick_patterns = [
            re.compile(r"^(\d{1,2})\.\s+(.+?)(?:\s*[-–—,]\s*(.+?))?(?:\s*[-–—,]\s*(.+))?$"),
            re.compile(r"^(?:Pick|#)\s*(\d{1,2})[:\s]+(.+?)(?:\s*[-–—,]\s*(.+?))?(?:\s*[-–—,]\s*(.+))?$", re.IGNORECASE),
            re.compile(r"^Round\s+\d+,?\s*(?:Pick|#)?\s*(\d{1,2})[:\s]+(.+?)(?:\s*[-–—,]\s*(.+?))?$", re.IGNORECASE),
        ]

        for line in lines:
            for pattern in pick_patterns:
                match = pattern.match(line)
                if match:
                    rank = int(match.group(1))
                    name = match.group(2).strip()
                    school = match.group(3).strip() if match.group(3) else None
                    position = match.group(4).strip() if match.lastindex >= 4 and match.group(4) else None

                    # Skip if "name" looks like a team or is too short
                    if len(name) < 3 or name.isupper() and len(name) > 20:
                        continue

                    players.append({
                        "name": name,
                        "rank": rank,
                        "projected_pick": rank,
                        "projected_round": 1 if rank <= 12 else 2 if rank <= 24 else 3,
                        "school": school,
                        "position": position,
                    })
                    break

        # Also try to find tables
        if not players:
            for table in soup.find_all("table"):
                rows = table.find_all("tr")
                for row in rows[1:]:  # skip header
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 2:
                        # Try to find a number and a name
                        for i, cell in enumerate(cells):
                            text_val = cell.get_text(strip=True)
                            if text_val.isdigit() and int(text_val) <= 50:
                                rank = int(text_val)
                                name = cells[i + 1].get_text(strip=True) if i + 1 < len(cells) else None
                                school = cells[i + 2].get_text(strip=True) if i + 2 < len(cells) else None
                                if name and len(name) >= 3:
                                    players.append({
                                        "name": name,
                                        "rank": rank,
                                        "projected_pick": rank,
                                        "school": school,
                                    })
                                break

        return players

    def parse(self, html, draft_year, url):
        """Parse HTML, using LLM if available, falling back to BeautifulSoup."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            print("    Using LLM parser (Claude)")
            return self.parse_with_llm(html, draft_year, url)
        else:
            print("    Using BeautifulSoup parser (set ANTHROPIC_API_KEY for better results)")
            return self.parse_with_beautifulsoup(html, draft_year, url)

    def scrape(self, url, draft_year):
        """Scrape a single URL and store results."""
        print(f"  Scraping {self.SOURCE_NAME} ({self.SPORT}) for {draft_year}: {url}")

        try:
            if getattr(self, "REQUIRES_JS", False):
                html = self.fetch_with_playwright(url)
            else:
                html = self.fetch_html(url)

            players_data = self.parse(html, draft_year, url)
            today = date.today().isoformat()

            for p in players_data:
                player_id = upsert_player(
                    name=p["name"],
                    draft_year=draft_year,
                    sport=self.SPORT,  # Pass sport for multi-sport support
                    school=p.get("school"),
                    position=p.get("position"),
                )
                add_ranking(
                    player_id=player_id,
                    source=self.SOURCE_NAME,
                    rank=p.get("rank"),
                    projected_pick=p.get("projected_pick"),
                    projected_round=p.get("projected_round"),
                    url=url,
                    raw_text=p.get("notes"),
                    scrape_date=today,
                )

            log_scrape(self.SOURCE_NAME, url, draft_year, "success",
                       players_found=len(players_data))
            print(f"    Found {len(players_data)} players")
            return players_data

        except Exception as e:
            log_scrape(self.SOURCE_NAME, url, draft_year, "error",
                       error_message=str(e))
            print(f"    ERROR: {e}")
            return []
