import json
import subprocess
import sys
import tempfile
import os
import traceback
import logging

from nash_mcp.constants import MAC_TASKS_PATH
from nash_mcp.execute.execute_command import execute_command
from nash_mcp.execute.execute_python import execute_python


def save_nash_task(name: str, task_prompt: str, scripts: list = None) -> str:
    """Save a reusable task with optional executable scripts for future use.

    This tool saves a complete set of instructions, explanations, and code that can be recalled 
    and reused later without needing to recreate the solution from scratch. Tasks can include
    predefined scripts that can be executed directly without having to rewrite the code.

    PURPOSE:
    The goal is to create a reusable solution that can be executed again later to produce
    the same result or be adapted for similar needs. Tasks serve as both documentation and
    a repository of executable scripts.
    
    WHEN TO USE:
    - When the user wants to save a workflow for future reuse
    - For operations that will be performed repeatedly
    - To create a library of executable code snippets
    - When complex processes should be preserved for later execution

    TASK TYPES:
    1. Prompt-Only Tasks:
       - For tasks leveraging AI capabilities (writing, analysis, creativity)
       - No scripts needed - the task_prompt serves as instructions for the AI
       - Ideal for content generation, creative writing, analysis requests
    
    2. Script-Based Tasks:
       - For tasks requiring data retrieval, computation, or external interactions
       - Scripts execute code to perform specific operations
       - Ideal for API interactions, data fetching, automation, and computational analysis
       - Keep scripts as minimal as possible, focusing on:
         * Data retrieval (API calls, web requests, file operations)
         * Data processing and transformations
         * Computational analysis and calculations
       - Leave non-computational analysis, reasoning, and interpretation to the LLM unless explicitly requested
       - Scripts should handle the technical operations while the LLM provides insights, explanations, and contextual understanding of the results

    SCRIPTS FEATURE:
    Tasks can include named scripts that can be executed directly:
    - Scripts can be Python code or shell commands
    - Scripts can accept arguments for customized execution
    - Scripts are stored as part of the task and can be executed with execute_task_script()
    
    SCRIPT STRUCTURE:
    Each script in the scripts list should be a dictionary with:
    - name: A unique name for the script within this task
    - type: Either "python" or "command" 
    - code: The actual code or command to execute
    - description: (Optional) Brief explanation of what the script does

    TASK PROMPT GUIDELINES:
    The task_prompt should clearly explain:
    - What the task accomplishes
    - Which scripts should be executed and in what order
    - How scripts work together in sequence when applicable
    - How output from one script might be used as input for another script
    - When to use each script and for what purpose
    - What parameters/arguments to pass to each script

    BEST PRACTICES:
    1. Use clear, descriptive task names that indicate functionality
       Good: "convert_csv_to_json", "system_health_check", "image_resize_tool"
       Bad: "task1", "code_snippet", "helper"
    
    2. Make tasks self-contained and reusable
       - Include detailed instructions in the task_prompt
       - Create scripts for executable portions of the task
       - Parameterize values that might change through script arguments
    
    3. For script creation:
       - Include all necessary imports and setup in Python scripts
       - Add error handling and input validation
       - Make scripts accept arguments for flexibility
       - Include clear comments in script code
    
    4. For multi-step tasks:
       - Create separate scripts for each major step
       - Explain the execution order in the task_prompt
       - Document how results from one script feed into another
       - Specify which script to run first and how to use its output

    IMPLEMENTATION DETAILS:
    - Each task has a unique name, a prompt, and optional scripts
    - Task storage is persistent between sessions
    
    SECURITY CONSIDERATIONS:
    - Don't include sensitive information like API keys in script code
    - Use nash_secrets() and os.environ.get() for credentials
    - Review scripts for security before saving them
    - Scripts execute with the same permissions as the MCP server

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
                with open(MAC_TASKS_PATH, 'r') as f:
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
        with open(MAC_TASKS_PATH, 'w') as f:
            json.dump(tasks, f, indent=2)
        logging.info(f"Task saved successfully: {name}")

        return f"Task '{name}' saved successfully with {script_count} scripts."
    except Exception as e:
        logging.error(f"Error saving task {name}: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error saving task: {str(e)}"


def list_nash_tasks() -> str:
    """List all saved tasks that can be recalled and reused.

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

        with open(MAC_TASKS_PATH, 'r') as f:
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

    This tool fetches the complete instructions, scripts, and explanation for a task that was
    previously saved with save_nash_task(). It returns the full task content so that it can
    be executed or adapted for current needs.

    PURPOSE:
    - Reuse previously created solutions without rewriting them
    - Access saved code templates and automation scripts
    - Retrieve complex workflows that were saved for future use
    - Build on existing solutions rather than starting from scratch

    USAGE WORKFLOW:
    1. Use list_nash_tasks() to see all available tasks
    2. Call run_nash_task(task_name) with the exact task name (case-sensitive) 
    3. Read the task prompt to understand what needs to be accomplished
    4. Accomplish the task described in the prompt by utilizing the provided scripts
    5. Run the appropriate scripts with execute_task_script() to complete the requested task

    TASKS WITH SCRIPTS:
    - Task prompts explain what needs to be done and how the scripts help accomplish it
    - Scripts are designed to perform the actions described in the task prompt
    - Choose the appropriate script based on the specific task requirements
    - Scripts can accept arguments for customized execution

    IMPLEMENTATION DETAILS:
    - Retrieves the full task content including prompt and any scripts
    - Returns appropriate error messages if the task doesn't exist
    - Task names are case-sensitive

    SECURITY CONSIDERATIONS:
    - Always review task code before execution, especially if it was created some time ago
    - Check for hardcoded values or paths that might need updating
    - Ensure the task is appropriate for the current context before running it
    - Scripts execute with the same permissions as the MCP server

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

        with open(MAC_TASKS_PATH, 'r') as f:
            tasks = json.load(f)
            logging.info(f"Loaded tasks file with {len(tasks)} tasks")

        if task_name not in tasks:
            logging.warning(f"Task '{task_name}' not found in tasks file")
            return (f"Task '{task_name}' not found. "
                    f"Use list_nash_tasks to see available tasks.")

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

    This tool runs a specific script that is stored as part of a task. Scripts can be
    either Python code or shell commands, and can accept arguments for customized execution.

    PURPOSE:
    - Execute saved scripts to accomplish the task described in the task prompt
    - Run parameterized scripts with different arguments each time
    - Reuse complex code snippets stored in the task repository
    - Execute multi-step processes through individual script execution

    USAGE WORKFLOW:
    1. Use list_nash_tasks() to see available tasks
    2. Use run_nash_task(task_name) to understand the task and view available scripts
    3. Call execute_task_script() with the task name, script name, and any arguments to complete the task
    4. Present the script output results to fulfill the task's purpose

    TASK ACCOMPLISHMENT:
    - Scripts are designed to perform the specific actions described in the task prompt
    - When a user requests a task to be run, execute the relevant script(s) to fulfill that request
    - Select the appropriate script based on what the user is trying to accomplish
    - Use script outputs to provide the information or results the user is seeking

    SCRIPT TYPES:
    - Python scripts: Full Python code executed in the same way as execute_python()
    - Command scripts: Shell commands executed in the same way as execute_command()

    ARGUMENTS:
    - Python scripts: Arguments are passed as a list that can be accessed in the script
    - Command scripts: Arguments are appended to the command
    
    ARGUMENT HANDLING:
    For Python scripts, arguments are made available through a variable named 'task_args':
    ```python
    # Example Python script that uses arguments
    print(f"Running with arguments: {task_args}")
    if len(task_args) > 0:
        print(f"First argument: {task_args[0]}")
    ```

    For command scripts, arguments are simply appended to the command:
    ```
    # If the script is "ls -la"
    # And args is ["/tmp"]
    # The executed command will be "ls -la /tmp"
    ```

    IMPLEMENTATION DETAILS:
    - Automatically determines script type and executes with appropriate runner
    - Returns detailed error messages if the task or script doesn't exist
    - Script names are case-sensitive
    - Scripts execute with the same permissions as the MCP server

    SECURITY CONSIDERATIONS:
    - Always review scripts before execution
    - Be careful with user-supplied arguments that could modify script behavior
    - Scripts have full access to the system just like execute_python/execute_command
    - Never use untrusted arguments with shell commands (risk of command injection)

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

        with open(MAC_TASKS_PATH, 'r') as f:
            tasks = json.load(f)
            logging.info(f"Loaded tasks file with {len(tasks)} tasks")

        if task_name not in tasks:
            logging.warning(f"Task '{task_name}' not found in tasks file")
            return (f"Task '{task_name}' not found. "
                    f"Use list_nash_tasks to see available tasks.")

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
            logging.warning(f"Script '{script_name}' not found in task '{task_name}'. Available: {', '.join(script_names)}")
            return (f"Script '{script_name}' not found in task '{task_name}'. "
                    f"Available scripts: {', '.join(script_names)}")
        
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
            
            # For Python, we need to inject the args into the code
            # Create a wrapper that defines task_args
            wrapped_code = f"task_args = {repr(args)}\n\n{script_code}"
            result = execute_python(wrapped_code)
            logging.info(f"Python script '{script_name}' execution completed")
            return result
            
        elif script_type == "command":
            # For command, we append args to the command string
            full_command = script_code
            if args:
                # Add space and join arguments with spaces
                arg_str = ' '.join(str(arg) for arg in args)
                full_command = f"{script_code} {arg_str}"
            
            logging.info(f"Executing command script '{script_name}'")
            logging.info(f"Command script code: {script_code}")
            result = execute_command(full_command)
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
            
        with open(MAC_TASKS_PATH, 'r') as f:
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
        with open(MAC_TASKS_PATH, 'r') as f:
            tasks = json.load(f)
        
        if name not in tasks:
            return f"Task '{name}' not found. Use list_nash_tasks() to see available tasks."
        
        # Remove the task
        del tasks[name]
        
        # Save the updated tasks
        with open(MAC_TASKS_PATH, 'w') as f:
            json.dump(tasks, f, indent=2)
        
        return f"Task '{name}' deleted successfully."
    except Exception as e:
        return f"Error deleting task: {str(e)}"
