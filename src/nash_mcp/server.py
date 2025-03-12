import os
import sys
import logging
import traceback
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Nash imports
from nash_mcp.constants import MAC_LOGS_PATH, NASH_SESSION_DIR, NASH_SESSION_ID

# Execute
from nash_mcp.execute import execute_command, execute_python, list_installed_packages

# Fetch
from nash_mcp.fetch_webpage import fetch_webpage

# Secrets
from nash_mcp.nash_secrets import nash_secrets

# Tasks
from nash_mcp.nash_tasks import (
    save_nash_task, list_nash_tasks, run_nash_task, delete_nash_task,
    execute_task_script, view_task_details
)

# Help
from nash_mcp.nash_help import nash_help


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
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stderr)
            ]
        )
        
        logging.info(f"Logging initialized. Log file: {log_file}")
        return True
    except Exception as e:
        print(f"Error setting up logging: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        return False


try:
    # Set up logging
    setup_logging()

    logging.info(f"Starting Nash MCP server with session ID: {NASH_SESSION_ID}")
    
    # Create session directory
    NASH_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    logging.info(f"Created session directory: {NASH_SESSION_DIR}")

    # Create MCP instance
    mcp = FastMCP("Nash")

    # Register tools
    logging.info("Registering MCP tools")

    # Execute
    mcp.add_tool(execute_command)
    mcp.add_tool(execute_python)
    mcp.add_tool(list_installed_packages)

    # Fetch
    mcp.add_tool(fetch_webpage)

    # Secrets
    mcp.add_tool(nash_secrets)

    # Tasks
    mcp.add_tool(save_nash_task)
    mcp.add_tool(list_nash_tasks)
    mcp.add_tool(run_nash_task)
    mcp.add_tool(delete_nash_task)
    mcp.add_tool(execute_task_script)
    mcp.add_tool(view_task_details)

    # Help
    mcp.add_tool(nash_help)

    # Start the server
    logging.info("All tools registered, starting MCP server")
    mcp.run()

except Exception as e:
    logging.critical(f"Fatal error in Nash MCP server: {str(e)}")
    logging.critical(f"Traceback: {traceback.format_exc()}")
    print(f"Failed to run server: {str(e)}", file=sys.stderr)
    sys.exit(1)
