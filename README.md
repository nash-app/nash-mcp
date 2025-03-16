# Nash MCP Server

Nash MCP (a Model Context Protocol (MCP) server) enables seamless execution of commands, Python code, web content fetching, and reusable task management.

## Requirements

- Python 3.11+
- Poetry package manager (recommended)

## Installation

```bash
git clone https://github.com/nash-run/nash-mcp.git
cd nash-mcp
poetry install
```

## Features

- **Command Execution**: Run shell commands with error handling
- **Python Execution**: Execute Python code with error handling
- **Secure Credentials**: Store and access API keys without exposing sensitive data to the LLM
- **Web Content Access**: Fetch and parse webpage content for analysis
- **Task Repository**: Save and organize reusable workflows and scripts

## Tools

### Execute Module

- **execute_command**: Run shell commands with proper error handling and output capture
- **list_session_files**: List all Python files in the current session (ALWAYS USE THIS FIRST before creating new files)
- **get_file_content**: Retrieve file contents for reviewing and editing existing code
- **edit_python_file**: Make targeted edits to existing Python files using exact string pattern matching (PREFERRED METHOD)
- **execute_python**: Execute Python code snippets with full access to installed packages (use only for new files)
- **list_installed_packages**: Get information about available Python packages

### Web Interaction

- **fetch_webpage**: Retrieve and convert webpage content to readable text format

### Secrets Management

- **nash_secrets**: Access stored API keys and credentials securely. Accessible via environment variables in scripts.

### Task Management

- **save_nash_task**: Create reusable tasks with embedded scripts
- **list_nash_tasks**: View all available saved tasks
- **run_nash_task**: Retrieve and display a previously saved task
- **execute_task_script**: Run a specific script from a saved task
- **view_task_details**: See complete details of a task, including script code
- **delete_nash_task**: Remove tasks that are no longer needed

## Running

This is the command to use for MCP config files

```bash
/path/to/this/repo/.venv/bin/mcp run /path/to/this/repo/src/nash_mcp/server.py
```

As an example, if you were to use this MCP with Claude Desktop, you would change your `~/Library/Application Support/Claude/claude_desktop_config.json` to:

```json
{
  "mcpServers": {
    "Nash": {
      "command": "/Users/john-nash/code/nash-mcp/.venv/bin/mcp",
      "args": ["run", "/Users/john-nash/code/nash-mcp/src/nash_mcp/server.py"]
    }
  }
}
```

### Environment Variables

Nash MCP requires environment variables to specify all data file paths. Create a `.env` file in the root directory with the following variables:

```
# Required environment variables
NASH_SECRETS_PATH=/path/to/secrets.json
NASH_TASKS_PATH=/path/to/tasks.json
NASH_LOGS_PATH=/path/to/logs/directory
NASH_SESSIONS_PATH=/path/to/sessions/directory
```

There are no default values - all paths must be explicitly configured.

### Session Management

The Nash MCP server creates a unique session directory for each server instance. This session directory stores:

- Python scripts executed during the session
- Backup files of edited scripts
- Error logs and exception information

This persistent storage enables powerful workflows:

1. Scripts are saved with descriptive names for easy reference
2. Previous scripts can be viewed and modified instead of rewritten
3. Errors are captured in companion files for debugging

### Mandatory Workflow

⚠️ MANDATORY PRE-CODING CHECKLIST - COMPLETE BEFORE WRITING ANY CODE: ⚠️

```
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
```

### File Editing Best Practices

When working with Nash MCP, balance efficiency and context preservation:

1. **Always check for existing files** before creating new ones using `list_session_files()`
2. **Prioritize editing** with `edit_python_file()` for minor to moderate changes
3. **Consider creating new files** when:
   - It would be more token-efficient than explaining complex edits
   - You would need to replace almost the entire file
   - The task involves completely new functionality
   - Creating a new file would result in a cleaner, smaller response

The golden rule is to **minimize token usage** while maintaining context and code history.

This approach preserves script history, maintains context, and makes incremental development more efficient. The editing workflow follows this pattern:

1. First, check available resources → `list_installed_packages()` and `nash_secrets()`
2. List all existing files → `list_session_files()`
3. Check content of relevant files → `get_file_content("file_name.py")`
4. Make changes to existing file → `edit_python_file("file_name.py", old_content, new_content)`
5. Run the modified file → `execute_python("", "file_name.py")` (empty code string to run without modifying)
6. Only create new files when nothing similar exists → `execute_python(new_code, "new_file.py")`

### Common Mistakes to Avoid

1. Creating a new file when a small edit would be more token-efficient
2. Making complex edits when creating a new file would be more token-efficient
3. Trying to use packages that aren't installed
4. Writing code that requires API keys you don't have
5. Rewriting functionality that already exists
6. Not considering token efficiency in your approach

### Token Efficiency Guidelines

When deciding whether to edit or create a new file, consider which approach will use fewer tokens:

- **Edit when**: Changes are small to moderate, localized to specific sections, and easy to describe
- **Create new when**: Changes would replace most of the file, edits would be complex to explain, or a completely new approach is needed

Always aim to produce the smallest, most efficient output that accomplishes the task while maintaining clarity and context.

## Security Considerations

- Commands and scripts run with the same permissions as the MCP server
- API keys and credentials are stored locally and loaded as environment variables
- Always review scripts before execution, especially when working with sensitive data

## Development

### Logs

Detailed timestamped logs of all operations and tool executions are emitted by the server. These logs are stored in the directory specified by the `NASH_LOGS_PATH` environment variable.

### Testing

```bash
poetry run pytest
```

With coverage

```bash
poetry run pytest --cov=nash_mcp
```

## License

MIT
