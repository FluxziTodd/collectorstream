"""Analysis module for detecting rising/falling prospects and card buying signals.

Supports multi-sport filtering via sport parameter (WNBA, NBA, NFL, NHL, MLB).
"""

from collections import defaultdict
from db.models import get_connection


def get_movers(draft_year=None, days_back=30, sport=None):
    """Find players whose rankings have changed significantly.

    Args:
        draft_year: Optional draft year filter
        days_back: Number of days to look back for changes (default 30)
        sport: Optional sport filter (WNBA, NBA, NFL, etc.)

    Returns players sorted by biggest rank improvement (risers first).
    """
    conn = get_connection()
    query = """
        WITH ranked AS (
            SELECT
                r.player_id,
                p.name,
                p.draft_year,
                p.school,
                p.sport,
                r.source,
                r.rank,
                r.projected_pick,
                r.scrape_date,
                ROW_NUMBER() OVER (
                    PARTITION BY r.player_id, r.source
                    ORDER BY r.scrape_date DESC
                ) as recency
            FROM rankings r
            JOIN players p ON p.id = r.player_id
            WHERE r.scrape_date >= date('now', ?)
    """
    params = [f"-{days_back} days"]

    if draft_year:
        query += " AND p.draft_year = ?"
        params.append(draft_year)

    if sport:
        query += " AND p.sport = ?"
        params.append(sport.upper())

    query += """
        ),
        changes AS (
            SELECT
                player_id, name, draft_year, school, source,
                MAX(CASE WHEN recency = 1 THEN rank END) as current_rank,
                MAX(CASE WHEN recency = 2 THEN rank END) as previous_rank,
                MAX(CASE WHEN recency = 1 THEN projected_pick END) as current_pick,
                MAX(CASE WHEN recency = 2 THEN projected_pick END) as previous_pick
            FROM ranked
            WHERE recency <= 2
            GROUP BY player_id, source
        )
        SELECT
            player_id, name, draft_year, school, source,
            current_rank, previous_rank,
            current_pick, previous_pick,
            (previous_rank - current_rank) as rank_change,
            (previous_pick - current_pick) as pick_change
        FROM changes
        WHERE previous_rank IS NOT NULL AND current_rank IS NOT NULL
        ORDER BY rank_change DESC
    """

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_consensus_board(draft_year, sport=None):
    """Build a consensus big board averaging rankings across all sources.

    Args:
        draft_year: The draft year to get board for
        sport: Optional sport filter (WNBA, NBA, NFL, etc.)
    """
    conn = get_connection()

    if sport:
        rows = conn.execute("""
            SELECT
                p.id, p.name, p.school, p.position, p.draft_year, p.sport,
                AVG(r.rank) as avg_rank,
                AVG(r.projected_pick) as avg_pick,
                COUNT(DISTINCT r.source) as num_sources,
                GROUP_CONCAT(DISTINCT r.source || ':' || COALESCE(r.rank, '?')) as source_ranks
            FROM players p
            LEFT JOIN rankings r ON p.id = r.player_id
                AND r.scrape_date = (
                    SELECT MAX(r2.scrape_date) FROM rankings r2
                    WHERE r2.player_id = r.player_id AND r2.source = r.source
                )
            WHERE p.draft_year = ? AND p.sport = ?
            GROUP BY p.id
            ORDER BY COALESCE(avg_rank, 999), p.name
        """, (draft_year, sport.upper())).fetchall()
    else:
        rows = conn.execute("""
            SELECT
                p.id, p.name, p.school, p.position, p.draft_year, p.sport,
                AVG(r.rank) as avg_rank,
                AVG(r.projected_pick) as avg_pick,
                COUNT(DISTINCT r.source) as num_sources,
                GROUP_CONCAT(DISTINCT r.source || ':' || COALESCE(r.rank, '?')) as source_ranks
            FROM players p
            LEFT JOIN rankings r ON p.id = r.player_id
                AND r.scrape_date = (
                    SELECT MAX(r2.scrape_date) FROM rankings r2
                    WHERE r2.player_id = r.player_id AND r2.source = r.source
                )
            WHERE p.draft_year = ?
            GROUP BY p.id
            ORDER BY COALESCE(avg_rank, 999), p.name
        """, (draft_year,)).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def get_new_entries(days_back=7):
    """Find players who just appeared in mock drafts for the first time."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.id, p.name, p.draft_year, p.school,
               r.source, r.rank, r.projected_pick, r.scrape_date
        FROM players p
        JOIN rankings r ON p.id = r.player_id
        WHERE p.created_at >= datetime('now', ?)
        ORDER BY p.draft_year, r.rank
    """, (f"-{days_back} days",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def card_buy_signals(draft_year=None, sport=None):
    """Identify players whose cards might be undervalued.

    Args:
        draft_year: Optional draft year filter
        sport: Optional sport filter (WNBA, NBA, NFL, etc.)

    Buy signals:
    - Rising in multiple mock drafts
    - Just entered top rankings for first time
    - Consensus rank better than individual source rank (market hasn't caught up)
    """
    signals = []

    # Risers across sources
    movers = get_movers(draft_year, days_back=30, sport=sport)
    riser_counts = defaultdict(int)
    for m in movers:
        if m["rank_change"] and m["rank_change"] > 0:
            riser_counts[m["player_id"]] += 1

    for player_id, count in riser_counts.items():
        if count >= 2:  # Rising in 2+ sources
            player_movers = [m for m in movers if m["player_id"] == player_id]
            signals.append({
                "player_id": player_id,
                "name": player_movers[0]["name"],
                "draft_year": player_movers[0]["draft_year"],
                "signal": "RISING",
                "detail": f"Rising in {count} sources",
                "sources": [
                    {"source": m["source"], "change": m["rank_change"]}
                    for m in player_movers if m["rank_change"] > 0
                ],
            })

    # New entries
    new = get_new_entries(days_back=14)
    seen = set()
    for n in new:
        if n["id"] not in seen:
            seen.add(n["id"])
            if draft_year is None or n["draft_year"] == draft_year:
                signals.append({
                    "player_id": n["id"],
                    "name": n["name"],
                    "draft_year": n["draft_year"],
                    "signal": "NEW_ENTRY",
                    "detail": f"Just appeared in {n['source']} at #{n.get('rank', '?')}",
                })

    return signals
