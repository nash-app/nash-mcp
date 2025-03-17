import subprocess
import traceback
import logging
import os
import signal
import sys
import atexit

# Import Nash constants
from nash_mcp.constants import NASH_SESSION_DIR

# Store active subprocesses
active_processes = []


# Cleanup function
def cleanup_subprocesses():
    for proc in active_processes:
        try:
            if proc.poll() is None:  # If process is still running
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            pass


# Register cleanup on exit
atexit.register(cleanup_subprocesses)


# For signal handling
def signal_handler(sig, frame):
    cleanup_subprocesses()
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


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
    # Log the full command but still sanitize potentially sensitive parts for security
    # Split the command on spaces to identify likely arguments
    cmd_parts = cmd.split()

    # For logging, replace potentially sensitive arguments (after flags)
    # This is a simple sanitization that focuses on common sensitivity patterns
    safe_parts = []
    for i, part in enumerate(cmd_parts):
        # Check for sensitive patterns
        # If it might be a sensitive argument (like an API key or password) after a flag
        if (
            i > 0
            and cmd_parts[i - 1].startswith("-")
            and (
                "key" in cmd_parts[i - 1].lower()
                or "token" in cmd_parts[i - 1].lower()
                or "pass" in cmd_parts[i - 1].lower()
                or "secret" in cmd_parts[i - 1].lower()
            )
        ):
            # Replace with [REDACTED] to avoid logging sensitive info
            safe_parts.append("[REDACTED]")
        # Otherwise keep the original part
        else:
            safe_parts.append(part)

    safe_cmd = " ".join(safe_parts)
    # Log the full command (but with sensitive parts redacted)
    logging.info(f"Executing command: {safe_cmd}")

    try:
        # Always use shell=True for simplicity and tilde expansion
        # Use preexec_fn=os.setpgrp to make this process the group leader
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            preexec_fn=os.setpgrp,  # Make this process the group leader
        )

        # Add to active processes list for cleanup
        active_processes.append(proc)
        
        # DIRECT ADD TO TRACKING FILE - Bypass all abstractions
        proc_pid = proc.pid
        tracking_file = NASH_SESSION_DIR / "tracked_pids.txt"
        
        try:
            # Ensure file exists
            if not tracking_file.exists():
                with open(tracking_file, 'w') as f:
                    f.write("")
            
            # Read existing content
            with open(tracking_file, 'r') as f:
                content = f.read().strip()
            
            # Parse existing PIDs or create empty set
            pids = set()
            if content:
                pids = set(int(p.strip()) for p in content.split(',') if p.strip())
            
            # Add new PID
            pids.add(proc_pid)
            
            # Write back to file
            with open(tracking_file, 'w') as f:
                f.write(','.join(str(p) for p in pids))
            
            print(f"EMERGENCY: DIRECTLY ADDED PID {proc_pid} TO TRACKING FILE: {tracking_file}")
            print(f"EMERGENCY: TRACKED PIDS: {','.join(str(p) for p in pids)}")
        except Exception as e:
            # Log any errors
            print(f"EMERGENCY: FAILED TO ADD PID TO TRACKING FILE: {e}")
            
        # Still try the module function as well
        try:
            import nash_mcp.constants
            nash_mcp.constants.add_pid(proc_pid)
        except Exception as e:
            print(f"EMERGENCY: FAILED TO ADD PID VIA MODULE FUNCTION: {e}")
        logging.info(f"Added PID {proc_pid} to global process tracker")

        try:
            stdout, stderr = proc.communicate()
            if proc.returncode == 0:
                logging.info(f"Command executed successfully (exit code 0)")
                return stdout if stdout.strip() else "Command executed (no output)."
            else:
                logging.warning(f"Command failed with exit code {proc.returncode}: {safe_cmd}")
                logging.debug(f"Command stderr: {stderr}")
                return f"Command failed (exit code {proc.returncode}).\n" f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        finally:
            # Remove from active processes list
            if proc in active_processes:
                active_processes.remove(proc)
                
            # IMPORTANT: Only remove from the global tracker if the process completed successfully
            # Don't remove if it's a long-running process that was detached (intentionally)
            # We'll still want to kill it during server shutdown
            if hasattr(proc, 'returncode') and proc.returncode == 0:
                # Use the same pattern as for adding
                import nash_mcp.constants
                nash_mcp.constants.remove_pid(proc_pid)
                logging.info(f"Removed PID {proc_pid} from global process tracker (completed successfully)")
            else:
                logging.info(f"Keeping PID {proc_pid} in global process tracker (non-zero or unknown return code)")
    except Exception as e:
        logging.error(f"Exception while executing command: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Exception: {e}\nTraceback:\n{traceback.format_exc()}"
