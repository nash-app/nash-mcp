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
- **execute_python**: Execute Python code snippets with full access to installed packages, saved to persistent files in the session directory
- **get_file_content**: Retrieve file contents for reviewing and editing existing code
- **edit_python_file**: Make targeted edits to existing Python files using exact string pattern matching
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

As an example, if you were to use this MCP with Claud Desktop, you would change your `~/Library/Application Support/Claude/claude_desktop_config.json` to:

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

### File Editing Best Practices

When working with Nash MCP, prioritize editing existing files rather than creating new ones:

1. **Always check for existing files** before creating new ones using `get_file_content()`
2. **Use pattern-based editing** with `edit_python_file()` for making changes to existing code
3. **Only create new files** when implementing entirely new functionality or when explicitly requested

This approach preserves script history, maintains context, and makes incremental development more efficient. The editing workflow follows this pattern:

1. Check if a file exists → `get_file_content("file_name.py")`
2. Make changes to existing file → `edit_python_file("file_name.py", old_content, new_content)`
3. Run the modified file → `execute_python("", "file_name.py")` (empty code string to run without modifying)

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
