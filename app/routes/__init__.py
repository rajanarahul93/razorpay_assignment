"""API routes for the books service."""

from flask import Blueprint, request, jsonify
from app.services.catalog import Catalog
from app.utils.errors import ValidationError, NotFoundError, APIError
from flask import current_app

books_bp = Blueprint("books", __name__, url_prefix="/api/v1")


def get_pagination_params():
    """Extract and validate pagination parameters from request."""
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", current_app.config["DEFAULT_PAGE_SIZE"]))
    except ValueError:
        raise ValidationError("page and page_size must be integers")

    # Clamp page to minimum 1
    if page < 1:
        page = 1

    # Validate and clamp page_size
    if page_size < 1 or page_size > current_app.config["MAX_PAGE_SIZE"]:
        raise ValidationError(f"page_size must be between 1 and {current_app.config['MAX_PAGE_SIZE']}")

    return page, page_size


def paginated_response(items, total_count, page, page_size):
    """Format a paginated response."""
    total_pages = (total_count + page_size - 1) // page_size
    return {
        "data": [item.to_dict() if hasattr(item, "to_dict") else item for item in items],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": total_pages,
        },
    }


@books_bp.route("/books", methods=["GET"])
def list_books():
    """List books from the catalog with optional filtering and pagination."""
    try:
        page, page_size = get_pagination_params()
    except APIError:
        raise

    try:
        category = request.args.get("category")
        search = request.args.get("search")

        catalog = Catalog()

        if search:
            books, total = catalog.search_books(search, page, page_size)
        elif category:
            books, total = catalog.get_books_by_category(category, page, page_size)
        else:
            books, total = catalog.get_books_page(page, page_size)

        return jsonify(paginated_response(books, total, page, page_size))
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Failed to fetch books: {str(e)}", 500)


@books_bp.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    """Get detailed information about a specific book."""
    try:
        catalog = Catalog()
        book = catalog.get_book_detail(book_id)
        return jsonify({"data": book.to_dict()})
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Failed to fetch book: {str(e)}", 500)


@books_bp.route("/categories", methods=["GET"])
def list_categories():
    """List all available book categories."""
    try:
        catalog = Catalog()
        categories = catalog.get_all_categories()
        return jsonify({
            "data": [{"name": cat} for cat in categories],
            "total": len(categories),
        })
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Failed to fetch categories: {str(e)}", 500)


@books_bp.route("/categories/<category_name>/books", methods=["GET"])
def get_category_books(category_name):
    """Get books in a specific category."""
    try:
        page, page_size = get_pagination_params()
    except APIError:
        raise

    try:
        catalog = Catalog()
        books, total = catalog.get_books_by_category(category_name, page, page_size)
        return jsonify(paginated_response(books, total, page, page_size))
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Failed to fetch category books: {str(e)}", 500)


@books_bp.route("/search", methods=["GET"])
def search():
    """Search for books by title."""
    query = request.args.get("q", "").strip()
    if not query:
        raise ValidationError("Search query 'q' is required and cannot be empty")

    try:
        page, page_size = get_pagination_params()
    except APIError:
        raise

    try:
        catalog = Catalog()
        books, total = catalog.search_books(query, page, page_size)
        return jsonify(paginated_response(books, total, page, page_size))
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Failed to search books: {str(e)}", 500)
