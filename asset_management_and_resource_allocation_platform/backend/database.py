import sqlite3
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATABASE_DIR = ROOT_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "asset_manager.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"
SEED_PATH = DATABASE_DIR / "seed_data.sql"


def connect():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    DATABASE_DIR.mkdir(exist_ok=True)
    with connect() as connection:
        connection.executescript(SCHEMA_PATH.read_text())
        has_users = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        if has_users == 0:
            connection.executescript(SEED_PATH.read_text())


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def one_to_dict(row):
    return dict(row) if row else None
