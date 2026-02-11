"""Portfolio price tracking, trend analysis, and buy/sell signals."""

import asyncio
import time
from datetime import date, datetime, timedelta

from db.models import (
    get_portfolio_cards, get_portfolio_card, add_portfolio_price,
    get_portfolio_price_history, add_title_mapping,
)
from analysis.fingerprint import (
    build_fingerprint, build_ebay_query, score_title_match, parse_title,
    card_description,
)


def price_check_card_ebay(card, ebay_client):
    """Look up eBay active listing prices for a specific portfolio card.

    Returns number of matched prices stored.
    """
    fp = build_fingerprint(card)
    stored = 0

    # Try progressively broader queries
    for level in (1, 2, 3):
        query = build_ebay_query(fp, level=level)
        try:
            items = ebay_client.search_specific_card(query, min_price=0.5, limit=50)
        except Exception as e:
            print(f"    eBay search failed (level {level}): {e}")
            continue

        for item in items:
            title = item.get("title", "")
            price = item.get("price")
            if not price or not title:
                continue
            score = score_title_match(title, fp)
            if score >= 0.5:
                add_portfolio_price(
                    card["id"], price, "ebay_active",
                    title=title, match_confidence=score,
                )
                stored += 1

                # Store title mapping for learning
                try:
                    parsed = parse_title(title, player_name=card["player_name"])
                    add_title_mapping(
                        raw_title=title, source="ebay",
                        player_name=card["player_name"],
                        card_year=parsed.get("card_year"),
                        manufacturer=parsed.get("manufacturer"),
                        set_name=parsed.get("set_name"),
                        parallel=parsed.get("parallel"),
                        is_numbered=parsed.get("is_numbered"),
                        numbered_to=parsed.get("numbered_to"),
                        is_autograph=parsed.get("is_autograph"),
                        is_rookie=parsed.get("is_rookie"),
                        grade=parsed.get("grade"),
                    )
                except Exception:
                    pass

        if stored > 0:
            break  # Got matches at this level, no need to broaden

    return stored


def price_check_card_cardladder(card, cl_client):
    """Look up Card Ladder sold prices for a specific portfolio card.

    Uses async Card Ladder client. Returns number of matched prices stored.
    """
    fp = build_fingerprint(card)

    async def _search():
        stored = 0
        try:
            matched = await cl_client.search_and_match(
                card["player_name"], fp, limit=20, min_confidence=0.5
            )
            for sale in matched:
                price = sale.get("price")
                if not price:
                    continue
                add_portfolio_price(
                    card["id"], price, "cardladder",
                    sale_type=sale.get("sale_type"),
                    title=sale.get("title"),
                    match_confidence=sale.get("match_confidence", 0.5),
                    recorded_date=sale.get("date_sold"),
                )
                stored += 1
        except Exception as e:
            print(f"    Card Ladder search failed: {e}")
        return stored

    return asyncio.run(_search())


def price_check_all(use_cardladder=False, delay=1.0):
    """Run price lookup for all active portfolio cards.

    Args:
        use_cardladder: If True, also check Card Ladder (requires browser).
        delay: Seconds between API calls for rate limiting.
    """
    from scrapers.ebay import EbayClient

    cards = get_portfolio_cards(status="active")
    if not cards:
        print("No active portfolio cards to check.")
        return

    print(f"Checking prices for {len(cards)} card(s)...")
    ebay = EbayClient()

    cl_client = None
    if use_cardladder:
        from scrapers.cardladder import CardLadderClient
        cl_client = CardLadderClient()

    for card in cards:
        desc = card_description(card)
        print(f"  {card['player_name']} — {desc}...", end=" ", flush=True)

        ebay_count = price_check_card_ebay(card, ebay)
        cl_count = 0

        if cl_client:
            cl_count = price_check_card_cardladder(card, cl_client)

        total = ebay_count + cl_count
        if total > 0:
            print(f"{total} price(s) matched (eBay: {ebay_count}, CL: {cl_count})")
        else:
            print("no matches")

        time.sleep(delay)

    if cl_client:
        asyncio.run(cl_client.close())

    print(f"\nPrice check complete for {len(cards)} card(s).")


def calculate_trends(card_id):
    """Calculate moving averages and price momentum for a portfolio card.

    Returns dict with current_price, ma_7, ma_30, momentum, signal,
    gain_loss, gain_loss_pct, price_history.
    """
    card = get_portfolio_card(card_id)
    if not card:
        return None

    history = get_portfolio_price_history(card_id)
    purchase_price = card.get("purchase_price") or 0

    if not history:
        return {
            "card_id": card_id,
            "current_price": None,
            "ma_7": None,
            "ma_30": None,
            "momentum": "insufficient_data",
            "signal": "HOLD",
            "signal_reason": "No price data yet",
            "gain_loss": None,
            "gain_loss_pct": None,
            "price_count": 0,
        }

    # Group prices by date, take average per day
    daily_prices = {}
    for h in history:
        d = h["recorded_date"]
        if d not in daily_prices:
            daily_prices[d] = []
        daily_prices[d].append(h["price"])

    sorted_dates = sorted(daily_prices.keys())
    daily_avgs = [(d, sum(daily_prices[d]) / len(daily_prices[d])) for d in sorted_dates]

    current_price = daily_avgs[-1][1] if daily_avgs else None

    # Moving averages
    def _ma(prices, n):
        if len(prices) < 1:
            return None
        recent = prices[-n:] if len(prices) >= n else prices
        return sum(p for _, p in recent) / len(recent)

    ma_7 = _ma(daily_avgs, 7)
    ma_30 = _ma(daily_avgs, 30)

    # Momentum
    momentum = "insufficient_data"
    if ma_7 is not None and ma_30 is not None and ma_30 > 0:
        pct_diff = (ma_7 - ma_30) / ma_30
        if pct_diff > 0.10:
            momentum = "rising"
        elif pct_diff < -0.10:
            momentum = "falling"
        else:
            momentum = "stable"
    elif len(daily_avgs) >= 2:
        # With limited data, compare first vs last
        first = daily_avgs[0][1]
        last = daily_avgs[-1][1]
        if first > 0:
            pct_change = (last - first) / first
            if pct_change > 0.10:
                momentum = "rising"
            elif pct_change < -0.10:
                momentum = "falling"
            else:
                momentum = "stable"

    # Signal logic
    signal = "HOLD"
    signal_reason = ""

    days_held = 0
    if card.get("purchase_date"):
        try:
            pdate = datetime.fromisoformat(card["purchase_date"])
            days_held = (datetime.now() - pdate).days
        except (ValueError, TypeError):
            pass

    if len(daily_avgs) < 3:
        signal = "HOLD"
        signal_reason = "Insufficient price data"
    elif days_held < 30:
        signal = "HOLD"
        signal_reason = f"Held {days_held} days — too early to signal"
    elif momentum == "falling":
        if current_price and purchase_price and current_price < purchase_price:
            signal = "SELL"
            signal_reason = "Falling price, below purchase — cut losses"
        elif current_price and purchase_price and current_price > purchase_price * 1.3:
            signal = "SELL"
            signal_reason = "Falling price, still profitable — lock in gains"
        else:
            signal = "HOLD"
            signal_reason = "Falling but near purchase price — monitor"
    elif momentum == "rising":
        signal = "HOLD"
        signal_reason = "Rising trend — hold for gains"
    else:
        signal = "HOLD"
        signal_reason = "Stable price — no urgency"

    # Gain/loss
    gain_loss = None
    gain_loss_pct = None
    if current_price is not None and purchase_price:
        gain_loss = current_price - purchase_price
        gain_loss_pct = (gain_loss / purchase_price) * 100

    return {
        "card_id": card_id,
        "current_price": current_price,
        "ma_7": round(ma_7, 2) if ma_7 else None,
        "ma_30": round(ma_30, 2) if ma_30 else None,
        "momentum": momentum,
        "signal": signal,
        "signal_reason": signal_reason,
        "gain_loss": round(gain_loss, 2) if gain_loss is not None else None,
        "gain_loss_pct": round(gain_loss_pct, 1) if gain_loss_pct is not None else None,
        "price_count": len(history),
    }


def get_portfolio_summary():
    """Get portfolio summary stats."""
    cards = get_portfolio_cards(status="active")
    total_invested = 0
    total_current = 0
    total_cards = len(cards)
    signals = {"HOLD": 0, "SELL": 0}

    card_details = []
    for card in cards:
        trends = calculate_trends(card["id"])
        purchase = card.get("purchase_price") or 0
        current = trends.get("current_price") or purchase
        total_invested += purchase
        total_current += current
        signals[trends.get("signal", "HOLD")] = signals.get(trends.get("signal", "HOLD"), 0) + 1

        card_details.append({
            **card,
            "description": card_description(card),
            "trends": trends,
        })

    return {
        "total_cards": total_cards,
        "total_invested": round(total_invested, 2),
        "total_current": round(total_current, 2),
        "unrealized_gain_loss": round(total_current - total_invested, 2),
        "unrealized_pct": round(((total_current - total_invested) / total_invested * 100), 1) if total_invested else 0,
        "signals": signals,
        "cards": card_details,
    }


def export_portfolio_json():
    """Export portfolio data as JSON for the web dashboard."""
    import json
    summary = get_portfolio_summary()

    # Serialize for JSON (handle sqlite3.Row leftovers)
    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_clean(i) for i in obj]
        return obj

    return json.dumps(_clean(summary), indent=2, default=str)
