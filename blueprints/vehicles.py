"""Blueprint for the vehicles table."""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from db import execute_query, execute_write
from mysql.connector import Error as MySQLError

vehicles_bp = Blueprint("vehicles", __name__, url_prefix="/vehicles")

TABLE = "vehicles"
PK = "vehicle_id"
COLUMNS = ["vehicle_id", "registration_number", "manufacture_year", "citizen_id"]
LABEL = "Vehicles"


def _get_citizens():
    rows, _, _ = execute_query("SELECT citizen_id, name FROM citizen ORDER BY name")
    return rows


@vehicles_bp.route("/")
def list_records():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    search_col = request.args.get("search_col", "registration_number")
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

    return render_template("vehicles/list.html", rows=data, columns=columns, page=page,
                           total_pages=total_pages, total=total, search=search, search_col=search_col,
                           all_columns=COLUMNS, label=LABEL, table=TABLE, pk=PK, query_time=query_time)


@vehicles_bp.route("/<int:record_id>")
def view_record(record_id):
    rows, columns, query_time = execute_query(f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("vehicles.list_records"))
    return render_template("vehicles/view.html", record=rows[0], columns=columns,
                           label=LABEL, table=TABLE, pk=PK, query_time=query_time)


@vehicles_bp.route("/create", methods=["GET", "POST"])
def create_record():
    if request.method == "POST":
        try:
            execute_write(
                "INSERT INTO vehicles (vehicle_id, registration_number, manufacture_year, citizen_id) VALUES (%s,%s,%s,%s)",
                (request.form["vehicle_id"], request.form.get("registration_number") or None,
                 request.form.get("manufacture_year") or None, request.form["citizen_id"]))
            flash("✅ Vehicle inserted successfully.", "success")
            return redirect(url_for("vehicles.list_records"))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    return render_template("vehicles/create.html", label=LABEL, table=TABLE, citizens=_get_citizens())


@vehicles_bp.route("/edit/<int:record_id>", methods=["GET", "POST"])
def edit_record(record_id):
    if request.method == "POST":
        try:
            execute_write(
                "UPDATE vehicles SET registration_number=%s, manufacture_year=%s, citizen_id=%s WHERE vehicle_id=%s",
                (request.form.get("registration_number") or None,
                 request.form.get("manufacture_year") or None,
                 request.form["citizen_id"], record_id))
            flash("✅ Vehicle updated successfully.", "success")
            return redirect(url_for("vehicles.view_record", record_id=record_id))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    rows, columns, query_time = execute_query(f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("vehicles.list_records"))
    return render_template("vehicles/edit.html", record=rows[0], label=LABEL, table=TABLE,
                           pk=PK, citizens=_get_citizens(), query_time=query_time)


@vehicles_bp.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    try:
        execute_write(f"DELETE FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
        flash("✅ Vehicle deleted.", "success")
    except MySQLError as e:
        if e.errno == 1451:
            flash("❌ Cannot delete: vehicle is referenced by other records (violations, tax, liability).", "error")
        else:
            flash(f"❌ MySQL Error: {e.msg}", "error")
    return redirect(url_for("vehicles.list_records"))
