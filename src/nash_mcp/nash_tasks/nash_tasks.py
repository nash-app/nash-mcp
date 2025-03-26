import json
import traceback
import logging

from nash_mcp.constants import MAC_TASKS_PATH
from nash_mcp.execute.execute_command import execute_command
from nash_mcp.execute.execute_python import execute_python


def save_nash_task(name: str, task_prompt: str, scripts: list = None) -> str:
    """Save a reusable task with optional executable scripts for future use.

    ⚠️ REQUIRED PARAMETERS - MUST BE PROVIDED IN A SINGLE FUNCTION CALL: ⚠️

    - name: Short, descriptive name for the task (string)
    - task_prompt: Complete instructions and explanations (string)
    - scripts: Optional list of script dictionaries (list)

    CORRECT USAGE EXAMPLES:

    ```python
    # Example 1: Basic task without scripts
    save_nash_task(
        name="daily_weather_report",
        task_prompt="Create a summary of today's weather forecast for New York City."
    )

    # Example 2: Task with scripts
    save_nash_task(
        name="fetch_stock_prices",
        task_prompt="This task fetches current stock prices for specified tickers.",
        scripts=[
            {
                "name": "get_stock_data",
                "type": "python",
                "code": "import requests\nimport os\n\ndef get_stock_price(ticker):\n    print(f'Getting price for {ticker}')\n    # API call code would go here\n    return f'{ticker}: $150.00'\n\n# Use the task_args passed when this script is executed\nif task_args and len(task_args) > 0:\n    for ticker in task_args:\n        print(get_stock_price(ticker))\nelse:\n    print('No tickers provided')",
                "description": "Fetches stock prices for given ticker symbols"
            },
            {
                "name": "show_help",
                "type": "command",
                "code": "echo 'Usage: execute_task_script(\"fetch_stock_prices\", \"get_stock_data\", args=[\"AAPL\", \"MSFT\"])'",
                "description": "Displays help information about this task"
            },
            {
                "name": "get_stock_bash",
                "type": "command",
                "code": "#!/bin/bash\n\n# Check if a ticker symbol was provided\nif [ -z \"$1\" ]; then\n  echo \"Error: No ticker symbol provided\"\n  echo \"Usage: execute_task_script(\\\"fetch_stock_prices\\\", \\\"get_stock_bash\\\", args=[\\\"AAPL\\\"])\"\n  exit 1\nfi\n\n# Get the ticker symbol from the first argument\nTICKER=$1\n\n# Use curl to fetch stock data (placeholder)\necho \"Fetching stock price for $TICKER...\"\necho \"$TICKER: $150.00 (example data)\"",
                "description": "Fetches a stock price using bash with positional arguments"
            }
        ]
    )
    ```

    ❌ COMMON ERRORS - DO NOT DO THIS:

    ```python
    # ERROR: Missing required parameters
    save_nash_task()  # Will fail! Missing both name and task_prompt

    # ERROR: Missing task_prompt parameter
    save_nash_task(name="my_task")  # Will fail! Missing task_prompt

    # ERROR: Incorrect script format (scripts must be a list of dictionaries)
    save_nash_task(
        name="broken_task",
        task_prompt="This will fail",
        scripts="print('hello')"  # Wrong! Scripts must be a list of dictionaries
    )
    ```

    SCRIPT STRUCTURE:
    Each script must be a dictionary with these keys:
    - name: A unique name for the script (required)
    - type: Either "python" or "command" (required)
    - code: The actual code or command to execute (required)
    - description: Brief explanation of what the script does (optional)

    PURPOSE:
    This tool saves reusable solutions that can be executed later without
    rewriting code. Tasks serve as both documentation and a repository of executable scripts.

    TASK TYPES:
    1. Prompt-Only Tasks:
       - For tasks leveraging AI capabilities (writing, analysis, creativity)
       - No scripts needed - just provide name and task_prompt

    2. Script-Based Tasks:
       - For data retrieval, computation, or external interactions
       - Include Python code or shell commands as scripts
       - Scripts can be executed later with execute_task_script()

    BEST PRACTICES:
    - Use descriptive task names (e.g., "convert_csv_to_json", "system_health_check")
    - Make tasks self-contained and reusable
    - For Python scripts, include all necessary imports and error handling
    - For multi-step tasks, create separate scripts for each major step
    - Don't include sensitive information like API keys in script code
    - Use nash_secrets() and os.environ.get() for credentials

    Args:
        name: Short, descriptive name for the task (used to recall it later)
        task_prompt: Complete instructions and explanations for the task
        scripts: Optional list of script dictionaries containing executable code

    Returns:
        Confirmation message indicating successful save
    """
    logging.info(f"Saving task: {name}")
    script_count = len(scripts) if scripts else 0
    logging.info(f"Task contains {script_count} scripts")

    try:
        # Load existing tasks or create new dict
        tasks = {}
        if MAC_TASKS_PATH.exists():
            try:
                with open(MAC_TASKS_PATH, "r") as f:
                    tasks = json.load(f)
                logging.info(f"Loaded existing tasks file with {len(tasks)} tasks")
            except json.JSONDecodeError:
                # If file exists but is invalid JSON, start fresh
                logging.warning(f"Tasks file exists but contains invalid JSON, starting fresh")
                tasks = {}
        else:
            logging.info("Tasks file does not exist, creating new one")

        # Add or update the task with prompt and scripts
        task_data = {
            "prompt": task_prompt,
        }

        # Add scripts if provided
        if scripts:
            task_data["scripts"] = scripts

        # Check if we're updating an existing task
        if name in tasks:
            logging.info(f"Updating existing task: {name}")
        else:
            logging.info(f"Creating new task: {name}")

        tasks[name] = task_data

        # Ensure directory exists
        MAC_TASKS_PATH.parent.mkdir(parents=True, exist_ok=True)
        logging.info(f"Ensuring task directory exists: {MAC_TASKS_PATH.parent}")

        # Save the updated tasks
        with open(MAC_TASKS_PATH, "w") as f:
            json.dump(tasks, f, indent=2)
        logging.info(f"Task saved successfully: {name}")

        return f"Task '{name}' saved successfully with {script_count} scripts."
    except Exception as e:
        logging.error(f"Error saving task {name}: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error saving task: {str(e)}"


def list_nash_tasks() -> str:
    """List all saved tasks that can be recalled and reused.

    USAGE EXAMPLES:

    ```python
    # Step 1: List all available tasks
    list_nash_tasks()

    # Step 2: View details of a specific task
    run_nash_task(task_name="task_name_here")

    # Step 3: Execute a script from the task
    execute_task_script(
        task_name="task_name_here",
        script_name="script_name_here",
        args=["optional", "arguments"]
    )
    ```

    This tool shows all previously saved tasks that can be accessed with
    run_nash_task() and their available scripts. Use this to see what capabilities
    are already available without creating them from scratch.

    PURPOSE:
    - Discover previously saved automation tasks
    - Find reusable code snippets and tools
    - Avoid recreating solutions that already exist
    - Review available task names and their scripts

    USAGE WORKFLOW:
    1. Call list_nash_tasks() to see what's available
    2. Identify relevant tasks for your current needs
    3. Use run_nash_task(task_name) to retrieve a specific task's details
    4. Execute scripts with execute_task_script() or modify as needed

    IMPLEMENTATION DETAILS:
    - Shows task names and a summary of scripts if available
    - Task and script names are case-sensitive
    - Returns appropriate messages if no tasks exist

    Returns:
        A formatted list of all available tasks and their scripts
        Message indicating no tasks if none exist
    """
    try:
        if not MAC_TASKS_PATH.exists():
            return "No tasks file found. Use save_nash_task to create tasks."

        with open(MAC_TASKS_PATH, "r") as f:
            tasks = json.load(f)

        if not tasks:
            return "No tasks available."

        result = "Available tasks:\n\n"
        for task_name, task_data in tasks.items():
            scripts = task_data.get("scripts", [])
            script_count = len(scripts)

            result += f"- {task_name}"

            if script_count > 0:
                result += f" ({script_count} script{'s' if script_count > 1 else ''})"
                result += "\n  Scripts:"
                for script in scripts:
                    script_name = script.get("name", "unnamed")
                    script_type = script.get("type", "unknown")
                    result += f"\n  - {script_name} ({script_type})"
            else:
                result += " (no scripts)"

            result += "\n\n"

        result += "Use run_nash_task(task_name) to view complete task details."
        return result
    except Exception as e:
        return f"Error listing tasks: {str(e)}"


def run_nash_task(task_name: str) -> str:
    """Retrieve a previously saved task for execution.

    ⚠️ REQUIRED PARAMETER: task_name (string) ⚠️

    CORRECT USAGE:

    ```python
    # First, list available tasks
    list_nash_tasks()

    # Then, retrieve a specific task
    run_nash_task(task_name="daily_weather_report")

    # Finally, execute a script from the task
    execute_task_script(
        task_name="daily_weather_report",
        script_name="get_weather",
        args=["New York"]
    )
    ```

    This tool fetches the complete instructions, scripts, and explanation for a task that was
    previously saved with save_nash_task(). It returns the full task content so that it can
    be executed or adapted for current needs.

    USAGE WORKFLOW:
    1. Use list_nash_tasks() to see all available tasks
    2. Call run_nash_task(task_name) with the exact task name (case-sensitive)
    3. Read the task prompt to understand what needs to be accomplished
    4. Execute scripts with execute_task_script() to complete the task

    COMMON ERRORS:
    - Task not found: Check for exact spelling and case with list_nash_tasks()
    - Missing task_name parameter: Must provide the task name

    PURPOSE:
    - Reuse previously created solutions without rewriting them
    - Access saved code templates and automation scripts
    - Retrieve complex workflows for reuse

    TASKS WITH SCRIPTS:
    - Scripts are designed to perform specific actions
    - Scripts can accept arguments for customized execution
    - Multiple scripts may work together to complete complex tasks

    Args:
        task_name: The exact name of the task to retrieve (case-sensitive)

    Returns:
        The complete task information with instructions, available scripts, and explanation
        Error message if the task doesn't exist or can't be retrieved
    """
    logging.info(f"Running task: {task_name}")

    try:
        if not MAC_TASKS_PATH.exists():
            logging.warning(f"Tasks file not found at {MAC_TASKS_PATH}")
            return "No tasks file found. Use save_nash_task to create tasks."

        with open(MAC_TASKS_PATH, "r") as f:
            tasks = json.load(f)
            logging.info(f"Loaded tasks file with {len(tasks)} tasks")

        if task_name not in tasks:
            logging.warning(f"Task '{task_name}' not found in tasks file")
            return f"Task '{task_name}' not found. " f"Use list_nash_tasks to see available tasks."

        task_data = tasks[task_name]
        prompt = task_data.get("prompt", "No prompt available")
        scripts = task_data.get("scripts", [])

        logging.info(f"Retrieved task '{task_name}' with {len(scripts)} scripts")

        result = f"TASK: {task_name}\n\nPROMPT:\n{prompt}\n"

        if scripts:
            result += "\nAVAILABLE SCRIPTS:\n"
            for i, script in enumerate(scripts, 1):
                script_name = script.get("name", f"Script {i}")
                script_type = script.get("type", "unknown")
                description = script.get("description", "No description provided")

                result += f"\n{i}. {script_name} ({script_type})\n"
                result += f"   Description: {description}\n"
                result += f"   Execute with: execute_task_script('{task_name}', '{script_name}', args=[])\n"

                logging.info(f"Script available: {script_name} ({script_type})")
        else:
            result += "\nThis task has no executable scripts."
            logging.info(f"Task '{task_name}' has no scripts")

        return result

    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error reading tasks file: {str(e)}")
        return f"Error: Tasks file contains invalid JSON. {str(e)}"
    except Exception as e:
        logging.error(f"Error retrieving task '{task_name}': {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error retrieving task: {str(e)}"


def execute_task_script(task_name: str, script_name: str, args: list = None) -> str:
    """Execute a script from a previously saved task.

    ⚠️ REQUIRED PARAMETERS - MUST BE PROVIDED IN A SINGLE FUNCTION CALL: ⚠️

    - task_name: The name of the task containing the script (string)
    - script_name: The name of the script to execute (string)
    - args: Optional list of arguments to pass to the script (list)

    CORRECT USAGE EXAMPLES:

    ```python
    # Example 1: Execute script without arguments
    execute_task_script(
        task_name="daily_weather_report",
        script_name="get_default_weather"
    )

    # Example 2: Execute script with arguments
    execute_task_script(
        task_name="fetch_stock_prices",
        script_name="get_stock_data",
        args=["AAPL", "MSFT", "GOOG"]
    )
    ```

    ❌ COMMON ERRORS - DO NOT DO THIS:

    ```python
    # ERROR: Missing required parameters
    execute_task_script()  # Will fail! Missing task_name and script_name

    # ERROR: Missing script_name parameter
    execute_task_script(task_name="my_task")  # Will fail! Missing script_name

    # ERROR: Using non-existent task or script name
    execute_task_script(
        task_name="non_existent_task",  # Check list_nash_tasks() first!
        script_name="unknown_script"
    )
    ```

    USAGE WORKFLOW:
    1. Use list_nash_tasks() to see available tasks
    2. Use run_nash_task(task_name) to understand the task and view available scripts
    3. Call execute_task_script() with the task name, script name, and any arguments

    SCRIPT TYPES AND ARGUMENTS:

    - Python Scripts:
      Arguments are available in a variable named 'task_args':
      ```python
      # In your script:
      print(f"Running with arguments: {task_args}")
      if len(task_args) > 0:
          print(f"First argument: {task_args[0]}")
      ```

    - Command Scripts:
      Arguments are properly passed as positional parameters to your script:
      ```bash
      # Example command script:
      #!/bin/bash

      # Check if argument is provided
      if [ -z "$1" ]; then
        echo "Error: No argument provided"
        exit 1
      fi

      echo "First argument: $1"
      echo "Second argument: $2"
      echo "All arguments: $@"

      # With args=["hello", "world"]
      # The script will receive "hello" as $1 and "world" as $2
      ```

      EXAMPLES:
      ```python
      # Play a Spotify track using a script that expects a track ID
      execute_task_script(
          task_name="spotify_controls",
          script_name="play_track",
          args=["spotify:track:4uLU6hMCjMI75M1A2tKUQC"]
      )

      # Run a script with multiple arguments
      execute_task_script(
          task_name="file_utils",
          script_name="copy_file",
          args=["/path/to/source.txt", "/path/to/destination.txt"]
      )
      ```

    PURPOSE:
    - Execute saved scripts from the task repository
    - Run scripts with different arguments each time
    - Complete multi-step processes through individual script execution

    SECURITY NOTES:
    - Always review scripts before execution
    - Be careful with user-supplied arguments
    - Scripts have the same system access as execute_python/execute_command

    Args:
        task_name: The name of the task containing the script
        script_name: The name of the script to execute
        args: Optional list of arguments to pass to the script

    Returns:
        The output from executing the script
        Error message if the task, script, or execution fails
    """
    logging.info(f"Executing script '{script_name}' from task '{task_name}'")

    # Format args for logging
    args_str = str(args) if args else "None"
    if len(args_str) > 100:
        args_str = args_str[:100] + "..."
    logging.info(f"Script arguments: {args_str}")

    try:
        if not MAC_TASKS_PATH.exists():
            logging.warning(f"Tasks file not found at {MAC_TASKS_PATH}")
            return "No tasks file found. Use save_nash_task to create tasks first."

        with open(MAC_TASKS_PATH, "r") as f:
            tasks = json.load(f)
            logging.info(f"Loaded tasks file with {len(tasks)} tasks")

        if task_name not in tasks:
            logging.warning(f"Task '{task_name}' not found in tasks file")
            return f"Task '{task_name}' not found. " f"Use list_nash_tasks to see available tasks."

        task_data = tasks[task_name]
        scripts = task_data.get("scripts", [])

        if not scripts:
            logging.warning(f"Task '{task_name}' does not contain any scripts")
            return f"Task '{task_name}' does not contain any scripts."

        # Find the requested script
        target_script = None
        for script in scripts:
            if script.get("name") == script_name:
                target_script = script
                break

        if not target_script:
            script_names = [s.get("name", "unnamed") for s in scripts]
            logging.warning(
                f"Script '{script_name}' not found in task '{task_name}'. Available: {', '.join(script_names)}"
            )
            return (
                f"Script '{script_name}' not found in task '{task_name}'. "
                f"Available scripts: {', '.join(script_names)}"
            )

        # Get script details
        script_type = target_script.get("type", "").lower()
        script_code = target_script.get("code", "")

        logging.info(f"Found script '{script_name}' of type '{script_type}'")

        if not script_code:
            logging.warning(f"Script '{script_name}' contains no code to execute")
            return f"Script '{script_name}' contains no code to execute."

        # Prepare arguments
        args = args or []

        # Execute based on script type
        if script_type == "python":
            logging.info(f"Executing Python script '{script_name}' with {len(args)} arguments")

            # Log the full script code
            logging.info(f"Python script code:\n{script_code}")

            # For Python, we can now directly pass the args to execute_python
            # while still maintaining backward compatibility with task_args in the script
            wrapped_code = f"task_args = {repr(args)}\n\n{script_code}"
            # Create a descriptive filename that includes both task and script name
            script_filename = f"task_{task_name}_{script_name}"
            result = execute_python(wrapped_code, script_filename, args)
            logging.info(f"Python script '{script_name}' execution completed")
            return result

        elif script_type == "command":
            # For command, use execute_command directly with the script code and args
            logging.info(f"Executing command script '{script_name}' with {len(args)} arguments")
            logging.info(f"Command script code: {script_code}")

            # Pass the script code and args directly to execute_command
            # execute_command now handles script creation internally
            result = execute_command(script_code, args)

            logging.info(f"Command script '{script_name}' execution completed")
            return result

        else:
            logging.error(f"Unknown script type '{script_type}' for script '{script_name}'")
            return f"Unknown script type '{script_type}'. Supported types are 'python' and 'command'."

    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error reading tasks file: {str(e)}")
        return f"Error: Tasks file contains invalid JSON. {str(e)}"
    except Exception as e:
        logging.error(f"Error executing script '{script_name}' from task '{task_name}': {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error executing script: {str(e)}\nTraceback: {traceback.format_exc()}"


def view_task_details(task_name: str) -> str:
    """View complete details of a task including all script code.

    This tool retrieves comprehensive information about a task including its prompt
    and the full code of all its scripts. Use this to understand what scripts do
    without executing them, to learn from existing scripts, or to decide which
    scripts are appropriate for accomplishing the task.

    PURPOSE:
    - View complete task details before execution
    - Understand what all scripts in a task do before running them
    - Examine script code to understand its functionality
    - Learn how scripts in a task work together
    - Decide which scripts to execute for specific purposes

    USAGE WORKFLOW:
    1. Use list_nash_tasks() to see available tasks
    2. Call view_task_details(task_name) to get complete information about a task
    3. After reviewing, use run_nash_task() to accomplish the task or
       execute_task_script() to run specific scripts

    WHEN TO USE:
    - When you want to see the full implementation details of a task
    - When you need to understand how scripts work before running them
    - When deciding which scripts in a task to execute
    - When learning how to create your own tasks and scripts

    IMPLEMENTATION DETAILS:
    - Shows the task prompt and the complete code for all scripts
    - Task names are case-sensitive
    - Returns appropriate error messages if the task doesn't exist

    Args:
        task_name: The name of the task to view (case-sensitive)

    Returns:
        The complete task details including prompt and script code
        Error message if the task doesn't exist
    """
    logging.info(f"Viewing detailed information for task: {task_name}")

    try:
        if not MAC_TASKS_PATH.exists():
            logging.warning(f"Tasks file not found at {MAC_TASKS_PATH}")
            return "No tasks file found. Use save_nash_task to create tasks first."

        with open(MAC_TASKS_PATH, "r") as f:
            tasks = json.load(f)
            logging.info(f"Loaded tasks file with {len(tasks)} tasks")

        if task_name not in tasks:
            logging.warning(f"Task '{task_name}' not found in tasks file")
            return f"Task '{task_name}' not found. Use list_nash_tasks to see available tasks."

        task_data = tasks[task_name]
        prompt = task_data.get("prompt", "No prompt available")
        scripts = task_data.get("scripts", [])

        logging.info(f"Retrieved details for task '{task_name}' with {len(scripts)} scripts")

        result = f"TASK: {task_name}\n\nPROMPT:\n{prompt}\n"

        if scripts:
            result += "\nSCRIPTS:\n"
            for i, script in enumerate(scripts, 1):
                script_name = script.get("name", f"Script {i}")
                script_type = script.get("type", "unknown")
                description = script.get("description", "No description provided")
                code = script.get("code", "No code available")

                logging.info(f"Including code for script: {script_name} ({script_type})")

                result += f"\n{i}. {script_name} ({script_type})\n"
                result += f"   Description: {description}\n"
                result += f"   Code:\n```{script_type}\n{code}\n```\n"
                result += f"   Execute with: execute_task_script('{task_name}', '{script_name}', args=[])\n"
        else:
            result += "\nThis task has no executable scripts."
            logging.info(f"Task '{task_name}' has no scripts")

        return result

    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error reading tasks file: {str(e)}")
        return f"Error: Tasks file contains invalid JSON. {str(e)}"
    except Exception as e:
        logging.error(f"Error viewing task details for '{task_name}': {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error viewing task details: {str(e)}"


def delete_nash_task(name: str) -> str:
    """Delete a saved task from the tasks storage.

    This tool permanently removes a task from storage. Use this when a task is no longer
    needed, has been superseded by a better version, or contains outdated information.

    PURPOSE:
    - Remove obsolete or redundant tasks
    - Clean up the task list for better organization
    - Delete tasks that are no longer relevant or useful
    - Remove tasks with errors or issues before replacing them

    USAGE WORKFLOW:
    1. Use list_nash_tasks() first to see what tasks are available
    2. Call delete_nash_task(name) with the exact task name to delete it
    3. Verify deletion with list_nash_tasks() if needed

    IMPLEMENTATION DETAILS:
    - Task names are case-sensitive
    - Returns appropriate error messages if the task doesn't exist
    - The deletion is permanent and cannot be undone

    BEST PRACTICES:
    - Consider saving an updated version before deleting the old one
    - Verify the task name carefully before deletion
    - Use descriptive names for new tasks to avoid confusion

    Args:
        name: The exact name of the task to delete (case-sensitive)

    Returns:
        Confirmation message if successful
        Error message if the task doesn't exist or can't be deleted
    """
    try:
        if not MAC_TASKS_PATH.exists():
            return "No tasks file found. Nothing to delete."

        # Load existing tasks
        with open(MAC_TASKS_PATH, "r") as f:
            tasks = json.load(f)

        if name not in tasks:
            return f"Task '{name}' not found. Use list_nash_tasks() to see available tasks."

        # Remove the task
        del tasks[name]

        # Save the updated tasks
        with open(MAC_TASKS_PATH, "w") as f:
            json.dump(tasks, f, indent=2)

        return f"Task '{name}' deleted successfully."
    except Exception as e:
        return f"Error deleting task: {str(e)}"
