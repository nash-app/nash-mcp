import json
import os
import subprocess
import sys
import tempfile
import traceback
import logging
from pathlib import Path

from nash_mcp.constants import MAC_SECRETS_PATH


def execute_python(code: str) -> str:
    """Execute arbitrary Python code and return the result.

    This function executes standard Python code with access to imported modules and packages.
    The code is written to a temporary file and executed in a subprocess using the same Python
    interpreter. All available secrets are automatically loaded as environment variables.
    
    USAGE GUIDE:
    1. Use list_installed_packages() first to check available packages
    2. Write standard Python code including imports, functions, and print statements
    3. All output from print() statements will be returned to the conversation
    4. Always include proper error handling with try/except blocks
    5. Clean up any resources (files, connections) your code creates

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
    - Code is written to a temporary Python file
    - File is executed as a subprocess with the system Python interpreter
    - Temporary file is automatically deleted after execution
    - All secrets are passed as environment variables to the subprocess
    - All stdout output is captured and returned

    SECURITY CONSIDERATIONS:
    - Never write code that could harm the user's system
    - Avoid creating persistent files; use tempfile module when needed
    - Don't leak or expose secret values in output
    - Avoid making unauthorized network requests
    - Do not attempt to bypass system security controls

    BEST PRACTICES:
    - Keep Python code focused on data retrieval, computation, and transformations
    - Write minimal code that extracts and formats data, letting the LLM analyze the results
    - Avoid embedding complex analysis logic in Python when the LLM can do it better
    - Return clean, structured data that the LLM can easily interpret
    
    Args:
        code: Python code to execute (multi-line string)

    Returns:
        Captured stdout from code execution or detailed error message
    """
    # Log the full code being executed
    logging.info(f"Executing Python code:\n{code}")
    
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

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
            temp_path = temp.name
            # Write the code to the file
            temp.write(code.encode('utf-8'))
            logging.info(f"Created temporary Python file")

        try:
            # Execute the file using the same Python interpreter
            logging.info("Running Python code")
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                env=env_vars
            )

            # Remove the temp file
            os.unlink(temp_path)
            logging.info("Removed temporary Python file")

            # Return stdout if successful, or stderr if there was an error
            if result.returncode == 0:
                logging.info("Python code executed successfully")
                return result.stdout if result.stdout else "Code executed successfully (no output)"
            else:
                logging.warning(f"Python code execution failed with return code {result.returncode}")
                return f"Error (return code {result.returncode}):\n{result.stderr}"
        except Exception as e:
            # Make sure to clean up the temp file if there's an exception
            logging.error(f"Exception during Python execution: {str(e)}")
            try:
                os.unlink(temp_path)
                logging.info("Cleaned up temporary file after exception")
            except Exception:
                pass
            raise e
    except Exception as e:
        logging.error(f"Python execution error: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error: {str(e)}\nTraceback: {traceback.format_exc()}\n\n"
