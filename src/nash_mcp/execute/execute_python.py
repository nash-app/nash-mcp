import json
import os
import subprocess
import sys
import tempfile
import traceback
import logging
import glob
from pathlib import Path

from nash_mcp.constants import MAC_SECRETS_PATH, NASH_SESSION_DIR


def execute_python(code: str, file_name: str) -> str:
    """Execute arbitrary Python code and return the result.

    This function executes standard Python code with access to imported modules and packages.
    The code is saved to a named file in the session directory and executed in a subprocess 
    using the same Python interpreter. All available secrets are automatically loaded as 
    environment variables.
    
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
        
        # Write the code to the file
        with open(file_path, 'w') as f:
            f.write(code)
        logging.info(f"Saved Python code to: {file_path}")

        try:
            # Execute the file using the same Python interpreter
            logging.info(f"Running Python code from: {file_path}")
            try:
                result = subprocess.run(
                    [sys.executable, str(file_path)],
                    capture_output=True,
                    text=True,
                    env=env_vars
                )
                
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
