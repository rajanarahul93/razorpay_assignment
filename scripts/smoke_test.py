#!/usr/bin/env python3
"""
Smoke test for the books API.

This script tests the API against a live running server.
It is conservative and suitable for manual execution.

Usage:
    python scripts/smoke_test.py [--skip-live]

    --skip-live: Skip testing against the real books.toscrape.com website
"""

import sys
import time
import requests
import argparse


def test_endpoint(base_url, method, endpoint, **kwargs):
    """Test an API endpoint."""
    url = f"{base_url}{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10, **kwargs)
        else:
            response = requests.post(url, timeout=10, **kwargs)

        return response.status_code, response.json() if response.text else None
    except requests.exceptions.RequestException as e:
        return None, str(e)


def run_smoke_tests(base_url="http://localhost:5000", skip_live=False):
    """Run smoke tests against the API."""
    print("=" * 60)
    print("Books API Smoke Test")
    print("=" * 60)
    print(f"Testing against: {base_url}")
    print()

    # Wait for server to be ready
    max_retries = 10
    for attempt in range(max_retries):
        try:
            requests.get(f"{base_url}/api/v1/books", timeout=2)
            break
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                print(f"Waiting for server... ({attempt + 1}/{max_retries})")
                time.sleep(1)
            else:
                print("ERROR: Could not connect to server")
                return False

    tests_passed = 0
    tests_failed = 0

    # Test 1: List books
    print("\n[1] GET /api/v1/books - List all books")
    status, data = test_endpoint(base_url, "GET", "/api/v1/books")
    if status == 200 and data and "data" in data:
        print(f"    ✓ Success: Retrieved {len(data['data'])} books")
        print(f"    Total available: {data['pagination']['total']}")
        tests_passed += 1
    else:
        print(f"    ✗ Failed: Status {status}")
        tests_failed += 1

    # Test 2: List books with pagination
    print("\n[2] GET /api/v1/books?page=1&page_size=5 - Paginated list")
    status, data = test_endpoint(base_url, "GET", "/api/v1/books?page=1&page_size=5")
    if status == 200 and data and len(data["data"]) <= 5:
        print(f"    ✓ Success: Retrieved {len(data['data'])} books (page_size=5)")
        tests_passed += 1
    else:
        print(f"    ✗ Failed: Status {status}")
        tests_failed += 1

    # Test 3: Get book detail
    print("\n[3] GET /api/v1/books/1000 - Get specific book")
    status, data = test_endpoint(base_url, "GET", "/api/v1/books/1000")
    if status == 200 and data and "data" in data:
        book = data["data"]
        print(f"    ✓ Success: {book['title']}")
        print(f"      Price: £{book['price']}, Rating: {book['rating']}/5")
        tests_passed += 1
    else:
        print(f"    ✗ Failed: Status {status}")
        tests_failed += 1

    # Test 4: Get non-existent book
    print("\n[4] GET /api/v1/books/99999 - Non-existent book (should 404)")
    status, data = test_endpoint(base_url, "GET", "/api/v1/books/99999")
    if status == 404:
        print(f"    ✓ Success: Correctly returned 404")
        tests_passed += 1
    else:
        print(f"    ✗ Failed: Expected 404, got {status}")
        tests_failed += 1

    # Test 5: List categories
    print("\n[5] GET /api/v1/categories - List all categories")
    status, data = test_endpoint(base_url, "GET", "/api/v1/categories")
    if status == 200 and data and "data" in data:
        print(f"    ✓ Success: Retrieved {data['total']} categories")
        if data["data"]:
            print(f"      First few: {', '.join(c['name'] for c in data['data'][:3])}")
        tests_passed += 1
    else:
        print(f"    ✗ Failed: Status {status}")
        tests_failed += 1

    # Test 6: Search
    print("\n[6] GET /api/v1/search?q=light - Search for books")
    status, data = test_endpoint(base_url, "GET", "/api/v1/search?q=light")
    if status == 200 and data:
        print(f"    ✓ Success: Found {len(data['data'])} books matching 'light'")
        tests_passed += 1
    else:
        print(f"    ✗ Failed: Status {status}")
        tests_failed += 1

    # Test 7: Empty search query
    print("\n[7] GET /api/v1/search (no query) - Empty search should fail")
    status, data = test_endpoint(base_url, "GET", "/api/v1/search")
    if status == 400:
        print(f"    ✓ Success: Correctly rejected empty search")
        tests_passed += 1
    else:
        print(f"    ✗ Failed: Expected 400, got {status}")
        tests_failed += 1

    # Test 8: Invalid pagination
    print("\n[8] GET /api/v1/books?page=invalid - Invalid page number")
    status, data = test_endpoint(base_url, "GET", "/api/v1/books?page=invalid")
    if status == 400:
        print(f"    ✓ Success: Correctly rejected invalid page")
        tests_passed += 1
    else:
        print(f"    ✗ Failed: Expected 400, got {status}")
        tests_failed += 1

    # Test 9: Non-existent endpoint
    print("\n[9] GET /api/v1/nonexistent - Non-existent endpoint")
    status, data = test_endpoint(base_url, "GET", "/api/v1/nonexistent")
    if status == 404:
        print(f"    ✓ Success: Correctly returned 404")
        tests_passed += 1
    else:
        print(f"    ✗ Failed: Expected 404, got {status}")
        tests_failed += 1

    # Optional: Test against real website
    if not skip_live:
        print("\n" + "=" * 60)
        print("Live Website Connectivity Check")
        print("=" * 60)

        print("\n[LIVE] Testing connectivity to books.toscrape.com")
        try:
            response = requests.get("https://books.toscrape.com", timeout=5)
            if response.status_code == 200:
                print("    ✓ Website is accessible")
            else:
                print(f"    ⚠ Website returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"    ⚠ Could not reach website: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    total = tests_passed + tests_failed
    print(f"Tests passed: {tests_passed}/{total}")
    print(f"Tests failed: {tests_failed}/{total}")

    if tests_failed == 0:
        print("\n✓ All tests passed!")
        return True
    else:
        print(f"\n✗ {tests_failed} test(s) failed")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smoke test for Books API")
    parser.add_argument("--skip-live", action="store_true", help="Skip live website test")
    parser.add_argument("--url", default="http://localhost:5000", help="API base URL")

    args = parser.parse_args()

    success = run_smoke_tests(args.url, args.skip_live)
    sys.exit(0 if success else 1)
