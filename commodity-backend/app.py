import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from models import db
from routes.admin import bp as admin_bp
from routes.alert_routes import bp as alert_bp
from routes.auth import bp as auth_bp
from routes.dashboard import bp as dashboard_bp
from routes.detail import bp as detail_bp
from routes.user import bp as user_bp
from services.scheduler_service import init_scheduler, should_start_scheduler
from services.schema_migrate_service import ensure_schema
from seed import seed_if_empty


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}}, supports_credentials=True)

    db.init_app(app)
    jwt = JWTManager(app)

    # Make JWT errors return JSON (to match frontend `request.ts`).
    from utils.response import err

    @jwt.unauthorized_loader
    def unauthorized_loader_callback(_err_string):
        return err("未登录或token无效", code=401, http_status=401)

    @jwt.invalid_token_loader
    def invalid_token_loader_callback(_err_string):
        return err("token无效", code=401, http_status=401)

    @jwt.needs_fresh_token_loader
    def needs_fresh_token_loader_callback(_err_string):
        return err("token需要刷新", code=401, http_status=401)

    api_prefix = "/api"
    app.register_blueprint(auth_bp, url_prefix=api_prefix + "/auth")
    app.register_blueprint(user_bp, url_prefix=api_prefix + "/user")
    app.register_blueprint(admin_bp, url_prefix=api_prefix + "/admin")
    app.register_blueprint(dashboard_bp, url_prefix=api_prefix + "/dashboard")
    app.register_blueprint(detail_bp, url_prefix=api_prefix + "/detail")
    app.register_blueprint(alert_bp, url_prefix=api_prefix + "/alert")
    # app.register_blueprint(auth_bp, url_prefix=api_prefix)
    # app.register_blueprint(user_bp, url_prefix=api_prefix)
    # app.register_blueprint(admin_bp, url_prefix=api_prefix)
    # app.register_blueprint(dashboard_bp, url_prefix=api_prefix)
    # app.register_blueprint(detail_bp, url_prefix=api_prefix)
    # app.register_blueprint(alert_bp, url_prefix=api_prefix)

    with app.app_context():
        db.create_all()
        ensure_schema()
        seed_if_empty()
        if should_start_scheduler(app):
            init_scheduler(app)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
    print("\n===== ROUTES =====")
    for rule in app.url_map.iter_rules():
        print(rule)
