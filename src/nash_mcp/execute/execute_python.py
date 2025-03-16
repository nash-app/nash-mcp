import json
import os
import subprocess
import sys
import traceback
import logging
import signal
import atexit
from datetime import datetime

# Store active subprocesses
active_python_processes = []

# Cleanup function
def cleanup_python_subprocesses():
    for proc in active_python_processes:
        try:
            if proc.poll() is None:  # If process is still running
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            pass

# Register cleanup on exit
atexit.register(cleanup_python_subprocesses)

# For signal handling
def python_signal_handler(sig, frame):
    cleanup_python_subprocesses()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, python_signal_handler)
signal.signal(signal.SIGTERM, python_signal_handler)

from nash_mcp.constants import MAC_SECRETS_PATH, NASH_SESSION_DIR


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
            
        result += "\nTo view file content: get_file_content(\"filename.py\")"
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
        if not file_name.endswith('.py'):
            file_name = f"{file_name}.py"
            
        file_path = NASH_SESSION_DIR / file_name
        
        if not file_path.exists():
            return f"Error: File '{file_name}' not found in the current session."
            
        with open(file_path, 'r') as f:
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
        if not file_name.endswith('.py'):
            file_name = f"{file_name}.py"
            
        file_path = NASH_SESSION_DIR / file_name
        
        if not file_path.exists():
            return f"Error: File '{file_name}' not found in the current session."
        
        # Read the original file
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Check if the old content exists in the file
        if old_content not in content:
            return f"Error: The specified content was not found in '{file_name}'. Please check that the content matches exactly, including whitespace and indentation."
            
        # Create a backup of the original file
        backup_path = file_path.with_suffix('.py.bak')
        with open(backup_path, 'w') as f:
            f.write(content)
            
        # Replace the content
        new_file_content = content.replace(old_content, new_content)
        
        # Write the modified content back to the file
        with open(file_path, 'w') as f:
            f.write(new_file_content)
            
        # Generate a unified diff for the changes
        from difflib import unified_diff
        
        old_lines = content.splitlines()
        new_lines = new_file_content.splitlines()
        
        diff = list(unified_diff(
            old_lines, 
            new_lines,
            fromfile=f"{file_name} (original)",
            tofile=f"{file_name} (modified)",
            lineterm='',
            n=3  # Context lines
        ))
        
        if diff:
            diff_result = '\n'.join(diff)
        else:
            diff_result = "No changes detected."
            
        return f"Successfully edited '{file_name}'.\n\nChanges:\n{diff_result}"
        
    except Exception as e:
        logging.error(f"Error editing file '{file_name}': {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error editing file: {str(e)}"


def execute_python(code: str, file_name: str) -> str:
    """Execute arbitrary Python code and return the result.

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
    
    AFTER completing the checklist, consider output efficiency:
    
    - If a similar file exists with MINOR or MODERATE changes needed:
      - Use edit_python_file() to make targeted changes
      - This is usually more efficient for small to medium changes
      
    - When it's MORE EFFICIENT to create a new file:
      - If changes would require replacing almost the entire file
      - If explaining the edits would require more tokens than a new file
      - If creating a brand new file results in a cleaner, smaller response
      
    Remember: The goal is to minimize token usage while maintaining context.
    Choose the approach that results in the smallest, most efficient output.
    
    This function executes standard Python code with access to imported modules and packages.
    The code is saved to a named file in the session directory and executed in a subprocess 
    using the same Python interpreter. All available secrets are automatically loaded as 
    environment variables.
    
    If you provide an empty code string and the file already exists, it will execute the 
    existing file without overwriting it. This is useful for running previously edited files.
    
    USAGE GUIDE:
    1. Use list_installed_packages() first to check available packages
    2. Provide a descriptive file_name that reflects the purpose of your code
    3. Write standard Python code including imports, functions, and print statements
    4. All output from print() statements will be returned to the conversation
    5. Always include proper error handling with try/except blocks
    6. Clean up any resources (files, connections) your code creates

    FILE NAMING:
    - Always provide a descriptive filename that reflects what the code does
    - Examples: "data_analysis.py", "api_fetch.py", "report_generation.py"
    - Files are saved in the session directory for later reference or modification

    EXAMPLES:
    ```python
    # Basic operations
    import os
    print(f"Current directory: {os.getcwd()}")

    # Using subprocess
    import subprocess
    result = subprocess.run(["ls", "-la"], capture_output=True, text=True)
    print(result.stdout)

    # Data processing
    import json
    data = {"name": "John", "age": 30}
    print(json.dumps(data, indent=2))
    
    # Using temporary files
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write("Hello World".encode('utf-8'))
    
    try:
        with open(tmp_path, 'r') as f:
            print(f.read())
    finally:
        os.unlink(tmp_path)  # Always clean up
    ```

    SECRET MANAGEMENT:
    - Use nash_secrets() to see available API keys/credentials
    - Access secrets in your code with: os.environ.get('SECRET_NAME')
    - Secrets are loaded from: ~/Library/Application Support/Nash/secrets.json

    IMPLEMENTATION DETAILS:
    - Code is saved to a file in the session directory with the provided name
    - File is executed as a subprocess with the system Python interpreter
    - Files are preserved in the session directory for reference and reuse
    - All secrets are passed as environment variables to the subprocess
    - All stdout output is captured and returned

    WEB AUTOMATION NOTE:
    For interactive web automation, browser-based scraping of dynamic sites, 
    or any tasks requiring browser interactions (clicking, form filling, etc.),
    use the operate_browser tool instead of writing custom automation code.
    
    SECURITY CONSIDERATIONS:
    - Never write code that could harm the user's system
    - Avoid creating persistent files; use tempfile module when needed
    - Don't leak or expose secret values in output
    - Avoid making unauthorized network requests
    - Do not attempt to bypass system security controls
    - When scraping websites, respect robots.txt and rate limits

    BEST PRACTICES:
    - Keep Python code focused on data retrieval, computation, and transformations
    - Write minimal code that extracts and formats data, letting the LLM analyze the results
    - Avoid embedding complex analysis logic in Python when the LLM can do it better
    - Return clean, structured data that the LLM can easily interpret
    - For static web content, use fetch_webpage; for dynamic sites or interactive features, use operate_browser
    
    Args:
        code: Python code to execute (multi-line string)
        file_name: Descriptive name for the Python file (will be saved in session directory)

    Returns:
        Captured stdout from code execution or detailed error message
    """
    # Log the full code being executed
    logging.info(f"Executing Python code in file '{file_name}':\n{code}")
    
    try:
        # Load secrets as environment variables
        env_vars = os.environ.copy()

        if MAC_SECRETS_PATH.exists():
            try:
                with open(MAC_SECRETS_PATH, 'r') as f:
                    secrets = json.load(f)

                # Add secrets to environment variables for subprocess
                for secret in secrets:
                    if 'key' in secret and 'value' in secret:
                        env_vars[secret['key']] = secret['value']
                
                logging.info("Loaded secrets for Python execution")
            except Exception as e:
                # Log the error but continue execution
                logging.warning(f"Error loading secrets: {str(e)}")
                print(f"Warning: Error loading secrets: {str(e)}")
        else:
            logging.info("No secrets file found")

        # Ensure file name has .py extension
        if not file_name.endswith('.py'):
            file_name = f"{file_name}.py"
            
        # Create the full file path in the session directory
        file_path = NASH_SESSION_DIR / file_name
        
        # If code is empty and file exists, use existing file
        if not code and file_path.exists():
            logging.info(f"Using existing file: {file_path}")
        else:
            # Write the code to the file
            with open(file_path, 'w') as f:
                f.write(code)
            logging.info(f"Saved Python code to: {file_path}")

        try:
            # Execute the file using the same Python interpreter
            logging.info(f"Running Python code from: {file_path}")
            try:
                proc = subprocess.Popen(
                    [sys.executable, str(file_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env_vars,
                    preexec_fn=os.setpgrp  # Make this process the group leader
                )
                
                # Add to active processes list for cleanup
                active_python_processes.append(proc)
                
                try:
                    stdout, stderr = proc.communicate()
                    result = subprocess.CompletedProcess(
                        [sys.executable, str(file_path)],
                        proc.returncode,
                        stdout,
                        stderr
                    )
                finally:
                    # Remove from active processes list
                    if proc in active_python_processes:
                        active_python_processes.remove(proc)
                
                # Return stdout if successful, or stderr if there was an error
                if result.returncode == 0:
                    logging.info(f"Python code in {file_name} executed successfully")
                    return result.stdout if result.stdout else f"Code in {file_name} executed successfully (no output)"
                else:
                    logging.warning(f"Python code execution of {file_name} failed with return code {result.returncode}")
                    
                    # Save error information to companion file
                    try:
                        error_file = file_path.with_suffix('.error')
                        with open(error_file, 'w') as f:
                            f.write(result.stderr)
                        logging.info(f"Saved error output to: {error_file}")
                    except Exception as write_err:
                        logging.error(f"Failed to write error file: {str(write_err)}")
                    
                    return f"Error in {file_name} (return code {result.returncode}):\n{result.stderr}"
            
            except subprocess.SubprocessError as sub_err:
                # Specifically handle subprocess errors
                error_msg = f"Subprocess error executing {file_name}: {str(sub_err)}"
                logging.error(error_msg)
                
                try:
                    exception_file = file_path.with_suffix('.exception')
                    with open(exception_file, 'w') as f:
                        f.write(f"SubprocessError: {str(sub_err)}\nTraceback: {traceback.format_exc()}")
                    logging.info(f"Saved exception information to: {exception_file}")
                except Exception:
                    logging.error("Failed to write exception file")
                
                return error_msg
                
            except Exception as exec_err:
                # Handle other exceptions during execution
                error_msg = f"Error executing {file_name}: {str(exec_err)}"
                logging.error(error_msg)
                logging.error(traceback.format_exc())
                
                try:
                    exception_file = file_path.with_suffix('.exception')
                    with open(exception_file, 'w') as f:
                        f.write(f"Error: {str(exec_err)}\nTraceback: {traceback.format_exc()}")
                    logging.info(f"Saved exception information to: {exception_file}")
                except Exception:
                    logging.error("Failed to write exception file")
                
                return error_msg
                
        except Exception as e:
            # Catch-all for any other exceptions in the outer try block
            logging.error(f"Unexpected error in execute_python for {file_name}: {str(e)}")
            logging.error(traceback.format_exc())
            
            try:
                if 'file_path' in locals():
                    exception_file = file_path.with_suffix('.exception')
                    with open(exception_file, 'w') as f:
                        f.write(f"Unexpected error: {str(e)}\nTraceback: {traceback.format_exc()}")
                    logging.info(f"Saved exception information to: {exception_file}")
            except Exception:
                logging.error("Failed to write exception file")
            
            # Return error message instead of raising to prevent MCP server crash
            return f"Unexpected error in {file_name}: {str(e)}\nSee logs for details."
    except Exception as e:
        logging.error(f"Python execution error: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error in {file_name}: {str(e)}\nTraceback: {traceback.format_exc()}\n\n"
