import hashlib
import hmac
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "quizify.db"
HASH_ITERATIONS = 200_000

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    username_key TEXT,
    salt TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    bio TEXT NOT NULL DEFAULT '',
    avatar BLOB
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users (id),
    created_at TEXT NOT NULL,
    percent INTEGER NOT NULL,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS friendships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_a INTEGER NOT NULL REFERENCES users (id),
    user_b INTEGER NOT NULL REFERENCES users (id),
    created_at TEXT NOT NULL,
    UNIQUE (user_a, user_b)
);
"""


@contextmanager
def connection():
    """Отваря базата, записва промените при успех и винаги затваря връзката."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _username_key(username):
    """Ключ за сравняване на имена без значение от главни/малки букви (работи и за кирилица)."""
    return username.strip().casefold()


def _add_column(conn, table, column, definition):
    existing = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})")]
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    with connection() as conn:
        conn.executescript(SCHEMA)
        # по-старите бази нямат био и снимка
        _add_column(conn, "users", "bio", "TEXT NOT NULL DEFAULT ''")
        _add_column(conn, "users", "avatar", "BLOB")
        _add_column(conn, "users", "username_key", "TEXT")
        for row in conn.execute("SELECT id, username FROM users WHERE username_key IS NULL").fetchall():
            conn.execute(
                "UPDATE users SET username_key = ? WHERE id = ?",
                (_username_key(row["username"]), row["id"]),
            )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_key ON users (username_key)"
        )


def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, HASH_ITERATIONS)


def _password_matches(row, password):
    expected = bytes.fromhex(row["password_hash"])
    actual = _hash_password(password, bytes.fromhex(row["salt"]))
    return hmac.compare_digest(expected, actual)


def create_user(username, password):
    """Връща False, ако потребителското име е заето."""
    salt = os.urandom(16)
    try:
        with connection() as conn:
            conn.execute(
                "INSERT INTO users (username, username_key, salt, password_hash, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    username.strip(),
                    _username_key(username),
                    salt.hex(),
                    _hash_password(password, salt).hex(),
                    _now(),
                ),
            )
    except sqlite3.IntegrityError:
        return False
    return True


def verify_user(username, password):
    """Връща {'id', 'username'} при вярна парола, иначе None."""
    with connection() as conn:
        row = conn.execute(
            "SELECT id, username, salt, password_hash FROM users WHERE username_key = ?",
            (_username_key(username),),
        ).fetchone()
    if row is not None and _password_matches(row, password):
        return {"id": row["id"], "username": row["username"]}
    return None


def change_password(user_id, old_password, new_password):
    """Сменя паролата. Връща False, ако старата парола не е вярна."""
    with connection() as conn:
        row = conn.execute(
            "SELECT salt, password_hash FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None or not _password_matches(row, old_password):
            return False
        salt = os.urandom(16)
        conn.execute(
            "UPDATE users SET salt = ?, password_hash = ? WHERE id = ?",
            (salt.hex(), _hash_password(new_password, salt).hex(), user_id),
        )
    return True


def change_password(user_id, old_password, new_password):
    """Сменя паролата. Връща False, ако старата парола не е вярна."""
    with connection() as conn:
        row = conn.execute(
            "SELECT salt, password_hash FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None or not _password_matches(row, old_password):
            return False
        salt = os.urandom(16)
        conn.execute(
            "UPDATE users SET salt = ?, password_hash = ? WHERE id = ?",
            (salt.hex(), _hash_password(new_password, salt).hex(), user_id),

        )


def get_profile(user_id):
    with connection() as conn:
        row = conn.execute(
            "SELECT username, bio, avatar, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return None
    return {
        "username": row["username"],
        "bio": row["bio"] or "",
        "avatar": row["avatar"],
        "created_at": row["created_at"],
    }


def update_profile(user_id, bio, avatar=None):
    """Запазва биото; снимката се сменя само ако е подадена нова."""
    with connection() as conn:
        conn.execute("UPDATE users SET bio = ? WHERE id = ?", (bio, user_id))
        if avatar is not None:
            conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar, user_id))


def count_friends(user_id):
    with connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM friendships WHERE user_a = ? OR user_b = ?",
            (user_id, user_id),
        ).fetchone()
    return row["n"]


def save_result(user_id, result):
    with connection() as conn:
        conn.execute(
            "INSERT INTO results (user_id, created_at, percent, data) VALUES (?, ?, ?, ?)",
            (user_id, _now(), result["percent"], json.dumps(result, ensure_ascii=False)),
        )


def delete_result(user_id, result_id):
    """Изтрива тест, само ако е на този потребител. Връща True при успех."""
    with connection() as conn:
        cursor = conn.execute(
            "DELETE FROM results WHERE id = ? AND user_id = ?", (result_id, user_id)
        )
        return cursor.rowcount > 0


def list_results(user_id):
    """Тестовете на потребителя, най-новите първи."""
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, created_at, percent, data FROM results WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "percent": row["percent"],
            "data": json.loads(row["data"]),
        }
        for row in rows
    ]
