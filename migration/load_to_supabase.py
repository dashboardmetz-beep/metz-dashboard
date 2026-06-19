"""
Copy all rows from local budget.db → Supabase Postgres.

Usage:
    export DATABASE_URL='postgresql://postgres:PASSWORD@db.xxxx.supabase.co:5432/postgres'
    python3 migration/load_to_supabase.py

What it does:
    1. Iterates every user table in budget.db.
    2. Skips empty tables.
    3. INSERTs all rows into Postgres using ON CONFLICT DO NOTHING so the
       script is safe to re-run (idempotent).
    4. Resets every BIGSERIAL sequence so future INSERTs continue from the
       right id.

Requires:
    pip install psycopg2-binary
"""
import os
import sqlite3
import sys
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import execute_batch
except ImportError:
    print("psycopg2 not installed. Run: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "budget.db"

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL env var is required.", file=sys.stderr)
    print("Example:\n  export DATABASE_URL='postgresql://postgres:PWD@db.xxx.supabase.co:5432/postgres'",
          file=sys.stderr)
    sys.exit(1)

BATCH = 200


def list_tables(sqlite_conn):
    cur = sqlite_conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [r[0] for r in cur.fetchall()]


def col_names(sqlite_conn, table):
    cur = sqlite_conn.cursor()
    cur.execute('PRAGMA table_info("{}")'.format(table))
    return [r[1] for r in cur.fetchall()]  # r[1] = column name


def copy_table(sqlite_conn, pg_conn, table):
    cols = col_names(sqlite_conn, table)
    if not cols:
        return 0

    src = sqlite_conn.cursor()
    src.execute('SELECT * FROM "{}"'.format(table))
    rows = src.fetchall()
    if not rows:
        return 0

    col_list = ", ".join('"{}"'.format(c) for c in cols)
    placeholders = ", ".join(["%s"] * len(cols))
    sql = 'INSERT INTO "{}" ({}) VALUES ({}) ON CONFLICT DO NOTHING'.format(
        table, col_list, placeholders,
    )

    cur = pg_conn.cursor()
    execute_batch(cur, sql, rows, page_size=BATCH)
    pg_conn.commit()
    return len(rows)


def reset_sequences(pg_conn):
    """Bump every BIGSERIAL sequence past the max id currently in its table."""
    cur = pg_conn.cursor()
    cur.execute(
        "SELECT c.table_name, c.column_name "
        "FROM information_schema.columns c "
        "WHERE c.column_default LIKE 'nextval(%' "
        "AND c.table_schema = 'public'"
    )
    cols = cur.fetchall()
    for tbl, col in cols:
        cur.execute(
            "SELECT pg_get_serial_sequence(%s, %s)", (tbl, col)
        )
        seq = cur.fetchone()[0]
        if not seq:
            continue
        cur.execute(
            'SELECT setval(%s, COALESCE((SELECT MAX("{}") FROM "{}"), 1))'.format(col, tbl),
            (seq,),
        )
    pg_conn.commit()


def main():
    sqlite_conn = sqlite3.connect(str(DB))
    pg_conn = psycopg2.connect(DATABASE_URL)

    # Defer FK enforcement during the load so referenced tables can be inserted
    # after their referrers without alphabetical ordering issues.
    with pg_conn.cursor() as _c:
        try:
            _c.execute("SET session_replication_role = 'replica'")
            pg_conn.commit()
            fk_deferred = True
        except psycopg2.Error:
            pg_conn.rollback()
            fk_deferred = False

    tables = list_tables(sqlite_conn)
    total_rows = 0
    total_tables = 0

    print("Copying {} tables → Postgres...\n".format(len(tables)))
    for t in tables:
        try:
            n = copy_table(sqlite_conn, pg_conn, t)
            if n:
                print("  {:35s} {:>6} rows".format(t, n))
                total_rows += n
                total_tables += 1
            else:
                print("  {:35s}    (empty, skipped)".format(t))
        except psycopg2.Error as e:
            pg_conn.rollback()
            print("  {:35s} ERROR: {}".format(t, str(e)[:120]))

    # Re-enable FK enforcement
    if fk_deferred:
        with pg_conn.cursor() as _c:
            _c.execute("SET session_replication_role = 'origin'")
            pg_conn.commit()

    print("\nResetting BIGSERIAL sequences...")
    reset_sequences(pg_conn)

    print("\nDone. Copied {} rows across {} tables.".format(total_rows, total_tables))
    sqlite_conn.close()
    pg_conn.close()


if __name__ == "__main__":
    main()
