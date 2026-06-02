import psycopg2
import psycopg2.extras


def connect_pg():
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


def log_access(conn, user_id: int, action: str,
               target_type: str = None, target_id: int = None):

    try:
        cur = get_cursor(conn)
        cur.execute("""
            INSERT INTO access_log (user_id, action, target_type, target_id)
            VALUES (%s, %s, %s, %s)
        """, (user_id, action, target_type, target_id))
    except Exception:
        pass
