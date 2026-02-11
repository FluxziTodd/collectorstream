"""Card price tracking and analysis using eBay data."""

import time
from datetime import date

from db.models import (
    get_connection, get_players_by_draft_year, add_card_value,
    get_latest_card_values, get_card_price_history,
)
from scrapers.ebay import EbayClient
from analysis.movers import get_consensus_board

DRAFT_YEARS = [2026, 2027, 2028, 2029, 2030]


def track_player_cards(player_id, player_name, ebay_client=None):
    """Search eBay for a player's autograph cards and store prices."""
    if ebay_client is None:
        ebay_client = EbayClient()

    summary = ebay_client.get_player_card_summary(player_name)

    add_card_value(
        player_id=player_id,
        value_dollars=summary["lowest_bin"],
        card_type="autograph",
        source="ebay",
        listing_count=summary["listing_count"],
        lowest_bin=summary["lowest_bin"],
        avg_price=summary["avg_price"],
        ebay_search_url=summary["ebay_search_url"],
        notes=f"{summary['listing_count']} listings found" if summary["listing_count"] else "No listings found",
    )

    return summary


def track_all_players(draft_year=None, delay=1.0):
    """Search eBay for all tracked players and store card prices.

    Args:
        draft_year: Optional filter to specific draft class
        delay: Seconds between API calls (rate limiting)
    """
    ebay = EbayClient()
    years = [draft_year] if draft_year else DRAFT_YEARS

    total = 0
    found = 0

    for year in years:
        players = get_players_by_draft_year(year)
        if not players:
            continue

        print(f"\n--- {year} Draft Class ({len(players)} players) ---")

        for p in players:
            total += 1
            print(f"  Searching: {p['name']}...", end=" ", flush=True)

            try:
                summary = track_player_cards(p["id"], p["name"], ebay)
                if summary["listing_count"] > 0:
                    found += 1
                    print(f"${summary['lowest_bin']:.2f} lowest "
                          f"(${summary['avg_price']:.2f} avg, "
                          f"{summary['listing_count']} listings)")
                else:
                    print("no listings")
            except Exception as e:
                print(f"ERROR: {e}")

            time.sleep(delay)

    print(f"\nDone: {found}/{total} players have cards on eBay")
    return {"total": total, "found": found}


def get_best_buys(draft_year=None):
    """Find undervalued cards: high-ranked players with cheap autographs.

    Returns players sorted by value score (rank / price — higher is better buy).
    """
    conn = get_connection()

    query = """
        SELECT p.id, p.name, p.draft_year, p.school,
               cv.lowest_bin, cv.avg_price, cv.listing_count, cv.ebay_search_url,
               r_avg.avg_rank
        FROM players p
        JOIN card_values cv ON p.id = cv.player_id
            AND cv.source = 'ebay'
            AND cv.recorded_date = (
                SELECT MAX(cv2.recorded_date) FROM card_values cv2
                WHERE cv2.player_id = cv.player_id AND cv2.source = 'ebay'
            )
        LEFT JOIN (
            SELECT player_id, AVG(rank) as avg_rank
            FROM rankings r
            WHERE r.scrape_date = (
                SELECT MAX(r2.scrape_date) FROM rankings r2
                WHERE r2.player_id = r.player_id AND r2.source = r.source
            )
            GROUP BY player_id
        ) r_avg ON p.id = r_avg.player_id
        WHERE cv.lowest_bin IS NOT NULL AND cv.lowest_bin > 0
    """
    params = []
    if draft_year:
        query += " AND p.draft_year = ?"
        params.append(draft_year)

    query += " ORDER BY cv.lowest_bin ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        # Value score: lower rank (better player) + lower price = better buy
        if d["avg_rank"] and d["lowest_bin"]:
            d["value_score"] = round(d["avg_rank"] / d["lowest_bin"] * 100, 1)
        else:
            d["value_score"] = None
        results.append(d)

    # Sort by value score descending (best buys first)
    results.sort(key=lambda x: x.get("value_score") or 0, reverse=True)
    return results


def get_price_changes(days_back=7):
    """Find players whose card prices changed significantly."""
    conn = get_connection()
    rows = conn.execute("""
        WITH latest AS (
            SELECT player_id, lowest_bin, avg_price, listing_count, recorded_date,
                   ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY recorded_date DESC) as rn
            FROM card_values WHERE source = 'ebay'
        ),
        previous AS (
            SELECT player_id, lowest_bin, avg_price, listing_count, recorded_date,
                   ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY recorded_date DESC) as rn
            FROM card_values
            WHERE source = 'ebay'
              AND recorded_date < (SELECT MAX(recorded_date) FROM card_values WHERE source = 'ebay')
        )
        SELECT p.id, p.name, p.draft_year,
               l.lowest_bin as current_price, l.listing_count as current_listings,
               prev.lowest_bin as prev_price, prev.listing_count as prev_listings,
               l.recorded_date as current_date, prev.recorded_date as prev_date
        FROM players p
        JOIN latest l ON p.id = l.player_id AND l.rn = 1
        JOIN previous prev ON p.id = prev.player_id AND prev.rn = 1
        WHERE l.lowest_bin IS NOT NULL AND prev.lowest_bin IS NOT NULL
          AND l.lowest_bin != prev.lowest_bin
        ORDER BY (prev.lowest_bin - l.lowest_bin) / prev.lowest_bin DESC
    """).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        if d["prev_price"] and d["prev_price"] > 0:
            d["pct_change"] = round(
                (d["current_price"] - d["prev_price"]) / d["prev_price"] * 100, 1
            )
        else:
            d["pct_change"] = None
        results.append(d)

    return results
