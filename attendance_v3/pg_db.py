"""
pg_db.py  —  Single PostgreSQL connection module.
All database operations go through Postgres
"""

import psycopg2
import psycopg2.extras


def connect_pg():
    """Return a live psycopg2 connection. Raises on failure."""
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="Awab2004",
        port="5432"
    )


def get_cursor(conn):
    """Return a DictCursor so rows are accessible by column name."""
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
