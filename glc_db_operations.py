"""Database migration helpers for local SQLite DB used during development.

This script is idempotent and safe to run multiple times. It will check for
missing columns and add them with sensible defaults. Run via:

    python glc_db_operations.py

It prints a summary of actions taken.
"""

import sqlite3
import sys
import argparse
from typing import List

DB_PATH = "glc_data.db"


def get_table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    c = conn.cursor()
    c.execute(f"PRAGMA table_info('{table}')")
    return [r[1] for r in c.fetchall()]


def add_column_if_missing(conn: sqlite3.Connection, table: str, column_name: str, column_sql: str) -> bool:
    """Adds column to table if it does not exist.

    Args:
        conn: sqlite3 connection
        table: table name
        column_name: simple name of the column to check
        column_sql: full SQL fragment used in ALTER TABLE ... ADD COLUMN (e.g. "shareholder_entities INTEGER NOT NULL DEFAULT 0")

    Returns:
        True if the column was added, False if it already existed.
    """
    cols = get_table_columns(conn, table)
    if column_name in cols:
        print(f"ℹ️ Column '{column_name}' already present on '{table}'")
        return False

    cur = conn.cursor()
    sql = f"ALTER TABLE {table} ADD COLUMN {column_sql}"
    print(f"🔧 Running: {sql}")
    cur.execute(sql)
    conn.commit()
    print(f"✅ Added column '{column_name}' to '{table}'")
    return True


def migrate():
    try:
        conn = sqlite3.connect(DB_PATH)
    except Exception as e:
        print("ERROR: unable to open database:", e)
        sys.exit(1)

    actions = []

    # Ensure shareholder_entities exists on loan_applications
    try:
        added = add_column_if_missing(
            conn,
            "loan_applications",
            "shareholder_entities",
            "shareholder_entities INTEGER NOT NULL DEFAULT 0",
        )
        actions.append(("shareholder_entities", added))
    except Exception as e:
        print("ERROR while adding shareholder_entities:", e)
        conn.close()
        sys.exit(1)

    # Ensure annual_revenue column exists
    try:
        added = add_column_if_missing(
            conn,
            "loan_applications",
            "annual_revenue",
            "annual_revenue REAL"
        )
        actions.append(("annual_revenue", added))
    except Exception as e:
        print("ERROR while adding annual_revenue:", e)
        conn.close()
        sys.exit(1)

    # Add organization & project columns that mirror the frontend JSON structure
    new_cols = [
        ("organization_name", "organization_name TEXT"),
        ("tax_id", "tax_id TEXT"),
        ("credit_score", "credit_score INTEGER"),
        ("headquarters_location", "headquarters_location TEXT"),
        ("project_title", "project_title TEXT"),
        ("project_sector", "project_sector TEXT"),
        ("use_of_proceeds_description", "use_of_proceeds_description TEXT"),
        ("ghg_target_reduction", "ghg_target_reduction INTEGER"),
        ("ghg_baseline_year", "ghg_baseline_year INTEGER")
    ]
    for name, sql in new_cols:
        try:
            added = add_column_if_missing(conn, "loan_applications", name, sql)
            actions.append((name, added))
        except Exception as e:
            print(f"ERROR while adding {name}:", e)
            conn.close()
            sys.exit(1)

    # Make sure supporting_documents mapping exists for existing rows
    try:
        cur.execute("UPDATE loan_applications SET raw_application_json = json_insert(COALESCE(raw_application_json, '{}'), '$.supporting_documents', json('{}')) WHERE raw_application_json IS NULL OR json_extract(raw_application_json, '$.supporting_documents') IS NULL")
        # Note: sqlite3 json_* functions are available on modern SQLite builds; if unavailable this is best-effort
        conn.commit()
    except Exception:
        # Ignore if sqlite build does not support json functions; we'll init supporting_documents on-demand
        pass

    # Make sure existing project_description values are populated (avoid nulls)
    try:
        cur = conn.cursor()
        # Normalize empty project_description to 'none' fallback per frontend contract
        cur.execute("UPDATE loan_applications SET project_description = 'none' WHERE project_description IS NULL OR TRIM(project_description) = ''")
        # Also convert legacy 'N/A' sentinel to 'none' to match frontend contract
        cur.execute("UPDATE loan_applications SET project_description = 'none' WHERE project_description = 'N/A'")
        updated = cur.rowcount
        if updated:
            conn.commit()
            print(f"✅ Updated {updated} rows to set default project_description='none'")
        actions.append(("ensure_project_description_values", updated > 0))
    except Exception as e:
        print("ERROR while updating project_description values:", e)
        conn.close()
        sys.exit(1)

    # Normalize other string sentinel values of 'N/A' to 'none' across loan_applications
    try:
        cur = conn.cursor()
        cols_to_normalize = [
            'location', 'project_location', 'use_of_proceeds', 'additional_info', 'cloud_doc_url',
            'org_name', 'use_of_proceeds_description', 'project_pin_code', 'contact_email', 'contact_phone',
            'installed_capacity', 'target_reduction'
        ]
        total_updated = 0
        for col in cols_to_normalize:
            sql = f"UPDATE loan_applications SET {col} = 'none' WHERE {col} = 'N/A'"
            cur.execute(sql)
            if cur.rowcount:
                total_updated += cur.rowcount
        if total_updated:
            conn.commit()
            print(f"✅ Normalized {total_updated} 'N/A' values to 'none' across columns: {cols_to_normalize}")
        actions.append(("normalize_na_to_none", total_updated > 0))
    except Exception as e:
        print("ERROR while normalizing 'N/A' values:", e)
        # Non-fatal; continue
        actions.append(("normalize_na_to_none", False))

    conn.close()

    print('\nSummary:')
    for name, done in actions:
        print(f" - {name}: {'added' if done else 'already present'}")

    print('\nDone.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run simple sqlite migrations for the GLC dev DB')
    parser.add_argument('--dry-run', action='store_true', help='List planned actions without applying')
    args = parser.parse_args()

    if args.dry_run:
        try:
            conn = sqlite3.connect(DB_PATH)
            cols = get_table_columns(conn, 'loan_applications')
            print("loan_applications columns:", cols)
            conn.close()
        except Exception as e:
            print('ERROR:', e)
            sys.exit(1)
        sys.exit(0)

    migrate()