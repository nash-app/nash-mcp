import subprocess
import traceback
import logging
import os

# Import Nash constants
from nash_mcp.process_manager import ProcessManager

# Process management is now handled by ProcessManager


def execute_command(cmd: str) -> str:
    """
    Execute an arbitrary shell command and return its output.

    ⚠️ MANDATORY PRE-EXECUTION CHECKLIST: ⚠️

    STOP! Before running ANY command, have you completed these REQUIRED checks?

    1. Check available packages: list_installed_packages()
       - Know what tools are available in the environment

    2. Check available secrets: nash_secrets()
       - See what API keys and credentials are available
       - Don't run commands requiring credentials you don't have

    3. Check existing files: list_session_files()
       - See what code already exists that might help

    These steps are MANDATORY. Skipping them can lead to wasted effort.

    This function runs shell commands with full access to your system.
    Use with caution and follow security best practices.

    Examples:
        execute_command("ls -la ~")
        execute_command("find /usr/local -name 'python*'")
        execute_command("grep -r 'TODO' ./src")

    Security considerations:
    - Uses shell=True which means shell metacharacters are interpreted
    - Never run commands that could damage your system (rm -rf, etc.)
    - Avoid commands that might expose sensitive information
    - Consider using safer alternatives for file operations

    WHEN TO USE:
    - For quick system information gathering (file listings, processes, etc.)
    - When specific shell utilities provide the most efficient solution
    - For running installed command-line tools not accessible via Python
    - When file/directory operations are simpler with shell commands

    Consider using execute_python() instead when:
    - Complex data processing is required
    - Error handling needs to be more robust
    - The operation involves multiple steps or conditional logic

    Args:
        cmd: Shell command to execute (string)

    Returns:
        Command output (stdout) if successful
        Detailed error information with exit code and stderr if command fails
        Exception details with traceback if execution fails
    """
    logging.info(f"Executing command: {cmd}")

    try:
        # Always use shell=True for simplicity and tilde expansion
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

        # Track the process in the process manager
        proc_pid = proc.pid
        process_manager = ProcessManager.get_instance()
        process_manager.add_pid(proc_pid)

        try:
            stdout, stderr = proc.communicate()
            if proc.returncode == 0:
                logging.info(f"Command executed successfully (exit code 0)")
                return stdout if stdout.strip() else "Command executed (no output)."
            else:
                logging.warning(f"Command failed with exit code {proc.returncode}: {cmd}")
                logging.debug(f"Command stderr: {stderr}")
                return f"Command failed (exit code {proc.returncode}).\n" f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        finally:
            # Process cleanup will happen via ProcessManager

            # IMPORTANT: Only remove from the process manager if the process completed successfully
            # Don't remove if it's a long-running process that was detached (intentionally)
            # We'll still want to kill it during server shutdown
            if hasattr(proc, "returncode") and proc.returncode == 0:
                process_manager.remove_pid(proc_pid)
            else:
                logging.info(f"Keeping PID {proc_pid} in process manager (non-zero or unknown return code)")
    except Exception as e:
        logging.error(f"Exception while executing command: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Exception: {e}\nTraceback:\n{traceback.format_exc()}"
