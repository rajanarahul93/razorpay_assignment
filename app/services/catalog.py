"""Business logic for books catalog."""

from typing import Dict, List, Optional, Tuple
from flask import current_app
from app.services.scraper import (
    fetch_page,
    parse_html,
    extract_book_id,
    extract_rating_value,
    extract_price,
    extract_availability_quantity,
)
from app.utils.errors import NotFoundError, ParsingError


class Book:
    """Represents a book from the catalog."""

    def __init__(
        self,
        book_id: str,
        title: str,
        price: float,
        rating: int,
        availability: str,
        available_quantity: int,
        category: Optional[str] = None,
        url: Optional[str] = None,
    ):
        self.id = book_id
        self.title = title
        self.price = price
        self.rating = rating
        self.availability = availability
        self.available_quantity = available_quantity
        self.category = category
        self.url = url

    def to_dict(self) -> Dict:
        """Convert book to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "price": self.price,
            "rating": self.rating,
            "availability": self.availability,
            "available_quantity": self.available_quantity,
            "category": self.category,
            "url": self.url,
        }


class Catalog:
    """Handles fetching and parsing books from the catalog."""

    def __init__(self):
        self.base_url = current_app.config["BOOKS_BASE_URL"]
        self._categories_cache = None

    def get_all_categories(self) -> List[str]:
        """
        Fetch and parse all available categories.

        Returns:
            List of category names (slugified).
        """
        if self._categories_cache is not None:
            return self._categories_cache

        html = fetch_page(f"{self.base_url}/index.html")
        soup = parse_html(html)

        categories = []
        # Find all category links in the sidebar
        for link in soup.find_all("a", href=True):
            href = link["href"]
            # Category links are in format: catalogue/category/books/category-name_XX/index.html
            if "/category/" in href and "/books/" in href:
                parts = href.split("/")
                for part in parts:
                    if "_" in part and part[0] != "_":
                        # Extract category name (before the number)
                        category_slug = part.rsplit("_", 1)[0]
                        if category_slug and category_slug not in ["books"]:
                            categories.append(category_slug)
                            break

        # Remove duplicates while preserving order
        seen = set()
        unique_categories = []
        for cat in categories:
            if cat not in seen:
                seen.add(cat)
                unique_categories.append(cat)

        self._categories_cache = unique_categories
        return unique_categories

    def parse_book_listing(self, html: str, category: Optional[str] = None) -> List[Book]:
        """
        Parse a books listing page.

        Args:
            html: The HTML content of the page.
            category: Optional category name for context.

        Returns:
            List of Book objects.

        Raises:
            ParsingError: If parsing fails.
        """
        try:
            soup = parse_html(html)
            books = []

            for article in soup.find_all("article", class_="product_pod"):
                try:
                    # Extract title and URL
                    title_elem = article.find("h3").find("a")
                    if not title_elem:
                        continue

                    title = title_elem.get("title", "").strip()
                    book_url = title_elem.get("href", "")

                    # Extract book ID from URL
                    book_id = extract_book_id(book_url)
                    if not book_id:
                        continue

                    # Build full URL
                    if book_url and not book_url.startswith("http"):
                        book_url = f"{self.base_url}/{book_url}"

                    # Extract price
                    price_elem = article.find("p", class_="price_color")
                    price = extract_price(price_elem.text) if price_elem else None

                    # Extract rating
                    rating_elem = article.find("p", class_="star-rating")
                    rating = (
                        extract_rating_value(rating_elem.get("class", []))
                        if rating_elem
                        else 0
                    )

                    # Extract availability
                    avail_elem = article.find("p", class_="instock")
                    availability = "In stock" if avail_elem else "Out of stock"
                    available_quantity = (
                        extract_availability_quantity(avail_elem.text)
                        if avail_elem
                        else 0
                    )

                    book = Book(
                        book_id=book_id,
                        title=title,
                        price=price,
                        rating=rating,
                        availability=availability,
                        available_quantity=available_quantity,
                        category=category,
                        url=book_url,
                    )
                    books.append(book)
                except (AttributeError, ValueError):
                    continue

            return books
        except Exception as e:
            raise ParsingError(f"Failed to parse book listing: {str(e)}")

    def get_books_page(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Book], int]:
        """
        Fetch a page of books with optional filtering.

        Args:
            page: Page number (1-indexed).
            page_size: Number of books per page.
            category: Optional category filter.
            search: Optional search query.

        Returns:
            Tuple of (list of Book objects, total book count).

        Raises:
            NotFoundError: If category not found.
            UpstreamError: If upstream fetch fails.
        """
        # Validate pagination
        if page < 1:
            page = 1
        if page_size < 1 or page_size > current_app.config["MAX_PAGE_SIZE"]:
            page_size = current_app.config["DEFAULT_PAGE_SIZE"]

        # Build upstream page URL
        if category:
            # Category pages: /catalogue/category/books/category-name_N/index.html (page 1)
            # or /catalogue/category/books/category-name_N/page-X.html (page X)
            if page == 1:
                url = f"{self.base_url}/catalogue/category/books/{category}_/index.html"
            else:
                url = f"{self.base_url}/catalogue/category/books/{category}_/page-{page}.html"
        else:
            # Main pages: /index.html (page 1) or /catalogue/page-X.html (page X)
            if page == 1:
                url = f"{self.base_url}/index.html"
            else:
                url = f"{self.base_url}/catalogue/page-{page}.html"

        # Fetch upstream page
        html = fetch_page(url)
        books_on_page = self.parse_book_listing(html, category)

        # Apply search filter
        if search:
            search_lower = search.lower()
            books_on_page = [b for b in books_on_page if search_lower in b.title.lower()]

        # Apply client-side pagination for the page_size limit
        # This allows limiting results within a single upstream page
        paginated_books = books_on_page[:page_size]
        total_on_page = len(books_on_page)

        return paginated_books, total_on_page

    def get_book_detail(self, book_id: str) -> Book:
        """
        Fetch detailed information about a specific book.

        Args:
            book_id: The book ID.

        Returns:
            Book object with full details.

        Raises:
            NotFoundError: If book not found.
        """
        # Fetch the detail page (we need to search for it since we don't have a direct URL)
        html = fetch_page(f"{self.base_url}/index.html")
        books = self.parse_book_listing(html)

        for book in books:
            if book.id == book_id:
                # Fetch the detail page for additional info
                if book.url:
                    try:
                        detail_html = fetch_page(book.url)
                        detail_soup = parse_html(detail_html)

                        # Extract availability from detail page
                        avail_elem = detail_soup.find("p", class_="instock")
                        if avail_elem:
                            book.availability = "In stock"
                            book.available_quantity = extract_availability_quantity(
                                avail_elem.text
                            )
                        else:
                            book.availability = "Out of stock"
                            book.available_quantity = 0
                    except Exception:
                        pass

                return book

        raise NotFoundError(f"Book with ID '{book_id}' not found")

    def search_books(
        self, query: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Book], int]:
        """
        Search for books by title on a specific catalog page.

        Note: Searches only the requested upstream page, not the entire catalog.
        This keeps response times reasonable while still providing search capability.

        Args:
            query: Search query string.
            page: Upstream page number to search (1-indexed).
            page_size: Results per page.

        Returns:
            Tuple of (results, total count of matches on this page).
        """
        if not query or not query.strip():
            return [], 0

        # Fetch the requested upstream page
        if page == 1:
            url = f"{self.base_url}/index.html"
        else:
            url = f"{self.base_url}/catalogue/page-{page}.html"

        html = fetch_page(url)
        books_on_page = self.parse_book_listing(html)

        # Filter by search query
        query_lower = query.lower()
        matching = [b for b in books_on_page if query_lower in b.title.lower()]

        # Apply pagination for page_size limit
        paginated = matching[:page_size]
        total_matching = len(matching)

        return paginated, total_matching

    def get_books_by_category(
        self, category: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Book], int]:
        """
        Get books in a specific category.

        Args:
            category: Category name (slugified).
            page: Page number.
            page_size: Results per page.

        Returns:
            Tuple of (books, total count).

        Raises:
            NotFoundError: If category not found.
        """
        valid_categories = self.get_all_categories()
        if category not in valid_categories:
            raise NotFoundError(f"Category '{category}' not found")

        return self.get_books_page(page, page_size, category)
