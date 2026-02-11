"""Tier rating system for player classification based on consensus draft rankings."""

from db.models import get_connection, update_player_tier
from analysis.movers import get_consensus_board


def calculate_tier(avg_rank, num_sources):
    """
    Calculate tier based on consensus draft ranking.

    Tier A: avg_rank 1-5 (lottery picks, sure things)
    Tier B: avg_rank 6-12 (first round)
    Tier C: avg_rank 13-24 (second round)
    Tier D: avg_rank 25+ or unranked (fringe/developmental)

    Requires at least 2 sources to avoid single-source bias.
    Returns None if insufficient data.
    """
    if num_sources < 2 or avg_rank is None:
        return None  # Not enough data for reliable tier

    if avg_rank <= 5:
        return 'A'
    elif avg_rank <= 12:
        return 'B'
    elif avg_rank <= 24:
        return 'C'
    else:
        return 'D'


def recalculate_all_tiers(draft_year=None):
    """
    Recalculate tiers for all players based on current consensus rankings.

    Args:
        draft_year: Optional year to filter (None = all years)

    Returns:
        dict with counts: {'A': n, 'B': n, 'C': n, 'D': n, 'unranked': n}
    """
    conn = get_connection()

    # Get all draft years if not specified
    if draft_year:
        years = [draft_year]
    else:
        rows = conn.execute("SELECT DISTINCT draft_year FROM players ORDER BY draft_year").fetchall()
        years = [r['draft_year'] for r in rows]

    conn.close()

    tier_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'unranked': 0}
    updated_players = []

    for year in years:
        board = get_consensus_board(year)

        for player in board:
            avg_rank = player.get('avg_rank')
            num_sources = player.get('num_sources', 0)

            tier = calculate_tier(avg_rank, num_sources)

            # Update player's tier in database
            update_player_tier(player['id'], tier)

            if tier:
                tier_counts[tier] += 1
                updated_players.append({
                    'name': player['name'],
                    'draft_year': year,
                    'avg_rank': round(avg_rank, 1) if avg_rank else None,
                    'num_sources': num_sources,
                    'tier': tier
                })
            else:
                tier_counts['unranked'] += 1

    return tier_counts, updated_players


def get_tier_summary(draft_year):
    """Get a summary of players by tier for a draft year."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT tier, COUNT(*) as count
        FROM players
        WHERE draft_year = ? AND tier IS NOT NULL
        GROUP BY tier
        ORDER BY tier
    """, (draft_year,)).fetchall()
    conn.close()
    return {r['tier']: r['count'] for r in rows}


def get_players_by_tier(draft_year, tier):
    """Get all players with a specific tier for a draft year."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.*,
               (SELECT AVG(r.rank) FROM rankings r WHERE r.player_id = p.id) as avg_rank
        FROM players p
        WHERE p.draft_year = ? AND p.tier = ?
        ORDER BY avg_rank, p.name
    """, (draft_year, tier.upper())).fetchall()
    conn.close()
    return [dict(r) for r in rows]
