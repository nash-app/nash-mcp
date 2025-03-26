import logging
import sys
import traceback
from datetime import datetime

from nash_mcp.constants import MAC_LOGS_PATH


def setup_logging():
    """Configure logging for the Nash MCP server."""
    try:
        # Create logs directory if it doesn't exist
        MAC_LOGS_PATH.mkdir(parents=True, exist_ok=True)

        # Create a timestamped log file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = MAC_LOGS_PATH / f"nash_mcp_{timestamp}.log"

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stderr)],
        )

        logging.info(f"Logging initialized. Log file: {log_file}")
        return True
    except Exception as e:
        print(f"Error setting up logging: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        return False
