"""eBay Browse API client for searching autograph/rookie card prices."""

import os
import time
import base64
import requests
from datetime import datetime, date
from urllib.parse import quote_plus


class EbayClient:
    """eBay Browse API client with OAuth token management."""

    TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    SCOPE = "https://api.ebay.com/oauth/api_scope"

    # Sports Trading Cards category
    CATEGORY_ID = "183050"

    def __init__(self):
        self.client_id = os.environ.get("EBAY_CLIENT_ID", "")
        self.client_secret = os.environ.get("EBAY_CLIENT_SECRET", "")
        self._token = None
        self._token_expires = 0

    def _get_token(self):
        """Get OAuth access token using client credentials grant."""
        if self._token and time.time() < self._token_expires - 60:
            return self._token

        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        resp = requests.post(
            self.TOKEN_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {credentials}",
            },
            data={
                "grant_type": "client_credentials",
                "scope": self.SCOPE,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        self._token = data["access_token"]
        self._token_expires = time.time() + data.get("expires_in", 7200)
        return self._token

    def search_cards(self, player_name, card_type="autograph", min_price=1.0,
                     limit=50, category_id="DEFAULT"):
        """Search eBay for cards matching a player name.

        Returns list of items with price, title, URL, image.
        """
        token = self._get_token()

        # Build search query — don't quote the name to get broader matches
        query = f"{player_name} {card_type}"

        params = {
            "q": query,
            "filter": f"price:[{min_price}..],priceCurrency:USD",
            "limit": min(limit, 200),
            "sort": "price",
        }

        # Use default category unless explicitly set to None
        cat = self.CATEGORY_ID if category_id == "DEFAULT" else category_id
        if cat:
            params["category_ids"] = cat

        resp = requests.get(
            self.SEARCH_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            },
            params=params,
            timeout=15,
        )

        if resp.status_code == 204:
            return []

        resp.raise_for_status()
        data = resp.json()

        items = []
        for item in data.get("itemSummaries", []):
            price_val = None
            price_info = item.get("price", {})
            if price_info.get("value"):
                try:
                    price_val = float(price_info["value"])
                except (ValueError, TypeError):
                    pass

            items.append({
                "title": item.get("title", ""),
                "price": price_val,
                "currency": price_info.get("currency", "USD"),
                "url": item.get("itemWebUrl", ""),
                "image": item.get("image", {}).get("imageUrl", ""),
                "condition": item.get("condition", ""),
                "item_id": item.get("itemId", ""),
                "buying_options": item.get("buyingOptions", []),
            })

        return items

    def search_specific_card(self, query, min_price=0.5, limit=50):
        """Search eBay with a precise query string built from a card fingerprint.

        Unlike get_player_card_summary which uses a broad fallback cascade,
        this uses the exact query to find a specific card variant.
        """
        token = self._get_token()

        params = {
            "q": query,
            "filter": f"price:[{min_price}..],priceCurrency:USD",
            "limit": min(limit, 200),
            "sort": "price",
            "category_ids": self.CATEGORY_ID,
        }

        resp = requests.get(
            self.SEARCH_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            },
            params=params,
            timeout=15,
        )

        if resp.status_code == 204:
            return []

        resp.raise_for_status()
        data = resp.json()

        items = []
        for item in data.get("itemSummaries", []):
            price_val = None
            price_info = item.get("price", {})
            if price_info.get("value"):
                try:
                    price_val = float(price_info["value"])
                except (ValueError, TypeError):
                    pass

            items.append({
                "title": item.get("title", ""),
                "price": price_val,
                "currency": price_info.get("currency", "USD"),
                "url": item.get("itemWebUrl", ""),
                "image": item.get("image", {}).get("imageUrl", ""),
                "condition": item.get("condition", ""),
                "item_id": item.get("itemId", ""),
                "buying_options": item.get("buyingOptions", []),
            })

        return items

    def get_player_card_summary(self, player_name):
        """Get price summary for a player's autograph cards.

        Tries multiple search strategies to find listings:
        1. "player auto" in sports cards category
        2. "player autograph" in sports cards category
        3. "player auto" without category restriction
        4. "player card" without category restriction

        Returns dict with lowest_bin, avg_price, listing_count, ebay_url.
        """
        # Deduplicate items across searches by item_id
        seen_ids = set()
        all_items = []

        def _add_items(new_items):
            for item in new_items:
                iid = item.get("item_id")
                if iid and iid not in seen_ids:
                    seen_ids.add(iid)
                    all_items.append(item)

        # Try "auto" first (more common in card listings than "autograph")
        _add_items(self.search_cards(player_name, card_type="auto", limit=200))

        # Try "autograph" in category
        if len(all_items) < 5:
            _add_items(self.search_cards(player_name, card_type="autograph", limit=200))

        # Try without category restriction if still few results
        if len(all_items) < 3:
            _add_items(self.search_cards(
                player_name, card_type="auto", limit=200, category_id=None))

        # Last resort: broader "card" search without category
        if not all_items:
            _add_items(self.search_cards(
                player_name, card_type="card", limit=200, category_id=None))

        prices = [i["price"] for i in all_items if i["price"] and i["price"] > 0]

        ebay_search_url = (
            f"https://www.ebay.com/sch/i.html?_nkw="
            f"{quote_plus(player_name + ' auto card')}"
        )

        if not prices:
            return {
                "player_name": player_name,
                "lowest_bin": None,
                "avg_price": None,
                "listing_count": 0,
                "items": [],
                "ebay_search_url": ebay_search_url,
            }

        # Sort by price
        all_items.sort(key=lambda x: x.get("price") or 999999)

        return {
            "player_name": player_name,
            "lowest_bin": min(prices),
            "avg_price": round(sum(prices) / len(prices), 2),
            "listing_count": len(prices),
            "items": all_items[:10],
            "ebay_search_url": ebay_search_url,
        }
