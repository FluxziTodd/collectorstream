"""
Database models and connection for CollectorStream API
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import uuid

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "collectorstream.db")

@contextmanager
def get_db():
    """Get database connection context manager."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with required tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with get_db() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                reset_token TEXT,
                reset_token_expires TEXT
            )
        """)

        # User cards collection table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_cards (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                team TEXT,
                year TEXT,
                card_set TEXT,
                card_number TEXT,
                manufacturer TEXT,
                sport TEXT DEFAULT 'MLB',
                condition TEXT,
                grading_company TEXT,
                grading_grade TEXT,
                grading_cert_number TEXT,
                front_image_url TEXT,
                back_image_url TEXT,
                purchase_price REAL,
                estimated_value REAL,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Card market prices history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS card_market_prices (
                id TEXT PRIMARY KEY,
                card_id TEXT NOT NULL,
                market_price REAL NOT NULL,
                source TEXT NOT NULL,
                sample_size INTEGER,
                confidence_level REAL,
                price_range_low REAL,
                price_range_high REAL,
                checked_at TEXT NOT NULL,
                FOREIGN KEY (card_id) REFERENCES user_cards(id) ON DELETE CASCADE
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_cards_user_id ON user_cards(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_cards_sport ON user_cards(sport)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_card_market_prices_card_id ON card_market_prices(card_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_card_market_prices_checked_at ON card_market_prices(checked_at)")

        conn.commit()

# ============================================================================
# User Functions
# ============================================================================

def create_user(email: str, username: str, password_hash: str) -> Dict[str, Any]:
    """Create a new user."""
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (id, email, username, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, email.lower(), username, password_hash, now, now))
        conn.commit()

    return get_user_by_id(user_id)

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_user_password(user_id: str, password_hash: str):
    """Update user's password."""
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET password_hash = ?, updated_at = ?, reset_token = NULL, reset_token_expires = NULL
            WHERE id = ?
        """, (password_hash, now, user_id))
        conn.commit()

def set_reset_token(user_id: str, token: str, expires: str):
    """Set password reset token."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET reset_token = ?, reset_token_expires = ?
            WHERE id = ?
        """, (token, expires, user_id))
        conn.commit()

def get_user_by_reset_token(token: str) -> Optional[Dict[str, Any]]:
    """Get user by reset token."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE reset_token = ?", (token,))
        row = cursor.fetchone()
        return dict(row) if row else None

# ============================================================================
# Card Functions
# ============================================================================

def create_card(user_id: str, card_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new card in user's collection."""
    card_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_cards (
                id, user_id, player_name, team, year, card_set, card_number,
                manufacturer, sport, condition, grading_company, grading_grade,
                grading_cert_number, front_image_url, back_image_url,
                purchase_price, estimated_value, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            card_id, user_id,
            card_data.get("player_name"),
            card_data.get("team"),
            card_data.get("year"),
            card_data.get("set"),
            card_data.get("card_number"),
            card_data.get("manufacturer"),
            card_data.get("sport", "MLB"),
            card_data.get("condition"),
            card_data.get("grading_company"),
            card_data.get("grading_grade"),
            card_data.get("grading_cert_number"),
            card_data.get("front_image_url"),
            card_data.get("back_image_url"),
            card_data.get("purchase_price"),
            card_data.get("estimated_value"),
            card_data.get("notes"),
            now, now
        ))
        conn.commit()

    return get_card_by_id(card_id)

def get_card_by_id(card_id: str) -> Optional[Dict[str, Any]]:
    """Get card by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_cards WHERE id = ?", (card_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_cards(user_id: str, page: int = 1, per_page: int = 50, sport: Optional[str] = None) -> Dict[str, Any]:
    """Get all cards for a user with pagination."""
    offset = (page - 1) * per_page

    with get_db() as conn:
        cursor = conn.cursor()

        # Build query
        query = "SELECT * FROM user_cards WHERE user_id = ?"
        params = [user_id]

        if sport:
            query += " AND sport = ?"
            params.append(sport)

        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # Get cards with pagination
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        cards = [format_card(dict(row)) for row in rows]

        return {
            "cards": cards,
            "total": total,
            "page": page,
            "per_page": per_page
        }

def update_card(card_id: str, user_id: str, card_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a card."""
    now = datetime.utcnow().isoformat()

    # Build SET clause dynamically
    allowed_fields = [
        "player_name", "team", "year", "card_set", "card_number",
        "manufacturer", "sport", "condition", "grading_company",
        "grading_grade", "grading_cert_number", "front_image_url",
        "back_image_url", "purchase_price", "estimated_value", "notes"
    ]

    updates = []
    params = []

    for field in allowed_fields:
        if field in card_data:
            # Handle 'set' vs 'card_set' naming
            db_field = "card_set" if field == "set" else field
            updates.append(f"{db_field} = ?")
            params.append(card_data[field])

    if not updates:
        return get_card_by_id(card_id)

    updates.append("updated_at = ?")
    params.append(now)
    params.extend([card_id, user_id])

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE user_cards SET {', '.join(updates)}
            WHERE id = ? AND user_id = ?
        """, params)
        conn.commit()

        if cursor.rowcount == 0:
            return None

    return get_card_by_id(card_id)

def delete_card(card_id: str, user_id: str) -> bool:
    """Delete a card."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_cards WHERE id = ? AND user_id = ?", (card_id, user_id))
        conn.commit()
        return cursor.rowcount > 0

def format_card(card: Dict[str, Any]) -> Dict[str, Any]:
    """Format card for API response."""
    grading = None
    if card.get("grading_company") or card.get("grading_grade"):
        grading = {
            "company": card.get("grading_company"),
            "grade": card.get("grading_grade"),
            "certNumber": card.get("grading_cert_number")
        }

    # Get latest market value if available
    market_value = None
    latest_price = get_latest_market_price(card["id"])
    if latest_price:
        market_value = {
            "currentValue": latest_price.get("market_price"),
            "confidence": latest_price.get("confidence_level", 0.0),
            "lastChecked": latest_price.get("checked_at")
        }

    return {
        "id": card["id"],
        "playerName": card["player_name"],
        "team": card.get("team"),
        "year": card.get("year"),
        "set": card.get("card_set"),
        "cardNumber": card.get("card_number"),
        "manufacturer": card.get("manufacturer"),
        "sport": card.get("sport", "MLB"),
        "condition": card.get("condition"),
        "grading": grading,
        "frontImageUrl": card.get("front_image_url"),
        "backImageUrl": card.get("back_image_url"),
        "purchasePrice": card.get("purchase_price"),
        "estimatedValue": card.get("estimated_value"),
        "marketValue": market_value,
        "notes": card.get("notes"),
        "createdAt": card["created_at"],
        "updatedAt": card["updated_at"]
    }

# ============================================================================
# Market Price Functions
# ============================================================================

def add_market_price(card_id: str, price_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a market price record for a card."""
    price_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO card_market_prices (
                id, card_id, market_price, source, sample_size,
                confidence_level, price_range_low, price_range_high, checked_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            price_id, card_id,
            price_data["market_price"],
            price_data.get("source", "ebay"),
            price_data.get("sample_size", 0),
            price_data.get("confidence_level", 0.0),
            price_data.get("price_range_low"),
            price_data.get("price_range_high"),
            now
        ))
        conn.commit()

    return get_market_price_by_id(price_id)

def get_market_price_by_id(price_id: str) -> Optional[Dict[str, Any]]:
    """Get market price record by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM card_market_prices WHERE id = ?", (price_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_latest_market_price(card_id: str) -> Optional[Dict[str, Any]]:
    """Get the most recent market price for a card."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM card_market_prices
            WHERE card_id = ?
            ORDER BY checked_at DESC
            LIMIT 1
        """, (card_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_market_price_history(card_id: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Get market price history for a card."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM card_market_prices
            WHERE card_id = ?
            ORDER BY checked_at DESC
            LIMIT ?
        """, (card_id, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
