import sqlite3

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/waitlist", tags=["waitlist"])


class WaitlistJoin(BaseModel):
    email: EmailStr


class InviteRequest(BaseModel):
    email: EmailStr
    type: str = "signup"  # signup, affiliate, referral


def init_waitlist_db():
    """Initialize the waitlist database"""
    db_path = "waitlist.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    """
    )

    conn.commit()
    conn.close()


@router.post("/join")
async def join_waitlist(data: WaitlistJoin):
    """Add email to waitlist"""
    try:
        email = data.email.lower()

        # Initialize DB if it doesn't exist
        init_waitlist_db()

        conn = sqlite3.connect("waitlist.db")
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO waitlist (email) VALUES (?)", (email,))
            conn.commit()

            return {"success": True, "message": "Successfully joined waitlist"}

        except sqlite3.IntegrityError:
            return {"success": True, "message": "Email already on waitlist"}

        finally:
            conn.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def get_waitlist():
    """Get all waitlist entries (admin only)"""
    try:
        init_waitlist_db()

        conn = sqlite3.connect("waitlist.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, email, joined_at, status FROM waitlist ORDER BY joined_at DESC"
        )

        entries = []
        for row in cursor.fetchall():
            entries.append(
                {"id": row[0], "email": row[1], "joined_at": row[2], "status": row[3]}
            )

        conn.close()

        return {"success": True, "entries": entries, "total": len(entries)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-invite")
async def send_invite(data: InviteRequest):
    """Send invite to waitlist member (admin only)"""
    try:
        email = data.email.lower()
        invite_type = data.type

        # Update status in database
        conn = sqlite3.connect("waitlist.db")
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE waitlist SET status = ? WHERE email = ?",
            (f"invited_{invite_type}", email),
        )

        conn.commit()
        conn.close()

        # Here you would send the actual email with the appropriate link
        # For now, just return success

        return {
            "success": True,
            "message": f"{invite_type.title()} invite sent to {email}",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
