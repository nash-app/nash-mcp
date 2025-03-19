import sys
import logging
import traceback
import os

from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any

from mcp.server.fastmcp import FastMCP

# Nash imports
from nash_mcp.constants import NASH_SESSION_DIR, NASH_SESSION_ID, MAC_SESSIONS_PATH
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


@asynccontextmanager
async def nash_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """
    Manage application lifecycle and process cleanup.

    This context manager ensures all child processes are properly cleaned up
    when the server shuts down, regardless of how termination occurs.
    """
    # Initialize the process manager
    process_manager = ProcessManager.initialize(NASH_SESSION_DIR)

    context = {"server_pid": os.getpid(), "process_manager": process_manager}

    logging.info(f"Server starting with PID {context['server_pid']}")

    try:
        yield context
    finally:
        # Clean up happens here when the server is shutting down
        process_manager = context["process_manager"]

        # Comprehensive cleanup using our new process manager
        process_manager.cleanup(session_base_path=str(MAC_SESSIONS_PATH))


# Main MCP server setup and execution
try:
    # Set up logging
    setup_logging()

    logging.info(f"Starting Nash MCP server with session ID: {NASH_SESSION_ID}")

    # Create session directory
    NASH_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    logging.info(f"Created session directory: {NASH_SESSION_DIR}")

    # Create MCP instance with lifespan management
    mcp = FastMCP("Nash", lifespan=nash_lifespan)

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
