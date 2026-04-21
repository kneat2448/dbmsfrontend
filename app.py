"""
Flask DBMS Frontend – Transport Office
Main application entry point.
Registers all 9 table blueprints.
"""

from flask import Flask, render_template, request
from config import Config
import db as database
from db import execute_query

# Blueprint imports
from blueprints.citizen import citizen_bp
from blueprints.driving_license import driving_license_bp
from blueprints.vehicles import vehicles_bp
from blueprints.vehicle_registrations import vehicle_registrations_bp
from blueprints.violations import violations_bp
from blueprints.tax import tax_bp
from blueprints.payment_info import payment_info_bp
from blueprints.liability import liability_bp
from blueprints.paid_using import paid_using_bp


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=Config.SECRET_KEY,
        MYSQL_HOST=Config.MYSQL_HOST,
        MYSQL_PORT=Config.MYSQL_PORT,
        MYSQL_USER=Config.MYSQL_USER,
        MYSQL_PASSWORD=Config.MYSQL_PASSWORD,
        MYSQL_DATABASE=Config.MYSQL_DATABASE,
    )

    # Register DB teardown
    database.init_app(app)

    # Register blueprints
    app.register_blueprint(citizen_bp)
    app.register_blueprint(driving_license_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(vehicle_registrations_bp)
    app.register_blueprint(violations_bp)
    app.register_blueprint(tax_bp)
    app.register_blueprint(payment_info_bp)
    app.register_blueprint(liability_bp)
    app.register_blueprint(paid_using_bp)

    # ── Index / Dashboard ──────────────────────────────────
    @app.route("/")
    def index():
        tables = [
            "citizen",
            "driving_license",
            "vehicles",
            "vehicle_registrations",
            "violations",
            "tax",
            "payment_info",
            "liability",
            "paid_using",
        ]
        stats = []
        total_time = 0
        for t in tables:
            rows, _, elapsed = execute_query(f"SELECT COUNT(*) AS cnt FROM `{t}`")
            stats.append({"table": t, "count": rows[0]["cnt"]})
            total_time += elapsed
        return render_template(
            "index.html", stats=stats, query_time=round(total_time, 2)
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
