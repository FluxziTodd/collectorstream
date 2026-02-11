"""Name normalization to handle spelling variations across sources."""

import re
from db.models import get_connection

# Known name mappings: {variant: canonical_name}
# Add entries here as you discover spelling differences between sources
NAME_ALIASES = {
    # 2026 class
    "azzi fam": "Azzi Fudd",
    "flau'jae johnson": "Flau'Jae Johnson",
    "flaujae johnson": "Flau'Jae Johnson",
    "gabriela jaquez": "Gabriella Jaquez",
    "cotie mcmahhon": "Cotie McMahon",
    "marta suárez": "Marta Suarez",
    "marta suarez": "Marta Suarez",
    "ta'niya latson": "Ta'Niya Latson",
    "taniya latson": "Ta'Niya Latson",
    "serah williams": "Sarah Williams",
    # 2027 class
    "juju watkins": "JuJu Watkins",
    "milaysia fulwiley": "MiLaysia Fulwiley",
    "milaysia fulwiley": "MiLaysia Fulwiley",
    "mikaylah williams": "Mikalah Williams",
    "mikalah williams": "Mikalah Williams",
    "zoey brooks": "Zoe Brooks",
    "zoe brooks": "Zoe Brooks",
    "taliah scott": "Talia Scott",
    "talia scott": "Talia Scott",
    "talaysia cooper": "Talausia Cooper",
    "talausia cooper": "Talausia Cooper",
    # 2028 class
    "sara strong": "Sarah Strong",
    "sarah strong": "Sarah Strong",
    "jana eli alfy": "Jana El Alfy",
    "jana el alfy": "Jana El Alfy",
    "tajanna roberts": "Tajianna Roberts",
    "tajianna roberts": "Tajianna Roberts",
    "kiyomi mcmiller": "Kiyomi McMiller",
}


def normalize_name(name):
    """Return the canonical form of a player name."""
    key = name.strip().lower()
    return NAME_ALIASES.get(key, name.strip())


def merge_duplicate_players():
    """Find and merge players with the same normalized name in the database."""
    conn = get_connection()

    # Get all players
    players = conn.execute("SELECT id, name, draft_year FROM players ORDER BY id").fetchall()

    # Group by (normalized_name, draft_year)
    groups = {}
    for p in players:
        key = (normalize_name(p["name"]).lower(), p["draft_year"])
        groups.setdefault(key, []).append(dict(p))

    merged_count = 0
    for key, dupes in groups.items():
        if len(dupes) < 2:
            continue

        canonical_name = normalize_name(dupes[0]["name"])

        # Prefer the record that already has the canonical name
        canonical = None
        for d in dupes:
            if d["name"] == canonical_name:
                canonical = d
                break
        if canonical is None:
            canonical = dupes[0]

        # Update canonical record's name to the normalized form
        if canonical["name"] != canonical_name:
            conn.execute("UPDATE players SET name = ? WHERE id = ?",
                         (canonical_name, canonical["id"]))

        for dupe in dupes:
            if dupe["id"] == canonical["id"]:
                continue
            # Move rankings to canonical player
            conn.execute("UPDATE OR IGNORE rankings SET player_id = ? WHERE player_id = ?",
                         (canonical["id"], dupe["id"]))
            # Move card values
            conn.execute("UPDATE OR IGNORE card_values SET player_id = ? WHERE player_id = ?",
                         (canonical["id"], dupe["id"]))
            # Delete leftover rankings (conflicts from OR IGNORE)
            conn.execute("DELETE FROM rankings WHERE player_id = ?", (dupe["id"],))
            conn.execute("DELETE FROM card_values WHERE player_id = ?", (dupe["id"],))
            # Delete duplicate player
            conn.execute("DELETE FROM players WHERE id = ?", (dupe["id"],))
            print(f"  Merged '{dupe['name']}' -> '{canonical_name}'")
            merged_count += 1

    conn.commit()
    conn.close()
    print(f"Merged {merged_count} duplicate players")
    return merged_count
