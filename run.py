"""Application entry point."""

from app import create_app
from app.utils.errors import register_error_handlers

app = create_app()
register_error_handlers(app)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
