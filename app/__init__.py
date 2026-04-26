import os

from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()


def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://postgres:password@localhost:5432/task_manager"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes.categories import categories_bp
    from app.routes.tasks import tasks_bp

    app.register_blueprint(tasks_bp)
    app.register_blueprint(categories_bp)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}, 200

    @app.errorhandler(404)
    def handle_404(_):
        return jsonify({"error": "Not found"}), 404

    return app
