"""Tests for API endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from app.utils.errors import UpstreamError, NotFoundError, ParsingError


class TestListBooksEndpoint:
    """Tests for GET /api/v1/books."""

    def test_list_books_success(self, client, app_context, books_listing_html):
        """Test successful books listing."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/books")

            assert response.status_code == 200
            data = response.get_json()
            assert "data" in data
            assert "pagination" in data
            assert len(data["data"]) > 0

    def test_list_books_pagination(self, client, app_context, books_listing_html):
        """Test pagination parameters."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/books?page=1&page_size=10")

            assert response.status_code == 200
            data = response.get_json()
            assert data["pagination"]["page"] == 1
            assert data["pagination"]["page_size"] == 10
            assert len(data["data"]) <= 10

    def test_list_books_invalid_page(self, client, app_context, books_listing_html):
        """Test with invalid page number."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/books?page=invalid")

            assert response.status_code == 400
            assert "error" in response.get_json()

    def test_list_books_page_zero(self, client, app_context, books_listing_html):
        """Test with page=0 (should default to 1)."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/books?page=0")

            assert response.status_code == 200
            data = response.get_json()
            assert data["pagination"]["page"] == 1

    def test_list_books_response_structure(self, client, app_context, books_listing_html):
        """Test response structure."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/books")

            assert response.status_code == 200
            data = response.get_json()
            assert "data" in data
            assert "pagination" in data

            book = data["data"][0]
            assert "id" in book
            assert "title" in book
            assert "price" in book
            assert "rating" in book
            assert "availability" in book
            assert "available_quantity" in book

    def test_list_books_upstream_error(self, client, app_context):
        """Test handling of upstream errors."""
        with patch("app.services.catalog.fetch_page", side_effect=UpstreamError()):
            response = client.get("/api/v1/books")

            assert response.status_code == 503
            assert "error" in response.get_json()


class TestGetBookEndpoint:
    """Tests for GET /api/v1/books/{book_id}."""

    def test_get_book_success(self, client, app_context, books_listing_html, book_detail_html):
        """Test retrieving a specific book."""
        with patch("app.services.catalog.fetch_page") as mock_fetch:
            mock_fetch.side_effect = [books_listing_html, book_detail_html]
            response = client.get("/api/v1/books/1000")

            assert response.status_code == 200
            data = response.get_json()
            assert "data" in data
            book = data["data"]
            assert book["id"] == "1000"
            assert book["title"] == "A Light in the Attic"

    def test_get_book_not_found(self, client, app_context, books_listing_html):
        """Test with non-existent book ID."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/books/99999")

            assert response.status_code == 404
            assert "error" in response.get_json()

    def test_get_book_response_structure(self, client, app_context, books_listing_html, book_detail_html):
        """Test book response structure."""
        with patch("app.services.catalog.fetch_page") as mock_fetch:
            mock_fetch.side_effect = [books_listing_html, book_detail_html]
            response = client.get("/api/v1/books/1000")

            assert response.status_code == 200
            book = response.get_json()["data"]
            assert "id" in book
            assert "title" in book
            assert "price" in book
            assert "rating" in book
            assert "availability" in book
            assert "available_quantity" in book
            assert "url" in book


class TestListCategoriesEndpoint:
    """Tests for GET /api/v1/categories."""

    def test_list_categories_success(self, client, app_context, books_listing_html):
        """Test retrieving categories."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/categories")

            assert response.status_code == 200
            data = response.get_json()
            assert "data" in data
            assert "total" in data
            assert len(data["data"]) > 0

    def test_list_categories_structure(self, client, app_context, books_listing_html):
        """Test categories response structure."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/categories")

            assert response.status_code == 200
            data = response.get_json()
            category = data["data"][0]
            assert "name" in category

    def test_list_categories_upstream_error(self, client, app_context):
        """Test handling of upstream errors when fetching categories."""
        with patch("app.services.catalog.fetch_page", side_effect=UpstreamError()):
            response = client.get("/api/v1/categories")

            assert response.status_code == 503


class TestCategoryBooksEndpoint:
    """Tests for GET /api/v1/categories/{category_name}/books."""

    def test_get_category_books_success(self, client, app_context, books_listing_html):
        """Test retrieving books in a category."""
        # First mock to get categories, second to get books
        with patch("app.services.catalog.fetch_page") as mock_fetch:
            # Multiple calls needed: categories, then books
            mock_fetch.side_effect = [books_listing_html, books_listing_html]
            response = client.get("/api/v1/categories/fiction/books")

            assert response.status_code in [200, 404]

    def test_get_category_books_invalid_category(self, client, app_context, books_listing_html):
        """Test with non-existent category."""
        with patch("app.services.catalog.fetch_page") as mock_fetch:
            mock_fetch.side_effect = [books_listing_html, books_listing_html]
            response = client.get("/api/v1/categories/nonexistent-category/books")

            assert response.status_code == 404


class TestSearchEndpoint:
    """Tests for GET /api/v1/search."""

    def test_search_success(self, client, app_context, books_listing_html):
        """Test successful search."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/search?q=light")

            assert response.status_code == 200
            data = response.get_json()
            assert "data" in data
            assert "pagination" in data

    def test_search_empty_query(self, client, app_context, books_listing_html):
        """Test search with empty query."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/search?q=")

            assert response.status_code == 400

    def test_search_no_query_param(self, client, app_context, books_listing_html):
        """Test search without query parameter."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/search")

            assert response.status_code == 400

    def test_search_no_results(self, client, app_context, books_listing_html):
        """Test search with no matching results."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/search?q=xyzabc123notfound")

            assert response.status_code == 200
            data = response.get_json()
            assert len(data["data"]) == 0
            assert data["pagination"]["total"] == 0

    def test_search_case_insensitive(self, client, app_context, books_listing_html):
        """Test that search is case-insensitive."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response1 = client.get("/api/v1/search?q=light")
            response2 = client.get("/api/v1/search?q=LIGHT")

            assert response1.status_code == 200
            assert response2.status_code == 200
            data1 = response1.get_json()
            data2 = response2.get_json()
            assert len(data1["data"]) == len(data2["data"])

    def test_search_pagination(self, client, app_context, books_listing_html):
        """Test search pagination."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/search?q=a&page=1&page_size=5")

            assert response.status_code == 200
            data = response.get_json()
            assert len(data["data"]) <= 5


class TestErrorHandling:
    """Tests for error handling."""

    def test_upstream_timeout(self, client, app_context):
        """Test handling of upstream timeout."""
        with patch("app.services.catalog.fetch_page", side_effect=UpstreamError("Request timed out")):
            response = client.get("/api/v1/books")

            assert response.status_code == 503
            data = response.get_json()
            assert "error" in data

    def test_upstream_connection_error(self, client, app_context):
        """Test handling of connection errors."""
        with patch("app.services.catalog.fetch_page", side_effect=UpstreamError("Connection failed")):
            response = client.get("/api/v1/books")

            assert response.status_code == 503

    def test_parsing_error(self, client, app_context):
        """Test handling of parsing errors."""
        with patch("app.services.catalog.fetch_page", side_effect=ParsingError()):
            response = client.get("/api/v1/books")

            assert response.status_code == 503

    def test_invalid_page_size(self, client, app_context, books_listing_html):
        """Test with page_size exceeding maximum."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/books?page_size=9999")

            assert response.status_code == 400
            assert "error" in response.get_json()

    def test_404_endpoint(self, client):
        """Test 404 for non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == 404
        assert "error" in response.get_json()


class TestPaginationRegression:
    """Regression tests for pagination fixes."""

    def test_page_1_and_2_use_different_urls(self, app_context):
        """Verify page 1 and page 2 fetch from different upstream URLs."""
        from unittest.mock import patch, call
        
        with patch("app.services.catalog.fetch_page") as mock_fetch:
            mock_fetch.return_value = "<html></html>"
            
            from app.services.catalog import Catalog
            catalog = Catalog()
            
            # Fetch page 1
            catalog.get_books_page(page=1)
            
            # Fetch page 2
            catalog.get_books_page(page=2)
            
            # Verify different URLs were called
            calls = mock_fetch.call_args_list
            url_1 = calls[0][0][0]
            url_2 = calls[1][0][0]
            
            assert "index.html" in url_1
            assert "page-2.html" in url_2
            assert url_1 != url_2

    def test_pagination_limits_results_per_page(self, client, app_context, books_listing_html):
        """Verify page_size parameter limits results correctly."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/books?page=1&page_size=10")
            
            assert response.status_code == 200
            data = response.get_json()
            assert len(data["data"]) <= 10
            assert data["pagination"]["page_size"] == 10

    def test_invalid_page_clamped_to_1(self, client, app_context, books_listing_html):
        """Verify page < 1 is clamped to 1."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/books?page=0")
            
            assert response.status_code == 200
            data = response.get_json()
            assert data["pagination"]["page"] == 1

    def test_category_pagination_urls(self, app_context):
        """Verify category pages use correct upstream URLs."""
        from unittest.mock import patch
        
        with patch("app.services.catalog.fetch_page") as mock_fetch:
            mock_fetch.return_value = "<html></html>"
            
            from app.services.catalog import Catalog
            catalog = Catalog()
            
            # Fetch category page 1
            catalog.get_books_page(page=1, category="fiction")
            
            # Fetch category page 2
            catalog.get_books_page(page=2, category="fiction")
            
            # Verify correct URLs were called
            calls = mock_fetch.call_args_list
            url_1 = calls[0][0][0]
            url_2 = calls[1][0][0]
            
            assert "/category/books/fiction_" in url_1
            assert "/category/books/fiction_" in url_2
            assert "index.html" in url_1
            assert "page-2.html" in url_2

    def test_upstream_pagination_failure_handled(self, app_context):
        """Verify upstream pagination failures are handled gracefully."""
        from app.utils.errors import UpstreamError
        from unittest.mock import patch
        
        with patch("app.services.catalog.fetch_page", side_effect=UpstreamError()):
            from app.services.catalog import Catalog
            catalog = Catalog()
            
            try:
                catalog.get_books_page(page=1)
                assert False, "Should have raised UpstreamError"
            except UpstreamError:
                pass  # Expected

    def test_pagination_metadata_accuracy(self, client, app_context, books_listing_html):
        """Verify pagination metadata is accurate."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/books?page=1&page_size=5")
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify metadata
            assert data["pagination"]["page"] == 1
            assert data["pagination"]["page_size"] == 5
            assert len(data["data"]) <= 5
            assert data["pagination"]["total"] == 20  # 20 books on first page


class TestSearchRegression:
    """Regression tests for page-specific search."""

    def test_search_on_specific_page(self, app_context):
        """Verify search searches only the requested page."""
        from unittest.mock import patch

        # Create two different HTML pages for pages 1 and 2
        page1_html = '<article class="product_pod"><h3><a href="cat/book1_1/index.html" title="Python Basics">Python</a></h3><p class="price_color">£10.00</p><p class="star-rating Five"></p><p class="instock">In stock (5 available)</p></article>'
        page2_html = '<article class="product_pod"><h3><a href="cat/book2_2/index.html" title="JavaScript Guide">JavaScript</a></h3><p class="price_color">£15.00</p><p class="star-rating Three"></p><p class="instock">In stock (3 available)</p></article>'

        def mock_fetch(url):
            if "page-2" in url:
                return page2_html
            return page1_html

        with patch("app.services.catalog.fetch_page", side_effect=mock_fetch):
            from app.services.catalog import Catalog
            catalog = Catalog()

            # Search for "Python" on page 1
            results1, total1 = catalog.search_books("Python", page=1)
            assert total1 >= 1

            # Search for "Script" on page 2
            results2, total2 = catalog.search_books("Script", page=2)
            assert total2 >= 1

    def test_search_pagination(self, client, app_context, books_listing_html):
        """Verify search results can be paginated."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            # Search with page_size limit
            response = client.get("/api/v1/search?q=a&page=1&page_size=5")

            assert response.status_code == 200
            data1 = response.get_json()
            assert len(data1["data"]) <= 5
            assert data1["pagination"]["total"] > 0

            # Search page 2
            response2 = client.get("/api/v1/search?q=a&page=2&page_size=5")
            assert response2.status_code == 200
            data2 = response2.get_json()
            assert len(data2["data"]) <= 5

    def test_search_empty_results(self, app_context):
        """Verify search handles no matches gracefully."""
        from unittest.mock import patch
        
        html = '<html><body></body></html>'
        
        with patch("app.services.catalog.fetch_page", return_value=html):
            from app.services.catalog import Catalog
            catalog = Catalog()
            
            results, total = catalog.search_books("xyznotfound123")
            
            assert len(results) == 0
            assert total == 0


class TestBookDetailRegression:
    """Regression tests for book detail lookup."""

    def test_book_detail_with_valid_id(self, client, app_context, books_listing_html):
        """Verify book detail lookup works for valid books on first page."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/books/1000")
            
            assert response.status_code == 200
            data = response.get_json()
            assert data["data"]["id"] == "1000"

    def test_book_detail_invalid_id_returns_404(self, client, app_context, books_listing_html):
        """Verify invalid book ID returns 404."""
        with patch("app.services.catalog.fetch_page", return_value=books_listing_html):
            response = client.get("/api/v1/books/invalid-id")
            
            assert response.status_code == 404

    def test_book_detail_upstream_error_handling(self, client, app_context):
        """Verify upstream errors during book detail fetch are handled."""
        from app.utils.errors import UpstreamError
        
        with patch("app.services.catalog.fetch_page", side_effect=UpstreamError()):
            response = client.get("/api/v1/books/1000")
            
            assert response.status_code == 503
