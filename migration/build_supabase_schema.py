"""
Generate a Postgres-compatible schema.sql from the local SQLite budget.db.

Run:
    python3 migration/build_supabase_schema.py

Outputs:
    migration/supabase_schema.sql  — paste this into Supabase SQL Editor

Translation rules applied:
    INTEGER PRIMARY KEY AUTOINCREMENT  → BIGSERIAL PRIMARY KEY
    REAL                                → DOUBLE PRECISION
    DATETIME                            → TIMESTAMPTZ
    DATE                                → DATE
    TEXT                                → TEXT
    INTEGER                             → BIGINT
    BLOB                                → BYTEA
    datetime('now','localtime')         → now()
    CURRENT_TIMESTAMP                   → now()
    DEFAULT 0.0                         → unchanged
    AUTOINCREMENT (alone)               → stripped (BIGSERIAL handles it)

All tables get an `IF NOT EXISTS` guard so the file is idempotent.
"""
import os
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "budget.db"
OUT = ROOT / "migration" / "supabase_schema.sql"


def extract_foreign_keys(ddl: str, table_name: str):
    """Pull FOREIGN KEY (...) REFERENCES ...(...) clauses out of a CREATE TABLE.

    Returns (cleaned_ddl, list_of_alter_statements).
    """
    fk_pat = re.compile(
        r",?\s*FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+(\w+)\s*\(([^)]+)\)",
        re.IGNORECASE,
    )
    alters = []
    for m in fk_pat.finditer(ddl):
        local_cols, ref_table, ref_cols = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        alters.append(
            'ALTER TABLE "{tbl}" ADD CONSTRAINT "fk_{tbl}_{cols}" '
            'FOREIGN KEY ({local}) REFERENCES "{ref}"({ref_cols});'.format(
                tbl=table_name,
                cols=local_cols.replace(",", "_").replace(" ", ""),
                local=local_cols, ref=ref_table, ref_cols=ref_cols,
            )
        )
    cleaned = fk_pat.sub("", ddl)
    return cleaned, alters


def translate(ddl: str) -> str:
    s = ddl

    # CREATE TABLE → CREATE TABLE IF NOT EXISTS
    s = re.sub(
        r"CREATE\s+TABLE\s+(\"?\w+\"?)",
        r"CREATE TABLE IF NOT EXISTS \1",
        s, count=1, flags=re.IGNORECASE,
    )

    # ORDER MATTERS: rewrite SQLite-specific FUNCTION CALLS first, before the
    # type-substitution pass (which is case-insensitive and would otherwise
    # mangle lowercase `datetime(...)` calls into `TIMESTAMPTZ(...)`).

    # datetime('now', 'localtime')   → now()
    # datetime('now')                → now()
    # date('now')                    → CURRENT_DATE
    # CURRENT_TIMESTAMP              → now()
    s = re.sub(
        r"datetime\(\s*'now'(\s*,\s*'localtime')?\s*\)",
        "now()", s, flags=re.IGNORECASE,
    )
    s = re.sub(
        r"date\(\s*'now'(\s*,\s*'localtime')?\s*\)",
        "CURRENT_DATE", s, flags=re.IGNORECASE,
    )
    s = re.sub(r"\bCURRENT_TIMESTAMP\b", "now()", s, flags=re.IGNORECASE)

    # Now safe to do the type conversions.

    # INTEGER PRIMARY KEY AUTOINCREMENT → BIGSERIAL PRIMARY KEY
    s = re.sub(
        r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT",
        "BIGSERIAL PRIMARY KEY",
        s, flags=re.IGNORECASE,
    )
    # Some SQLite tables omit AUTOINCREMENT but still want serial behavior
    s = re.sub(
        r"INTEGER\s+PRIMARY\s+KEY(?!\s+AUTOINCREMENT)",
        "BIGSERIAL PRIMARY KEY",
        s, flags=re.IGNORECASE,
    )

    # Type translations — only as a TYPE TOKEN (preceded by a column name
    # token and whitespace, so we don't accidentally match inside a function
    # name or comment).
    type_map = [
        (r"(?<![\w(])DATETIME\b",        "TIMESTAMPTZ"),
        (r"(?<![\w(])TIMESTAMP\b(?!TZ)", "TIMESTAMPTZ"),
        (r"(?<![\w(])REAL\b",            "DOUBLE PRECISION"),
        (r"(?<![\w(])BLOB\b",            "BYTEA"),
        # Bare INTEGER (not PRIMARY KEY AUTOINCREMENT — handled above)
        (r"(?<![\w(])INTEGER\b",         "BIGINT"),
        # BOOLEAN — SQLite stores as 0/1; Postgres has real boolean
        (r"(?<![\w(])BOOLEAN\b",         "BOOLEAN"),
    ]
    for pat, repl in type_map:
        s = re.sub(pat, repl, s, flags=re.IGNORECASE)

    # Strip stray AUTOINCREMENT (Postgres doesn't know the word)
    s = re.sub(r"\s+AUTOINCREMENT", "", s, flags=re.IGNORECASE)

    # SQLite allows DEFAULT "string" (double quotes); Postgres treats double
    # quotes as identifier references and rejects this. Convert string-literal
    # defaults to single quotes.
    s = re.sub(
        r'DEFAULT\s+"([^"]*)"',
        lambda m: "DEFAULT '{}'".format(m.group(1).replace("'", "''")),
        s,
    )

    # CHECK constraints with SQLite-only functions — strip them; the app
    # enforces these. Catches CHECK (datetime(...))  or CHECK (typeof(...)).
    s = re.sub(
        r",?\s*CHECK\s*\([^)]*\b(typeof|datetime|date|strftime|julianday)\b[^)]*\)",
        "", s, flags=re.IGNORECASE,
    )

    return s.strip()


def main():
    if not DB.exists():
        raise SystemExit("budget.db not found at {}".format(DB))

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute(
        "SELECT name, sql FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    )
    tables = cur.fetchall()

    # Indexes too
    cur.execute(
        "SELECT name, sql FROM sqlite_master "
        "WHERE type='index' AND sql IS NOT NULL "
        "AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    )
    indexes = cur.fetchall()

    OUT.parent.mkdir(exist_ok=True)
    all_alters = []
    with open(OUT, "w") as f:
        f.write(
            "-- Auto-generated Postgres schema for Supabase.\n"
            "-- Source: budget.db (SQLite). Built by migration/build_supabase_schema.py.\n"
            "-- Safe to re-run: every statement is IF NOT EXISTS.\n\n"
        )
        for name, ddl in tables:
            if not ddl:
                continue
            cleaned, alters = extract_foreign_keys(ddl, name)
            all_alters.extend(alters)
            f.write("-- ─── {} ───\n".format(name))
            f.write(translate(cleaned))
            f.write(";\n\n")

        if all_alters:
            f.write("\n-- ═══ Foreign keys (added after all tables exist) ═══\n\n")
            for stmt in all_alters:
                # Wrap in DO block so re-running doesn't error on existing FKs
                f.write(
                    "DO $$ BEGIN\n"
                    "  {};\n"
                    "EXCEPTION WHEN duplicate_object THEN NULL;\n"
                    "END $$;\n".format(stmt.rstrip(";"))
                )

        if indexes:
            f.write("\n-- ═══ Indexes ═══\n\n")
            for name, ddl in indexes:
                ddl_t = re.sub(
                    r"CREATE\s+(UNIQUE\s+)?INDEX\s+",
                    lambda m: "CREATE {}INDEX IF NOT EXISTS ".format(
                        m.group(1) or ""),
                    ddl, count=1, flags=re.IGNORECASE,
                )
                f.write(ddl_t.strip() + ";\n")

    print("Wrote {} ({} tables, {} indexes)".format(
        OUT.relative_to(ROOT), len(tables), len(indexes)))


if __name__ == "__main__":
    main()
