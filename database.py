import hashlib
import hmac
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "quizify.db"
ITERATIONS = 200_000

def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # за да четем колоните по име
    return conn


def _add_column_if_missing(conn, table, column, definition):
    """Добавя колона към стара таблица, ако още я няма (без да губи данните)."""
    columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})")]
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    """Създава таблиците, ако още ги няма."""
    with closing(_connect()) as conn:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    salt TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    bio TEXT NOT NULL DEFAULT '',
                    avatar BLOB
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    percent INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS friendships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_a INTEGER NOT NULL,
                    user_b INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (user_a, user_b),
                    FOREIGN KEY (user_a) REFERENCES users (id),
                    FOREIGN KEY (user_b) REFERENCES users (id)
                )
                """
            )
            _add_column_if_missing(conn, "users", "bio", "TEXT NOT NULL DEFAULT ''")
            _add_column_if_missing(conn, "users", "avatar", "BLOB")


def _hash_password(password, salt):
    """Превръща паролата в нечетим низ. От него не може да се върне паролата."""
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)


def create_user(username, password):
    """Създава профил. Връща True, а ако името е заето - False."""
    salt = os.urandom(16)  # случайна сол, различна за всеки потребител
    password_hash = _hash_password(password, salt)
    try:
        with closing(_connect()) as conn:
            with conn:
                # Знаците ? пазят от SQL инжекция: данните никога не се вмъкват направо в заявката
                conn.execute(
                    "INSERT INTO users (username, salt, password_hash, created_at) VALUES (?, ?, ?, ?)",
                    (
                        username.strip(),
                        salt.hex(),
                        password_hash.hex(),
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )
    except sqlite3.IntegrityError:
        return False  # такова име вече има
    return True


def verify_user(username, password):
    """Проверява името и паролата. Връща {'id', 'username'} или None."""
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username.strip(),)
        ).fetchone()
    if row is None:
        return None
    expected = bytes.fromhex(row["password_hash"])
    actual = _hash_password(password, bytes.fromhex(row["salt"]))
    if hmac.compare_digest(expected, actual):  # безопасно сравняване
        return {"id": row["id"], "username": row["username"]}
    return None


def get_profile(user_id):
    """Данните за профила: име, био, снимка (или None) и кога е създаден."""
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT username, bio, avatar, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "username": row["username"],
        "bio": row["bio"] or "",
        "avatar": row["avatar"],  # байтове на снимката или None
        "created_at": row["created_at"],
    }


def update_profile(user_id, bio, avatar=None):
    """Запазва биото. Ако има нова снимка, сменя и нея."""
    with closing(_connect()) as conn:
        with conn:
            conn.execute("UPDATE users SET bio = ? WHERE id = ?", (bio, user_id))
            if avatar is not None:
                conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar, user_id))


def count_friends(user_id):
    """Колко приятели има потребителят (засега винаги 0, докато не добавим приятелствата)."""
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM friendships WHERE user_a = ? OR user_b = ?",
            (user_id, user_id),
        ).fetchone()
    return row["n"]


def save_result(user_id, result):
    """Запазва един решен тест (целият речник като текст във формат JSON)."""
    data = json.dumps(result, ensure_ascii=False)
    with closing(_connect()) as conn:
        with conn:
            conn.execute(
                "INSERT INTO results (user_id, created_at, percent, data) VALUES (?, ?, ?, ?)",
                (
                    user_id,
                    datetime.now().isoformat(timespec="seconds"),
                    result["percent"],
                    data,
                ),
            )


def count_results(user_id):
    """Колко теста е запазил потребителят."""
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM results WHERE user_id = ?", (user_id,)
        ).fetchone()
    return row["n"]


def list_results(user_id):
    """Всички тестове на потребителя, най-новите първи."""
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT id, created_at, percent, data FROM results WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "percent": row["percent"],
            "data": json.loads(row["data"]),  # връщаме текста обратно в речник
        }
        for row in rows
    ]