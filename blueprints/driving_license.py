"""Blueprint for the driving_license table."""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from db import execute_query, execute_write
from mysql.connector import Error as MySQLError

driving_license_bp = Blueprint("driving_license", __name__, url_prefix="/driving_license")

TABLE = "driving_license"
PK = "dl_number"
COLUMNS = ["dl_number", "issue_date", "expiry_date", "citizen_id"]
LABEL = "Driving Licenses"


def _get_citizens():
    rows, _, _ = execute_query("SELECT citizen_id, name FROM citizen ORDER BY name")
    return rows


@driving_license_bp.route("/")
def list_records():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    search_col = request.args.get("search_col", "dl_number")
    per_page = 10
    offset = (page - 1) * per_page

    if search:
        count_q = f"SELECT COUNT(*) AS cnt FROM `{TABLE}` WHERE `{search_col}` LIKE %s"
        rows, _, _ = execute_query(count_q, (f"%{search}%",))
    else:
        rows, _, _ = execute_query(f"SELECT COUNT(*) AS cnt FROM `{TABLE}`")
    total = rows[0]["cnt"]
    total_pages = max(1, -(-total // per_page))

    if search:
        data_q = f"SELECT * FROM `{TABLE}` WHERE `{search_col}` LIKE %s ORDER BY `{PK}` LIMIT %s OFFSET %s"
        data, columns, query_time = execute_query(data_q, (f"%{search}%", per_page, offset))
    else:
        data_q = f"SELECT * FROM `{TABLE}` ORDER BY `{PK}` LIMIT %s OFFSET %s"
        data, columns, query_time = execute_query(data_q, (per_page, offset))

    return render_template(
        "driving_license/list.html",
        rows=data, columns=columns, page=page, total_pages=total_pages,
        total=total, search=search, search_col=search_col,
        all_columns=COLUMNS, label=LABEL, table=TABLE, pk=PK,
        query_time=query_time,
    )


@driving_license_bp.route("/<record_id>")
def view_record(record_id):
    rows, columns, query_time = execute_query(
        f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,)
    )
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("driving_license.list_records"))
    return render_template(
        "driving_license/view.html",
        record=rows[0], columns=columns, label=LABEL, table=TABLE, pk=PK,
        query_time=query_time,
    )


@driving_license_bp.route("/create", methods=["GET", "POST"])
def create_record():
    if request.method == "POST":
        try:
            execute_write(
                "INSERT INTO driving_license (dl_number, issue_date, expiry_date, citizen_id) VALUES (%s, %s, %s, %s)",
                (
                    request.form["dl_number"],
                    request.form.get("issue_date") or None,
                    request.form.get("expiry_date") or None,
                    request.form["citizen_id"],
                ),
            )
            flash("✅ Driving license record inserted successfully.", "success")
            return redirect(url_for("driving_license.list_records"))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    citizens = _get_citizens()
    return render_template("driving_license/create.html", label=LABEL, table=TABLE, citizens=citizens)


@driving_license_bp.route("/edit/<record_id>", methods=["GET", "POST"])
def edit_record(record_id):
    if request.method == "POST":
        try:
            execute_write(
                "UPDATE driving_license SET issue_date=%s, expiry_date=%s, citizen_id=%s WHERE dl_number=%s",
                (
                    request.form.get("issue_date") or None,
                    request.form.get("expiry_date") or None,
                    request.form["citizen_id"],
                    record_id,
                ),
            )
            flash("✅ Driving license updated successfully.", "success")
            return redirect(url_for("driving_license.view_record", record_id=record_id))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")

    rows, columns, query_time = execute_query(
        f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,)
    )
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("driving_license.list_records"))
    citizens = _get_citizens()
    return render_template(
        "driving_license/edit.html",
        record=rows[0], label=LABEL, table=TABLE, pk=PK, citizens=citizens,
        query_time=query_time,
    )


@driving_license_bp.route("/delete/<record_id>", methods=["POST"])
def delete_record(record_id):
    try:
        execute_write(f"DELETE FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
        flash("✅ Driving license record deleted.", "success")
    except MySQLError as e:
        if e.errno == 1451:
            flash("❌ Cannot delete: referenced by other records.", "error")
        else:
            flash(f"❌ MySQL Error: {e.msg}", "error")
    return redirect(url_for("driving_license.list_records"))
