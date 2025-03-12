def nash_help() -> str:
    """
    Nash MCP User Guide: A Complete Reference

    Nash MCP is a Model Context Protocol server that gives LLMs like Claude the ability to interact
    with your computer through Python execution and shell commands. This powerful integration enables
    AI assistants to perform tasks directly on your system.
    
    CORE CAPABILITIES:
    
    1. COMMAND EXECUTION
       - execute_command(cmd: str) -> str: Run any shell command
         Example: execute_command("ls -la ~")
         Returns: Command output or detailed error information
    
    2. PYTHON EXECUTION
       - execute_python(code: str, file_name: str) -> str: Execute Python code
         Example: execute_python("import os; print(os.getcwd())", "system_info.py")
         Returns: Captured stdout or detailed error message
         Note: Saves code to the session directory with the provided name
       - get_file_with_line_numbers(file_name: str) -> str: View file with line numbers
         Example: get_file_with_line_numbers("data_analysis.py")
         Returns: File contents with line numbers for easy reference
       - edit_python_file(file_name: str, edits: list) -> str: Make targeted edits to a file
         Example: edit_python_file("data_analysis.py", [{"operation": "replace", "line_start": 10, "content": "new_code"}])
         Returns: Detailed diff of changes made
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
    
    CODE EDITING WORKFLOW:
    
    IMPORTANT: ALWAYS PRIORITIZE EDITING EXISTING FILES RATHER THAN CREATING NEW ONES!
    
    Standard Workflow:
    
    1. FIRST, check if relevant files already exist:
       ```python
       get_file_content("data_analysis.py")
       ```
    
    2. If the file exists, make edits instead of creating a new one:
       ```python
       edit_python_file(
           "data_analysis.py",
           "df = pd.read_csv('data.csv')\nprint(df.head())",
           "df = pd.read_csv('data.csv', index_col=0)\ndf = df.dropna()\nprint(df.head())"
       )
       ```
    
    3. Run the modified code without changing it:
       ```python
       execute_python("", "data_analysis.py")
       ```
    
    4. Only create new files for entirely new utilities:
       ```python
       execute_python("import pandas as pd\n\ndef analyze_sales():\n    df = pd.read_csv('sales.csv')\n    return df.groupby('region').sum()", "sales_analyzer.py")
       ```
       
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
    
    IMPORTANT: When the user asks to "fix", "update", "modify", or "change" something,
    they typically want edits to existing files, not brand new files. Always check if
    relevant files already exist before creating a new one.
    
    For more detailed information about specific tools, examine their individual docstrings.
    
    Returns:
        This guide as a formatted string
    """
    return "Nash MCP Help displayed. See the docstring for complete usage guide."
