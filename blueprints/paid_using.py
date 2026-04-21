"""Blueprint for the paid_using table (composite PK: liability_id + payment_id)."""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from db import execute_query, execute_write
from mysql.connector import Error as MySQLError

paid_using_bp = Blueprint("paid_using", __name__, url_prefix="/paid_using")

TABLE = "paid_using"
COLUMNS = ["liability_id", "payment_id"]
LABEL = "Paid Using"


def _get_liabilities():
    rows, _, _ = execute_query("SELECT liability_id, liability_type FROM liability ORDER BY liability_id")
    return rows


def _get_payments():
    rows, _, _ = execute_query("SELECT payment_id, payment_mode, amount_paid FROM payment_info ORDER BY payment_id")
    return rows


@paid_using_bp.route("/")
def list_records():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    search_col = request.args.get("search_col", "liability_id")
    per_page = 10
    offset = (page - 1) * per_page

    if search:
        cnt_rows, _, _ = execute_query(
            f"SELECT COUNT(*) AS cnt FROM `{TABLE}` WHERE `{search_col}` LIKE %s", (f"%{search}%",))
    else:
        cnt_rows, _, _ = execute_query(f"SELECT COUNT(*) AS cnt FROM `{TABLE}`")
    total = cnt_rows[0]["cnt"]
    total_pages = max(1, -(-total // per_page))

    if search:
        data, columns, query_time = execute_query(
            f"SELECT * FROM `{TABLE}` WHERE `{search_col}` LIKE %s ORDER BY liability_id, payment_id LIMIT %s OFFSET %s",
            (f"%{search}%", per_page, offset))
    else:
        data, columns, query_time = execute_query(
            f"SELECT * FROM `{TABLE}` ORDER BY liability_id, payment_id LIMIT %s OFFSET %s",
            (per_page, offset))

    return render_template("paid_using/list.html", rows=data, columns=columns, page=page,
                           total_pages=total_pages, total=total, search=search, search_col=search_col,
                           all_columns=COLUMNS, label=LABEL, table=TABLE,
                           query_time=query_time)


@paid_using_bp.route("/<int:liability_id>/<int:payment_id>")
def view_record(liability_id, payment_id):
    rows, columns, query_time = execute_query(
        "SELECT * FROM paid_using WHERE liability_id=%s AND payment_id=%s",
        (liability_id, payment_id))
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("paid_using.list_records"))
    return render_template("paid_using/view.html", record=rows[0], columns=columns,
                           label=LABEL, table=TABLE, query_time=query_time)


@paid_using_bp.route("/create", methods=["GET", "POST"])
def create_record():
    if request.method == "POST":
        try:
            execute_write(
                "INSERT INTO paid_using (liability_id, payment_id) VALUES (%s, %s)",
                (request.form["liability_id"], request.form["payment_id"]))
            flash("✅ Paid-using link inserted.", "success")
            return redirect(url_for("paid_using.list_records"))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    return render_template("paid_using/create.html", label=LABEL, table=TABLE,
                           liabilities=_get_liabilities(), payments=_get_payments())


@paid_using_bp.route("/delete/<int:liability_id>/<int:payment_id>", methods=["POST"])
def delete_record(liability_id, payment_id):
    try:
        execute_write(
            "DELETE FROM paid_using WHERE liability_id=%s AND payment_id=%s",
            (liability_id, payment_id))
        flash("✅ Paid-using link deleted.", "success")
    except MySQLError as e:
        flash(f"❌ MySQL Error: {e.msg}", "error")
    return redirect(url_for("paid_using.list_records"))
