from flask import Flask
from app.config import Config
from app.utils.errors import register_error_handlers


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    from app.routes import books_bp
    app.register_blueprint(books_bp)

    register_error_handlers(app)

    return app
