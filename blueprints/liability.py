"""Blueprint for the liability table."""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from db import execute_query, execute_write
from mysql.connector import Error as MySQLError

liability_bp = Blueprint("liability", __name__, url_prefix="/liability")

TABLE = "liability"
PK = "liability_id"
COLUMNS = ["liability_id", "liability_type", "reference_id", "vehicle_id"]
LABEL = "Liability"


def _get_vehicles():
    rows, _, _ = execute_query("SELECT vehicle_id, registration_number FROM vehicles ORDER BY vehicle_id")
    return rows


@liability_bp.route("/")
def list_records():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    search_col = request.args.get("search_col", "liability_type")
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

    return render_template("liability/list.html", rows=data, columns=columns, page=page,
                           total_pages=total_pages, total=total, search=search, search_col=search_col,
                           all_columns=COLUMNS, label=LABEL, table=TABLE, pk=PK, query_time=query_time)


@liability_bp.route("/<int:record_id>")
def view_record(record_id):
    rows, columns, query_time = execute_query(f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("liability.list_records"))
    return render_template("liability/view.html", record=rows[0], columns=columns,
                           label=LABEL, table=TABLE, pk=PK, query_time=query_time)


@liability_bp.route("/create", methods=["GET", "POST"])
def create_record():
    if request.method == "POST":
        try:
            execute_write(
                "INSERT INTO liability (liability_id, liability_type, reference_id, vehicle_id) VALUES (%s,%s,%s,%s)",
                (request.form["liability_id"], request.form["liability_type"],
                 request.form["reference_id"], request.form["vehicle_id"]))
            flash("✅ Liability inserted.", "success")
            return redirect(url_for("liability.list_records"))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    return render_template("liability/create.html", label=LABEL, table=TABLE, vehicles=_get_vehicles())


@liability_bp.route("/edit/<int:record_id>", methods=["GET", "POST"])
def edit_record(record_id):
    if request.method == "POST":
        try:
            execute_write(
                "UPDATE liability SET liability_type=%s, reference_id=%s, vehicle_id=%s WHERE liability_id=%s",
                (request.form["liability_type"], request.form["reference_id"],
                 request.form["vehicle_id"], record_id))
            flash("✅ Liability updated.", "success")
            return redirect(url_for("liability.view_record", record_id=record_id))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    rows, _, query_time = execute_query(f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("liability.list_records"))
    return render_template("liability/edit.html", record=rows[0], label=LABEL, table=TABLE,
                           pk=PK, vehicles=_get_vehicles(), query_time=query_time)


@liability_bp.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    try:
        execute_write(f"DELETE FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
        flash("✅ Liability deleted.", "success")
    except MySQLError as e:
        if e.errno == 1451:
            flash("❌ Cannot delete: referenced by paid_using records.", "error")
        else:
            flash(f"❌ MySQL Error: {e.msg}", "error")
    return redirect(url_for("liability.list_records"))
