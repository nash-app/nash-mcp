import sys
import logging
import traceback
import atexit
import signal

from mcp.server.fastmcp import FastMCP

# Nash imports
from nash_mcp.constants import NASH_SESSION_DIR, NASH_SESSION_ID
from nash_mcp.logging import setup_logging
from nash_mcp.process_manager import ProcessManager

# Execute
from nash_mcp.execute import (
    execute_command,
    execute_python,
    list_installed_packages,
    get_file_content,
    edit_python_file,
    list_session_files,
)

# Fetch
from nash_mcp.fetch_webpage import fetch_webpage

# Web Automation
from nash_mcp.operate_browser import operate_browser

# Secrets
from nash_mcp.nash_secrets import nash_secrets

# Tasks
from nash_mcp.nash_tasks import (
    save_nash_task,
    list_nash_tasks,
    run_nash_task,
    delete_nash_task,
    execute_task_script,
    view_task_details,
)


# Global process manager reference
_process_manager = None


# Cleanup handler for atexit and signals
def cleanup_handler(*args):
    """Clean up processes when exiting."""
    logging.info("Running process cleanup")

    if _process_manager:
        _process_manager.cleanup()
    else:
        logging.warning("No process manager available for cleanup")


# Register the handler for both atexit and signals
atexit.register(cleanup_handler)

# Main MCP server setup and execution
try:
    # Set up logging
    setup_logging()

    logging.info(f"Starting Nash MCP server with session ID: {NASH_SESSION_ID}")

    # Create session directory
    NASH_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    logging.info(f"Created session directory: {NASH_SESSION_DIR}")

    # Initialize process manager and save global reference
    _process_manager = ProcessManager.initialize(NASH_SESSION_DIR)

    # Register signal handlers
    signal.signal(signal.SIGTERM, cleanup_handler)
    signal.signal(signal.SIGINT, cleanup_handler)

    # Create MCP instance with lifespan management
    mcp = FastMCP("Nash")

    # Register tools
    logging.info("Registering MCP tools")

    # Execute
    mcp.add_tool(execute_command)
    mcp.add_tool(execute_python)
    mcp.add_tool(list_session_files)
    mcp.add_tool(get_file_content)
    mcp.add_tool(edit_python_file)
    mcp.add_tool(list_installed_packages)

    # Fetch
    mcp.add_tool(fetch_webpage)

    # Web Automation
    mcp.add_tool(operate_browser)

    # Secrets
    mcp.add_tool(nash_secrets)

    # Tasks
    mcp.add_tool(save_nash_task)
    mcp.add_tool(list_nash_tasks)
    mcp.add_tool(run_nash_task)
    mcp.add_tool(delete_nash_task)
    mcp.add_tool(execute_task_script)
    mcp.add_tool(view_task_details)

    # Start the server
    logging.info("All tools registered, starting MCP server")
    mcp.run()

except Exception as e:
    logging.critical(f"Fatal error in Nash MCP server: {str(e)}")
    logging.critical(f"Traceback: {traceback.format_exc()}")
    print(f"Failed to run server: {str(e)}", file=sys.stderr)
    sys.exit(1)
