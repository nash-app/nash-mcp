from unittest.mock import patch, MagicMock
from nash_mcp.fetch_webpage.fetch_webpage import fetch_webpage
import requests


class TestFetchWebpage:

    @patch("nash_mcp.fetch_webpage.fetch_webpage.requests.get")
    def test_successful_fetch(self, mock_get):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = "<html><body><h1>Test Page</h1><p>This is content</p></body></html>"
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Call function
        result = fetch_webpage("https://example.com")

        # Assertions
        mock_get.assert_called_once_with("https://example.com")
        mock_response.raise_for_status.assert_called_once()

        # Check result contains expected content (using real html2text)
        assert "Test Page" in result
        assert "This is content" in result

    @patch("nash_mcp.fetch_webpage.fetch_webpage.requests.get")
    def test_http_error(self, mock_get):
        # Setup mock to raise HTTPError
        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = requests.exceptions.HTTPError("404 Client Error")
        http_error.response = mock_response
        mock_get.return_value.raise_for_status.side_effect = http_error

        # Call function
        result = fetch_webpage("https://example.com/notfound")

        # Assertions
        assert "Error fetching https://example.com/notfound: HTTP status code 404" in result

    @patch("nash_mcp.fetch_webpage.fetch_webpage.requests.get")
    def test_connection_error(self, mock_get):
        # Setup mock to raise ConnectionError
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        # Call function
        result = fetch_webpage("https://nonexistent.example")

        # Assertions
        assert "Error fetching https://nonexistent.example: Connection failed" in result

    @patch("nash_mcp.fetch_webpage.fetch_webpage.requests.get")
    def test_timeout_error(self, mock_get):
        # Setup mock to raise Timeout
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        # Call function
        result = fetch_webpage("https://slow.example.com")

        # Assertions
        assert "Error fetching https://slow.example.com: Request timed out" in result

    @patch("nash_mcp.fetch_webpage.fetch_webpage.requests.get")
    def test_general_request_exception(self, mock_get):
        # Setup mock to raise RequestException
        mock_get.side_effect = requests.exceptions.RequestException("General error")

        # Call function
        result = fetch_webpage("https://example.com")

        # Assertions
        assert "Error fetching https://example.com: General error" in result

    @patch("nash_mcp.fetch_webpage.fetch_webpage.requests.get")
    def test_unexpected_exception(self, mock_get):
        # Setup mock to raise unexpected exception
        mock_get.side_effect = Exception("Unexpected error")

        # Call function
        result = fetch_webpage("https://example.com")

        # Assertions
        assert "Error fetching https://example.com: Unexpected error" in result
