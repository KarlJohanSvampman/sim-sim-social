import json
import psycopg
from psycopg.rows import dict_row
from services.config import POSTGRES_DSN

def conn():
    return psycopg.connect(POSTGRES_DSN, row_factory=dict_row)

def init_db():
    with conn() as c:
        with c.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS characters (
                    id TEXT PRIMARY KEY,
                    data JSONB NOT NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS institutions (
                    id TEXT PRIMARY KEY,
                    payload JSONB NOT NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS relationships (
                    a_id TEXT NOT NULL,
                    b_id TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    PRIMARY KEY (a_id, b_id)
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    payload JSONB NOT NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS timeline_events (
                    id BIGSERIAL PRIMARY KEY,
                    tick INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    actor_id TEXT NULL,
                    target_id TEXT NULL,
                    payload JSONB NOT NULL
                )
            ''')
        c.commit()

def upsert_character(char_id, data):
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(
                "INSERT INTO characters (id,data) VALUES (%s,%s) ON CONFLICT (id) DO UPDATE SET data=EXCLUDED.data",
                (char_id, json.dumps(data)),
            )
        c.commit()

def upsert_institution(inst_id, payload):
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(
                "INSERT INTO institutions (id,payload) VALUES (%s,%s) ON CONFLICT (id) DO UPDATE SET payload=EXCLUDED.payload",
                (inst_id, json.dumps(payload)),
            )
        c.commit()

def upsert_relationship(a_id, b_id, payload):
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(
                "INSERT INTO relationships (a_id,b_id,payload) VALUES (%s,%s,%s) ON CONFLICT (a_id,b_id) DO UPDATE SET payload=EXCLUDED.payload",
                (a_id, b_id, json.dumps(payload)),
            )
        c.commit()

def upsert_conversation(conv_id, payload):
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(
                "INSERT INTO conversations (id,payload) VALUES (%s,%s) ON CONFLICT (id) DO UPDATE SET payload=EXCLUDED.payload",
                (conv_id, json.dumps(payload)),
            )
        c.commit()

def log_event(tick, kind, actor_id=None, target_id=None, payload=None):
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(
                "INSERT INTO timeline_events (tick,kind,actor_id,target_id,payload) VALUES (%s,%s,%s,%s,%s)",
                (tick, kind, actor_id, target_id, json.dumps(payload or {})),
            )
        c.commit()

def list_timeline_events(limit=200):
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT * FROM timeline_events ORDER BY id DESC LIMIT %s", (limit,))
            return cur.fetchall()

def replay_events(start_tick, end_tick):
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(
                "SELECT * FROM timeline_events WHERE tick >= %s AND tick <= %s ORDER BY id ASC",
                (start_tick, end_tick),
            )
            return cur.fetchall()

def replay_window(cursor_tick, radius=15):
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(
                "SELECT * FROM timeline_events WHERE tick >= %s AND tick <= %s ORDER BY id ASC",
                (max(1, cursor_tick - radius), cursor_tick + radius),
            )
            return cur.fetchall()
