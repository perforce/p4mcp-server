![Support](https://img.shields.io/badge/Support-Community-yellow.svg)

# Perforce P4 MCP Server

Perforce P4 MCP Server is a Model Context Protocol (MCP) server that integrates with the Perforce P4 version control system. It is built on FastMCP with direct P4 Python bindings to expose safe, structured read/write tools for changelists, files, shelves, workspaces, jobs, and server metadata.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Local P4 MCP Server installation](#local-p4-mcp-server-installation)
- [MCP client configuration](#mcp-client-configuration)
- [P4 configuration](#p4-configuration)
  - [User configuration](#user-configuration)
  - [Admin configuration](#admin-configuration)
- [Available tools](#available-tools)
  - [Query tools (read operations)](#query-tools-read-operations)
  - [Modify tools (write operations)](#modify-tools-write-operations)
- [Logging and usage data](#logging-and-usage-data)
- [Troubleshooting](#troubleshooting)
- [Support](#support)
- [Contributions](#contributions)
- [License](#license)

## Features

- **Comprehensive P4 integration**: Read/write tools across files, changelists, shelves, workspaces, jobs, and server information
- **Safety first**: Read-only mode by default, ownership checks, explicit confirmation for destructive deletes.
- **Flexible toolsets**: Configure which tool categories to enable: files, changelists, shelves, workspaces, and jobs.
- **Robust logging**: Application and session logging to the `logs/` directory.
- **Optional telemetry**: Consent-gated usage statistics. Disabled by default.
- **Cross platform**: Supported on macOS and Windows with pre-built binaries.

## Prerequisites

- **P4 Server access**: Connection to a P4 Server with proper credentials
- **Authentication**: Valid P4 login (ticket-based or password)

## Local P4 MCP Server installation
<details><summary><b>Pre-built binaries (recommended)</b></summary>

Download the appropriate binary for your operating system:
- **Windows**: `binaries/win/p4-mcp-server-2025.1.0.zip`
- **macOS**: `binaries/mac/p4-mcp-server-2025.1.0.tgz`

Extract and use the executable directly. No Python installation is required.

```bash
# Windows
unzip p4-mcp-server-2025.1.0.zip
cd p4-mcp-server-2025.1.0
./p4-mcp-server.exe --help

# macOS
tar -xzf p4-mcp-server-2025.1.0.tgz
cd p4-mcp-server-2025.1.0
./p4-mcp-server --help
```

</details>

<details><summary><b>Build from source</b></summary>

Requirements:
  - Python 3.11+ (with Tkinter)

Build:
  - macOS:  <code>chmod +x build.sh &amp;&amp; ./build.sh package</code>
  - Linux:  <code>chmod +x build.sh &amp;&amp; ./build.sh package</code>
  - Windows: <code>build.bat package</code>

Output:
  - macOS: <code>p4-mcp-server-&lt;version&gt;.tgz</code>
  - Windows: <code>p4-mcp-server-&lt;version&gt;.zip</code>

</details>

## MCP client configuration

> **Note:** In all configuration examples below, if `P4CONFIG` is set, you do not need to set any environment variables in the `env` block. The server will use the configuration from the specified P4CONFIG file instead.
> <details> <summary><strong>Server configuration example</strong></summary>
>
>  ```json
>{
>   "mcpServers": {
>      "perforce-p4-mcp": {
>         "command": "/absolute/path/to/p4-mcp-server",
>         "env": {
>         },
>         "args": [
>            "--readonly", "--allow-usage"
>         ]
>      }
>    }
>}
>```
</details>

<br>
<details>
  <summary><strong>Claude Code</strong></summary>

See the [Claude Code MCP docs](https://docs.anthropic.com/en/docs/claude-code/mcp) for more information.

```json
{
  "mcpServers": {
    "perforce-p4-mcp": {
      "command": "/absolute/path/to/p4-mcp-server",
      "env": {
        "P4PORT": "ssl:perforce.example.com:1666",
        "P4USER": "your_username",
        "P4CLIENT": "your_workspace"
      },
      "args": [
        "--readonly", "--allow-usage"
      ]
    }
  }
}
```
</details>

<details>
  <summary><strong>Cursor</strong></summary>

See the [Cursor MCP documentation](https://docs.cursor.com/en/context/mcp) for more information.

```json
{
  "mcpServers": {
    "perforce-p4-mcp": {
      "command": "/absolute/path/to/p4-mcp-server",
      "env": {
        "P4PORT": "ssl:perforce.example.com:1666",
        "P4USER": "your_username",
        "P4CLIENT": "your_workspace"
      },
      "args": [
        "--readonly", "--allow-usage"
      ]
    }
  }
}
```
</details>

<details>
  <summary><strong>Eclipse</strong></summary>

See the [Eclipse MCP documentation](https://eclipse.dev/lmos/docs/arc/mcp) for more information.

```json
{
  "servers": {
    "perforce-p4-mcp": {
      "command": "/absolute/path/to/p4-mcp-server",
      "env": {
        "P4PORT": "ssl:perforce.example.com:1666",
        "P4USER": "your_username",
        "P4CLIENT": "your_workspace"
      },
      "args": [
        "--readonly", "--allow-usage"
      ]
    }
  }
}
```
</details>

<details>
  <summary><strong>IntelliJ</strong></summary>

See the [Intellij MCP documentation](https://www.jetbrains.com/help/idea/mcp-server.html) for more information.

```json
{
  "servers": {
    "perforce-p4-mcp": {
      "command": "/absolute/path/to/p4-mcp-server",
      "env": {
        "P4PORT": "ssl:perforce.example.com:1666",
        "P4USER": "your_username",
        "P4CLIENT": "your_workspace"
      },
      "args": [
        "--readonly", "--allow-usage"
      ]
    }
  }
}
```
</details>

<details><summary><strong>Kiro</strong></summary>

See the [Kiro MCP documentation](https://kiro.dev/docs/mcp/configuration/) for more information.

```json
{
  "mcpServers": {
    "perforce-p4-mcp": {
      "command": "/absolute/path/to/p4-mcp-server",
      "env": {
        "P4PORT": "ssl:perforce.example.com:1666",
        "P4USER": "your_username",
        "P4CLIENT": "your_workspace"
      },
      "args": [
        "--readonly", "--allow-usage"
      ]
    }
  }
}
```

</details>

<details><summary><strong>Rider</strong></summary>

See the [Rider MCP documentation](https://www.jetbrains.com/help/rider/MCP_Server.html) for information.

```json
{
  "mcpServers": {
    "perforce-p4-mcp": {
      "command": "/absolute/path/to/p4-mcp-server",
      "env": {
        "P4PORT": "ssl:perforce.example.com:1666",
        "P4USER": "your_username",
        "P4CLIENT": "your_workspace"
      },
      "args": [
        "--readonly", "--allow-usage"
      ]
    }
  }
}
```

</details>

<details>
  <summary><strong>VS Code</strong></summary>

See the [VS Code documentation](https://code.visualstudio.com/docs/copilot/customization/mcp-servers) for more information.
Add the following to your VS Code MCP settings:

```json
{
  "servers": {
    "perforce-p4-mcp": {
      "command": "/absolute/path/to/p4-mcp-server",
      "env": {
        "P4PORT": "ssl:perforce.example.com:1666",
        "P4USER": "your_username",
        "P4CLIENT": "your_workspace"
      },
      "args": [
        "--readonly", "--allow-usage"
      ]
    }
  }
}
```
</details>

<details>
  <summary><strong>Windsurf</strong></summary>

See the [Windsurf MCP documentation](https://docs.windsurf.com/windsurf/cascade/mcp) for more information.

```json
{
  "mcpServers": {
    "perforce-p4-mcp": {
      "command": "/absolute/path/to/p4-mcp-server",
      "env": {
        "P4PORT": "ssl:perforce.example.com:1666",
        "P4USER": "your_username",
        "P4CLIENT": "your_workspace"
      },
      "args": [
        "--readonly", "--allow-usage"
      ]
    }
  }
}
```
</details>

###  P4 environment variables
- `P4PORT` - P4 Server address. Examples: `ssl:perforce.example.com:1666`, `localhost:1666`
- `P4USER` - Your P4 username
- `P4CLIENT` - Your current P4 workspace. Optional, but recommended

### Supported arguments

- `--readonly` - Control write operations.
  - If present, uses read-only mode. Safe for exploration and testing.
  - If missing, enables write operations. Requires proper permissions on your P4 Server.

- `--allow-usage` - Allow usage statistics.
  - If present, allows anonymous usage statistics collection.
  - If missing, disables all usage statistics.

- `--toolsets` - Specify which tool categories to enable.
  - Available: `files`, `changelists`, `shelves`, `workspaces`, `jobs`
  - Default: All toolsets enabled.

### Required configurations
- Use absolute paths for the `command` field in all configurations.
- Ensure environment variables are properly set for each host.
- Different hosts may have different argument parsing. Refer to the host's documentation.



## P4 configuration

### User configuration

**Example setup**
```bash
# Windows (PowerShell)
$env:P4PORT = "ssl:perforce.example.com:1666"
$env:P4USER = "your_username"
$env:P4CLIENT = "your_workspace"
```

```bash
# macOS (Bash)
export P4PORT="ssl:perforce.example.com:1666"
export P4USER="your_username"
export P4CLIENT="your_workspace"
```


### Admin configuration
Manage access through group-level and user-level server properties.
These follow a strict order of precedence:
- User-level properties override group properties.
- Group-level properties are evaluated in the order of their sequence number (set with `-s`).
- If no property applies, MCP remains enabled unless explicitly disabled.

#### Master switch (global disable)
To disable MCP for all users:

```
p4 property -a -n mcp.enabled -v false
```


To re-enable group/user-based control, delete the global property first:

```
p4 property -d -n mcp.enabled
```

<details><summary><b>Group-based restrictions</b></summary>

To prevent access for all members of a specific group:

```
p4 property -a -n mcp.enabled -v false -g noaccessgroup
```

You can set multiple group restrictions the same way.

When a user belongs to multiple groups with conflicting settings, sequence order (-s) determines which settings apply.

Lower sequence numbers are evaluated first.

Example:
```
p4 property -a -n mcp.enabled -v false -s1 -g noaccessgroup
p4 property -a -n mcp.enabled -v true  -s2 -g accessgroup
```
In this example, `accessgroup` overrides `noaccessgroup` because it is evaluated later.
</details>

<details><summary><b>User-based restrictions</b></summary>

To block a specific user regardless of group membership:

```
p4 property -a -n mcp.enabled -v false -u noaccessuser
```


User-level properties always override group-level settings.

Example: Even if `noaccessuser` is in `accessgroup` (where MCP is enabled), the user property takes precedence and MCP is disabled.
</details>

<br><strong>Important notes </strong>

- `mcp.enabled` acts as the main switch.

- Avoid global properties (`-a` without `-u` or `-g`) unless you absolutely need to disable MCP for everyone.

## Available tools

### Query tools (read operations)

<details>
  <summary><strong><code>query_server</code></strong> - Get server information and current user details</summary>

- **Actions**: 
  - `server_info` - Get P4 version, uptime, and configuration
  - `current_user` - Get current user information and permissions
- **Use cases** - Server diagnostics, user verification, connection testing

</details>

<details>
  <summary><strong><code>query_workspaces</code></strong> - Workspace information and management</summary>

- **Actions**: 
  - `list` - List all workspaces (optionally filtered by user)
  - `get` - Get a detailed workspace specification
  - `type` - Check workspace type and configuration
  - `status` - Check workspace sync status
- **Parameters**: `workspace_name`, `user`, `max_results`
- **Use cases**: Workspace discovery, configuration review, status checking

</details>

<details>
  <summary><strong><code>query_changelists</code></strong> - Access changelist information and history</summary>

- **Actions**:
  - `get` - Get detailed changelist information (files, description, jobs)
  - `list` - List changelists with filters (status, user, workspace)
- **Parameters**: `changelist_id`, `status` (pending/submitted), `workspace_name`, `max_results`
- **Use cases**: Code review, history tracking, changelist analysis

</details>

<details>
  <summary><strong><code>query_files</code></strong> - File operations and information</summary>

- **Actions**:
  - `content` - Get file content at a specific revision
  - `history` - Get file revision history and integration records
  - `info` - Get file basic details (type, size, permissions)
  - `metadata` - Get file metadata (attributes, filesize,  etc.)
  - `diff` - Compare file versions (depot-to-depot or mixed)
  - `annotations` - Get file annotations with blame information
- **Parameters**: `file_path`, `file2` (for diff), `max_results`, `diff2` (boolean)
- **Use cases**: Code analysis, file comparison, history tracking, blame analysis

</details>

<details>
  <summary><strong><code>query_shelves</code></strong> - Shelved changelist operations and inspection</summary>

- **Actions**:
  - `list` - List shelved changes by user or globally
  - `diff` - Show differences in shelved files
  - `files` - List files in a specific shelf
- **Parameters**: `changelist_id`, `user`, `max_results`
- **Use cases**: Code review, work-in-progress tracking, collaboration

</details>

<details>
  <summary><strong><code>query_jobs</code></strong> - Job tracking and defect management</summary>

- **Actions**:
  - `list_jobs` - List jobs associated with a changelist
  - `get_job` - Get detailed job information and status
- **Parameters**: `changelist_id`, `job_id`, `max_results`
- **Use cases**: Defect tracking, requirement traceability, project management

</details>

### Modify tools (write operations)

<details>
  <summary><strong><code>modify_workspaces</code></strong> - Workspace creation and management</summary>

- **Actions** - `create`, `update`, `delete`, `switch`
- **Parameters** - `name`, `specs` (WorkspaceSpec object with View, Root, Options, etc.)
- **Requires** - Non-read only mode, appropriate permissions
- **Use cases** - Environment setup, workspace maintenance, branch switching

</details>

<details>
  <summary><strong><code>modify_changelists</code></strong> - Changelist lifecycle management</summary>

- **Actions** - `create`, `update`, `submit`, `delete`, `move_files`
- **Parameters** - `changelist_id`, `description`, `file_paths`
- **Safety** - Ownership checks, confirmation for destructive operations
- **Use cases** - Code submission, work organization, file grouping

</details>

<details>
  <summary><strong><code>modify_files</code></strong> - File system operations and version control</summary>

- **Actions** - `add`, `edit`, `delete`, `move`, `revert`, `reconcile`, `resolve`, `sync`
- **Parameters** - `file_paths`, `changelist`, `force`, `mode` (for resolve operations)
- **Resolve modes** - `auto`, `safe`, `force`, `preview`, `theirs`, `yours`
- **Use cases** - File editing, conflict resolution, workspace synchronization

</details>

<details>
  <summary><strong><code>modify_shelves</code></strong> - Shelving operations for work in progress</summary>

- **Actions** - `shelve`, `unshelve`, `update`, `delete`, `unshelve_to_changelist`
- **Parameters** - `changelist_id`, `file_paths`, `target_changelist`, `force`
- **Use cases** - Temporary storage, code sharing, backup before experiments

</details>

<details>
  <summary><strong><code>modify_jobs</code></strong> - Job and changelist integration</summary>

- **Actions** - `link_job`, `unlink_job`
- **Parameters** - `changelist_id`, `job_id`
- **Use cases** - Defect tracking integration, requirement linking

</details>

<details>
  <summary><strong><code>execute_delete</code></strong> - Execute approved delete operations</summary>

- **Parameters** - `operation_id`, `source_tool`, `user_confirmed`
- **Safety** - Requires explicit user confirmation, logs all operations
- **Supported Resources** - Changelists, workspaces, shelves
- **Use cases** - Cleanup operations, resource management

</details>
<br>

## Logging and usage data

### Logging system

**Log locations:**
- **Application log**: `logs/p4mcp.log` - Main server operations and errors
- **Session logs**: `logs/sessions/*.log` - Individual session activities are recorded only when the `--allow-usage` is specified in the server's startup arguments.


### Usage data

**Privacy-first approach:**
- **Disabled by default**: No data collection without explicit consent
- **Consent-gated**: First-run prompt for telemetry permission
- **Transparent**: Clear explanation of data collected
- **Revocable**: Easy opt-out at any time

**Data collected (if consented):**
- Tool usage frequency (anonymized)
- Error rates and types (no personal data)
- Performance metrics
- Feature adoption statistics
- P4 server version

**Data not collected:**
- File contents or names
- P4 Server details except version
- User credentials or personal information
- Specific project information

**Control:**
- Usage data is only collected if the `--allow-usage` argument is provided at startup.

## Troubleshooting

### Server startup issues
<details>
  <summary><strong>Unable to start server</strong></summary>

**Symptoms**: OS cannot find or execute the binary; error includes `ENOENT` or "No such file or directory".
<br>**Solutions**:
1. **Check the path:** Make sure the `command` field uses the correct absolute path for your OS:  
   - macOS/Linux: `/absolute/path/to/p4-mcp-server`  
   - Windows: `C:\absolute\path\to\p4-mcp-server.exe`
2. **Ensure the binary exists and is executable:**  
   - macOS/Linux:  
     ```bash
     ls -l /absolute/path/to/p4-mcp-server && chmod +x /absolute/path/to/p4-mcp-server
     ```
   - Windows:  
     ```powershell
     dir C:\absolute\path\to\p4-mcp-server.exe
     ```
3. **On Windows, ensure the binary is not blocked:**  
   - Right-click the `.exe` file, select **Properties**, and if present, click **Unblock**.

</details>

### Connection issues
<details>
  <summary><strong>Connect to server failed; check $P4PORT</strong></summary>

**Symptoms**: Cannot connect to P4 Server  
**Solutions**:
1. Verify the `P4PORT` environment variable: `echo $P4PORT` (macOS) or `echo $env:P4PORT` (Windows)
2. Test the direct connection: `p4 info`
3. Check server availability: `ping perforce.example.com`
4. Verify the port and protocol (`ssl:` prefix for SSL connections).

</details>

<details>
  <summary><strong>SSL certificate not trusted</strong></summary>

**Symptoms**: SSL trust errors when connecting  
**Solutions**:
1. Trust the server: `p4 trust -f -y`
2. Check trust status: `p4 trust -l`
3. For persistent issues, verify the SSL configuration.

</details>

### Authentication problems
<details>
  <summary><strong>User not logged in</strong></summary>

**Symptoms**: Authentication failures  
**Solutions**:
1. Log in to P4: `p4 login -a`
2. Check login status: `p4 login -s`
3. Verify the user exists: `p4 users -m 1 your_username`
4. For persistent issues, check password or use ticket-based authentication.

</details>

<details>
  <summary><strong>Password invalid</strong></summary>

**Symptoms**: Login failures  
**Solutions**:
1. Reset the password through P4 administrator.
2. Use ticket-based authentication: `p4 login -a`
3. Verify the username is correct: `p4 info`

</details>

### Workspace issues
<details>
  <summary><strong>Client unknown</strong></summary>

**Symptoms**: Workspace not found errors  
**Solutions**:
1. List the available workspaces: `p4 clients`
2. Verify the `P4CLIENT` environment variable.
3. Create a workspace if needed: `p4 client workspace_name`
4. Check the workspace ownership: `p4 client -o workspace_name`

</details>

<details>
  <summary><strong>File(s) not in client view</strong></summary>

**Symptoms**: Files are outside the workspace mapping  
**Solutions**:
1. Check the client view: `p4 client -o workspace_name`
2. Update the workspace mapping to include the required paths.
3. Use `p4 where file_path` to check the mapping.

</details>

### Permission errors
<details>
  <summary><strong>Operation not permitted</strong></summary>

**Symptoms**: Insufficient permissions for operations  
**Solutions**:
1. Check the file ownership: `p4 opened file_path`
2. Verify the user permissions: `p4 protects file_path`
3. Ensure proper group membership.
4. For admin operations, verify admin permissions.

</details>

<details>
  <summary><strong>File is opened by another user</strong></summary>

**Symptoms**: Exclusive lock conflicts  
**Solutions**:
1. Check who has the file open: `p4 opened file_path`
2. Contact the user to resolve conflicts.
3. Admin can force operations if necessary.

</details>

### Performance issues
<details>
  <summary><strong>Slow operations</strong></summary>

**Symptoms**: Long response times  
**Solutions**:
1. Use the `max_results` parameter to limit the query size.
2. Use specific file paths instead of wildcards.
3. Check network connectivity to P4.
4. Monitor server performance.

</details>

<details>
  <summary><strong>Memory issues</strong></summary>

**Symptoms**: High memory usage  
**Solutions**:
1. Reduce `max_results` for large queries.
2. Process files in batches.
3. Restart the MCP server periodically for long-running sessions.

</details>

### Tool execution
<details>
  <summary><strong>Unable to execute tools</strong></summary>

**Symptoms**: Conflict with built-in or other MCP tools
<br>**Solutions**:
1. Disable any built-in or conflicting MCP server tools in your environment or configuration.
2. Ensure the P4 MCP server tools are properly registered and enabled.
3. Restart the MCP server after applying configuration changes to load the correct tools.

</details>

<details>
  <summary><strong>Correct tools not picked up</strong></summary>

**Symptoms**: Invalid context or outdated session history
<br>**Solutions**:
1. Provide a P4-related context when writing prompts.
2. Start a new session if the existing session is old or contains conflicting prompt history.

</details>


### Common error patterns

1. **Authentication**: Ensure valid login before MCP operations.
2. **Workspace mapping**: Verify client views include target files.
3. **Permissions**: Check user and file permissions for write operations.
4. **Network**: Verify connectivity for remote P4 Servers.

### Getting help

1. **Check the logs**: Always check `logs/p4mcp.log` first.
2. **Test P4**: Ensure `p4 info` works before troubleshooting MCP.
3. **Report issues to the community**: Report issues with log excerpts and environment details.

## Support

Perforce P4 MCP Server is a community supported project and is not officially supported by Perforce
Pull requests and issues are the responsibility of the project's moderator(s); this may be a vetted individual or team with members outside of the Perforce organization.
Perforce does not officially support these projects, therefore all issues should be reported and managed via GitHub (not via Perforce's standard support process).

## Contributions

We welcome contributions to the P4 MCP Server project.


## License

This project is licensed under the [MIT License](LICENSE.txt). See the LICENSE file for details.