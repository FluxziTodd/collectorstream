"""
Admin routes for CollectorStream API
User management, admin management, scraper scheduling
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import subprocess
import os

from auth import get_current_user
from database import get_db

router = APIRouter()

# Admin email whitelist
ADMIN_EMAILS = ["todd@collectorstream.com", "todd@fluxzi.com"]

def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin privileges"""
    if current_user["email"] not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ============================================================================
# Models
# ============================================================================

class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None

class PasswordReset(BaseModel):
    new_password: str

class ScraperJob(BaseModel):
    scraper: str  # cardladder, ebay, ncaa_stats, psa_pop, etc.
    sport: str = "basketball"
    year: int = 2026

# ============================================================================
# User Management
# ============================================================================

@router.get("/users")
async def list_users(
    page: int = 1,
    per_page: int = 50,
    admin: dict = Depends(require_admin)
):
    """List all users (admin only)"""
    offset = (page - 1) * per_page

    with get_db() as conn:
        cursor = conn.cursor()

        # Get total count
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]

        # Get users with pagination
        cursor.execute("""
            SELECT id, email, username, created_at, is_active
            FROM users
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))

        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row[0],
                "email": row[1],
                "username": row[2],
                "createdAt": row[3],
                "isActive": bool(row[4]),
                "isAdmin": row[1] in ADMIN_EMAILS
            })

        return {
            "users": users,
            "total": total,
            "page": page,
            "perPage": per_page
        }

@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """Get user details (admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, username, created_at, updated_at, is_active
            FROM users
            WHERE id = ?
        """, (user_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user's card count
        cursor.execute("SELECT COUNT(*) FROM user_cards WHERE user_id = ?", (user_id,))
        card_count = cursor.fetchone()[0]

        return {
            "id": row[0],
            "email": row[1],
            "username": row[2],
            "createdAt": row[3],
            "updatedAt": row[4],
            "isActive": bool(row[5]),
            "isAdmin": row[1] in ADMIN_EMAILS,
            "cardCount": card_count
        }

@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    updates: UserUpdate,
    admin: dict = Depends(require_admin)
):
    """Update user (admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Build update query
        set_clauses = []
        params = []

        if updates.email is not None:
            set_clauses.append("email = ?")
            params.append(updates.email.lower())

        if updates.username is not None:
            set_clauses.append("username = ?")
            params.append(updates.username)

        if updates.is_active is not None:
            set_clauses.append("is_active = ?")
            params.append(1 if updates.is_active else 0)

        if not set_clauses:
            raise HTTPException(status_code=400, detail="No updates provided")

        set_clauses.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(user_id)

        cursor.execute(f"""
            UPDATE users
            SET {', '.join(set_clauses)}
            WHERE id = ?
        """, params)

        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": "User updated successfully"}

@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: str,
    reset: PasswordReset,
    admin: dict = Depends(require_admin)
):
    """Reset user password (admin only)"""
    import bcrypt

    with get_db() as conn:
        cursor = conn.cursor()

        # Hash new password
        password_hash = bcrypt.hashpw(
            reset.new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        cursor.execute("""
            UPDATE users
            SET password_hash = ?, updated_at = ?
            WHERE id = ?
        """, (password_hash, datetime.utcnow().isoformat(), user_id))

        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": "Password reset successfully"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """Delete user (admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Prevent deleting admin users
        if user[0] in ADMIN_EMAILS:
            raise HTTPException(status_code=403, detail="Cannot delete admin users")

        # Delete user's cards first (CASCADE)
        cursor.execute("DELETE FROM user_cards WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

        conn.commit()

        return {"message": "User deleted successfully"}

# ============================================================================
# Admin Management
# ============================================================================

@router.get("/admins")
async def list_admins(admin: dict = Depends(require_admin)):
    """List all admin users"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, username, created_at
            FROM users
            WHERE email IN ({})
            ORDER BY created_at
        """.format(','.join('?' * len(ADMIN_EMAILS))), ADMIN_EMAILS)

        admins = []
        for row in cursor.fetchall():
            admins.append({
                "id": row[0],
                "email": row[1],
                "username": row[2],
                "createdAt": row[3]
            })

        return {"admins": admins}

# ============================================================================
# Scraper Management
# ============================================================================

@router.post("/scrapers/run")
async def run_scraper(
    job: ScraperJob,
    admin: dict = Depends(require_admin)
):
    """Run a scraper job (admin only)"""
    scraper_map = {
        "cardladder": "cardladder.py",
        "ebay": "ebay.py",
        "ncaa_stats": "ncaa_stats.py",
        "psa_pop": "psa_pop.py",
        "photo_hunter": "photo_hunter.py",
        "deep_photo_hunt": "deep_photo_hunt.py"
    }

    if job.scraper not in scraper_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scraper: {job.scraper}. Available: {list(scraper_map.keys())}"
        )

    scraper_file = scraper_map[job.scraper]
    scraper_path = os.path.join(os.path.dirname(__file__), "..", "scrapers", scraper_file)

    if not os.path.exists(scraper_path):
        raise HTTPException(status_code=404, detail=f"Scraper file not found: {scraper_file}")

    # Run scraper in background
    try:
        # Build command
        cmd = ["python3", scraper_path, "--sport", job.sport, "--year", str(job.year)]

        print(f"🤖 Starting scraper: {job.scraper} (sport={job.sport}, year={job.year})")

        # Run in background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(scraper_path)
        )

        return {
            "message": f"Scraper {job.scraper} started",
            "pid": process.pid,
            "scraper": job.scraper,
            "sport": job.sport,
            "year": job.year
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scraper: {str(e)}")

@router.get("/scrapers")
async def list_scrapers(admin: dict = Depends(require_admin)):
    """List available scrapers"""
    scrapers = [
        {
            "id": "cardladder",
            "name": "CardLadder",
            "description": "Scrape price data from CardLadder"
        },
        {
            "id": "ebay",
            "name": "eBay",
            "description": "Scrape sold listings from eBay"
        },
        {
            "id": "ncaa_stats",
            "name": "NCAA Stats",
            "description": "Scrape player statistics from NCAA"
        },
        {
            "id": "psa_pop",
            "name": "PSA Population",
            "description": "Scrape PSA population reports"
        },
        {
            "id": "photo_hunter",
            "name": "Photo Hunter",
            "description": "Find and download player photos"
        },
        {
            "id": "deep_photo_hunt",
            "name": "Deep Photo Hunt",
            "description": "Deep search for player photos"
        }
    ]

    return {"scrapers": scrapers}

# ============================================================================
# System Stats
# ============================================================================

@router.get("/stats")
async def get_system_stats(admin: dict = Depends(require_admin)):
    """Get system statistics (admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()

        # User stats
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        active_users = cursor.fetchone()[0]

        # Card stats
        cursor.execute("SELECT COUNT(*) FROM user_cards")
        total_cards = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_cards")
        users_with_cards = cursor.fetchone()[0]

        # Recent activity
        cursor.execute("""
            SELECT COUNT(*) FROM user_cards
            WHERE created_at > datetime('now', '-7 days')
        """)
        cards_last_week = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM users
            WHERE created_at > datetime('now', '-7 days')
        """)
        new_users_last_week = cursor.fetchone()[0]

        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "newLastWeek": new_users_last_week
            },
            "cards": {
                "total": total_cards,
                "usersWithCards": users_with_cards,
                "addedLastWeek": cards_last_week
            }
        }
