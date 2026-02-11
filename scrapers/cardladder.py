"""Card Ladder scraper — logs in and pulls card sales data using Playwright."""

import os
import asyncio
import json
import re
from datetime import datetime, date
from playwright.async_api import async_playwright


class CardLadderClient:
    """Scrape card prices from Card Ladder Pro using browser automation."""

    LOGIN_URL = "https://app.cardladder.com/login"
    SALES_URL = "https://app.cardladder.com/sales-history"

    def __init__(self):
        self.email = os.environ.get("CARDLADDER_EMAIL", "")
        self.password = os.environ.get("CARDLADDER_PASSWORD", "")
        self._browser = None
        self._context = None
        self._page = None

    async def _launch(self):
        """Launch browser and log in."""
        pw = await async_playwright().start()
        self._browser = await pw.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )
        )
        self._page = await self._context.new_page()
        await self._page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

    async def _login(self):
        """Log into Card Ladder."""
        await self._page.goto(self.LOGIN_URL, timeout=30000)
        await self._page.wait_for_timeout(3000)

        # Check if already on dashboard (session persisted)
        if "dashboard" in self._page.url or "sales" in self._page.url:
            return

        await self._page.fill('input[name="email"]', self.email)
        await self._page.fill('input[name="password"]', self.password)
        await self._page.click('button[type="submit"]')
        await self._page.wait_for_timeout(5000)

        if "login" in self._page.url:
            raise RuntimeError("Card Ladder login failed — check credentials")

    async def _ensure_ready(self):
        """Launch browser and log in if needed."""
        if not self._browser:
            await self._launch()
            await self._login()

    async def search_sales(self, player_name, limit=20):
        """Search Card Ladder sales history for a player.

        Returns list of dicts: {title, date_sold, sale_type, price, source}
        """
        await self._ensure_ready()
        page = self._page

        # Use the visible search bar at the top of the page
        search = page.locator('input[placeholder="Search"]').first
        try:
            await search.click(timeout=5000)
        except Exception:
            # Navigate to dashboard and try again
            await page.goto("https://app.cardladder.com/dashboard", timeout=30000)
            await page.wait_for_timeout(3000)
            search = page.locator('input[placeholder="Search"]').first
            await search.click(timeout=5000)

        await search.fill("")
        await search.fill(player_name)
        await page.wait_for_timeout(3000)

        # Extract sales from dropdown via JavaScript
        dropdown_text = await page.evaluate("""() => {
            const els = document.querySelectorAll('[class*="dropdown"]');
            let texts = [];
            els.forEach(el => {
                if (el.offsetHeight > 0) texts.push(el.innerText);
            });
            return texts;
        }""")

        sales = []
        for text_block in dropdown_text:
            if player_name.split()[-1].lower() not in text_block.lower():
                continue
            sales = self._parse_sales_from_text(text_block, player_name, limit)
            if sales:
                break

        # Close search dropdown
        await page.keyboard.press("Escape")
        return sales

    def _parse_sale_item(self, text, player_name):
        """Parse a single sale item from its text content."""
        if player_name.split()[0].lower() not in text.lower():
            return None

        lines = [l.strip() for l in text.split("\n") if l.strip()]

        sale = {
            "title": "",
            "date_sold": None,
            "sale_type": None,
            "price": None,
            "source": "cardladder",
        }

        for i, line in enumerate(lines):
            # Source line (e.g., "EBAY - KK CARDS 2025")
            if line.startswith("EBAY") or line.startswith("GOLDIN") or line.startswith("HERITAGE"):
                sale["source"] = line

            # Price (e.g., "$44.99")
            price_match = re.search(r'\$[\d,]+\.?\d*', line)
            if price_match:
                price_str = price_match.group().replace("$", "").replace(",", "")
                try:
                    sale["price"] = float(price_str)
                except ValueError:
                    pass

            # Date (e.g., "Feb 6, 2026")
            date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}', line)
            if date_match:
                try:
                    sale["date_sold"] = datetime.strptime(
                        date_match.group().replace(",", ""), "%b %d %Y"
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    pass

            # Sale type
            if line in ("Auction", "Best Offer", "Fixed Price", "Buy It Now"):
                sale["sale_type"] = line

            # Title — usually the longest descriptive line
            if len(line) > 30 and player_name.split()[-1].lower() in line.lower():
                sale["title"] = line

        return sale if sale["price"] else None

    def _parse_sales_from_text(self, body_text, player_name, limit):
        """Parse sales data from raw page text when selectors fail."""
        sales = []
        # Split by common patterns
        chunks = re.split(r'(?=EBAY\s*-|GOLDIN\s*-|HERITAGE\s*-)', body_text)

        for chunk in chunks:
            if player_name.split()[-1].lower() not in chunk.lower():
                continue

            sale = self._parse_sale_item(chunk, player_name)
            if sale:
                sales.append(sale)
                if len(sales) >= limit:
                    break

        return sales

    async def get_player_sales_summary(self, player_name):
        """Get price summary for a player's recent card sales.

        Returns dict with avg_sale, lowest_sale, highest_sale,
        num_sales, recent_sales list.
        """
        sales = await self.search_sales(player_name, limit=20)

        prices = [s["price"] for s in sales if s.get("price")]

        if not prices:
            return {
                "player_name": player_name,
                "avg_sale": None,
                "lowest_sale": None,
                "highest_sale": None,
                "num_sales": 0,
                "recent_sales": [],
            }

        return {
            "player_name": player_name,
            "avg_sale": round(sum(prices) / len(prices), 2),
            "lowest_sale": min(prices),
            "highest_sale": max(prices),
            "num_sales": len(prices),
            "recent_sales": sales,
        }

    async def search_and_match(self, player_name, fingerprint, limit=20,
                               min_confidence=0.5):
        """Search Card Ladder and filter results matching a card fingerprint.

        Returns only sales whose title scores >= min_confidence against
        the fingerprint. Also stores title mappings for learning.
        """
        from analysis.fingerprint import score_title_match, parse_title
        from db.models import add_title_mapping

        sales = await self.search_sales(player_name, limit=limit)
        matched = []
        for sale in sales:
            title = sale.get("title", "")
            if not title:
                continue
            score = score_title_match(title, fingerprint)
            if score >= min_confidence:
                sale["match_confidence"] = score
                matched.append(sale)

            # Store title mapping for learning
            try:
                parsed = parse_title(title, player_name=player_name)
                add_title_mapping(
                    raw_title=title,
                    player_name=player_name,
                    card_year=parsed.get("card_year"),
                    manufacturer=parsed.get("manufacturer"),
                    set_name=parsed.get("set_name"),
                    parallel=parsed.get("parallel"),
                    is_numbered=parsed.get("is_numbered"),
                    numbered_to=parsed.get("numbered_to"),
                    is_autograph=parsed.get("is_autograph"),
                    is_rookie=parsed.get("is_rookie"),
                    grade=parsed.get("grade"),
                    source="cardladder",
                )
            except Exception:
                pass  # Don't fail price lookup due to mapping error

        return matched

    async def close(self):
        """Close browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None


def search_cardladder(player_name):
    """Synchronous wrapper for Card Ladder search."""
    async def _run():
        client = CardLadderClient()
        try:
            summary = await client.get_player_sales_summary(player_name)
            return summary
        finally:
            await client.close()

    return asyncio.run(_run())


def search_cardladder_batch(player_names):
    """Search Card Ladder for multiple players in one browser session."""
    async def _run():
        client = CardLadderClient()
        results = {}
        try:
            for name in player_names:
                print(f"  Card Ladder: {name}...", end=" ", flush=True)
                try:
                    summary = await client.get_player_sales_summary(name)
                    if summary["num_sales"] > 0:
                        print(f"{summary['num_sales']} sales, "
                              f"${summary['lowest_sale']:.2f}-${summary['highest_sale']:.2f}")
                    else:
                        print("no sales found")
                    results[name] = summary
                except Exception as e:
                    print(f"ERROR: {e}")
                    results[name] = {"player_name": name, "num_sales": 0, "error": str(e)}
                await asyncio.sleep(1)
        finally:
            await client.close()
        return results

    return asyncio.run(_run())
