import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.db"),
)

_db_dir = os.path.dirname(DB_PATH)
if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """DB 테이블을 생성한다."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS creators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            channel_id TEXT,
            channel_name TEXT,
            thumbnail_url TEXT,
            subscriber_count INTEGER DEFAULT 0,
            last_score REAL,
            last_recommendation TEXT,
            last_ai_summary TEXT,
            last_evaluated_at TEXT,
            supercent_filter INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS evaluation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER NOT NULL,
            composite_score REAL,
            recommendation TEXT,
            ai_summary TEXT,
            result_json TEXT,
            evaluated_at TEXT NOT NULL,
            FOREIGN KEY (creator_id) REFERENCES creators(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cron_expression TEXT NOT NULL DEFAULT '0 9 * * *',
            enabled INTEGER DEFAULT 1,
            last_run_at TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );
    """)

    # 기본 스케줄이 없으면 생성 (매일 09:00)
    row = conn.execute("SELECT COUNT(*) as cnt FROM schedules").fetchone()
    if row["cnt"] == 0:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO schedules (cron_expression, enabled, created_at) VALUES (?, 1, ?)",
            ("0 9 * * *", now),
        )

    # 키워드 테이블이 비었으면 settings 기본값을 1회 seed
    row = conn.execute("SELECT COUNT(*) as cnt FROM keywords").fetchone()
    if row["cnt"] == 0:
        from backend.config import settings
        now = datetime.now(timezone.utc).isoformat()
        for kw in settings.supercent_keywords:
            kw_clean = (kw or "").strip()
            if not kw_clean:
                continue
            try:
                conn.execute(
                    "INSERT INTO keywords (keyword, created_at) VALUES (?, ?)",
                    (kw_clean, now),
                )
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    conn.close()


# --- Creator CRUD ---

def create_creator(url: str, supercent_filter: bool = True) -> dict:
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute(
            "INSERT INTO creators (url, supercent_filter, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (url, int(supercent_filter), now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM creators WHERE url = ?", (url,)).fetchone()
        return dict(row)
    except sqlite3.IntegrityError:
        raise ValueError("이미 등록된 URL입니다.")
    finally:
        conn.close()


def get_all_creators() -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM creators ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_creator(creator_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM creators WHERE id = ?", (creator_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_creator(creator_id: int) -> bool:
    conn = get_db()
    cursor = conn.execute("DELETE FROM creators WHERE id = ?", (creator_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def update_creator_evaluation(creator_id: int, channel_id: str, channel_name: str,
                               thumbnail_url: str, subscriber_count: int,
                               score: float, recommendation: str, ai_summary: str,
                               result_json: str):
    """평가 결과를 creator에 저장하고 히스토리에 추가한다."""
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()

    try:
        conn.execute("""
            UPDATE creators SET
                channel_id = ?, channel_name = ?, thumbnail_url = ?,
                subscriber_count = ?, last_score = ?, last_recommendation = ?,
                last_ai_summary = ?, last_evaluated_at = ?, updated_at = ?
            WHERE id = ?
        """, (channel_id, channel_name, thumbnail_url, subscriber_count,
              score, recommendation, ai_summary, now, now, creator_id))

        conn.execute("""
            INSERT INTO evaluation_history
                (creator_id, composite_score, recommendation, ai_summary, result_json, evaluated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (creator_id, score, recommendation, ai_summary, result_json, now))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_creator_history(creator_id: int, limit: int = 10) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM evaluation_history WHERE creator_id = ? ORDER BY evaluated_at DESC LIMIT ?",
        (creator_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Schedule ---

def get_schedule() -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM schedules ORDER BY id LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None


def update_schedule(cron_expression: str, enabled: bool) -> dict:
    conn = get_db()
    schedule = get_schedule()
    if schedule:
        conn.execute(
            "UPDATE schedules SET cron_expression = ?, enabled = ? WHERE id = ?",
            (cron_expression, int(enabled), schedule["id"]),
        )
    conn.commit()
    conn.close()
    return get_schedule()


def update_schedule_last_run():
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("UPDATE schedules SET last_run_at = ?", (now,))
    conn.commit()
    conn.close()


# --- Keywords ---

def get_keywords() -> list[str]:
    """저장된 슈퍼센트 키워드 전체를 문자열 리스트로 반환한다."""
    conn = get_db()
    rows = conn.execute("SELECT keyword FROM keywords ORDER BY id ASC").fetchall()
    conn.close()
    return [r["keyword"] for r in rows]


def list_keywords() -> list[dict]:
    """관리 UI 용 — id 포함 레코드 전체."""
    conn = get_db()
    rows = conn.execute("SELECT id, keyword, created_at FROM keywords ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_keyword(keyword: str) -> dict:
    """키워드를 추가한다. 빈 값·중복은 ValueError."""
    kw = (keyword or "").strip()
    if not kw:
        raise ValueError("키워드는 비어 있을 수 없습니다.")
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    try:
        cursor = conn.execute(
            "INSERT INTO keywords (keyword, created_at) VALUES (?, ?)",
            (kw, now),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, keyword, created_at FROM keywords WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return dict(row)
    except sqlite3.IntegrityError:
        raise ValueError("이미 등록된 키워드입니다.")
    finally:
        conn.close()


def delete_keyword(keyword_id: int) -> bool:
    conn = get_db()
    cursor = conn.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0
