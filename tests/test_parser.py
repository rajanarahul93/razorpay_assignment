"""Tests for HTML parsing and data extraction."""

import pytest
from app.services.scraper import (
    extract_book_id,
    extract_rating_value,
    extract_price,
    extract_availability_quantity,
)
from app.services.catalog import Catalog


class TestBookIDExtraction:
    """Tests for book ID extraction."""

    def test_extract_valid_book_id(self):
        """Test extracting ID from a valid book URL."""
        url = "/catalogue/a-light-in-the-attic_1000/index.html"
        assert extract_book_id(url) == "1000"

    def test_extract_id_with_dashes(self):
        """Test extracting ID from URL with dashes in title."""
        url = "/catalogue/the-third-world-war_123/index.html"
        assert extract_book_id(url) == "123"

    def test_extract_id_invalid_url(self):
        """Test with malformed URL."""
        assert extract_book_id("invalid") is None

    def test_extract_id_empty(self):
        """Test with empty string."""
        assert extract_book_id("") is None


class TestRatingExtraction:
    """Tests for rating extraction."""

    def test_extract_rating_one(self):
        """Test extracting One star rating."""
        classes = ["star-rating", "One"]
        assert extract_rating_value(" ".join(classes)) == 1

    def test_extract_rating_five(self):
        """Test extracting Five star rating."""
        classes = ["star-rating", "Five"]
        assert extract_rating_value(" ".join(classes)) == 5

    def test_extract_rating_invalid(self):
        """Test with invalid rating class."""
        assert extract_rating_value("star-rating invalid") == 0

    def test_extract_rating_three(self):
        """Test extracting Three star rating."""
        classes = ["star-rating", "Three"]
        assert extract_rating_value(" ".join(classes)) == 3


class TestPriceExtraction:
    """Tests for price extraction."""

    def test_extract_valid_price(self):
        """Test extracting price with currency symbol."""
        assert extract_price("£51.77") == 51.77

    def test_extract_price_large(self):
        """Test extracting large price."""
        assert extract_price("£123.45") == 123.45

    def test_extract_price_no_decimals(self):
        """Test extracting whole number price."""
        assert extract_price("£10.00") == 10.0

    def test_extract_price_invalid(self):
        """Test with invalid price string."""
        assert extract_price("invalid") is None

    def test_extract_price_empty(self):
        """Test with empty string."""
        assert extract_price("") is None


class TestAvailabilityExtraction:
    """Tests for availability extraction."""

    def test_extract_availability_with_quantity(self):
        """Test extracting quantity from availability text."""
        text = "In stock (22 available)"
        assert extract_availability_quantity(text) == 22

    def test_extract_availability_one_item(self):
        """Test extracting single item availability."""
        text = "In stock (1 available)"
        assert extract_availability_quantity(text) == 1

    def test_extract_availability_large_quantity(self):
        """Test extracting large quantity."""
        text = "In stock (999 available)"
        assert extract_availability_quantity(text) == 999

    def test_extract_availability_no_quantity(self):
        """Test with text without quantity."""
        text = "In stock"
        assert extract_availability_quantity(text) == 0

    def test_extract_availability_invalid(self):
        """Test with malformed availability text."""
        assert extract_availability_quantity("Out of stock") == 0


class TestBookListingParsing:
    """Tests for parsing book listings."""

    def test_parse_valid_listing(self, app_context, books_listing_html):
        """Test parsing a valid books listing page."""
        catalog = Catalog()
        books = catalog.parse_book_listing(books_listing_html)

        assert len(books) > 0
        assert all(hasattr(b, "id") for b in books)
        assert all(hasattr(b, "title") for b in books)
        assert all(hasattr(b, "price") for b in books)
        assert all(hasattr(b, "rating") for b in books)

    def test_parse_listing_has_titles(self, app_context, books_listing_html):
        """Test that parsed books have non-empty titles."""
        catalog = Catalog()
        books = catalog.parse_book_listing(books_listing_html)

        assert all(b.title and len(b.title) > 0 for b in books)

    def test_parse_listing_has_prices(self, app_context, books_listing_html):
        """Test that parsed books have valid prices."""
        catalog = Catalog()
        books = catalog.parse_book_listing(books_listing_html)

        assert all(b.price is not None and b.price > 0 for b in books)

    def test_parse_listing_has_ratings(self, app_context, books_listing_html):
        """Test that parsed books have ratings."""
        catalog = Catalog()
        books = catalog.parse_book_listing(books_listing_html)

        assert all(0 <= b.rating <= 5 for b in books)

    def test_parse_listing_first_book(self, app_context, books_listing_html):
        """Test details of first book in listing."""
        catalog = Catalog()
        books = catalog.parse_book_listing(books_listing_html)

        first = books[0]
        assert first.title == "A Light in the Attic"
        assert first.price == 51.77
        assert first.rating == 3
        assert first.id == "1000"

    def test_parse_listing_with_category(self, app_context, books_listing_html):
        """Test parsing with category context."""
        catalog = Catalog()
        books = catalog.parse_book_listing(books_listing_html, category="fiction")

        assert all(b.category == "fiction" for b in books)

    def test_parse_malformed_html(self, app_context):
        """Test parsing with malformed HTML."""
        catalog = Catalog()
        html = "<html><body><invalid></invalid></body></html>"
        books = catalog.parse_book_listing(html)

        assert books == []

    def test_parse_empty_html(self, app_context):
        """Test parsing empty HTML."""
        catalog = Catalog()
        books = catalog.parse_book_listing("")

        assert books == []


class TestBookDetailParsing:
    """Tests for parsing book detail pages."""

    def test_detail_page_has_required_fields(self, app_context, book_detail_html):
        """Test that detail page contains expected elements."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(book_detail_html, "html.parser")

        assert soup.find("h1") is not None
        assert soup.find("p", class_="price_color") is not None
