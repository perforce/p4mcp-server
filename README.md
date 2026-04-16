
<p align="center">
  <img src="./icons/logo-p4mcp-reg.svg" alt="Perforce P4 MCP Server" width="480" />
</p><br>


<div align="center">

![Support](https://img.shields.io/badge/Support-Community-yellow.svg)

![GitHub release](https://img.shields.io/github/v/release/perforce/p4mcp-server?color=blue)

<h1>Perforce P4 MCP Server</h1>

<p>
  <strong>Perforce P4 MCP Server is a Model Context Protocol (MCP) server that integrates with the Perforce P4 version control system. It is built on FastMCP with direct P4 Python bindings to expose safe, structured read/write tools for changelists, files, shelves, workspaces, jobs, reviews, and server metadata.</strong>
</p>

<nav aria-label="Quick navigation">
  <p align="center">
    <a href="#features">Features</a> ·
    <a href="#prerequisites">Prerequisites</a> ·
    <a href="#system-requirements">System Requirements</a> ·
    <a href="#local-p4-mcp-server-installation">Install</a> ·
    <a href="#mcp-client-configuration">Client Configurations</a> ·
    <a href="#p4-configuration">P4 Configurations</a> ·
    <a href="#available-tools">Tools</a> 
  </p>
   <p align="center">
    <a href="#logging-and-usage-data">Logging</a> ·
    <a href="#troubleshooting">Troubleshoot</a> ·
    <a href="#support">Support</a> ·
    <a href="#contributions">Contributions</a> ·
    <a href="#license">License</a>
  </p>
</nav>
</div>

## Features

- **Comprehensive P4 integration**: Read/write tools across files, changelists, shelves, workspaces, jobs, reviews, and server information
- **Code review workflows**: P4 Code Review support for review discovery, voting, state transitions, commenting, and participant management
- **Safety first**: Read-only mode by default, ownership checks, explicit confirmation for destructive deletes.
- **Flexible toolsets**: Configure which tool categories to enable: files, changelists, shelves, workspaces, jobs and reviews.
- **Robust logging**: Application and session logging to the `logs/` directory.
- **Optional telemetry**: Consent-gated usage statistics. Disabled by default.
- **Cross platform**: Supported on macOS and Windows with pre-built binaries.

## Prerequisites

- **P4 Server access**: Connection to a P4 Server with proper credentials
- **Authentication**: Valid P4 login (ticket-based or password)

## System Requirements

| Component | Supported Versions |
|-----------|-------------------|
| **Operating Systems** | Windows 10+<br>macOS 12+<br>Ubuntu 20.04+ |
| **Perforce P4 Server** | 2025.2 *(earlier versions untested)* |
| **Python** | 3.11+ *(required only for building from source)* |

## Local P4 MCP Server installation
<details><summary><b>Pre-built binaries (recommended)</b></summary>

Download the appropriate binary for your operating system:
- **macOS**: [p4-mcp-server-mac.zip](https://github.com/perforce/p4mcp-server/releases/latest/download/p4-mcp-server-mac.zip)
- **Windows**: [p4-mcp-server-win.zip](https://github.com/perforce/p4mcp-server/releases/latest/download/p4-mcp-server-win.zip)

Extract and use the executable directly. No Python installation is required.

```bash
# Windows
unzip p4-mcp-server-2025.2.0.zip
cd p4-mcp-server-2025.2.0
./p4-mcp-server.exe --help

# macOS
tar -xzf p4-mcp-server-2025.2.0.tgz
cd p4-mcp-server-2025.2.0
./p4-mcp-server --help
```

</details>

<details><summary><b>Install via uvx or pip</b></summary>

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/) or pip.

**uvx (no install required)**

Run directly without a permanent install:

```bash
uvx p4mcp-server --readonly
```

**pip**

```bash
pip install p4mcp-server
p4mcp-server --readonly
```

**MCP client configuration**

```json
{
  "mcpServers": {
    "perforce-p4-mcp": {
      "command": "uvx",
      "args": [
        "p4mcp-server",
        "--readonly"
      ],
      "env": {
        "P4PORT": "ssl:perforce.example.com:1666",
        "P4USER": "your_username",
        "P4CLIENT": "your_workspace"
      }
    }
  }
}
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

<details><summary><b>Run from Docker</b></summary>

Run the P4 MCP Server from a Docker container with STDIO transport, allowing MCP clients to manage the container lifecycle.

> **Note:** Docker-based execution is currently supported on macOS and Linux only.

**Prerequisites**

- Docker installed and running
- Valid P4 credentials and access to a P4 server

**Build the Docker Image**

```bash
cd /path/to/p4mcp-server
docker build -t p4-mcp-server .
```

**Configure MCP Client**

Add the following to your `mcp.json`:

```json
{
    "servers": {
        "perforce-p4mcp-docker": {
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "--hostname", "your-hostname",
                "-e", "P4PORT=ssl:perforce.example.com:1666",
                "-e", "P4USER=your_username",
                "-e", "P4CLIENT=your_workspace",
                "-v", "/Users/your_username/.p4tickets:/home/mcpuser/.p4tickets:ro",
                "p4-mcp-server"
            ]
        }
    }
}
```

**Configuration Options**

| Flag | Description |
|------|-------------|
| `-i` | Interactive mode (required for STDIO) |
| `--rm` | Remove container when stopped |
| `--hostname` | Match workspace host restriction |
| `-e P4PORT` | P4 server address |
| `-e P4USER` | P4 username |
| `-e P4CLIENT` | Workspace name |
| `-v` | Mount P4 tickets file |

**Authentication**

Using P4 tickets:
```bash
# macOS/Linux
-v /Users/your_username/.p4tickets:/home/mcpuser/.p4tickets:ro
```

> **Note:** Use the full path to your tickets file (not `~`). After running `p4 login`, restart the MCP server to pick up the new ticket.

Using a password:
```bash
-e P4PASSWD="your_password"
```

**Workspace Host Restrictions**

> ⚠️ **Important:** Docker containers have their own hostname, which differs from your local machine. If your P4 workspace is restricted to a specific host, operations like `sync` will fail.

To resolve this, set the container hostname to match your workspace's host restriction:

```bash
--hostname your-hostname
```

To find your workspace host name:
```bash
# macOS/Linux
p4 client -o your_workspace | grep "^Host:"
```

**Mounting Client Root for Write Operations**

> ⚠️ **Important:** By default, the Docker container cannot access your local workspace files. For write operations like `sync`, `submit`, or `reconcile`, you must mount your client root directory into the container at the **same path**.

Add a volume mount for your client root:
```bash
-v /path/to/your/client/root:/path/to/your/client/root
```

Example configuration with client root mounted:
```json
{
    "servers": {
        "perforce-p4mcp-docker": {
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "--hostname", "your-hostname",
                "-e", "P4PORT=ssl:perforce.example.com:1666",
                "-e", "P4USER=your_username",
                "-e", "P4CLIENT=your_workspace",
                "-v", "/Users/your_username/.p4tickets:/home/mcpuser/.p4tickets",
                "-v", "/path/to/client/root:/path/to/client/root",
                "p4-mcp-server"
            ]
        }
    }
}
```

To find your client root:
```bash
p4 client -o your_workspace | grep "^Root:"
```

> **Note:** The mount path inside the container must match the client root path exactly, as P4 tracks files by their absolute paths.

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
  <summary><strong>JetBrains IDEs (IntelliJ IDEA, Rider, PyCharm, etc.)</strong></summary>
 
See the [JetBrains AI Assistant VCS Integration documentation](https://www.jetbrains.com/help/ai-assistant/ai-in-vcs-integration.html#configure-a-perforce-mcp-server) for detailed configuration steps.

</details>

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
  - Available: `files`, `changelists`, `shelves`, `workspaces`, `jobs`, `reviews`
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

<details>
  <summary><strong><code>query_reviews</code></strong> - Review discovery, details, and activity</summary>

- **Actions**: 
  - `list` - List all reviews with optional filtering
  - `dashboard` - Get current user's review dashboard (my reviews, needs attention)
  - `get` - Get detailed review information
  - `transitions` - Get available state transitions for a review
  - `files_readby` - Get files read status by users
  - `files` - Get files in a review (with optional version range)
  - `activity` - Get review activity history
  - `comments` - Get comments on a review
- **Parameters**: 
  - `review_id` - Review ID (required for get, transitions, files_readby, files, comments, activity)
  - `review_fields` - Comma-separated fields to return (e.g., "id,description,author,state")
  - `comments_fields` - Fields for comments (default: "id,body,user,time")
  - `up_voters` - List of up voters for transitions
  - `from_version`, `to_version` - Version range for files action
  - `max_results` - Maximum results (default: 10)
- **Use cases**: Code review discovery, review status tracking, comment retrieval, review activity monitoring

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
  <summary><strong><code>modify_reviews</code></strong> - Review creation, transitions, participants, and comments</summary>

- **Actions**: 
  - `create` - Create a new review from a changelist
  - `refresh_projects` - Refresh project associations
  - `vote` - Vote on a review (up, down, clear)
  - `transition` - Change review state (needsRevision, needsReview, approved, committed, rejected, archived)
  - `append_participants` - Add reviewers/groups to a review
  - `replace_participants` - Replace all participants
  - `delete_participants` - Remove participants from a review
  - `add_comment` - Add a comment to a review
  - `reply_comment` - Reply to an existing comment
  - `append_change` - Add a changelist to an existing review
  - `replace_with_change` - Replace review content with a changelist
  - `join` - Join a review as a participant
  - `leave` - Leave a review
  - `archive_inactive` - Archive inactive reviews
  - `mark_comment_read` / `mark_comment_unread` - Mark individual comment read status
  - `mark_all_comments_read` / `mark_all_comments_unread` - Mark all comments read status
  - `update_author` - Change the review author
  - `update_description` - Update review description
  - `obliterate` - Permanently delete a review
- **Parameters**: 
  - `review_id` - Review ID (required for most actions)
  - `change_id` - Changelist ID (required for create, append_change, replace_with_change)
  - `description` - Review description
  - `reviewers`, `required_reviewers` - Lists of reviewer usernames
  - `reviewer_groups` - Reviewer groups with requirements
  - `vote_value` - Vote value: `up`, `down`, `clear`
  - `version` - Review version for voting
  - `transition` - Target state: `needsRevision`, `needsReview`, `approved`, `committed`, `approved:commit`, `rejected`, `archived`
  - `jobs`, `fix_status`, `cleanup` - Job linking and cleanup options for transitions
  - `users`, `groups` - Structured participant data for append/replace/delete
  - `body` - Comment body text
  - `task_state` - Comment task state: `open`, `comment`
  - `notify` - Notification mode: `immediate`, `delayed`
  - `comment_id` - Comment ID for replies or marking read/unread
  - `context` - Comment context (file, line numbers, content, version)
  - `not_updated_since`, `max_reviews` - Filters for archive_inactive
  - `new_author`, `new_description` - Values for update actions
- **Use cases**: Code review workflow, review state management, collaborative commenting, participant management, review cleanup

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

Perforce P4 MCP Server is a community supported project and is not officially supported by Perforce.
Pull requests and issues are the responsibility of the project's moderator(s); this may be a vetted individual or team with members outside of the Perforce organization.
Perforce does not officially support these projects, therefore all issues should be reported and managed via GitHub (not via Perforce's standard support process).

## Contributions

We welcome contributions to the P4 MCP Server project.


## License
This project is licensed under the MIT License. See [LICENSE](LICENSE.txt) for details.

### Third-Party Notices
This project includes third-party components. Their licenses and attributions are listed in [THIRD-PARTY-NOTICES](THIRD-PARTY-NOTICES.txt).