import subprocess
import traceback
import logging
import os

# Import Nash constants
from nash_mcp.process_manager import ProcessManager

# Process management is now handled by ProcessManager


def execute_command(cmd: str, args: list = None) -> str:
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

    ARGUMENTS HANDLING:
    - Any command or script is executed as a temporary shell script
    - Arguments are passed as positional parameters to the script
    - Inside the command/script, use $1, $2, etc. to access arguments
    - All arguments are properly passed to the shell script

    EXAMPLES:
    # Simple command without arguments
    execute_command("ls -la ~")

    # Command with arguments passed as list
    execute_command("find", args=["/usr/local", "-name", "python*"])

    # Shell script with positional argument reference
    execute_command('''
    if [ -z "$1" ]; then
      echo "No argument provided"
    else
      echo "Argument: $1"
    fi
    ''', args=["hello"])

    # Using a script file
    execute_command("./my_script.sh", args=["arg1", "arg2"])

    # Simple command using positional arguments
    execute_command("echo \"First arg: $1\"", args=["hello"])

    Security considerations:
    - Commands are executed in a shell environment
    - Never run commands that could damage your system (rm -rf, etc.)
    - Avoid commands that might expose sensitive information
    - Consider using safer alternatives for file operations

    WHEN TO USE:
    - For quick system information gathering (file listings, processes, etc.)
    - When specific shell utilities provide the most efficient solution
    - For running installed command-line tools not accessible via Python
    - When file/directory operations are simpler with shell commands
    - When you need script-like behavior with positional arguments ($1, $2, etc.)

    Consider using execute_python() instead when:
    - Complex data processing is required
    - Error handling needs to be more robust
    - The operation involves multiple steps or conditional logic

    Args:
        cmd: Shell command or script to execute (string)
        args: Optional list of arguments to pass to the command as positional parameters (list)

    Returns:
        Command output (stdout) if successful
        Detailed error information with exit code and stderr if command fails
        Exception details with traceback if execution fails
    """
    logging.info(f"Executing command: {cmd} with args: {args if args else '[]'}")

    try:
        import tempfile
        import os

        # Always create a temporary shell script
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as script_file:
            # Add shebang line if not present
            if not cmd.startswith("#!/"):
                script_file.write("#!/bin/bash\n")

            # Write the command as script content
            script_file.write(cmd)
            script_path = script_file.name

        # Make the script executable
        os.chmod(script_path, 0o755)

        try:
            # Convert args to strings
            arg_strings = [str(arg) for arg in args] if args else []

            # Execute the script with arguments
            full_cmd = [script_path] + arg_strings

            logging.info(f"Executing script from temporary file: {script_path}")
            proc = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Track the process in the process manager
            proc_pid = proc.pid
            process_manager = ProcessManager.get_instance()
            process_manager.add_pid(proc_pid)

            # Execute the process and capture output
            try:
                stdout, stderr = proc.communicate()
                if proc.returncode == 0:
                    logging.info(f"Command executed successfully (exit code 0)")
                    return stdout if stdout.strip() else "Command executed (no output)."
                else:
                    logging.warning(f"Command failed with exit code {proc.returncode}")
                    logging.debug(f"Command stderr: {stderr}")
                    return f"Command failed (exit code {proc.returncode}).\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
            finally:
                # Process cleanup via ProcessManager
                # IMPORTANT: Only remove from the process manager if the process completed successfully
                if hasattr(proc, "returncode") and proc.returncode == 0:
                    process_manager.remove_pid(proc_pid)
                else:
                    logging.info(f"Keeping PID {proc_pid} in process manager (non-zero or unknown return code)")
        finally:
            # Always clean up the temporary file
            try:
                os.remove(script_path)
                logging.info(f"Removed temporary script file: {script_path}")
            except Exception as e:
                logging.warning(f"Failed to remove temporary script file: {e}")
    except Exception as e:
        logging.error(f"Exception while executing command: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Exception: {e}\nTraceback:\n{traceback.format_exc()}"
