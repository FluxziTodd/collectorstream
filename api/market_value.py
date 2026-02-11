"""
Market value tracking for sports cards
Fetches real sold comps from eBay Browse API
"""

import os
import httpx
import statistics
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

# eBay API Configuration
EBAY_APP_ID = os.environ.get("EBAY_APP_ID", "")
EBAY_CERT_ID = os.environ.get("EBAY_CERT_ID", "")
EBAY_API_URL = "https://api.ebay.com/buy/browse/v1"


class MarketValueFetcher:
    """Fetch market values from eBay sold listings"""

    def __init__(self):
        self.app_id = EBAY_APP_ID
        self.cert_id = EBAY_CERT_ID
        self.access_token = None
        self.token_expires = None

    async def get_oauth_token(self) -> str:
        """Get OAuth token for eBay API"""
        # Check if we have a valid cached token
        if self.access_token and self.token_expires and datetime.utcnow() < self.token_expires:
            return self.access_token

        # Get new token
        token_url = "https://api.ebay.com/identity/v1/oauth2/token"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                auth=(self.app_id, self.cert_id),
                data={
                    "grant_type": "client_credentials",
                    "scope": "https://api.ebay.com/oauth/api_scope"
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"eBay OAuth failed: {response.status_code}")

            data = response.json()
            self.access_token = data["access_token"]
            # Token expires in seconds, cache it with 5min buffer
            expires_in = data.get("expires_in", 7200) - 300
            self.token_expires = datetime.utcnow() + timedelta(seconds=expires_in)

            return self.access_token

    def build_search_query(self, card: Dict[str, Any]) -> str:
        """Build eBay search query from card details"""
        parts = []

        if card.get("player_name"):
            parts.append(card["player_name"])

        if card.get("year"):
            parts.append(card["year"])

        if card.get("card_set"):
            parts.append(card["card_set"])

        if card.get("card_number"):
            parts.append(f"#{card['card_number']}")

        # Add sport category for better filtering
        sport = card.get("sport", "").lower()
        if sport in ["baseball", "mlb"]:
            parts.append("baseball card")
        elif sport in ["basketball", "nba"]:
            parts.append("basketball card")
        elif sport in ["football", "nfl"]:
            parts.append("football card")
        elif sport in ["hockey", "nhl"]:
            parts.append("hockey card")

        return " ".join(parts)

    async def fetch_sold_comps(self, card: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch sold comps from eBay for a card"""
        token = await self.get_oauth_token()
        query = self.build_search_query(card)

        print(f"🔍 Searching eBay for: {query}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EBAY_API_URL}/item_summary/search",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
                },
                params={
                    "q": query,
                    "filter": "buyingOptions:{FIXED_PRICE|AUCTION},itemEndDate:[..],priceCurrency:USD",
                    "sort": "endDate",  # Most recent first
                    "limit": limit
                },
                timeout=30.0
            )

            if response.status_code != 200:
                print(f"❌ eBay API error: {response.status_code}")
                print(f"   Response: {response.text}")
                raise Exception(f"eBay API failed: {response.status_code}")

            data = response.json()
            items = data.get("itemSummaries", [])

            print(f"✅ Found {len(items)} sold listings")
            return items

    def filter_comps(self, items: List[Dict[str, Any]]) -> List[float]:
        """
        Filter sold comps to remove outliers and invalid listings

        Removes:
        - Lots (multiple cards)
        - Reprints
        - Graded cards (unless we're pricing a graded card)
        - Extreme outliers (> 2 std dev from median)
        """
        prices = []

        for item in items:
            title = item.get("title", "").lower()

            # Skip lots
            if "lot" in title or "bundle" in title or "set of" in title:
                continue

            # Skip reprints
            if "reprint" in title or "reproduction" in title or "tribute" in title:
                continue

            # Skip graded cards (PSA, BGS, CGC, SGC)
            # TODO: Only skip if our card is NOT graded
            if any(grade in title for grade in ["psa", "bgs", "beckett", "cgc", "sgc"]):
                continue

            # Get price
            price_info = item.get("price", {})
            if price_info and "value" in price_info:
                price = float(price_info["value"])
                if price > 0:
                    prices.append(price)

        if not prices:
            return prices

        # Remove statistical outliers (> 2 standard deviations from median)
        if len(prices) >= 5:
            median = statistics.median(prices)
            stdev = statistics.stdev(prices)

            filtered_prices = [
                p for p in prices
                if abs(p - median) <= 2 * stdev
            ]

            if filtered_prices:
                print(f"📊 Filtered {len(prices)} → {len(filtered_prices)} comps (removed outliers)")
                return filtered_prices

        return prices

    def calculate_market_value(self, prices: List[float]) -> Dict[str, Any]:
        """
        Calculate market value from filtered sold comps
        Uses MEDIAN (not average) to avoid skew from outliers
        """
        if not prices:
            return {
                "market_price": None,
                "sample_size": 0,
                "confidence_level": 0.0,
                "price_range_low": None,
                "price_range_high": None
            }

        # Use median as the market price (more robust than mean)
        market_price = statistics.median(prices)

        # Confidence based on sample size
        sample_size = len(prices)
        if sample_size >= 20:
            confidence = 0.9
        elif sample_size >= 10:
            confidence = 0.75
        elif sample_size >= 5:
            confidence = 0.6
        else:
            confidence = 0.4

        # Price range (25th to 75th percentile)
        sorted_prices = sorted(prices)
        low_idx = int(len(sorted_prices) * 0.25)
        high_idx = int(len(sorted_prices) * 0.75)

        price_range_low = sorted_prices[low_idx] if low_idx < len(sorted_prices) else sorted_prices[0]
        price_range_high = sorted_prices[high_idx] if high_idx < len(sorted_prices) else sorted_prices[-1]

        print(f"💰 Market Value: ${market_price:.2f}")
        print(f"   Range: ${price_range_low:.2f} - ${price_range_high:.2f}")
        print(f"   Sample Size: {sample_size} comps")
        print(f"   Confidence: {confidence:.0%}")

        return {
            "market_price": round(market_price, 2),
            "sample_size": sample_size,
            "confidence_level": confidence,
            "price_range_low": round(price_range_low, 2),
            "price_range_high": round(price_range_high, 2),
            "source": "ebay_sold"
        }

    async def get_card_market_value(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get current market value for a card

        1. Search eBay for sold listings
        2. Filter out lots, reprints, outliers
        3. Calculate median price
        4. Return market value with confidence
        """
        try:
            # Fetch sold comps
            items = await self.fetch_sold_comps(card)

            # Filter to valid comps
            prices = self.filter_comps(items)

            # Calculate market value
            market_value = self.calculate_market_value(prices)

            return market_value

        except Exception as e:
            print(f"❌ Market value fetch failed: {e}")
            return {
                "market_price": None,
                "sample_size": 0,
                "confidence_level": 0.0,
                "price_range_low": None,
                "price_range_high": None,
                "source": "ebay_sold",
                "error": str(e)
            }


# Global instance
_fetcher = None

def get_market_fetcher() -> MarketValueFetcher:
    """Get global market value fetcher instance"""
    global _fetcher
    if _fetcher is None:
        _fetcher = MarketValueFetcher()
    return _fetcher
