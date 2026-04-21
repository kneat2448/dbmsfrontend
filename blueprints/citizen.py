"""Blueprint for the citizen table."""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from db import execute_query, execute_write
from mysql.connector import Error as MySQLError

citizen_bp = Blueprint("citizen", __name__, url_prefix="/citizen")

TABLE = "citizen"
PK = "citizen_id"
COLUMNS = ["citizen_id", "name", "date_of_birth", "email"]
LABEL = "Citizens"


@citizen_bp.route("/")
def list_records():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    search_col = request.args.get("search_col", "name")
    per_page = 10
    offset = (page - 1) * per_page

    # Count
    if search:
        count_q = f"SELECT COUNT(*) AS cnt FROM `{TABLE}` WHERE `{search_col}` LIKE %s"
        rows, _, _ = execute_query(count_q, (f"%{search}%",))
    else:
        count_q = f"SELECT COUNT(*) AS cnt FROM `{TABLE}`"
        rows, _, _ = execute_query(count_q)
    total = rows[0]["cnt"]
    total_pages = max(1, -(-total // per_page))

    # Data
    if search:
        data_q = f"SELECT * FROM `{TABLE}` WHERE `{search_col}` LIKE %s ORDER BY `{PK}` LIMIT %s OFFSET %s"
        data, columns, query_time = execute_query(data_q, (f"%{search}%", per_page, offset))
    else:
        data_q = f"SELECT * FROM `{TABLE}` ORDER BY `{PK}` LIMIT %s OFFSET %s"
        data, columns, query_time = execute_query(data_q, (per_page, offset))

    return render_template(
        "citizen/list.html",
        rows=data, columns=columns, page=page, total_pages=total_pages,
        total=total, search=search, search_col=search_col,
        all_columns=COLUMNS, label=LABEL, table=TABLE, pk=PK,
        query_time=query_time,
    )


@citizen_bp.route("/<int:record_id>")
def view_record(record_id):
    rows, columns, query_time = execute_query(
        f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,)
    )
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("citizen.list_records"))
    return render_template(
        "citizen/view.html",
        record=rows[0], columns=columns, label=LABEL, table=TABLE, pk=PK,
        query_time=query_time,
    )


@citizen_bp.route("/create", methods=["GET", "POST"])
def create_record():
    if request.method == "POST":
        try:
            execute_write(
                "INSERT INTO citizen (citizen_id, name, date_of_birth, email) VALUES (%s, %s, %s, %s)",
                (
                    request.form["citizen_id"],
                    request.form["name"],
                    request.form["date_of_birth"],
                    request.form.get("email") or None,
                ),
            )
            flash("✅ Citizen record inserted successfully.", "success")
            return redirect(url_for("citizen.list_records"))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
    return render_template("citizen/create.html", label=LABEL, table=TABLE)


@citizen_bp.route("/edit/<int:record_id>", methods=["GET", "POST"])
def edit_record(record_id):
    if request.method == "POST":
        try:
            execute_write(
                "UPDATE citizen SET name=%s, date_of_birth=%s, email=%s WHERE citizen_id=%s",
                (
                    request.form["name"],
                    request.form["date_of_birth"],
                    request.form.get("email") or None,
                    record_id,
                ),
            )
            flash("✅ Citizen record updated successfully.", "success")
            return redirect(url_for("citizen.view_record", record_id=record_id))
        except MySQLError as e:
            flash(f"❌ MySQL Error: {e.msg}", "error")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")

    rows, columns, query_time = execute_query(
        f"SELECT * FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,)
    )
    if not rows:
        flash("Record not found.", "error")
        return redirect(url_for("citizen.list_records"))
    return render_template(
        "citizen/edit.html",
        record=rows[0], label=LABEL, table=TABLE, pk=PK,
        query_time=query_time,
    )


@citizen_bp.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    try:
        execute_write(f"DELETE FROM `{TABLE}` WHERE `{PK}` = %s", (record_id,))
        flash("✅ Citizen record deleted successfully.", "success")
    except MySQLError as e:
        if e.errno == 1451:
            flash("❌ Cannot delete: this citizen is referenced by other records (foreign key constraint).", "error")
        else:
            flash(f"❌ MySQL Error: {e.msg}", "error")
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "error")
    return redirect(url_for("citizen.list_records"))
