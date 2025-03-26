from pathlib import Path
from unittest.mock import patch
from nash_mcp.nash_secrets.nash_secrets import nash_secrets


class TestNashSecrets:

    @patch("nash_mcp.nash_secrets.nash_secrets.MAC_SECRETS_PATH", Path(__file__).parent / "test_secrets.json")
    def test_successful_secrets_retrieval(self):
        # Call function with the test file we created
        result = nash_secrets()

        # Check result formatting
        assert "Available secrets:" in result
        assert "Key: API_KEY_1" in result
        assert "Description: First API key" in result
        assert "Key: API_KEY_2" in result
        assert "Description: Second API key" in result

    @patch("nash_mcp.nash_secrets.nash_secrets.MAC_SECRETS_PATH", Path(__file__).parent / "nonexistent_file.json")
    def test_no_secrets_file(self):
        # Call function with a path that doesn't exist
        result = nash_secrets()

        # Assertions
        assert "No secrets file found." in result

    @patch("nash_mcp.nash_secrets.nash_secrets.MAC_SECRETS_PATH", Path(__file__).parent / "empty_secrets.json")
    def test_empty_secrets(self):
        # Call function with our empty file
        result = nash_secrets()

        # Assertions
        assert "No secrets available." in result
