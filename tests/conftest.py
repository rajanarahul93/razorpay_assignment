"""Test configuration and fixtures."""

import os
import pytest
from app import create_app
from app.config import Config


class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    REQUEST_TIMEOUT = 5


@pytest.fixture
def app():
    """Create and configure a test app."""
    app = create_app(TestConfig)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Create an app context for tests."""
    with app.app_context():
        yield app


def load_fixture(filename):
    """Load a fixture file."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def books_listing_html():
    """Load the books listing HTML fixture."""
    return load_fixture("books_listing.html")


@pytest.fixture
def book_detail_html():
    """Load the book detail HTML fixture."""
    return load_fixture("book_detail.html")
