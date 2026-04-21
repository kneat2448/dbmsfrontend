"""Blueprint for the tax table — includes aggregate panel."""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from db import execute_query, execute_write
from mysql.connector import Error as MySQLError

tax_bp = Blueprint("tax", __name__, url_prefix="/tax")

TABLE = "tax"
PK = "tax_id"
COLUMNS = ["tax_id", "tax_type", "tax_amount", "due_date", "vehicle_id"]
LABEL = "Tax"


def _get_vehicles():
    rows, _, _ = execute_query("SELECT vehicle_id, registration_number FROM vehicles ORDER BY vehicle_id")
    return rows


def _get_aggregates():
    agg = {}
    rows, _, _ = execute_query("SELECT COUNT(*) AS cnt, SUM(tax_amount) AS total_tax, AVG(tax_amount) AS avg_tax FROM tax")
    if rows:
        agg["total_records"] = rows[0]["cnt"]
        agg["total_tax"] = rows[0]["total_tax"] or 0
        agg["avg_tax"] = round(float(rows[0]["avg_tax"] or 0), 2)
    rows2, _, _ = execute_query(
        """SELECT t.vehicle_id, v.registration_number, COUNT(*) AS cnt, SUM(t.tax_amount) AS total
           FROM tax t JOIN vehicles v ON t.vehicle_id = v.vehicle_id
           GROUP BY t.vehicle_id, v.registration_number ORDER BY total DESC LIMIT 5""")
    agg["per_vehicle"] = rows2
    return agg


@tax_bp.route("/")
def list_records():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    search_col = request.args.get("search_col", "tax_type")
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

    return render_template("tax/list.html", rows=data, columns=columns, page=page,
                           total_pages=total_pages, total=total, search=search, search_col=search_col,
                           all_columns=COLUMNS, label=LABEL, table=TABLE, pk=PK,
                           query_time=query_time, agg=aggregates)


@tax_bp.route("/<int:record_id>")
def view_record(record_id):
    rows, columns, query_time = execute_query(f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("tax.list_records"))
    return render_template("tax/view.html", record=rows[0], columns=columns,
                           label=LABEL, table=TABLE, pk=PK, query_time=query_time)


@tax_bp.route("/create", methods=["GET", "POST"])
def create_record():
    if request.method == "POST":
        try:
            execute_write(
                "INSERT INTO tax (tax_id, tax_type, tax_amount, due_date, vehicle_id) VALUES (%s,%s,%s,%s,%s)",
                (request.form["tax_id"], request.form.get("tax_type") or None,
                 request.form.get("tax_amount") or None, request.form.get("due_date") or None,
                 request.form["vehicle_id"]))
            flash("✅ Tax record inserted.", "success")
            return redirect(url_for("tax.list_records"))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    return render_template("tax/create.html", label=LABEL, table=TABLE, vehicles=_get_vehicles())


@tax_bp.route("/edit/<int:record_id>", methods=["GET", "POST"])
def edit_record(record_id):
    if request.method == "POST":
        try:
            execute_write(
                "UPDATE tax SET tax_type=%s, tax_amount=%s, due_date=%s, vehicle_id=%s WHERE tax_id=%s",
                (request.form.get("tax_type") or None, request.form.get("tax_amount") or None,
                 request.form.get("due_date") or None, request.form["vehicle_id"], record_id))
            flash("✅ Tax record updated.", "success")
            return redirect(url_for("tax.view_record", record_id=record_id))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    rows, _, query_time = execute_query(f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("tax.list_records"))
    return render_template("tax/edit.html", record=rows[0], label=LABEL, table=TABLE,
                           pk=PK, vehicles=_get_vehicles(), query_time=query_time)


@tax_bp.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    try:
        execute_write(f"DELETE FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
        flash("✅ Tax record deleted.", "success")
    except MySQLError as e:
        if e.errno == 1451:
            flash("❌ Cannot delete: referenced by liability records.", "error")
        else:
            flash(f"❌ MySQL Error: {e.msg}", "error")
    return redirect(url_for("tax.list_records"))
