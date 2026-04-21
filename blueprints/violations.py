"""Blueprint for the violations table — includes aggregate panel."""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from db import execute_query, execute_write
from mysql.connector import Error as MySQLError

violations_bp = Blueprint("violations", __name__, url_prefix="/violations")

TABLE = "violations"
PK = "violation_id"
COLUMNS = ["violation_id", "violation_type", "violation_date", "fine_amount", "vehicle_id"]
LABEL = "Violations"


def _get_vehicles():
    rows, _, _ = execute_query("SELECT vehicle_id, registration_number FROM vehicles ORDER BY vehicle_id")
    return rows


def _get_aggregates():
    """Return aggregate stats for the violations summary panel."""
    agg = {}
    rows, _, _ = execute_query("SELECT COUNT(*) AS cnt, SUM(fine_amount) AS total_fines, AVG(fine_amount) AS avg_fine FROM violations")
    if rows:
        agg["total_violations"] = rows[0]["cnt"]
        agg["total_fines"] = rows[0]["total_fines"] or 0
        agg["avg_fine"] = round(float(rows[0]["avg_fine"] or 0), 2)
    # Violations per vehicle (top 5)
    rows2, _, _ = execute_query(
        """SELECT v.vehicle_id, ve.registration_number, COUNT(*) AS cnt, SUM(v.fine_amount) AS total
           FROM violations v
           JOIN vehicles ve ON v.vehicle_id = ve.vehicle_id
           GROUP BY v.vehicle_id, ve.registration_number
           ORDER BY cnt DESC LIMIT 5""")
    agg["per_vehicle"] = rows2
    return agg


@violations_bp.route("/")
def list_records():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    search_col = request.args.get("search_col", "violation_type")
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

    aggregates = _get_aggregates()

    return render_template("violations/list.html", rows=data, columns=columns, page=page,
                           total_pages=total_pages, total=total, search=search, search_col=search_col,
                           all_columns=COLUMNS, label=LABEL, table=TABLE, pk=PK,
                           query_time=query_time, agg=aggregates)


@violations_bp.route("/<int:record_id>")
def view_record(record_id):
    rows, columns, query_time = execute_query(f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("violations.list_records"))
    return render_template("violations/view.html", record=rows[0], columns=columns,
                           label=LABEL, table=TABLE, pk=PK, query_time=query_time)


@violations_bp.route("/create", methods=["GET", "POST"])
def create_record():
    if request.method == "POST":
        try:
            execute_write(
                "INSERT INTO violations (violation_id, violation_type, violation_date, fine_amount, vehicle_id) VALUES (%s,%s,%s,%s,%s)",
                (request.form["violation_id"], request.form.get("violation_type") or None,
                 request.form.get("violation_date") or None, request.form.get("fine_amount") or None,
                 request.form["vehicle_id"]))
            flash("✅ Violation inserted.", "success")
            return redirect(url_for("violations.list_records"))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    return render_template("violations/create.html", label=LABEL, table=TABLE, vehicles=_get_vehicles())


@violations_bp.route("/edit/<int:record_id>", methods=["GET", "POST"])
def edit_record(record_id):
    if request.method == "POST":
        try:
            execute_write(
                "UPDATE violations SET violation_type=%s, violation_date=%s, fine_amount=%s, vehicle_id=%s WHERE violation_id=%s",
                (request.form.get("violation_type") or None, request.form.get("violation_date") or None,
                 request.form.get("fine_amount") or None, request.form["vehicle_id"], record_id))
            flash("✅ Violation updated.", "success")
            return redirect(url_for("violations.view_record", record_id=record_id))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    rows, _, query_time = execute_query(f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("violations.list_records"))
    return render_template("violations/edit.html", record=rows[0], label=LABEL, table=TABLE,
                           pk=PK, vehicles=_get_vehicles(), query_time=query_time)


@violations_bp.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    try:
        execute_write(f"DELETE FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
        flash("✅ Violation deleted.", "success")
    except MySQLError as e:
        if e.errno == 1451:
            flash("❌ Cannot delete: referenced by liability records.", "error")
        else:
            flash(f"❌ MySQL Error: {e.msg}", "error")
    return redirect(url_for("violations.list_records"))
