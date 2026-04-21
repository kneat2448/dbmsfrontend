"""
Database helper module.
Uses flask.g for per-request connection reuse.
All queries are parameterized with %s placeholders.
"""

import time
import mysql.connector
from mysql.connector import Error as MySQLError
from flask import g, current_app


def get_db():
    """Return the MySQL connection for this request, creating one if needed."""
    if "db" not in g:
        cfg = current_app.config
        g.db = mysql.connector.connect(
            host=cfg["MYSQL_HOST"],
            port=cfg["MYSQL_PORT"],
            user=cfg["MYSQL_USER"],
            password=cfg["MYSQL_PASSWORD"],
            database=cfg["MYSQL_DATABASE"],
        )
    return g.db


def close_db(exc=None):
    """Close the connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()


def execute_query(query, params=None):
    """
    Execute a SELECT query.
    Returns (rows, columns, exec_time_ms).
    """
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    start = time.perf_counter()
    cursor.execute(query, params or ())
    rows = cursor.fetchall()
    elapsed = (time.perf_counter() - start) * 1000  # ms
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    cursor.close()
    return rows, columns, round(elapsed, 2)


def execute_write(query, params=None):
    """
    Execute an INSERT / UPDATE / DELETE query.
    Returns (affected_rows, exec_time_ms).
    Raises MySQLError on failure.
    """
    conn = get_db()
    cursor = conn.cursor()
    start = time.perf_counter()
    cursor.execute(query, params or ())
    conn.commit()
    elapsed = (time.perf_counter() - start) * 1000
    affected = cursor.rowcount
    cursor.close()
    return affected, round(elapsed, 2)


def init_app(app):
    """Register teardown so connections close automatically."""
    app.teardown_appcontext(close_db)
