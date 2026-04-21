"""Blueprint for the vehicle_registrations table — includes JOIN display."""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from db import execute_query, execute_write
from mysql.connector import Error as MySQLError

vehicle_registrations_bp = Blueprint("vehicle_registrations", __name__, url_prefix="/vehicle_registrations")

TABLE = "vehicle_registrations"
PK = "registration_id"
COLUMNS = ["registration_id", "registration_date", "expiry_date", "citizen_id"]
LABEL = "Vehicle Registrations"


def _get_citizens():
    rows, _, _ = execute_query("SELECT citizen_id, name FROM citizen ORDER BY name")
    return rows


@vehicle_registrations_bp.route("/")
def list_records():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    search_col = request.args.get("search_col", "registration_id")
    per_page = 10
    offset = (page - 1) * per_page

    # JOIN query to show citizen name alongside registration
    base_query = """
        SELECT vr.registration_id, vr.registration_date, vr.expiry_date,
               vr.citizen_id, c.name AS citizen_name
        FROM vehicle_registrations vr
        JOIN citizen c ON vr.citizen_id = c.citizen_id
    """
    count_base = """
        SELECT COUNT(*) AS cnt
        FROM vehicle_registrations vr
        JOIN citizen c ON vr.citizen_id = c.citizen_id
    """

    if search:
        # Allow searching on joined columns too
        search_target = f"vr.{search_col}" if search_col in COLUMNS else f"c.{search_col}"
        count_q = count_base + f" WHERE {search_target} LIKE %s"
        cnt_rows, _, _ = execute_query(count_q, (f"%{search}%",))
        data_q = base_query + f" WHERE {search_target} LIKE %s ORDER BY vr.registration_id LIMIT %s OFFSET %s"
        data, columns, query_time = execute_query(data_q, (f"%{search}%", per_page, offset))
    else:
        cnt_rows, _, _ = execute_query(count_base)
        data_q = base_query + " ORDER BY vr.registration_id LIMIT %s OFFSET %s"
        data, columns, query_time = execute_query(data_q, (per_page, offset))

    total = cnt_rows[0]["cnt"]
    total_pages = max(1, -(-total // per_page))

    search_columns = COLUMNS + ["citizen_name"]

    return render_template("vehicle_registrations/list.html", rows=data, columns=columns,
                           page=page, total_pages=total_pages, total=total,
                           search=search, search_col=search_col,
                           all_columns=search_columns, label=LABEL, table=TABLE, pk=PK,
                           query_time=query_time)


@vehicle_registrations_bp.route("/<int:record_id>")
def view_record(record_id):
    rows, columns, query_time = execute_query(
        """SELECT vr.*, c.name AS citizen_name
           FROM vehicle_registrations vr
           JOIN citizen c ON vr.citizen_id = c.citizen_id
           WHERE vr.registration_id = %s""", (record_id,))
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("vehicle_registrations.list_records"))
    return render_template("vehicle_registrations/view.html", record=rows[0], columns=columns,
                           label=LABEL, table=TABLE, pk=PK, query_time=query_time)


@vehicle_registrations_bp.route("/create", methods=["GET", "POST"])
def create_record():
    if request.method == "POST":
        try:
            execute_write(
                "INSERT INTO vehicle_registrations (registration_id, registration_date, expiry_date, citizen_id) VALUES (%s,%s,%s,%s)",
                (request.form["registration_id"],
                 request.form.get("registration_date") or None,
                 request.form.get("expiry_date") or None,
                 request.form["citizen_id"]))
            flash("✅ Registration inserted.", "success")
            return redirect(url_for("vehicle_registrations.list_records"))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    return render_template("vehicle_registrations/create.html", label=LABEL, table=TABLE, citizens=_get_citizens())


@vehicle_registrations_bp.route("/edit/<int:record_id>", methods=["GET", "POST"])
def edit_record(record_id):
    if request.method == "POST":
        try:
            execute_write(
                "UPDATE vehicle_registrations SET registration_date=%s, expiry_date=%s, citizen_id=%s WHERE registration_id=%s",
                (request.form.get("registration_date") or None,
                 request.form.get("expiry_date") or None,
                 request.form["citizen_id"], record_id))
            flash("✅ Registration updated.", "success")
            return redirect(url_for("vehicle_registrations.view_record", record_id=record_id))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    rows, _, query_time = execute_query(f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("vehicle_registrations.list_records"))
    return render_template("vehicle_registrations/edit.html", record=rows[0], label=LABEL,
                           table=TABLE, pk=PK, citizens=_get_citizens(), query_time=query_time)


@vehicle_registrations_bp.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    try:
        execute_write(f"DELETE FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
        flash("✅ Registration deleted.", "success")
    except MySQLError as e:
        if e.errno == 1451:
            flash("❌ Cannot delete: referenced by other records.", "error")
        else:
            flash(f"❌ MySQL Error: {e.msg}", "error")
    return redirect(url_for("vehicle_registrations.list_records"))
