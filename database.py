# database.py
import aiosqlite
from datetime import datetime, date
from typing import Optional, Dict, List
import json

class Database:
    def __init__(self, db_path="accounts.db"):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    plan TEXT DEFAULT 'free',
                    plan_expiry TEXT,
                    join_date TEXT,
                    total_scans INTEGER DEFAULT 0,
                    total_hits INTEGER DEFAULT 0,
                    total_valid INTEGER DEFAULT 0,
                    total_invalid INTEGER DEFAULT 0,
                    settings TEXT DEFAULT '{}'
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_usage (
                    user_id INTEGER,
                    date TEXT,
                    scans_used INTEGER DEFAULT 0,
                    hits_today INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, date)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    service TEXT,
                    accounts TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    started_at TEXT,
                    completed_at TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    level TEXT,
                    message TEXT,
                    user_id INTEGER
                )
            """)

            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "user_id": row[0],
                        "username": row[1],
                        "plan": row[2],
                        "plan_expiry": row[3],
                        "join_date": row[4],
                        "total_scans": row[5],
                        "total_hits": row[6],
                        "total_valid": row[7],
                        "total_invalid": row[8],
                        "settings": json.loads(row[9]) if row[9] else {},
                    }
                return None

    async def create_user(self, user_id: int, username: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO users (user_id, username, join_date, settings) 
                   VALUES (?, ?, ?, ?)""",
                (user_id, username, date.today().isoformat(), json.dumps({})),
            )
            await db.commit()

    async def update_user_settings(self, user_id: int, settings: dict):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET settings = ? WHERE user_id = ?",
                (json.dumps(settings), user_id),
            )
            await db.commit()

    async def update_plan(self, user_id: int, plan: str, expiry: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET plan = ?, plan_expiry = ? WHERE user_id = ?",
                (plan, expiry, user_id),
            )
            await db.commit()

    async def increment_stats(self, user_id: int, hits: int = 0, valid: int = 0, invalid: int = 0):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE users 
                   SET total_scans = total_scans + ?, 
                       total_hits = total_hits + ?,
                       total_valid = total_valid + ?,
                       total_invalid = total_invalid + ?
                   WHERE user_id = ?""",
                (hits + valid + invalid, hits, valid, invalid, user_id),
            )
            await db.commit()

    async def get_daily_usage(self, user_id: int) -> int:
        today = date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT scans_used FROM daily_usage WHERE user_id = ? AND date = ?",
                (user_id, today),
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def increment_daily_usage(self, user_id: int, count: int = 1, hits: int = 0):
        today = date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO daily_usage (user_id, date, scans_used, hits_today) 
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(user_id, date) DO UPDATE SET
                   scans_used = scans_used + ?, hits_today = hits_today + ?""",
                (user_id, today, count, hits, count, hits),
            )
            await db.commit()

    async def reset_daily_usage(self, user_id: int):
        today = date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM daily_usage WHERE user_id = ? AND date = ?",
                (user_id, today),
            )
            await db.commit()

    async def get_all_users(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id, username, plan FROM users") as cursor:
                rows = await cursor.fetchall()
                return [{"user_id": r[0], "username": r[1], "plan": r[2]} for r in rows]

    async def add_to_queue(self, user_id: int, service: str, accounts: List[str]) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO queue (user_id, service, accounts, created_at, status) 
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, service, json.dumps(accounts), datetime.now().isoformat(), "pending"),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_queue_position(self, queue_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """SELECT COUNT(*) FROM queue 
                   WHERE status = 'pending' AND id < ?""",
                (queue_id,),
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] + 1 if row else 1

    async def get_pending_queue(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, user_id, service, created_at FROM queue WHERE status = 'pending' ORDER BY id"
            ) as cursor:
                rows = await cursor.fetchall()
                return [{"id": r[0], "user_id": r[1], "service": r[2], "created_at": r[3]} for r in rows]

    async def add_log(self, level: str, message: str, user_id: int = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO system_logs (timestamp, level, message, user_id) VALUES (?, ?, ?, ?)",
                (datetime.now().isoformat(), level, message, user_id),
            )
            await db.commit()

    async def get_logs(self, limit: int = 100) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT timestamp, level, message, user_id FROM system_logs ORDER BY id DESC LIMIT ?",
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [{"timestamp": r[0], "level": r[1], "message": r[2], "user_id": r[3]} for r in rows]

database = Database()