import subprocess
import traceback
import logging


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
        if (i > 0 and cmd_parts[i-1].startswith('-') and 
            ('key' in cmd_parts[i-1].lower() or 'token' in cmd_parts[i-1].lower() or 
             'pass' in cmd_parts[i-1].lower() or 'secret' in cmd_parts[i-1].lower())):
            # Replace with [REDACTED] to avoid logging sensitive info
            safe_parts.append('[REDACTED]')
        # Otherwise keep the original part
        else:
            safe_parts.append(part)
    
    safe_cmd = ' '.join(safe_parts)
    # Log the full command (but with sensitive parts redacted)
    logging.info(f"Executing command: {safe_cmd}")
    
    try:
        # Always use shell=True for simplicity and tilde expansion
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               text=True, shell=True)
        
        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            logging.info(f"Command executed successfully (exit code 0)")
            return stdout if stdout.strip() else "Command executed (no output)."
        else:
            logging.warning(f"Command failed with exit code {proc.returncode}: {safe_cmd}")
            logging.debug(f"Command stderr: {stderr}")
            return (f"Command failed (exit code {proc.returncode}).\n"
                    f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}")
    except Exception as e:
        logging.error(f"Exception while executing command: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Exception: {e}\nTraceback:\n{traceback.format_exc()}"
