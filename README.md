# Books API

A reverse-engineered REST API for the public book catalog at https://books.toscrape.com/

## Problem Statement

The website books.toscrape.com hosts a publicly accessible book catalog but does not provide a conventional REST API for programmatic access. This project extracts the website's catalog data and exposes it through a clean, well-structured API.

## Why This Website

books.toscrape.com was selected because:

1. It is explicitly designed for scraping practice ("We love being scraped!")
2. It is publicly accessible with no authentication or rate limits
3. It maintains a consistent, predictable HTML structure
4. It represents a real-world scenario (legacy HTML-only catalog)
5. It includes meaningful data: pricing, ratings, availability, categories

## Architecture Overview

The API follows a layered architecture:

- **HTTP Routes** (`app/routes/`): Flask route handlers, input validation, response formatting
- **Services** (`app/services/`):
  - `scraper.py`: HTTP requests, HTML parsing, data extraction
  - `catalog.py`: Business logic, book/category queries, data normalization
- **Utilities** (`app/utils/`): Error handling, API error classes
- **Config** (`app/config.py`): Configuration and constants


## Prerequisites

- Python 3.11 or later
- pip (Python package manager)

## Installation and Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd reverse-engineered-books-api
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## How to Run the Service

### Start the server

```bash
python run.py
```

The API will be available at `http://localhost:5000`

### Verify the service is running

```bash
curl http://localhost:5000/api/v1/books?page_size=1
```

## API Endpoint Documentation

### List Books

**Request:**
```
GET /api/v1/books
```

**Query Parameters:**
- `page` (optional): Page number, default=1
- `page_size` (optional): Results per page, default=20, max=50
- `category` (optional): Filter by category slug
- `search` (optional): Search by title

**Response:**
```json
{
  "data": [
    {
      "id": "1000",
      "title": "A Light in the Attic",
      "price": 51.77,
      "rating": 3,
      "availability": "In stock",
      "available_quantity": 22,
      "category": null,
      "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1000,
    "total_pages": 50
  }
}
```

### Get Book Detail

**Request:**
```
GET /api/v1/books/{book_id}
```

**Response:**
```json
{
  "data": {
    "id": "1000",
    "title": "A Light in the Attic",
    "price": 51.77,
    "rating": 3,
    "availability": "In stock",
    "available_quantity": 22,
    "category": null,
    "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
  }
}
```

**Error (404):**
```json
{
  "error": "Book with ID '99999' not found"
}
```

### List Categories

**Request:**
```
GET /api/v1/categories
```

**Response:**
```json
{
  "data": [
    {"name": "travel"},
    {"name": "mystery"},
    {"name": "historical-fiction"}
  ],
  "total": 20
}
```

### Get Books by Category

**Request:**
```
GET /api/v1/categories/{category_name}/books
```

**Query Parameters:**
- `page` (optional): Page number, default=1
- `page_size` (optional): Results per page, default=20, max=50

**Response:** Same structure as list books

**Error (404):**
```json
{
  "error": "Category 'invalid-category' not found"
}
```

### Search Books

**Request:**
```
GET /api/v1/search?q={query}
```

**Query Parameters:**
- `q` (required): Search term
- `page` (optional): Page number
- `page_size` (optional): Results per page

**Response:** Same structure as list books

**Error (400):**
```json
{
  "error": "Search query 'q' is required and cannot be empty"
}
```

## Example Requests

### Get the first 5 books

```bash
curl 'http://localhost:5000/api/v1/books?page_size=5'
```

### Get a specific book

```bash
curl 'http://localhost:5000/api/v1/books/1000'
```

### List all categories

```bash
curl 'http://localhost:5000/api/v1/categories'
```

### Get books in the "Fiction" category

```bash
curl 'http://localhost:5000/api/v1/categories/fiction/books'
```

### Search for books with "light" in the title

```bash
curl 'http://localhost:5000/api/v1/search?q=light'
```

### Paginate through results

```bash
# Page 1
curl 'http://localhost:5000/api/v1/books?page=1&page_size=10'

# Page 2
curl 'http://localhost:5000/api/v1/books?page=2&page_size=10'
```

## How to Run Tests

### Run all tests

```bash
pytest
```

### Run with verbose output

```bash
pytest -v
```

### Run only parser tests

```bash
pytest tests/test_parser.py -v
```

### Run only API tests

```bash
pytest tests/test_api.py -v
```

### Run with coverage

```bash
pytest --cov=app tests/
```

## How to Run the Smoke Test

The smoke test script exercises the API against a live running server. It is conservative and suitable for manual execution.

### Prerequisites

- The API server must be running (`python run.py`)
- Internet connectivity for the optional live website check

### Run the smoke test

```bash
python scripts/smoke_test.py
```

### Skip the live website check

```bash
python scripts/smoke_test.py --skip-live
```

### Test against a different server

```bash
python scripts/smoke_test.py --url http://example.com:3000
```

## Assumptions

1. The website's HTML structure remains stable
2. Book IDs are derived from URLs and are unique within the catalog
3. Ratings are represented by CSS classes (One, Two, Three, Four, Five)
4. Availability status is indicated by the presence of an "instock" class
5. Prices are denoted in British pounds (£)
6. The website does not enforce strict rate limiting for automated requests
7. The site is publicly accessible without authentication

## Known Limitations

1. **HTML Dependency**: The implementation depends directly on the website's HTML structure. If the website changes its markup, the parser will fail.

2. **No Full Pagination Fetch**: The API fetches only the requested page from the upstream website, not the entire catalog. Each request may hit the live website.

3. **No Persistent Storage**: Data is not cached in a database. Every request to the API may trigger a request to the upstream website.

4. **Limited Data Fields**: Only fields visible on the website (title, price, rating, availability) are available. Fields like ISBN, author, publication date, and description are not extracted.

5. **Single-threaded Parsing**: The parser is not optimized for concurrent requests or high load.

6. **Website Availability**: If books.toscrape.com becomes unavailable, the API cannot serve data.

7. **Search Scope**: Search queries only search the requested catalog page, not the entire catalog. To search across all books, clients must paginate through search results or query multiple pages. This design choice prioritizes response time over complete catalog search.

8. **Category Resolution**: Categories must be discovered from the main listing page, which may not include all possible categories.

## Failure Behavior

### Upstream Website Unavailable

```json
{
  "error": "Unable to fetch data from the upstream website"
}
```
Status: 503 Service Unavailable

### Malformed or Changed HTML

```json
{
  "error": "Failed to parse book listing"
}
```
Status: 503 Service Unavailable

### Request Timeout

```json
{
  "error": "Request to upstream website timed out"
}
```
Status: 503 Service Unavailable

### Connection Error

```json
{
  "error": "Failed to connect to upstream website"
}
```
Status: 503 Service Unavailable

### Invalid Input

```json
{
  "error": "page must be >= 1"
}
```
Status: 400 Bad Request

## Configuration

Default settings are in `app/config.py`:

- `REQUEST_TIMEOUT`: 10 seconds
- `MAX_PAGE_SIZE`: 50 books per page
- `DEFAULT_PAGE_SIZE`: 20 books per page
- `BOOKS_BASE_URL`: https://books.toscrape.com

These can be modified by creating a `TestConfig` class or by setting environment variables in a Flask context.

## Production Readiness

**This implementation is not suitable for production use without significant changes:**

1. **Official API**: The ideal solution is an official, documented API provided by the website owner. This implementation should only be used if no official API exists.

2. **Authorized Integration**: Before deploying to production, obtain explicit authorization from the website owner or establish a formal data partnership.

3. **Rate Limiting**: Implement server-side rate limiting and request queuing to avoid overwhelming the upstream website.

4. **Caching**: Add Redis or similar caching to reduce repeated upstream requests and improve latency.

5. **Database**: Store fetched data in a database (PostgreSQL, MongoDB) to reduce dependency on live upstream availability.

6. **Error Recovery**: Implement retry logic, circuit breakers, and fallback responses for resilience.

7. **Monitoring**: Add logging, metrics, and alerts for upstream failures.

8. **Legal Review**: Ensure compliance with the website's terms of service, robots.txt, and data usage policies.

9. **SLA Guarantees**: Without direct control of the upstream website, you cannot guarantee availability or performance SLAs.

## Deployment Considerations

If this API must be deployed:

1. Run behind a reverse proxy (nginx) with request rate limiting
2. Implement caching at multiple layers (application, HTTP, database)
3. Monitor upstream website health and gracefully degrade
4. Use connection pools to limit concurrent requests
5. Implement comprehensive logging and alerting
6. Document the upstream dependency clearly in API documentation
7. Set realistic timeout and SLA expectations

## Technical Decisions

### Why Requests + BeautifulSoup4

- Lightweight and well-maintained
- No need for a heavyweight framework like Selenium
- Sufficient for stable HTML parsing
- Clear separation of concerns (HTTP vs. parsing)

### Why Flask

- Minimal framework for a simple REST API
- Easy to understand and extend
- No unnecessary abstraction layers
- Suitable for educational and small-scale use

### Why Mock External Requests in Tests

- Tests don't depend on internet connectivity
- Faster test execution
- Deterministic behavior (no flaky tests)
- Uses actual HTML fixtures from the website

### No Database

- Unnecessary for a simple reverse-engineered API
- Reduces deployment complexity
- Keeps the implementation lightweight
- Appropriate for the scope of this project

### Client-Side Search/Filtering

- Simple and transparent
- No need for server-side indexing
- Straightforward to understand and modify
- Acceptable given the catalog size (~1000 books)

## Contributing

This is a take-home assignment for Razorpay. Contributions are not expected. If you find issues, document them clearly.

## License

This project is provided as-is for evaluation purposes. See the appropriate license file if included.

## Contact

For questions about this implementation, refer to the assignment brief or contact the author.
