import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "media_buying.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                location TEXT NOT NULL,
                target_audience TEXT,
                total_budget REAL NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS media_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL REFERENCES deals(id),
                plan_json TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                approved INTEGER DEFAULT 0,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS placements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL REFERENCES deals(id),
                vendor_name TEXT NOT NULL,
                channel TEXT NOT NULL,
                description TEXT,
                contracted_cost REAL DEFAULT 0,
                actual_spend REAL DEFAULT 0,
                start_date TEXT,
                end_date TEXT,
                status TEXT DEFAULT 'pending',
                is_digital INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS performance_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL REFERENCES deals(id),
                platform TEXT NOT NULL,
                impressions INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                spend REAL DEFAULT 0.0,
                conversions INTEGER DEFAULT 0,
                synced_at TEXT DEFAULT (datetime('now'))
            );
        """)


# --- Deals ---

def create_deal(name, type_, location, target_audience, total_budget, start_date, end_date):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO deals (name, type, location, target_audience, total_budget, start_date, end_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, type_, location, target_audience, total_budget, start_date, end_date),
        )
        return cur.lastrowid


def get_deal(deal_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
        return dict(row) if row else None


def get_all_deals():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM deals ORDER BY created_at DESC")]


def update_deal_status(deal_id, status):
    with get_conn() as conn:
        conn.execute("UPDATE deals SET status = ? WHERE id = ?", (status, deal_id))


# --- Media Plans ---

def create_media_plan(deal_id, plan_json):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT MAX(version) AS v FROM media_plans WHERE deal_id = ?", (deal_id,)
        ).fetchone()
        version = (row["v"] or 0) + 1
        cur = conn.execute(
            "INSERT INTO media_plans (deal_id, plan_json, version) VALUES (?, ?, ?)",
            (deal_id, plan_json, version),
        )
        return cur.lastrowid


def get_media_plans(deal_id):
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM media_plans WHERE deal_id = ? ORDER BY version DESC", (deal_id,)
        )]


def approve_media_plan(plan_id):
    with get_conn() as conn:
        row = conn.execute("SELECT deal_id FROM media_plans WHERE id = ?", (plan_id,)).fetchone()
        if not row:
            return
        conn.execute("UPDATE media_plans SET approved = 0 WHERE deal_id = ?", (row["deal_id"],))
        conn.execute("UPDATE media_plans SET approved = 1 WHERE id = ?", (plan_id,))


def get_approved_plan(deal_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM media_plans WHERE deal_id = ? AND approved = 1", (deal_id,)
        ).fetchone()
        return dict(row) if row else None


# --- Placements ---

def create_placement(deal_id, vendor_name, channel, description,
                     contracted_cost, start_date, end_date, is_digital=False):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO placements (deal_id, vendor_name, channel, description, "
            "contracted_cost, start_date, end_date, is_digital) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (deal_id, vendor_name, channel, description, contracted_cost,
             start_date, end_date, 1 if is_digital else 0),
        )
        return cur.lastrowid


def get_placements(deal_id):
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM placements WHERE deal_id = ? ORDER BY id", (deal_id,)
        )]


def update_placement(placement_id, **kwargs):
    allowed = {"vendor_name", "channel", "description", "contracted_cost",
               "actual_spend", "start_date", "end_date", "status"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    with get_conn() as conn:
        conn.execute(
            f"UPDATE placements SET {set_clause} WHERE id = ?",
            [*fields.values(), placement_id],
        )


def delete_placement(placement_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM placements WHERE id = ?", (placement_id,))


# --- Performance Snapshots ---

def save_performance_snapshot(deal_id, platform, impressions, clicks, spend, conversions):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO performance_snapshots (deal_id, platform, impressions, clicks, spend, conversions) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (deal_id, platform, impressions, clicks, spend, conversions),
        )


def get_performance_snapshots(deal_id):
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM performance_snapshots WHERE deal_id = ? ORDER BY synced_at DESC",
            (deal_id,),
        )]


def get_latest_snapshots(deal_id):
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            """SELECT * FROM performance_snapshots
               WHERE id IN (
                   SELECT MAX(id) FROM performance_snapshots
                   WHERE deal_id = ? GROUP BY platform
               )""",
            (deal_id,),
        )]
