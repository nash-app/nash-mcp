def nash_help() -> str:
    """
    Nash MCP User Guide: A Complete Reference

    ------------------------------------------------------------------------------
    ⚠️ CRITICAL FIRST STEPS FOR ANY TASK - MANDATORY WORKFLOW ⚠️
    
    ALWAYS begin by discovering available resources before writing ANY code:
    
    1. list_installed_packages() - Know what libraries you can use
    2. nash_secrets() - Check available credentials and API keys
    3. list_session_files() - See what code already exists
    4. get_file_content() - Review relevant existing code
    
    THEN:
    - For existing files: edit_python_file() - Make changes to existing code
    - For new functionality: execute_python() - Create new files
    
    ALWAYS edit existing files rather than creating new ones when possible.
    NEVER write code requiring packages or credentials that aren't available.
    
    Skipping these steps is the #1 cause of inefficient code development.
    ------------------------------------------------------------------------------
    
    Nash MCP is a Model Context Protocol server that gives LLMs like Claude the ability to interact
    with your computer through Python execution and shell commands. This powerful integration enables
    AI assistants to perform tasks directly on your system.
    
    CORE CAPABILITIES:
    
    1. COMMAND EXECUTION
       - execute_command(cmd: str) -> str: Run any shell command
         Example: execute_command("ls -la ~")
         Returns: Command output or detailed error information
    
    2. PYTHON EXECUTION
       - list_session_files() -> str: List all Python files in the current session
         Always use this FIRST before creating any new file
         Returns: List of available Python files with modification times
         
       - get_file_content(file_name: str) -> str: View file contents
         Example: get_file_content("data_analysis.py")
         Returns: Complete file contents for review and editing
         
       - edit_python_file(file_name: str, old_content: str, new_content: str) -> str: Edit existing files
         Example: edit_python_file("data_analysis.py", "old code to replace", "new improved code")
         Returns: Detailed diff of changes made
         Note: This should be your DEFAULT approach for modifying code
         
       - execute_python(code: str, file_name: str) -> str: Execute Python code
         Example: execute_python("import os; print(os.getcwd())", "system_info.py")
         Returns: Captured stdout or detailed error message
         WARNING: Only use for new files after checking with list_session_files()
       - list_installed_packages() -> str: Returns Python version and all installed packages
         Always check available packages before importing libraries
    
    3. WEB ACCESS
       - fetch_webpage(url: str) -> str: Retrieve and parse content from websites
         Example: fetch_webpage("https://example.com")
         Returns: Plain text content with HTML elements removed
         Note: Uses html2text to convert HTML to readable format
    
    4. SECRETS MANAGEMENT
       - nash_secrets() -> str: View available API keys and credentials
         Returns: List of available secret keys and descriptions (not values)
         Access in code: os.environ.get('SECRET_NAME')

    5. TASK MANAGEMENT
       - save_nash_task(name: str, task_prompt: str, scripts: list = None) -> str: Save instructions and reusable scripts
         Creates a reusable task with executable scripts that can be recalled later
     
       TASK TYPES:
       1. Prompt-Only Tasks: For AI capabilities (writing, creativity, analysis)
          - No scripts needed - just provide a task_prompt
          - Example: save_nash_task("weekly_email", "Write a weekly team update email...")
     
       2. Script-Based Tasks: For data retrieval, computation, and system operations
          - Include scripts for technical operations
          - Keep scripts focused on data processing, leaving interpretation to the AI
          - See DATA ANALYSIS BEST PRACTICES section for more guidance on division of labor
          - Example: save_nash_task("weather_check", "Get weather for location", scripts=[...])
   
   - list_nash_tasks() -> str: View all saved tasks and their scripts
     Shows available tasks that can be accessed and executed
   
   - run_nash_task(task_name: str) -> str: Retrieve a task and accomplish it
     For prompt-only tasks: Read and follow the instructions in the task_prompt
     For script-based tasks: Use the provided scripts to complete the requested task
   
   - execute_task_script(task_name: str, script_name: str, args: list = None) -> str: Run a saved script with arguments
     Execute scripts to accomplish the specific actions described in the task prompt
   
   - view_task_details(task_name: str) -> str: View complete details of a task including all script code
     Examine the full implementation including script code to understand how it works
   
   - delete_nash_task(name: str) -> str: Remove a saved task
     Permanently removes a task when it's no longer needed 
    
    DATA ANALYSIS BEST PRACTICES:
    
    1. Default to Minimal Code Approach
       - When analyzing data, write minimal code to extract and format the raw data
       - Allow the AI (Claude) to perform the analytical reasoning, not the Python code
       - Avoid hardcoding analytical logic, thresholds, or complex processing in scripts
    
    2. Use Python for Data Retrieval, Claude for Analysis
       - Python's role: Extract, format, and present data to Claude
       - Claude's role: Interpret patterns, identify anomalies, and provide insights
       - Remember that Claude has strong analytical capabilities that should be leveraged
    
    3. When to Use More Complex Python:
       - Only use complex Python for data transformation that Claude cannot easily do
       - Use visualization when explicitly requested
       - Don't embed business logic or domain-specific rules in Python code
    
    4. Example Workflow:
       - Use execute_python() to load and extract raw data
       - Present data in a clean, readable format
       - Have Claude analyze the presented data directly
       - Let Claude determine what's significant, concerning, or noteworthy
    
    BEST PRACTICES:
    
    1. Start Simple
       - Begin with basic commands to explore your environment
       - Use execute_command("ls -la") to see files in the current directory
       - Check Python environment with list_installed_packages()
    
    2. Always Check Available Resources
       - Verify package availability before executing code that requires external libraries
       - Use nash_secrets() to see available credentials before accessing them
    
    3. Use Temporary Files Properly
       - For operations requiring file creation, use Python's tempfile module
         Example: 
         ```python
         import tempfile
         with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
             tmp_path = tmp.name
             tmp.write("content".encode('utf-8'))
         # Use tmp_path...
         import os
         os.unlink(tmp_path)  # Clean up when done
         ```
    
    4. Leverage Task Management with Scripts
       - Create tasks with reusable scripts that can be executed directly
       - Example for saving a task with a script:
         ```python
         scripts = [
           {
             "name": "system_info",
             "type": "python", 
             "code": "import platform; print(platform.uname())",
             "description": "Displays system information"
           }
         ]
         save_nash_task("system_utilities", "A collection of system utilities", scripts)
         ```
       - Execute scripts with arguments:
         ```python
         execute_task_script("file_tools", "find_files", args=[".txt", "/tmp"])
         ```
    
    5. Minimize Artifact Creation
       - Avoid creating unnecessary files on the user's system
       - Always clean up temporary files when finished
       - Use print() in execute_python() instead of writing to files when possible
    
    6. Implement Robust Error Handling
       - Always include try/except blocks in your Python code
       - Check command return codes when executing shell commands
       - Validate user input before execution
    
    SECURITY GUIDELINES:
    
    1. Code Execution Safety
       - Never execute commands that could harm the system (rm -rf, format, etc.)
       - Avoid commands that permanently alter system configuration without user confirmation
       - Don't execute commands that consume excessive resources (fork bombs, crypto mining, etc.)
    
    2. Data Protection
       - Do not extract sensitive data from the user's system
       - Avoid accessing personal files unless specifically requested
       - Never transmit user data to external servers without explicit permission
    
    3. Network Security
       - Avoid making excessive requests to external services
    
    4. Credential Handling
       - Only use credentials for their intended purpose
       - Don't expose full credential values in output
       - Be cautious with how you use secrets in execute_python()
    
    5. Responsible Creation
       - Never create or distribute malicious code
       - Don't implement tools for unauthorized access
       - Refuse to assist with potentially harmful operations
    
    IMPLEMENTATION DETAILS:
    
    - All tools implement consistent error handling, returning user-friendly error messages
    - Task and secret data are stored persistently between sessions
    - execute_python saves code to named files in the session directory for reuse
    - Session-based storage enables viewing, editing, and running previous code
    - execute_command uses shell=True for command execution (use proper escaping)
    
    RECOMMENDED WORKFLOW FOR ALL CODING TASKS:
    
    ⚠️ THIS IS THE MANDATORY WORKFLOW TO FOLLOW FOR EVERY TASK ⚠️
    
    1. DISCOVER AVAILABLE RESOURCES:
       ```python
       # ALWAYS check available packages first
       list_installed_packages()
       
       # ALWAYS check available secrets/API keys
       nash_secrets()
       
       # ALWAYS check what files already exist
       list_session_files()
       ```
    
    2. EVALUATE EXISTING CODE:
       ```python
       # Review relevant files that might help with your task
       get_file_content("data_analysis.py")
       ```
    
    3. MODIFY EXISTING CODE (PREFERRED):
       ```python
       # Make targeted changes to existing files instead of creating new ones
       edit_python_file(
           "data_analysis.py",
           "df = pd.read_csv('data.csv')\nprint(df.head())",  # Existing code to replace
           "df = pd.read_csv('data.csv', index_col=0)\ndf = df.dropna()\nprint(df.head())"  # New improved code
       )
       ```
    
    4. TEST AND ITERATE:
       ```python
       # Run the modified file without changing its content
       execute_python("", "data_analysis.py")  # Empty string means "run without modifying"
       
       # If changes are needed, use edit_python_file() again - don't create a new file!
       ```
    
    5. CHOOSE THE MOST EFFICIENT APPROACH:
       
       For minor to moderate changes (fewer tokens):
       ```python
       # When targeted changes are smaller than rewriting the whole file
       edit_python_file("data_analysis.py", "old_code", "updated_code")
       ```
       
       For major changes (when more efficient):
       ```python
       # When it's more token-efficient to create a new file than to explain complex edits
       # Or when replacing almost the entire content of a file
       execute_python("import pandas as pd\n\ndef analyze_sales():\n    df = pd.read_csv('sales.csv')\n    return df.groupby('region').sum()", "sales_analyzer.py")
       ```
       
       The golden rule: MINIMIZE TOKEN USAGE
       - Choose the approach that produces the smallest, cleanest output
       - If edit explanations are larger than a new file, create a new file
       - If edits are smaller than a new file, modify the existing one
       
    ⚠️ COMMON MISTAKES TO AVOID ⚠️
    
    1. Creating a new file when a small edit would be more efficient
    2. Making complex edits when creating a new file would be more efficient
    3. Trying to use packages that aren't installed
    4. Writing code that requires API keys you don't have
    5. Rewriting functionality that already exists
    6. Not considering token efficiency in your approach
       
    WHEN TO EDIT vs. CREATE NEW:
    
    EDIT when it's more token-efficient:
    - Making minor to moderate changes to existing code
    - Fixing small bugs or issues in existing code
    - Adding a few new functions to existing modules
    - Making targeted changes to specific sections
    - When the edit explanation is smaller than a new file
    
    CREATE NEW when it's more token-efficient:
    - When changes would require replacing most of the file
    - When explaining the edits would take more tokens than a new file
    - When creating a completely separate utility with a different purpose
    - When explicitly asked by the user to create a new standalone file
    - When the edit would be complex and hard to explain
    
    ALWAYS consider which approach will result in:
    1. The smallest token usage
    2. The clearest explanation
    3. The most maintainable code
    
    IMPORTANT: When the user asks to "fix", "update", "modify", or "change" something,
    they typically want edits to existing files, not brand new files. Always check if
    relevant files already exist before creating a new one.
    
    For more detailed information about specific tools, examine their individual docstrings.
    
    Returns:
        This guide as a formatted string
    """
    return "Nash MCP Help displayed. See the docstring for complete usage guide."
