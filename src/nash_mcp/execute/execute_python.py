import json
import os
import subprocess
import sys
import traceback
import logging
from datetime import datetime

from nash_mcp.constants import MAC_SECRETS_PATH, NASH_SESSION_DIR
from nash_mcp.process_manager import ProcessManager


def list_session_files() -> str:
    """
    List all Python files in the current session directory.

    This function is essential to check what files already exist before creating new ones.
    ALWAYS use this function before creating a new file to avoid duplicating functionality.

    USE CASES:
    - Before creating a new file to check if something similar already exists
    - When starting work on a new task to understand available resources
    - To discover relevant code that could be modified instead of rewritten
    - When fixing errors to find the file that needs editing

    EXAMPLES:
    ```python
    # List all existing Python files in the session
    list_session_files()

    # After seeing available files, check content of a specific file
    get_file_content("data_processor.py")
    ```

    WORKFLOW:
    1. ALWAYS start by listing available files with list_session_files()
    2. Check content of relevant files with get_file_content()
    3. Edit existing files with edit_python_file() instead of creating new ones
    4. Only create new files for entirely new functionality

    Returns:
        A formatted list of Python files in the current session directory
    """
    try:
        # Ensure session directory exists
        if not NASH_SESSION_DIR.exists():
            return "No session directory found."

        # Find all Python files in the session directory
        py_files = list(NASH_SESSION_DIR.glob("*.py"))

        if not py_files:
            return "No Python files found in the current session."

        # Sort files by modification time (newest first)
        py_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Format output
        result = "Python files in current session:\n\n"
        for file_path in py_files:
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            result += f"- {file_path.name} (Modified: {mod_time})\n"

        result += '\nTo view file content: get_file_content("filename.py")'
        return result
    except Exception as e:
        logging.error(f"Error listing session files: {str(e)}")
        return f"Error listing files: {str(e)}"


def get_file_content(file_name: str) -> str:
    """
    Retrieve the contents of a Python file from the session directory.

    This function reads a file from the current session directory and returns its
    contents. This is essential for viewing the current state of a file before
    making edits with edit_python_file().

    USE CASES:
    - Before making edits to an existing file
    - When checking the current implementation of a script
    - To understand the structure of a previously saved script
    - For reviewing code to identify parts that need modification

    EXAMPLES:
    ```python
    # View a file named "data_analysis.py"
    get_file_content("data_analysis.py")

    # View a file without .py extension (extension will be added automatically)
    get_file_content("data_analysis")
    ```

    WORKFLOW:
    1. Use get_file_content() to check if a file exists and view its current content
    2. Identify the exact content you want to modify
    3. Use edit_python_file() to make targeted changes by replacing specific content
    4. Use execute_python() with an empty code string to run the modified file

    Args:
        file_name: The name of the file to read from the session directory

    Returns:
        The file contents as a string, or an error message if the file doesn't exist
    """
    try:
        # Ensure file has .py extension
        if not file_name.endswith(".py"):
            file_name = f"{file_name}.py"

        file_path = NASH_SESSION_DIR / file_name

        if not file_path.exists():
            return f"Error: File '{file_name}' not found in the current session."

        with open(file_path, "r") as f:
            content = f.read()

        return content
    except Exception as e:
        logging.error(f"Error reading file '{file_name}': {str(e)}")
        return f"Error reading file: {str(e)}"


def edit_python_file(file_name: str, old_content: str, new_content: str) -> str:
    """
    Edit a Python file by replacing specific content with new content.

    ALWAYS PRIORITIZE EDITING EXISTING FILES RATHER THAN CREATING NEW ONES WHEN MAKING CHANGES.
    This should be your first choice whenever modifying existing code - even for seemingly significant changes.

    This function uses exact string matching to find and replace code snippets,
    similar to how Claude edits files. This approach is more reliable for complex
    changes and matches how LLMs naturally think about editing text.

    USE CASES:
    - Fix bugs or errors in existing code
    - Refactor code to improve readability or maintainability
    - Add new features to an existing script
    - Update variable names, function signatures, or other identifiers
    - Replace entire blocks of code with improved implementations
    - Change algorithm implementations or logic flows
    - Modify large portions of files (you can replace almost the entire content if needed)

    ADVANTAGES:
    - Uses exact pattern matching, similar to how Claude handles edits
    - Avoids problems with line numbers shifting during edits
    - Can replace multi-line content with precise context
    - More reliable for complex edits than line-based approaches
    - Preserves script history and context

    WHEN TO EDIT vs. CREATE NEW:

    EDIT when (almost always):
    - Making any modification to existing functionality
    - Fixing bugs or issues in existing code
    - Adding new functions or classes to existing modules
    - Changing logic, algorithms, or implementations
    - Adjusting parameters or configuration values
    - Updating imports or dependencies
    - Improving error handling or adding validation
    - Enhancing existing features in any way
    - Refactoring or restructuring code
    - Even for major changes that affect large portions of the file

    CREATE NEW only when:
    - Creating a completely separate utility with an entirely different purpose
    - Explicitly asked by the user to create a new standalone file
    - Testing isolated functionality that shouldn't affect existing code
    - The existing file is explicitly described as a template or example

    EXAMPLES:
    ```python
    # Fix a calculation by replacing the specific function
    edit_python_file(
        "data_analysis.py",
        "def calculate_average(values):\n    return sum(values) / len(values)",
        "def calculate_average(values):\n    return np.mean(values)  # Using numpy for better handling of edge cases"
    )

    # Fix a bug by replacing a specific line with its surrounding context
    edit_python_file(
        "processor.py",
        "    data = load_data()\n    result = process(data)\n    save_results(data)  # Bug: saving wrong data",
        "    data = load_data()\n    result = process(data)\n    save_results(result)  # Fixed: save processed results"
    )

    # Add a new import statement
    edit_python_file(
        "api_client.py",
        "import requests\nimport json",
        "import requests\nimport json\nimport logging"
    )

    # Adding error handling to a function (NOTICE INDENTATION IS PRESERVED)
    edit_python_file(
        "fetch_data.py",
        "def fetch_user_data(user_id):\n    url = f\"https://api.example.com/users/{user_id}\"\n    response = requests.get(url)\n    response.raise_for_status()\n    return response.json()",
        "def fetch_user_data(user_id):\n    url = f\"https://api.example.com/users/{user_id}\"\n    try:\n        response = requests.get(url)\n        response.raise_for_status()\n        return response.json()\n    except requests.RequestException as e:\n        logging.error(f\"Failed to fetch user data: {e}\")\n        return None"
    )

    # Major change: Replace an entire function with a completely new implementation
    edit_python_file(
        "processor.py",
        "def process_data(data):\n    # Old inefficient implementation\n    result = []\n    for item in data:\n        if item['value'] > 0:\n            result.append(item['value'] * 2)\n    return result",
        "def process_data(data):\n    # New vectorized implementation\n    import pandas as pd\n    df = pd.DataFrame(data)\n    return df[df['value'] > 0]['value'] * 2"
    )

    # Even major changes that add multiple functions should use edit_python_file
    edit_python_file(
        "utils.py",
        "# Utility functions for data processing",
        "# Utility functions for data processing\n\ndef validate_input(data):\n    \"\"\"Validate input data format.\"\"\"\n    if not isinstance(data, list):\n        raise TypeError(\"Data must be a list\")\n    return True\n\ndef normalize_data(data):\n    \"\"\"Normalize values to 0-1 range.\"\"\"\n    min_val = min(data)\n    max_val = max(data)\n    return [(x - min_val) / (max_val - min_val) for x in data]"
    )
    ```

    WORKFLOW:
    1. Always check if a relevant file already exists with get_file_content()
    2. When modifying any existing file, use edit_python_file()
    3. Identify the exact content to replace (including enough context)
    4. Create the new replacement content
    5. Apply the change with edit_python_file()
    6. Use execute_python() to run the modified file
    7. Only create new files when specifically creating a new utility

    BEST PRACTICES:
    - Include sufficient context around the text to be replaced (3-5 lines before and after)
    - For major rewrites, you can replace large chunks of the file or even nearly all content
    - Ensure the old_content exactly matches text in the file, including spacing and indentation
    - Make focused, targeted changes rather than multiple changes at once
    - When a user asks to "fix", "update", "modify", or "change" something, they typically want edits to existing files

    INDENTATION GUIDELINES (CRITICAL FOR PYTHON):
    - Always preserve correct indentation in both old_content and new_content
    - When adding control structures (if/else, try/except, loops), replace the entire block
    - Never try to insert just the opening part of a control structure without its closing part
    - For adding error handling, replace the entire function or block, not just parts of it
    - Watch for common indentation errors, especially with nested structures
    - When debugging indentation issues, view the entire file first with get_file_content()
    - For complex control flow changes, prefer replacing larger blocks to ensure consistency

    PATTERN RECOGNITION:
    - When a user asks to "fix", "update", "modify", or "change" something, they typically want edits to existing files
    - Use list_session_files() and get_file_content() first to check what files already exist
    - Only create new files when the user explicitly requests a completely new utility

    SAFETY FEATURES:
    - Creates a backup of the original file (.py.bak extension)
    - Returns a diff of changes made
    - Will only replace exact matches, preventing unintended changes

    Args:
        file_name: The name of the file to edit in the session directory
        old_content: The exact content to replace (must match exactly, including whitespace)
        new_content: The new content to insert as a replacement

    Returns:
        Success message with diff of changes, or error message if the operation fails
    """
    try:
        # Ensure file has .py extension
        if not file_name.endswith(".py"):
            file_name = f"{file_name}.py"

        file_path = NASH_SESSION_DIR / file_name

        if not file_path.exists():
            return f"Error: File '{file_name}' not found in the current session."

        # Read the original file
        with open(file_path, "r") as f:
            content = f.read()

        # Check if the old content exists in the file
        if old_content not in content:
            return f"Error: The specified content was not found in '{file_name}'. Please check that the content matches exactly, including whitespace and indentation."

        # Create a backup of the original file
        backup_path = file_path.with_suffix(".py.bak")
        with open(backup_path, "w") as f:
            f.write(content)

        # Replace the content
        new_file_content = content.replace(old_content, new_content)

        # Write the modified content back to the file
        with open(file_path, "w") as f:
            f.write(new_file_content)

        # Generate a unified diff for the changes
        from difflib import unified_diff

        old_lines = content.splitlines()
        new_lines = new_file_content.splitlines()

        diff = list(
            unified_diff(
                old_lines,
                new_lines,
                fromfile=f"{file_name} (original)",
                tofile=f"{file_name} (modified)",
                lineterm="",
                n=3,  # Context lines
            )
        )

        if diff:
            diff_result = "\n".join(diff)
        else:
            diff_result = "No changes detected."

        return f"Successfully edited '{file_name}'.\n\nChanges:\n{diff_result}"

    except Exception as e:
        logging.error(f"Error editing file '{file_name}': {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error editing file: {str(e)}"


def execute_python(code: str, file_name: str, args: list = None) -> str:
    """Execute arbitrary Python code and return the result.

    ⚠️ REQUIRED PARAMETERS - MUST BE PROVIDED IN A SINGLE FUNCTION CALL: ⚠️

    - code: The Python code to execute (string)
    - file_name: Name for the Python file (string)
    - args: Optional command-line arguments for the script (list)

    CORRECT EXAMPLES:

    ```python
    # Example 1: Basic usage
    execute_python(
        code="print('Hello world')",
        file_name="hello.py"
    )

    # Example 2: With imports
    execute_python(
        code="import os\nprint(os.getcwd())",
        file_name="show_dir.py"
    )

    # Example 3: With command-line arguments
    execute_python(
        code="import sys\nprint(f'Arguments: {sys.argv[1:]}')",
        file_name="show_args.py",
        args=["arg1", "arg2"]
    )

    # Example 4: Running an existing file without modifying it
    execute_python(
        code="",
        file_name="existing_script.py"
    )
    ```

    ❌ COMMON ERRORS - DO NOT DO THIS:

    ```python
    # ERROR: Missing required parameters
    execute_python()  # Will fail! Missing both code and file_name

    # ERROR: Missing file_name parameter
    execute_python(code="print('Hello')")  # Will fail! Missing file_name

    # ERROR: Trying to split function call across multiple steps
    # First call to "prepare" - THIS IS WRONG
    execute_python()
    # Then providing code separately - THIS DOESN'T WORK
    code = "print('Hello')"
    ```

    ⚠️ MANDATORY PRE-CODING CHECKLIST - COMPLETE BEFORE WRITING ANY CODE: ⚠️

    STOP! Before writing or executing ANY code, have you completed these REQUIRED checks?

    1. Check available packages: list_installed_packages()
       - Know what libraries you can use
       - Avoid importing unavailable packages

    2. Check available secrets: nash_secrets()
       - See what API keys and credentials are available
       - Don't write code requiring credentials you don't have

    3. Check existing files: list_session_files()
       - See what code already exists
       - Avoid duplicating existing functionality

    4. Review relevant file contents: get_file_content("filename.py")
       - Understand existing implementations
       - Decide whether to edit or create new

    These steps are MANDATORY. Skipping them is the #1 cause of inefficient code development.

    WHEN TO USE execute_python VS. edit_python_file:

    - Use edit_python_file() for MINOR or MODERATE changes to existing files
      - This is usually more efficient for small to medium changes
      - Always prefer editing when the file already exists

    - Use execute_python() only when:
      - Creating a completely new file
      - Changes would require replacing almost the entire existing file
      - Creating a brand new file results in a cleaner, smaller response

    FUNCTION BEHAVIOR:
    - This function executes standard Python code with access to imported modules
    - The code is saved to a file in the session directory and executed
    - All secrets are passed as environment variables to the subprocess
    - If code="" and the file exists, it will run the existing file without changes

    COMMAND-LINE ARGUMENTS:
    - The `args` parameter allows passing command-line arguments to the script
    - Arguments are accessed in your script using the standard sys.argv list:
      ```python
      import sys
      if len(sys.argv) > 1:
          input_file = sys.argv[1]
          print(f"Processing {input_file}")
      ```

    SECRET MANAGEMENT:
    - Use nash_secrets() to see available API keys/credentials
    - Access secrets in your code with: os.environ.get('SECRET_NAME')

    BEST PRACTICES:
    - Always provide both code and file_name in a single function call
    - Use descriptive filenames that reflect the purpose (e.g., "data_analysis.py")
    - Include proper error handling with try/except blocks
    - Clean up any resources (files, connections) your code creates
    - For web automation, use operate_browser instead of custom code

    SECURITY CONSIDERATIONS:
    - Never write code that could harm the user's system
    - Don't leak or expose secret values in output
    - Avoid making unauthorized network requests
    - Sanitize any arguments passed to the script

    Args:
        code: Python code to execute (multi-line string)
        file_name: Descriptive name for the Python file (will be saved in session directory)
        args: Optional list of command-line arguments to pass to the script

    Returns:
        Captured stdout from code execution or detailed error message
    """
    # Log the full code being executed
    logging.info(f"Executing Python code in file '{file_name}':\n{code}")

    # Format args for logging if provided
    args_str = str(args) if args else "None"
    if len(args_str) > 100:
        args_str = args_str[:100] + "..."
    logging.info(f"Script arguments: {args_str}")

    try:
        # Load secrets as environment variables
        env_vars = os.environ.copy()

        if MAC_SECRETS_PATH.exists():
            try:
                with open(MAC_SECRETS_PATH, "r") as f:
                    secrets = json.load(f)

                # Add secrets to environment variables for subprocess
                for secret in secrets:
                    if "key" in secret and "value" in secret:
                        env_vars[secret["key"]] = secret["value"]

                logging.info("Loaded secrets for Python execution")
            except Exception as e:
                # Log the error but continue execution
                logging.warning(f"Error loading secrets: {str(e)}")
                print(f"Warning: Error loading secrets: {str(e)}")
        else:
            logging.info("No secrets file found")

        # Ensure file name has .py extension
        if not file_name.endswith(".py"):
            file_name = f"{file_name}.py"

        # Create the full file path in the session directory
        file_path = NASH_SESSION_DIR / file_name

        # If code is empty and file exists, use existing file
        if not code and file_path.exists():
            logging.info(f"Using existing file: {file_path}")
        else:
            # Write the code to the file
            with open(file_path, "w") as f:
                f.write(code)
            logging.info(f"Saved Python code to: {file_path}")

        try:
            # Execute the file using the same Python interpreter
            logging.info(f"Running Python code from: {file_path}")
            try:
                # Prepare command arguments
                cmd_args = [sys.executable, str(file_path)]

                # Add any command-line arguments
                if args:
                    # Convert all arguments to strings
                    string_args = [str(arg) for arg in args]
                    cmd_args.extend(string_args)

                # Log the full command being executed
                logging.info(f"Launching subprocess with command: {' '.join(cmd_args)}")

                proc = subprocess.Popen(
                    cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env_vars
                )

                # Log process information
                proc_pid = proc.pid
                logging.info(f"Created subprocess with PID {proc_pid} for file {file_path}")

                # Track the process in the process manager
                process_manager = ProcessManager.get_instance()
                process_manager.add_pid(proc_pid)

                try:
                    logging.info(f"Waiting for process {proc_pid} to complete...")
                    stdout, stderr = proc.communicate()
                    logging.info(f"Process {proc_pid} completed with return code {proc.returncode}")
                    result = subprocess.CompletedProcess(cmd_args, proc.returncode, stdout, stderr)
                finally:
                    # Remove from the process manager if completed successfully
                    if hasattr(proc, "returncode") and proc.returncode == 0:
                        process_manager.remove_pid(proc_pid)
                    else:
                        logging.info(f"Keeping PID {proc_pid} in process manager (non-zero or unknown return code)")

                # Return stdout if successful, or stderr if there was an error
                if result.returncode == 0:
                    logging.info(f"Python code in {file_name} executed successfully")
                    return result.stdout if result.stdout else f"Code in {file_name} executed successfully (no output)"
                else:
                    logging.warning(f"Python code execution of {file_name} failed with return code {result.returncode}")
                    return f"Error in {file_name} (return code {result.returncode}):\n{result.stderr}"

            except Exception as exec_err:
                # Handle any execution exceptions
                error_msg = f"Error executing {file_name}: {str(exec_err)}"
                logging.error(error_msg)
                logging.error(traceback.format_exc())

                return error_msg

        except Exception as e:
            # Catch-all for any other exceptions in the outer try block
            logging.error(f"Unexpected error in execute_python for {file_name}: {str(e)}")
            logging.error(traceback.format_exc())

            # Return error message instead of raising to prevent MCP server crash
            return f"Unexpected error in {file_name}: {str(e)}\nSee logs for details."
    except Exception as e:
        logging.error(f"Python execution error: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error in {file_name}: {str(e)}\nTraceback: {traceback.format_exc()}\n\n"
