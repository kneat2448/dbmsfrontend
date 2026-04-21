"""Blueprint for the payment_info table."""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from db import execute_query, execute_write
from mysql.connector import Error as MySQLError

payment_info_bp = Blueprint("payment_info", __name__, url_prefix="/payment_info")

TABLE = "payment_info"
PK = "payment_id"
COLUMNS = ["payment_id", "payment_date", "amount_paid", "payment_mode"]
LABEL = "Payment Info"


@payment_info_bp.route("/")
def list_records():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    search_col = request.args.get("search_col", "payment_mode")
    per_page = 10
    offset = (page - 1) * per_page

    if search:
        cnt_rows, _, _ = execute_query(f"SELECT COUNT(*) AS cnt FROM `{TABLE}` WHERE `{search_col}` LIKE %s", (f"%{search}%",))
    else:
        cnt_rows, _, _ = execute_query(f"SELECT COUNT(*) AS cnt FROM `{TABLE}`")
    total = cnt_rows[0]["cnt"]
    total_pages = max(1, -(-total // per_page))

    if search:
        data, columns, query_time = execute_query(
            f"SELECT * FROM `{TABLE}` WHERE `{search_col}` LIKE %s ORDER BY `{PK}` LIMIT %s OFFSET %s",
            (f"%{search}%", per_page, offset))
    else:
        data, columns, query_time = execute_query(
            f"SELECT * FROM `{TABLE}` ORDER BY `{PK}` LIMIT %s OFFSET %s", (per_page, offset))

    return render_template("payment_info/list.html", rows=data, columns=columns, page=page,
                           total_pages=total_pages, total=total, search=search, search_col=search_col,
                           all_columns=COLUMNS, label=LABEL, table=TABLE, pk=PK, query_time=query_time)


@payment_info_bp.route("/<int:record_id>")
def view_record(record_id):
    rows, columns, query_time = execute_query(f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("payment_info.list_records"))
    return render_template("payment_info/view.html", record=rows[0], columns=columns,
                           label=LABEL, table=TABLE, pk=PK, query_time=query_time)


@payment_info_bp.route("/create", methods=["GET", "POST"])
def create_record():
    if request.method == "POST":
        try:
            execute_write(
                "INSERT INTO payment_info (payment_id, payment_date, amount_paid, payment_mode) VALUES (%s,%s,%s,%s)",
                (request.form["payment_id"], request.form.get("payment_date") or None,
                 request.form.get("amount_paid") or None, request.form.get("payment_mode") or None))
            flash("✅ Payment info inserted.", "success")
            return redirect(url_for("payment_info.list_records"))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    return render_template("payment_info/create.html", label=LABEL, table=TABLE)


@payment_info_bp.route("/edit/<int:record_id>", methods=["GET", "POST"])
def edit_record(record_id):
    if request.method == "POST":
        try:
            execute_write(
                "UPDATE payment_info SET payment_date=%s, amount_paid=%s, payment_mode=%s WHERE payment_id=%s",
                (request.form.get("payment_date") or None, request.form.get("amount_paid") or None,
                 request.form.get("payment_mode") or None, record_id))
            flash("✅ Payment info updated.", "success")
            return redirect(url_for("payment_info.view_record", record_id=record_id))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    rows, _, query_time = execute_query(f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("payment_info.list_records"))
    return render_template("payment_info/edit.html", record=rows[0], label=LABEL, table=TABLE,
                           pk=PK, query_time=query_time)


@payment_info_bp.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    try:
        execute_write(f"DELETE FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
        flash("✅ Payment info deleted.", "success")
    except MySQLError as e:
        if e.errno == 1451:
            flash("❌ Cannot delete: referenced by paid_using records.", "error")
        else:
            flash(f"❌ MySQL Error: {e.msg}", "error")
    return redirect(url_for("payment_info.list_records"))
