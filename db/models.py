"""SQLite database models for tracking sports prospects and mock draft rankings.

Supports multiple sports: WNBA, NBA, NFL, NHL, MLB
"""

import sqlite3
from pathlib import Path
from datetime import datetime, date

DB_PATH = Path(__file__).parent.parent / "data" / "prospects.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            draft_year INTEGER NOT NULL,
            school TEXT,
            position TEXT,
            height TEXT,
            hometown TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(name, draft_year)
        );

        CREATE TABLE IF NOT EXISTS rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL REFERENCES players(id),
            source TEXT NOT NULL,
            rank INTEGER,
            projected_pick INTEGER,
            projected_round INTEGER,
            scrape_date TEXT NOT NULL,
            url TEXT,
            raw_text TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(player_id, source, scrape_date)
        );

        CREATE TABLE IF NOT EXISTS card_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL REFERENCES players(id),
            card_type TEXT DEFAULT 'autograph',
            value_dollars REAL,
            recorded_date TEXT NOT NULL,
            notes TEXT,
            source TEXT DEFAULT 'manual',
            listing_count INTEGER,
            lowest_bin REAL,
            avg_price REAL,
            ebay_search_url TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(player_id, card_type, source, recorded_date)
        );

        CREATE TABLE IF NOT EXISTS scrape_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            url TEXT NOT NULL,
            draft_year INTEGER,
            status TEXT NOT NULL,
            players_found INTEGER DEFAULT 0,
            error_message TEXT,
            scraped_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            sport TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS watchlist_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            watchlist_id INTEGER NOT NULL REFERENCES watchlist(id),
            card_type TEXT DEFAULT 'autograph',
            lowest_bin REAL,
            avg_price REAL,
            listing_count INTEGER,
            ebay_search_url TEXT,
            recorded_date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(watchlist_id, card_type, recorded_date)
        );

        CREATE TABLE IF NOT EXISTS portfolio_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER REFERENCES players(id),
            player_name TEXT NOT NULL,
            card_year INTEGER NOT NULL,
            manufacturer TEXT NOT NULL,
            set_name TEXT NOT NULL,
            card_number TEXT,
            parallel TEXT DEFAULT 'Base',
            is_numbered INTEGER DEFAULT 0,
            numbered_to INTEGER,
            serial_number INTEGER,
            is_autograph INTEGER DEFAULT 0,
            is_rookie INTEGER DEFAULT 0,
            grade TEXT DEFAULT 'Raw',
            purchase_price REAL,
            purchase_date TEXT,
            notes TEXT,
            status TEXT DEFAULT 'active',
            sold_price REAL,
            sold_date TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS portfolio_price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_card_id INTEGER NOT NULL REFERENCES portfolio_cards(id),
            price REAL NOT NULL,
            source TEXT NOT NULL,
            sale_type TEXT,
            title TEXT,
            match_confidence REAL DEFAULT 1.0,
            recorded_date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS card_title_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_title TEXT NOT NULL UNIQUE,
            player_name TEXT,
            card_year INTEGER,
            manufacturer TEXT,
            set_name TEXT,
            parallel TEXT,
            is_numbered INTEGER,
            numbered_to INTEGER,
            is_autograph INTEGER,
            is_rookie INTEGER,
            grade TEXT,
            source TEXT,
            confirmed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS player_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL REFERENCES players(id),
            season TEXT NOT NULL,
            stat_type TEXT DEFAULT 'season_avg',
            game_date TEXT,
            opponent TEXT,
            games_played INTEGER,
            points_per_game REAL,
            rebounds_per_game REAL,
            assists_per_game REAL,
            steals_per_game REAL,
            blocks_per_game REAL,
            fg_pct REAL,
            three_pct REAL,
            ft_pct REAL,
            minutes_per_game REAL,
            source_url TEXT,
            scraped_date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(player_id, season, stat_type, game_date)
        );

        CREATE TABLE IF NOT EXISTS player_status_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL REFERENCES players(id),
            status TEXT NOT NULL,
            reason TEXT,
            detected_date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_rankings_player ON rankings(player_id);
        CREATE INDEX IF NOT EXISTS idx_rankings_source_date ON rankings(source, scrape_date);
        CREATE INDEX IF NOT EXISTS idx_players_draft_year ON players(draft_year);
        CREATE INDEX IF NOT EXISTS idx_portfolio_price_card ON portfolio_price_history(portfolio_card_id);
        CREATE INDEX IF NOT EXISTS idx_portfolio_price_date ON portfolio_price_history(recorded_date);
        CREATE INDEX IF NOT EXISTS idx_title_map_player ON card_title_mappings(player_name);
        CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_stats(player_id);
        CREATE INDEX IF NOT EXISTS idx_portfolio_cards_status ON portfolio_cards(status);
    """)
    # Add user_email column if it doesn't exist (migration for existing DBs)
    try:
        conn.execute("ALTER TABLE portfolio_cards ADD COLUMN user_email TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists
    # Create index on user_email
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_cards_user ON portfolio_cards(user_email)")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    # Add photo_url, country, tier columns for player dashboard (migration)
    for col in ["photo_url TEXT", "country TEXT", "tier TEXT"]:
        try:
            conn.execute(f"ALTER TABLE players ADD COLUMN {col}")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Add sport column for multi-sport support (migration)
    try:
        conn.execute("ALTER TABLE players ADD COLUMN sport TEXT DEFAULT 'WNBA'")
        conn.commit()
        # Set existing players to WNBA
        conn.execute("UPDATE players SET sport = 'WNBA' WHERE sport IS NULL")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Create index on sport for efficient filtering
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_players_sport ON players(sport)")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Create unique index for (name, draft_year, sport) - replaces old (name, draft_year) constraint
    # Note: SQLite doesn't support dropping constraints, so we create a new unique index instead
    try:
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_players_name_year_sport ON players(name, draft_year, sport)")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Index already exists

    conn.commit()
    conn.close()


def upsert_player(name, draft_year, sport='WNBA', school=None, position=None, height=None, hometown=None):
    """Insert or update a player. Returns the player ID.

    Args:
        name: Player's full name
        draft_year: Draft year (e.g., 2025, 2026)
        sport: Sport code (WNBA, NBA, NFL, NHL, MLB). Defaults to WNBA for backward compat.
        school: College/university name
        position: Playing position
        height: Height string
        hometown: Hometown string
    """
    from db.normalize import normalize_name
    name = normalize_name(name)
    sport = sport.upper() if sport else 'WNBA'
    conn = get_connection()

    # First try to find existing player by name, year, and sport
    existing = conn.execute(
        "SELECT id FROM players WHERE name = ? AND draft_year = ? AND sport = ?",
        (name.strip(), draft_year, sport)
    ).fetchone()

    if existing:
        # Update existing player
        conn.execute(
            """UPDATE players SET
                 school = COALESCE(?, school),
                 position = COALESCE(?, position),
                 height = COALESCE(?, height),
                 hometown = COALESCE(?, hometown),
                 updated_at = datetime('now')
               WHERE id = ?""",
            (school, position, height, hometown, existing[0])
        )
        player_id = existing[0]
    else:
        # Insert new player
        cursor = conn.execute(
            """INSERT INTO players (name, draft_year, sport, school, position, height, hometown)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               RETURNING id""",
            (name.strip(), draft_year, sport, school, position, height, hometown),
        )
        player_id = cursor.fetchone()[0]

    conn.commit()
    conn.close()
    return player_id


def add_ranking(player_id, source, rank=None, projected_pick=None,
                projected_round=None, url=None, raw_text=None, scrape_date=None):
    if scrape_date is None:
        scrape_date = date.today().isoformat()
    conn = get_connection()
    conn.execute(
        """INSERT INTO rankings (player_id, source, rank, projected_pick,
           projected_round, scrape_date, url, raw_text)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(player_id, source, scrape_date) DO UPDATE SET
             rank = excluded.rank,
             projected_pick = excluded.projected_pick,
             projected_round = excluded.projected_round,
             url = excluded.url,
             raw_text = excluded.raw_text""",
        (player_id, source, rank, projected_pick, projected_round,
         scrape_date, url, raw_text),
    )
    conn.commit()
    conn.close()


def add_card_value(player_id, value_dollars=None, card_type="autograph", notes=None,
                   recorded_date=None, source="manual", listing_count=None,
                   lowest_bin=None, avg_price=None, ebay_search_url=None):
    if recorded_date is None:
        recorded_date = date.today().isoformat()
    conn = get_connection()
    conn.execute(
        """INSERT INTO card_values
           (player_id, card_type, value_dollars, recorded_date, notes,
            source, listing_count, lowest_bin, avg_price, ebay_search_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(player_id, card_type, source, recorded_date) DO UPDATE SET
             value_dollars = excluded.value_dollars,
             listing_count = excluded.listing_count,
             lowest_bin = excluded.lowest_bin,
             avg_price = excluded.avg_price,
             ebay_search_url = excluded.ebay_search_url,
             notes = excluded.notes""",
        (player_id, card_type, value_dollars, recorded_date, notes,
         source, listing_count, lowest_bin, avg_price, ebay_search_url),
    )
    conn.commit()
    conn.close()


def get_latest_card_values(draft_year=None):
    """Get most recent card values for all players."""
    conn = get_connection()
    query = """
        SELECT p.id, p.name, p.draft_year, p.school, p.position,
               cv.lowest_bin, cv.avg_price, cv.listing_count,
               cv.ebay_search_url, cv.recorded_date, cv.card_type
        FROM players p
        LEFT JOIN card_values cv ON p.id = cv.player_id
            AND cv.source = 'ebay'
            AND cv.recorded_date = (
                SELECT MAX(cv2.recorded_date) FROM card_values cv2
                WHERE cv2.player_id = cv.player_id AND cv2.source = 'ebay'
            )
    """
    params = []
    if draft_year:
        query += " WHERE p.draft_year = ?"
        params.append(draft_year)
    query += " ORDER BY p.draft_year, cv.lowest_bin ASC NULLS LAST, p.name"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_card_price_history(player_id):
    """Get card price history for a player."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT recorded_date, lowest_bin, avg_price, listing_count, source
        FROM card_values
        WHERE player_id = ? AND source = 'ebay'
        ORDER BY recorded_date
    """, (player_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_watchlist_player(name, sport=None, notes=None):
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO watchlist (name, sport, notes) VALUES (?, ?, ?)
           ON CONFLICT(name) DO UPDATE SET
             sport = COALESCE(excluded.sport, sport),
             notes = COALESCE(excluded.notes, notes)
           RETURNING id""",
        (name.strip(), sport, notes),
    )
    wid = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return wid


def remove_watchlist_player(name):
    conn = get_connection()
    row = conn.execute("SELECT id FROM watchlist WHERE name = ?", (name.strip(),)).fetchone()
    if row:
        conn.execute("DELETE FROM watchlist_prices WHERE watchlist_id = ?", (row[0],))
        conn.execute("DELETE FROM watchlist WHERE id = ?", (row[0],))
        conn.commit()
    conn.close()
    return row is not None


def get_watchlist():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM watchlist ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_watchlist_price(watchlist_id, lowest_bin, avg_price, listing_count,
                        ebay_search_url, card_type="autograph", recorded_date=None):
    if recorded_date is None:
        recorded_date = date.today().isoformat()
    conn = get_connection()
    conn.execute(
        """INSERT INTO watchlist_prices
           (watchlist_id, card_type, lowest_bin, avg_price, listing_count,
            ebay_search_url, recorded_date)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(watchlist_id, card_type, recorded_date) DO UPDATE SET
             lowest_bin = excluded.lowest_bin,
             avg_price = excluded.avg_price,
             listing_count = excluded.listing_count,
             ebay_search_url = excluded.ebay_search_url""",
        (watchlist_id, card_type, lowest_bin, avg_price, listing_count,
         ebay_search_url, recorded_date),
    )
    conn.commit()
    conn.close()


def get_watchlist_with_prices():
    conn = get_connection()
    rows = conn.execute("""
        SELECT w.id, w.name, w.sport, w.notes,
               wp.lowest_bin, wp.avg_price, wp.listing_count,
               wp.ebay_search_url, wp.recorded_date
        FROM watchlist w
        LEFT JOIN watchlist_prices wp ON w.id = wp.watchlist_id
            AND wp.recorded_date = (
                SELECT MAX(wp2.recorded_date) FROM watchlist_prices wp2
                WHERE wp2.watchlist_id = wp.id
            )
        ORDER BY w.name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_scrape(source, url, draft_year, status, players_found=0, error_message=None):
    conn = get_connection()
    conn.execute(
        """INSERT INTO scrape_log (source, url, draft_year, status, players_found, error_message)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (source, url, draft_year, status, players_found, error_message),
    )
    conn.commit()
    conn.close()


def get_players_by_draft_year(draft_year, sport=None):
    """Get all players for a draft year, optionally filtered by sport."""
    conn = get_connection()
    if sport:
        rows = conn.execute(
            "SELECT * FROM players WHERE draft_year = ? AND sport = ? ORDER BY name",
            (draft_year, sport.upper())
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM players WHERE draft_year = ? ORDER BY name", (draft_year,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_rankings(player_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT source, rank, projected_pick, projected_round, scrape_date
           FROM rankings WHERE player_id = ?
           AND scrape_date = (
               SELECT MAX(scrape_date) FROM rankings r2
               WHERE r2.player_id = rankings.player_id AND r2.source = rankings.source
           )
           ORDER BY source""",
        (player_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_ranking_history(player_id, source=None):
    conn = get_connection()
    query = """SELECT source, rank, projected_pick, projected_round, scrape_date
               FROM rankings WHERE player_id = ?"""
    params = [player_id]
    if source:
        query += " AND source = ?"
        params.append(source)
    query += " ORDER BY scrape_date"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_players_with_rankings():
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.id, p.name, p.draft_year, p.school, p.position,
               r.source, r.rank, r.projected_pick, r.scrape_date
        FROM players p
        LEFT JOIN rankings r ON p.id = r.player_id
            AND r.scrape_date = (
                SELECT MAX(r2.scrape_date) FROM rankings r2
                WHERE r2.player_id = r.player_id AND r2.source = r.source
            )
        ORDER BY p.draft_year, p.name, r.source
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Portfolio CRUD ---

def add_portfolio_card(player_name, card_year, manufacturer, set_name,
                       card_number=None, parallel="Base", is_numbered=0,
                       numbered_to=None, serial_number=None, is_autograph=0,
                       is_rookie=0, grade="Raw", purchase_price=None,
                       purchase_date=None, notes=None, player_id=None,
                       user_email=None):
    if purchase_date is None:
        purchase_date = date.today().isoformat()
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO portfolio_cards
           (player_id, player_name, card_year, manufacturer, set_name,
            card_number, parallel, is_numbered, numbered_to, serial_number,
            is_autograph, is_rookie, grade, purchase_price, purchase_date, notes,
            user_email)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           RETURNING id""",
        (player_id, player_name.strip(), card_year, manufacturer.strip(),
         set_name.strip(), card_number, parallel or "Base", is_numbered,
         numbered_to, serial_number, is_autograph, is_rookie,
         grade or "Raw", purchase_price, purchase_date, notes, user_email),
    )
    card_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return card_id


def update_portfolio_card(card_id, **kwargs):
    allowed = {
        "player_name", "card_year", "manufacturer", "set_name", "card_number",
        "parallel", "is_numbered", "numbered_to", "serial_number",
        "is_autograph", "is_rookie", "grade", "purchase_price", "purchase_date",
        "notes", "status", "sold_price", "sold_date",
    }
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    updates["updated_at"] = datetime.now().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [card_id]
    conn = get_connection()
    conn.execute(f"UPDATE portfolio_cards SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_portfolio_card(card_id, user_email=None):
    """Delete a portfolio card. If user_email is provided, only delete if it belongs to that user."""
    conn = get_connection()
    if user_email:
        # Verify ownership first
        row = conn.execute(
            "SELECT user_email FROM portfolio_cards WHERE id = ?", (card_id,)
        ).fetchone()
        if not row or (row["user_email"] and row["user_email"] != user_email):
            conn.close()
            return False
    conn.execute("DELETE FROM portfolio_price_history WHERE portfolio_card_id = ?", (card_id,))
    conn.execute("DELETE FROM portfolio_cards WHERE id = ?", (card_id,))
    conn.commit()
    conn.close()
    return True


def get_portfolio_cards(status="active", user_email=None):
    conn = get_connection()
    query = """
        SELECT pc.*,
               ph.price as current_price,
               ph.source as price_source,
               ph.recorded_date as price_date
        FROM portfolio_cards pc
        LEFT JOIN portfolio_price_history ph ON pc.id = ph.portfolio_card_id
            AND ph.recorded_date = (
                SELECT MAX(ph2.recorded_date) FROM portfolio_price_history ph2
                WHERE ph2.portfolio_card_id = pc.id
            )
    """
    conditions = []
    params = []
    if status:
        conditions.append("pc.status = ?")
        params.append(status)
    if user_email:
        conditions.append("pc.user_email = ?")
        params.append(user_email)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY pc.player_name, pc.card_year"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_portfolio_card(card_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM portfolio_cards WHERE id = ?", (card_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_portfolio_price(portfolio_card_id, price, source, sale_type=None,
                        title=None, match_confidence=1.0, recorded_date=None):
    if recorded_date is None:
        recorded_date = date.today().isoformat()
    conn = get_connection()
    conn.execute(
        """INSERT INTO portfolio_price_history
           (portfolio_card_id, price, source, sale_type, title,
            match_confidence, recorded_date)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (portfolio_card_id, price, source, sale_type, title,
         match_confidence, recorded_date),
    )
    conn.commit()
    conn.close()


def get_portfolio_price_history(portfolio_card_id, days_back=None):
    conn = get_connection()
    query = """SELECT * FROM portfolio_price_history
               WHERE portfolio_card_id = ?"""
    params = [portfolio_card_id]
    if days_back:
        query += " AND recorded_date >= date('now', ?)"
        params.append(f"-{days_back} days")
    query += " ORDER BY recorded_date"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Card Title Mappings ---

def add_title_mapping(raw_title, player_name=None, card_year=None,
                      manufacturer=None, set_name=None, parallel=None,
                      is_numbered=None, numbered_to=None, is_autograph=None,
                      is_rookie=None, grade=None, source=None, confirmed=0):
    conn = get_connection()
    conn.execute(
        """INSERT INTO card_title_mappings
           (raw_title, player_name, card_year, manufacturer, set_name,
            parallel, is_numbered, numbered_to, is_autograph, is_rookie,
            grade, source, confirmed)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(raw_title) DO UPDATE SET
             player_name = COALESCE(excluded.player_name, player_name),
             card_year = COALESCE(excluded.card_year, card_year),
             manufacturer = COALESCE(excluded.manufacturer, manufacturer),
             set_name = COALESCE(excluded.set_name, set_name),
             parallel = COALESCE(excluded.parallel, parallel),
             confirmed = MAX(confirmed, excluded.confirmed)""",
        (raw_title, player_name, card_year, manufacturer, set_name,
         parallel, is_numbered, numbered_to, is_autograph, is_rookie,
         grade, source, confirmed),
    )
    conn.commit()
    conn.close()


def find_title_mapping(raw_title):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM card_title_mappings WHERE raw_title = ?", (raw_title,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# --- Player Stats ---

def add_player_stats(player_id, season, stat_type="season_avg", game_date=None,
                     opponent=None, games_played=None, points_per_game=None,
                     rebounds_per_game=None, assists_per_game=None,
                     steals_per_game=None, blocks_per_game=None,
                     fg_pct=None, three_pct=None, ft_pct=None,
                     minutes_per_game=None, source_url=None, scraped_date=None):
    if scraped_date is None:
        scraped_date = date.today().isoformat()
    conn = get_connection()
    conn.execute(
        """INSERT INTO player_stats
           (player_id, season, stat_type, game_date, opponent, games_played,
            points_per_game, rebounds_per_game, assists_per_game,
            steals_per_game, blocks_per_game, fg_pct, three_pct, ft_pct,
            minutes_per_game, source_url, scraped_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(player_id, season, stat_type, game_date) DO UPDATE SET
             games_played = excluded.games_played,
             points_per_game = excluded.points_per_game,
             rebounds_per_game = excluded.rebounds_per_game,
             assists_per_game = excluded.assists_per_game,
             steals_per_game = excluded.steals_per_game,
             blocks_per_game = excluded.blocks_per_game,
             fg_pct = excluded.fg_pct,
             three_pct = excluded.three_pct,
             ft_pct = excluded.ft_pct,
             minutes_per_game = excluded.minutes_per_game,
             source_url = excluded.source_url,
             scraped_date = excluded.scraped_date""",
        (player_id, season, stat_type, game_date, opponent, games_played,
         points_per_game, rebounds_per_game, assists_per_game,
         steals_per_game, blocks_per_game, fg_pct, three_pct, ft_pct,
         minutes_per_game, source_url, scraped_date),
    )
    conn.commit()
    conn.close()


def get_player_stats(player_id, season=None):
    conn = get_connection()
    query = "SELECT * FROM player_stats WHERE player_id = ?"
    params = [player_id]
    if season:
        query += " AND season = ?"
        params.append(season)
    query += " ORDER BY season DESC, game_date DESC NULLS LAST"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_player_status(player_id, status, reason=None, detected_date=None):
    if detected_date is None:
        detected_date = date.today().isoformat()
    conn = get_connection()
    conn.execute(
        """INSERT INTO player_status_log (player_id, status, reason, detected_date)
           VALUES (?, ?, ?, ?)""",
        (player_id, status, reason, detected_date),
    )
    conn.commit()
    conn.close()


def get_player_status_log(player_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM player_status_log WHERE player_id = ? ORDER BY detected_date DESC",
        (player_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_player_latest_status(player_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM player_status_log WHERE player_id = ? ORDER BY detected_date DESC LIMIT 1",
        (player_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_player_names():
    """Get all player names for autocomplete."""
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT name FROM players ORDER BY name").fetchall()
    conn.close()
    return [r["name"] for r in rows]


def update_player_photo(player_id, photo_url):
    """Update player's photo URL."""
    conn = get_connection()
    conn.execute(
        "UPDATE players SET photo_url = ?, updated_at = datetime('now') WHERE id = ?",
        (photo_url, player_id)
    )
    conn.commit()
    conn.close()


def update_player_tier(player_id, tier):
    """Update player's tier rating (A/B/C/D)."""
    if tier and tier.upper() not in ('A', 'B', 'C', 'D'):
        raise ValueError("Tier must be A, B, C, or D")
    conn = get_connection()
    conn.execute(
        "UPDATE players SET tier = ?, updated_at = datetime('now') WHERE id = ?",
        (tier.upper() if tier else None, player_id)
    )
    conn.commit()
    conn.close()


def update_player_country(player_id, country):
    """Update player's country code (ISO 2-letter)."""
    conn = get_connection()
    conn.execute(
        "UPDATE players SET country = ?, updated_at = datetime('now') WHERE id = ?",
        (country.upper() if country else None, player_id)
    )
    conn.commit()
    conn.close()


def get_player_full_profile(player_id):
    """Get complete player data including stats, rankings, card values, status."""
    conn = get_connection()

    # Basic player info
    player = conn.execute(
        "SELECT * FROM players WHERE id = ?", (player_id,)
    ).fetchone()
    if not player:
        conn.close()
        return None

    profile = dict(player)

    # Season stats
    stats = conn.execute("""
        SELECT * FROM player_stats
        WHERE player_id = ? AND stat_type = 'season_avg'
        ORDER BY season DESC
    """, (player_id,)).fetchall()
    profile['stats'] = [dict(s) for s in stats]

    # Latest rankings from each source
    rankings = conn.execute("""
        SELECT r.* FROM rankings r
        INNER JOIN (
            SELECT source, MAX(scrape_date) as max_date
            FROM rankings WHERE player_id = ?
            GROUP BY source
        ) latest ON r.source = latest.source AND r.scrape_date = latest.max_date
        WHERE r.player_id = ?
        ORDER BY r.rank
    """, (player_id, player_id)).fetchall()
    profile['rankings'] = [dict(r) for r in rankings]

    # Card values
    card_values = conn.execute("""
        SELECT * FROM card_values
        WHERE player_id = ?
        ORDER BY recorded_date DESC
        LIMIT 10
    """, (player_id,)).fetchall()
    profile['card_values'] = [dict(cv) for cv in card_values]

    # Latest status
    status = conn.execute("""
        SELECT * FROM player_status_log
        WHERE player_id = ?
        ORDER BY detected_date DESC
        LIMIT 1
    """, (player_id,)).fetchone()
    profile['status'] = dict(status) if status else None

    conn.close()
    return profile


def get_players_for_dashboard(draft_year, sport=None):
    """Get all players with photos, tiers, and basic info for dashboard grid.

    Args:
        draft_year: The draft year to filter by
        sport: Optional sport filter (WNBA, NBA, NFL, etc.). If None, returns all sports.
    """
    conn = get_connection()

    # Get players with their consensus ranking
    if sport:
        rows = conn.execute("""
            SELECT p.*,
                   AVG(r.rank) as avg_rank,
                   COUNT(DISTINCT r.source) as source_count
            FROM players p
            LEFT JOIN rankings r ON p.id = r.player_id
                AND r.scrape_date = (
                    SELECT MAX(r2.scrape_date) FROM rankings r2
                    WHERE r2.player_id = p.id AND r2.source = r.source
                )
            WHERE p.draft_year = ? AND p.sport = ?
            GROUP BY p.id
            ORDER BY COALESCE(AVG(r.rank), 999), p.name
        """, (draft_year, sport.upper())).fetchall()
    else:
        rows = conn.execute("""
            SELECT p.*,
                   AVG(r.rank) as avg_rank,
                   COUNT(DISTINCT r.source) as source_count
            FROM players p
            LEFT JOIN rankings r ON p.id = r.player_id
                AND r.scrape_date = (
                    SELECT MAX(r2.scrape_date) FROM rankings r2
                    WHERE r2.player_id = p.id AND r2.source = r.source
                )
            WHERE p.draft_year = ?
            GROUP BY p.id
            ORDER BY COALESCE(AVG(r.rank), 999), p.name
        """, (draft_year,)).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def get_player_by_id(player_id):
    """Get a single player by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_available_sports():
    """Get list of sports that have players in the database."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT sport FROM players WHERE sport IS NOT NULL ORDER BY sport"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_draft_years_for_sport(sport):
    """Get list of draft years that have players for a given sport."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT draft_year FROM players WHERE sport = ? ORDER BY draft_year",
        (sport.upper(),)
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_player_count_by_sport():
    """Get count of players per sport."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT sport, COUNT(*) as count
           FROM players
           GROUP BY sport
           ORDER BY sport"""
    ).fetchall()
    conn.close()
    return {r['sport']: r['count'] for r in rows}
