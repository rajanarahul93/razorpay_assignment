from flask import jsonify


class APIError(Exception):
    """Base class for API errors."""

    def __init__(self, message, status_code=500):
        super().__init__()
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {"error": self.message}


class UpstreamError(APIError):
    """Raised when the upstream website is unavailable or returns an error."""

    def __init__(self, message="Unable to fetch data from the upstream website"):
        super().__init__(message, 503)


class ValidationError(APIError):
    """Raised when input validation fails."""

    def __init__(self, message):
        super().__init__(message, 400)


class NotFoundError(APIError):
    """Raised when a resource is not found."""

    def __init__(self, message="Resource not found"):
        super().__init__(message, 404)


class ParsingError(APIError):
    """Raised when HTML parsing fails."""

    def __init__(self, message="Failed to parse upstream data"):
        super().__init__(message, 503)


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        return jsonify({"error": "Internal server error"}), 500
