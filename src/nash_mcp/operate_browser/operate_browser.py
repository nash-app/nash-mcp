import os
import sys
import json
import logging
import traceback
import subprocess
from pathlib import Path


def operate_browser(task: str) -> str:
    """
    Automate web browsing tasks using browser-use and Claude to control a browser.

    This tool uses Claude to operate a web browser, allowing it to perform complex web tasks
    like navigating websites, filling forms, clicking buttons, and extracting information.
    Use this tool when you need to interact with websites in a way that requires browser
    automation rather than simple HTTP requests.

    Examples of tasks this tool can handle:
    - "Search for topic X on Google and summarize the top 3 results"
    - "Go to website Y and fill out their contact form"
    - "Log into service Z and extract my account information"
    - "Find and download a specific report from a website"
    - "Complete a multi-step process on a website"

    WHEN TO USE:
    - When you need to interact with websites that require clicking, form filling or navigation
    - When you need to extract data from dynamic websites that load content with JavaScript
    - When you need to perform complex sequences of actions on a website
    - When simple HTTP requests with WebFetchTool would not work

    LIMITATIONS:
    - Requires Google Chrome to be installed on macOS
    - Cannot bypass CAPTCHA or advanced anti-bot measures
    - Cannot complete two-factor authentication (2FA) flows
    - Cannot handle biometric authentication or security questions
    - Task execution might take 30+ seconds for complex operations
    - Browser interactions have natural variance and may occasionally fail

    For sites with security measures like 2FA or CAPTCHA:
    - The tool will terminate and return a message describing what it encountered
    - You should report this limitation to the user with specific details
    - Recommend that the user complete authentication in their own browser first
    - Then run this tool again with a new task that starts from the authenticated state

    Example workflow for secured sites:
    1. Tool: "I encountered a 2FA challenge at example.com/login and cannot proceed."
    2. You: Inform the user they need to authenticate manually in their own browser
    3. User: Completes authentication in their own browser
    4. You: Use this tool again with "Now that you're logged in, extract account details..."

    Args:
        task: A detailed description of the web task to accomplish

    Returns:
        The result of the web automation task, typically containing extracted information
        or confirmation of task completion
    """
    try:
        # Get the path to the browser_agent.py script (in the same directory)
        script_dir = Path(__file__).resolve().parent
        script_path = script_dir / "browser_agent.py"

        if not script_path.exists():
            return f"Error: Browser agent script not found at {script_path}"

        # Log the operation
        logging.info(f"Running browser automation task in subprocess: {task}")

        # Run the browser_agent.py script as a subprocess
        result = subprocess.run(
            [sys.executable, str(script_path), task],
            env=os.environ.copy(),  # Copy current environment
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        # Process the output
        if result.returncode == 0:
            # Try to parse JSON output from stdout
            try:
                output = json.loads(result.stdout.strip())
                if "result" in output:
                    logging.info("Browser automation task completed successfully")
                    return output["result"]
                elif "error" in output:
                    error_message = output["error"]
                    logging.error(f"Browser automation error: {error_message}")

                    # Special handling for Chrome installation errors
                    if "Chrome is not installed" in error_message:
                        return (
                            f"Error: {error_message} Please install Google Chrome from https://www.google.com/chrome/"
                        )
                    return f"Error: {error_message}"
                else:
                    return str(output)
            except json.JSONDecodeError:
                # If we can't parse JSON, return raw output
                logging.warning("Could not parse JSON output from browser automation subprocess")
                if result.stdout:
                    return result.stdout.strip()
                else:
                    return "Browser automation completed but returned no output"
        else:
            # Handle subprocess error
            logging.error(f"Browser automation process failed with code {result.returncode}")
            error_output = result.stderr or "No error output"
            return f"Error: Browser automation process failed with code {result.returncode}. Error: {error_output}"

    except subprocess.TimeoutExpired as timeout_error:
        logging.error("Browser automation timed out after 300 seconds")

        # Attempt to kill any child processes (browsers) that might still be running
        if hasattr(timeout_error, "process") and timeout_error.process:
            try:
                timeout_error.process.kill()
                logging.info("Killed timeout process after browser automation timeout")
            except Exception as kill_error:
                logging.error(f"Error killing process after timeout: {str(kill_error)}")

        return "Error: Browser automation timed out after 300 seconds"
    except Exception as e:
        logging.error(f"Error in operate_browser: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error executing web task: {str(e)}"
