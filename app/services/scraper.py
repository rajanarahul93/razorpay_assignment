"""HTTP requests and HTML parsing for books.toscrape.com."""

import requests
from bs4 import BeautifulSoup
from flask import current_app
from app.utils.errors import UpstreamError, ParsingError


def fetch_page(url: str) -> str:
    """
    Fetch a page from the upstream website.

    Args:
        url: The URL to fetch.

    Returns:
        The HTML content as a string.

    Raises:
        UpstreamError: If the request fails or times out.
    """
    try:
        response = requests.get(
            url,
            timeout=current_app.config["REQUEST_TIMEOUT"],
        )
        response.raise_for_status()
        return response.text
    except requests.exceptions.Timeout:
        raise UpstreamError("Request to upstream website timed out")
    except requests.exceptions.ConnectionError:
        raise UpstreamError("Failed to connect to upstream website")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise UpstreamError("Resource not found on upstream website")
        raise UpstreamError(f"Upstream website returned HTTP {e.response.status_code}")
    except Exception:
        raise UpstreamError("Failed to fetch data from upstream website")


def parse_html(html: str) -> BeautifulSoup:
    """
    Parse HTML content using BeautifulSoup.

    Args:
        html: The HTML content as a string.

    Returns:
        A BeautifulSoup object.
    """
    return BeautifulSoup(html, "html.parser")


def extract_book_id(url: str) -> str:
    """Extract book ID from a book URL."""
    # URL format: /catalogue/book-title_XXXX/index.html
    parts = url.split("/")
    if len(parts) >= 2:
        # Get the second-to-last part (before /index.html)
        filename = parts[-2]
        # Extract the ID (number after the last underscore)
        if "_" in filename:
            return filename.split("_")[-1]
    return None


def extract_rating_value(rating_class: str) -> int:
    """Convert rating class name to numeric value."""
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    for name, value in rating_map.items():
        if name in rating_class:
            return value
    return 0


def extract_price(price_str: str) -> float:
    """Extract numeric price from string like '£51.77'."""
    try:
        return float(price_str.replace("£", "").strip())
    except (ValueError, AttributeError):
        return None


def extract_availability_quantity(availability_text: str) -> int:
    """Extract available quantity from text like 'In stock (22 available)'."""
    try:
        if "(" in availability_text and ")" in availability_text:
            quantity_str = availability_text.split("(")[1].split(")")[0]
            return int(quantity_str.split()[0])
    except (ValueError, IndexError):
        pass
    return 0
