
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
    <a href="#deployment">Deployment</a> ·
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

- **Comprehensive P4 integration**: Read/write tools across files, changelists, shelves, workspaces, jobs, reviews, streams, and server information.
- **Code review workflows**: P4 Code Review support for review discovery, voting, state transitions, commenting, and participant management.
- **Safety first**: Read-only mode by default, ownership checks, interactive MCP elicitation (PROCEED/CANCEL) for destructive delete and obliterate operations.
- **Flexible toolsets**: Configure which tool categories to enable: server, files, changelists, shelves, workspaces, jobs, reviews, and streams.
- **Robust logging**: Application and session logging to the `logs/` directory.
- **Optional telemetry**: Consent-gated usage statistics. Disabled by default.
- **Cross platform**: Supported on macOS, Linux and Windows with pre-built binaries.

## Prerequisites

- **P4 Server access**: Connection to a P4 Server with proper credentials
- **Authentication**: Valid P4 login (ticket-based or password)

## System Requirements

| Component | Supported Versions |
|-----------|-------------------|
| **Operating Systems** | Windows 10+<br>macOS 12+<br>Linux (glibc 2.34+, e.g. Ubuntu 22.04+, Rocky Linux 9+) |
| **Perforce P4 Server** | 2025.2 *(earlier versions untested)* |
| **Python** | 3.11+ *(required only for building from source)* |

## Local P4 MCP Server Installation
<details><summary><b>Pre-built binaries (recommended)</b></summary>

Download the appropriate binary for your operating system:
- **macOS**: [p4-mcp-server-mac.zip](https://github.com/perforce/p4mcp-server/releases/latest/download/p4-mcp-server-mac.zip)
- **Windows**: [p4-mcp-server-win.zip](https://github.com/perforce/p4mcp-server/releases/latest/download/p4-mcp-server-win.zip)
- **Linux**: [p4-mcp-server-linux.zip](https://github.com/perforce/p4mcp-server/releases/latest/download/p4-mcp-server-linux.zip)

Extract and use the executable directly. No Python installation is required.

```bash
# macOS / Linux
unzip p4-mcp-server-mac.zip   # or p4-mcp-server-linux.zip
./p4-mcp-server --help
```

```powershell
# Windows
Expand-Archive p4-mcp-server-win.zip -DestinationPath .
.\p4-mcp-server.exe --help
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
  - macOS & Linux: <code>p4-mcp-server-&lt;version&gt;.tgz</code>
  - Windows: <code>p4-mcp-server-&lt;version&gt;.zip</code>

</details>

## Deployment

### STDIO-based deployment

<details><summary><b>Local</b></summary>

Run the P4 MCP Server directly on your machine using the default STDIO transport.

Add the following to your `mcp.json`:

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

> **Note:** This example shows explicit `env` values. If `P4CONFIG` is set, you can omit them and use the generic configuration example in the `MCP client configuration` section instead.

</details>

<details><summary><b>Docker</b></summary>

Run the P4 MCP Server from a Docker container with STDIO transport, allowing MCP clients to manage the container lifecycle.

> **Note:** Docker-based execution is currently supported on macOS and Linux only.

**Prerequisites**

- Docker installed and running
- Valid P4 credentials and access to a P4 server

**Pull the Docker image**

```bash
docker pull ghcr.io/perforce/p4mcp-server:latest
```

<details><summary><b>Build from source instead</b></summary>

```bash
cd /path/to/p4mcp-server
docker build -t ghcr.io/perforce/p4mcp-server .
```

</details>

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
                "ghcr.io/perforce/p4mcp-server:latest"
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
                "ghcr.io/perforce/p4mcp-server:latest"
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

### HTTP-based deployment

<details><summary><b>VM</b></summary>

Run the MCP server on a VM using the HTTP transport, allowing clients to connect over the network.

**Start the server on the VM:**

```bash
P4PORT=ssl:perforce.example.com:1666 P4USER=your_username P4PASSWD=YOUR_TICKET ./p4-mcp-server --readonly --transport http --port 8000
```

**Configure the MCP client:**

Add the following to your `mcp.json`:

```json
{
    "servers": {
        "perforce-p4-mcp": {
            "type": "http",
            "url": "http://<ip-or-hostname>:8000/mcp"
        }
    }
}
```

> **Note:** Ensure the VM's firewall allows inbound connections on the chosen port. For production use, consider placing the server behind a reverse proxy with TLS.

</details>

<details><summary><b>Docker</b></summary>

Run the MCP server in a Docker container using HTTP transport and expose the MCP endpoint over a host port.

**Start the container:**

```bash
docker run --rm -p 8000:8000 \
  -e P4PORT=ssl:perforce.example.com:1666 \
  -e P4USER=your_username \
  -e P4PASSWD=YOUR_TICKET \
  ghcr.io/perforce/p4mcp-server:latest \
  python3 -m src.main --readonly --transport http --port 8000
```

**Configure the MCP client:**

Add the following to your `mcp.json`:

```json
{
  "servers": {
    "perforce-p4-mcp": {
      "type": "http",
      "url": "http://<ip-or-hostname>:8000/mcp"
    }
  }
}
```

> **Note:** Docker supports HTTP-based deployment as well. The container image defaults to STDIO transport, so the HTTP startup command must explicitly override the default command. If you need write operations, also mount the client root and ticket file paths into the container.

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

### P4 Environment Variables
- `P4PORT` - P4 Server address. Examples: `ssl:perforce.example.com:1666`, `localhost:1666`
- `P4USER` - Your P4 username
- `P4CLIENT` - Your current P4 workspace. Optional, but recommended

### SSL/TLS environment variables
- `P4MCP_TLS_CA_MODE` - TLS certificate source mode.
  - `system` (default): use OS trust store via `truststore`. **Note:** In this mode, `truststore` overrides the `verify=` parameter — custom CA bundles set via `P4MCP_CA_BUNDLE` or `--ca-bundle` are ignored. To use a custom CA bundle, set `P4MCP_TLS_CA_MODE=certifi`.
  - `certifi`: disable `truststore` injection and use default Python TLS certificate behavior. Custom CA bundles (`P4MCP_CA_BUNDLE` / `--ca-bundle`) take effect only in this mode.
- `P4MCP_SSL_VERIFY` - Set to `false` to disable SSL verification for P4 Code Review API requests. Default: `true`. Works in both TLS modes.
- `P4MCP_CA_BUNDLE` - Path to a custom CA certificate bundle (PEM) for P4 Code Review API requests. Takes priority over `P4MCP_SSL_VERIFY`. **Requires `P4MCP_TLS_CA_MODE=certifi`** to take effect.

### Supported arguments

- `--readonly` - Control write operations.
  - If present, uses read-only mode. Safe for exploration and testing.
  - If missing, enables write operations. Requires proper permissions on your P4 Server.

- `--allow-usage` - Allow usage statistics.
  - If present, allows anonymous usage statistics collection.
  - If missing, disables all usage statistics.

- `--toolsets` - Specify which tool categories to enable.
  - Available: `files`, `changelists`, `shelves`, `workspaces`, `jobs`, `reviews`, `streams`
  - Default: All toolsets enabled.
  - `query_server` is always available regardless of the `--toolsets` setting.

- `--search-transform` - Enable search-based tool discovery to reduce token overhead.
  - `regex` — Expose a regex pattern-matching search tool. Best for targeted lookups.
  - `bm25` — Expose a natural-language relevance-ranked search tool. Best for exploratory queries.
  - `both` — Expose both search tools with distinct names (`regex_search_tools`/`regex_call_tool` and `semantic_search_tools`/`semantic_call_tool`).
  - If omitted, the full tool catalog is sent to the client (default, backward-compatible).
  - When enabled, `query_server` is always directly visible to the client.
  - **Security:** Admin permission checks (`CheckPermissionMiddleware`) and `--readonly` filtering remain fully enforced. Search transforms query the real tool catalog internally, so tools blocked by middleware or excluded by read-only mode are never discoverable or callable through the search interface.

- `--ssl-no-verify` - Disable SSL certificate verification for P4 Code Review API requests.
  - Useful for environments with self-signed or internal CA certificates.
  - Works in both `system` and `certifi` TLS modes.
  - These SSL options only affect HTTPS Swarm connections. If the Swarm URL is `http://`, they have no effect.

- `--ca-bundle <path>` - Path to a custom CA certificate bundle (PEM) for P4 Code Review API requests.
  - Use this to trust an internal CA without disabling verification entirely.
  - **Requires `P4MCP_TLS_CA_MODE=certifi`** to take effect. In the default `system` mode, `truststore` uses the OS trust store and ignores this setting.
  - If both `--ca-bundle` and `--ssl-no-verify` are provided, `--ca-bundle` takes priority (verification is performed using the specified bundle).

  > **Priority order:** `--ca-bundle` > `--ssl-no-verify` > `P4MCP_CA_BUNDLE` > `P4MCP_SSL_VERIFY` > default (`true`). CLI args take priority over environment variables.

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
# macOS/Linux (Bash)
export P4PORT="ssl:perforce.example.com:1666"
export P4USER="your_username"
export P4CLIENT="your_workspace"
```


### Admin configuration
Manage access through group-level and user-level server properties.
P4 resolves each property to a single value using two rules, applied in order:
1. **Highest sequence number wins.** The `-s` flag is the primary sort key. It applies across all scopes — a group property at `-s5` beats a user property at `-s1` or default.
2. **At the same sequence number, scope is the tiebreaker:** user > group > global. Between groups at the same sequence, the alphabetically-first group name wins.

P4 does not compare values semantically. It does not know that `false` is more restrictive than `true`. The winning property's value is returned as-is and checked by the MCP server.

If no property applies, MCP remains enabled unless explicitly disabled.

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

When a user belongs to multiple groups with conflicting settings, P4's property resolution determines which value wins.

The highest sequence number (`-s`) wins. At equal sequence numbers, the alphabetically-first group name wins.

Example:
```
p4 property -a -n mcp.enabled -v false -s1 -g noaccessgroup
p4 property -a -n mcp.enabled -v true  -s2 -g accessgroup
```
In this example, `accessgroup` wins because `-s2` is higher than `-s1`.
</details>

<details><summary><b>User-based restrictions</b></summary>

To block a specific user regardless of group membership:

```
p4 property -a -n mcp.enabled -v false -u noaccessuser
```


At the same sequence number, user-level properties override group-level and global settings (P4's scope tiebreaker).

Example: Even if `noaccessuser` is in `accessgroup` (where MCP is enabled), the user property at the same sequence takes precedence and MCP is disabled.

> **Note:** A group property at a higher `-s` value can override a user property at a lower sequence number. To ensure a user-level property always wins, give it a high `-s` value or ensure no group properties use a higher sequence.
</details>

<details><summary><b>Toolset allowlist (global)</b></summary>

Restrict which toolsets are available server-wide using `mcp.toolsets.allowed`. Only listed toolsets will be enabled; all others are blocked.

Available toolsets: `server`, `changelists`, `files`, `jobs`, `reviews`, `shelves`, `workspaces`, `streams`

Allow only changelists and files:
```
p4 property -a -n mcp.toolsets.allowed -v changelists,files
```

Remove the allowlist to restore all toolsets:
```
p4 property -d -n mcp.toolsets.allowed
```
</details>

<details><summary><b>Global read-only mode</b></summary>

Disable all write operations (modify tools) while keeping read operations (query tools) available:
```
p4 property -a -n mcp.toolsets.write -v false
```

Re-enable writes:
```
p4 property -a -n mcp.toolsets.write -v true
```

When `write=false`, all `modify_*` tools are blocked but all `query_*` tools continue to work.
</details>

<details><summary><b>Toolset enable/disable per group</b></summary>

Enable or disable individual toolsets for a specific group.

Disable a toolset for a specific group:
```
p4 property -a -n mcp.toolset.changelists.enabled -v false -g reviewers
```
Users in `reviewers` are blocked from changelists. Users in other groups (with no explicit setting) retain default access.

To restrict a toolset to only one group, disable it for every other group that should not have access:
```
p4 property -a -n mcp.toolset.files.enabled -v false -g reviewers
p4 property -a -n mcp.toolset.files.enabled -v false -g interns
# Only groups without an explicit "false" retain default access to files
```

> **Note:** All toolsets are enabled by default. Setting `enabled=true` for a group is redundant unless you are explicitly overriding a previous `false` setting. At the same sequence number, a group property overrides a global property (P4's scope tiebreaker), so a group `enabled=true` can override a global `enabled=false`. To ensure a global setting cannot be overridden, give it a high `-s` value. To isolate a toolset to specific groups, disable it for the groups you want to block.
</details>

<details><summary><b>Write control per toolset per group</b></summary>

Control write access for each toolset at the group level.

Disable writes for a specific toolset per group:
```
p4 property -a -n mcp.toolset.workspaces.write -v false -g reviewers
```
This blocks `modify_workspaces` for the group while `query_workspaces` remains accessible.
</details>

<details><summary><b>Tool-specific overrides</b></summary>

Restrict a group to specific tools within a toolset using `mcp.toolset.<name>.tools`.

Allow only `query_files` (block `modify_files`) for developers:
```
p4 property -a -n mcp.toolset.files.tools -v query_files -g developers
```

Allow both query and modify for leads:
```
p4 property -a -n mcp.toolset.reviews.tools -v query_reviews,modify_reviews -g leads
```

Tool-specific overrides can restrict access even when writes are enabled:
```
p4 property -a -n mcp.toolsets.write -v true
p4 property -a -n mcp.toolset.files.tools -v query_files -g developers
# Result: modify_files is BLOCKED — tool list restricts
```

> **Note:** Tool-specific overrides cannot bypass write restrictions. The server checks write permissions before evaluating tool lists. If `write=false` is set at any level, write tools are blocked regardless of the tool list.
</details>

<details><summary><b>Multi-group conflict resolution</b></summary>

When a user belongs to multiple groups with conflicting settings, P4 resolves each property to a single value. The MCP server does not perform its own multi-group logic — it uses whichever value P4 returns.

P4's resolution rules for a given property name:
1. **Highest `-s` (sequence number) wins.** This is the primary sort key.
2. **At the same sequence number:** user scope > group scope > global scope.
3. **Between groups at the same sequence:** the alphabetically-first group name wins.

P4 does not compare values. It picks the winning entry by position, not by content.

**Example — groups at the same sequence (default):**
```
p4 property -a -n mcp.toolset.files.enabled -v true -g developers
p4 property -a -n mcp.toolset.files.enabled -v false -g leads
# User in both groups → resolved value is "true"
# Reason: "developers" < "leads" alphabetically, so developers wins
```
Swapping the values would give `false` — `developers` still wins regardless of the value.

**Example — only one group has a setting:**
```
p4 property -a -n mcp.toolset.files.enabled -v false -g leads
# developers has no setting
# User in developers + leads → resolved value is "false"
# Reason: leads is the only group with a value, so it wins
```

**Example — write access:**
```
p4 property -a -n mcp.toolset.files.write -v false -g developers
p4 property -a -n mcp.toolset.files.write -v true -g leads
# User in both groups → resolved value is "false"
# Reason: "developers" < "leads" alphabetically, not because false is "more restrictive"
```

**Example — tool lists (no union):**
```
p4 property -a -n mcp.toolset.reviews.tools -v query_reviews -g developers
p4 property -a -n mcp.toolset.reviews.tools -v query_reviews,modify_reviews -g leads
# User in both groups → resolved value is "query_reviews"
# Reason: "developers" wins alphabetically. P4 returns one value, not a union.
```

**Example — using `-s` to control which group wins:**
```
p4 property -a -n mcp.enabled -v false -s1 -g noaccessgroup
p4 property -a -n mcp.enabled -v true  -s2 -g accessgroup
# accessgroup wins because -s2 > -s1 (highest sequence wins)
```

> **Tip:** To get predictable results with multiple groups, always use explicit `-s` values rather than relying on alphabetical group name ordering.
</details>

<details><summary><b>Disabling a specific toolset globally</b></summary>

Disable a single toolset for all users without affecting others:
```
p4 property -a -n mcp.toolset.reviews.enabled -v false
```

This blocks both `query_reviews` and `modify_reviews` for all users. Other toolsets remain unaffected.
</details>

<details><summary><b>Emergency read-only for a specific group</b></summary>

Restrict a specific group to read-only without affecting other groups:
```
p4 property -a -n mcp.toolsets.write -v false -g problematic_group
```

Users in other groups retain full write access. If a user belongs to both the restricted group and an unrestricted group, P4's property resolution determines the outcome — typically the alphabetically-first group name wins at equal sequence numbers. Use explicit `-s` values for predictable results.
</details>

<br>

#### How properties are resolved

The MCP server checks properties in this order. Each property is resolved independently by P4 using the standard resolution rules (highest `-s` wins, then user > group > global at equal sequence, then alphabetically-first group name).

| Check order | Property | MCP server behavior |
|-------------|----------|---------------------|
| 1 | `mcp.enabled` | If resolved value is `false`, block all access |
| 2 | `mcp.toolsets.write` | If resolved value is `false` and tool is a write operation, block |
| 3 | `mcp.toolsets.allowed` | If set, only listed toolsets are available |
| 4 | `mcp.toolset.<name>.enabled` | If resolved value is `false`, block the toolset |
| 5 | `mcp.toolset.<name>.write` | If resolved value is `false` and tool is a write operation, block |
| 6 | `mcp.toolset.<name>.tools` | If set, only listed tools within the toolset are available |

<br><strong>Important notes </strong>

- Each property is resolved to a single value by P4 before the MCP server sees it. P4 uses: highest sequence number (`-s`) first, then scope (user > group > global) as a tiebreaker, then alphabetical group name. The MCP server does not perform its own multi-group or multi-scope resolution.

- `mcp.enabled` acts as the main switch. When its resolved value is `false`, all access is blocked.

- At the same sequence number, a group or user property overrides a global property. To ensure a global `false` cannot be overridden, assign it a high `-s` value.

- Scope hierarchy (user > group > global) only applies as a tiebreaker at equal sequence numbers. A group property at `-s5` will beat a user property at default sequence or `-s1`.

- When a user belongs to multiple groups, the alphabetically-first group name wins (at equal `-s`). The winning value is used as-is — P4 does not compare `true` vs `false` or pick the "most restrictive" value. Use explicit `-s` values to control which group takes priority.

- Tool-specific overrides (`mcp.toolset.<name>.tools`) can further restrict access but cannot bypass write restrictions. Write checks are evaluated before tool lists.

- Property changes take effect within 60 seconds due to server-side caching, or immediately on a new MCP server connection.

- Only the value `false` (case-insensitive) disables or blocks access. Any other value (including `true`, `1`, `yes`, or invalid strings) is treated as not blocking.

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
  - `metadata` - Get file metadata (attributes, filesize, etc.)
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

<details>
  <summary><strong><code>query_streams</code></strong> - Stream hierarchy, integration status, and workspace validation</summary>

- **Actions**:
  - `list` - List streams with optional filters (path pattern, owner, type)
  - `get` - Get a detailed stream specification
  - `children` - Get child streams of a given stream
  - `parent` - Get the parent stream
  - `graph` - Get the full stream graph (parent + children)
  - `integration_status` - Get integration status between stream and parent (p4 istat)
  - `get_workspace` - Get a workspace spec bound to a stream
  - `list_workspaces` - List workspaces bound to a stream
  - `validate_file` - Validate file paths against a stream's view
  - `validate_submit` - Validate opened files for submit in a stream workspace
  - `check_resolve` - Check for pending stream spec conflicts
  - `interchanges` - List changelists awaiting integration between streams
- **Parameters**:
  - `stream_name` - Stream depot path (required for get, children, parent, graph, check_resolve, interchanges)
  - `stream_path` - Path pattern(s) for list (e.g., `["//depot/..."]`)
  - `filter` - Filter expression for list (e.g., `"Owner=alice&Type=development"`)
  - `fields` - Fields to return for list (e.g., `["Stream", "Owner", "Type"]`)
  - `workspace` - Workspace name for get_workspace, validate_file, validate_submit
  - `file_paths` - File paths for validate_file
  - `view_without_edit` - View locked stream spec without opening for edit
  - `at_change` - Retrieve historical stream spec at a changelist number
  - `both_directions` - Show integration status in both directions
  - `force_refresh` - Force istat cache refresh
  - `reverse`, `long_output`, `limit` - Options for interchanges
  - `unloaded`, `all_streams`, `viewmatch` - Filters for list
  - `max_results` - Maximum results
- **Use cases**: Stream hierarchy exploration, integration status tracking, workspace validation, view compatibility checks

</details>

### Modify tools (write operations)

<details>
  <summary><strong><code>modify_workspaces</code></strong> - Workspace creation and management</summary>

- **Actions** - `create`, `update`, `delete`, `switch`
- **Parameters** - `name`, `specs` (WorkspaceSpec object with View, Root, Options, etc.)
- **Requires** - Read-only mode disabled, appropriate permissions
- **Use cases** - Environment setup, workspace maintenance, branch switching

</details>

<details>
  <summary><strong><code>modify_changelists</code></strong> - Changelist lifecycle management</summary>

- **Actions** - `create`, `update`, `submit`, `delete`, `move_files`
- **Parameters** - `changelist_id`, `description`, `file_paths`
- **Safety** - Ownership checks, interactive PROCEED/CANCEL elicitation prompt for delete operations with item details
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
  <summary><strong><code>modify_streams</code></strong> - Stream lifecycle, spec editing, propagation, and workspace management</summary>

- **Actions**:
  - `create` - Create a new stream (mainline, development, release, task, virtual, etc.)
  - `update` - Update stream properties (name, description, options, paths, parent_view)
  - `delete` - Delete a stream
  - `edit_spec` - Open stream spec for editing (p4 stream edit)
  - `resolve_spec` - Resolve stream spec conflicts
  - `revert_spec` - Revert stream spec edits
  - `shelve_spec` - Shelve stream spec edits to a numbered changelist
  - `unshelve_spec` - Unshelve stream spec edits
  - `copy` - Copy changes between parent and child streams
  - `merge` - Merge changes between parent and child streams
  - `integrate` - Integrate changes with advanced options
  - `populate` - Populate a new stream with files (branch)
  - `switch` - Switch a workspace to a different stream
  - `create_workspace` - Create a new workspace bound to a stream
- **Parameters**:
  - `stream_name` - Stream depot path (required for create, update, delete, edit_spec, resolve_spec, revert_spec, switch)
  - `stream_type` - Stream type for create: `mainline`, `development`, `sparsedev`, `release`, `sparserel`, `task`, `virtual`
  - `parent` - Parent stream for non-mainline create
  - `name`, `description` - Stream display name and description
  - `options` - Stream options: `allsubmit/ownersubmit`, `unlocked/locked`, `toparent/notoparent`, `fromparent/nofromparent`, `mergedown/mergeany`
  - `parent_view` - Parent view treatment: `inherit` or `noinherit`
  - `paths`, `remapped`, `ignored` - Stream view mappings
  - `changelist` - Changelist for spec editing or propagation operations
  - `resolve_mode` - Resolve mode for resolve_spec: `auto`, `accept_theirs`, `accept_yours`
  - `parent_stream` - Override parent for propagation (-P flag)
  - `branch` - Branch spec for integrate/populate (-b flag)
  - `file_paths` - File paths for propagation
  - `preview` - Preview only, no changes (-n flag)
  - `force` - Force operation (-f flag)
  - `reverse` - Reverse direction (-r flag)
  - `max_files` - Limit files processed (-m flag)
  - `quiet` - Suppress informational messages (-q flag)
  - `output_base` - Show base revision with scheduled resolve (-Ob flag for merge/integrate) or list files created (-o flag for populate)
  - `virtual` - Copy using virtual stream (-v flag, copy only)
  - `schedule_branch_resolve` - Schedule branch resolves instead of automatic branching (-Rb flag, integrate only)
  - `integrate_around_deleted` - Integrate around deleted revisions (-Di flag, integrate only)
  - `skip_cherry_picked` - Skip cherry-picked revisions already integrated (-Rs flag, integrate only)
  - `source_path`, `target_path` - Source and target paths for populate
  - `workspace` - Workspace name for switch
  - `workspace_name`, `root`, `host`, `alt_roots` - Workspace creation parameters
- **Safety**: Stream existence validation, locked stream detection, bound workspace warnings, open file checks for view-affecting changes
- **Use cases**: Stream creation and management, branch propagation (merge/copy/integrate), spec conflict resolution, workspace provisioning

</details>

<br>

## Logging and Usage Data

### Logging system

**Log locations:**
- **Application log**: `logs/p4mcp.log` - Main server operations and errors
- **Session logs**: `logs/sessions/*.log` - Individual session activities are recorded only when the `--allow-usage` flag is specified in the server's startup arguments.


### Usage Data

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

### Server Startup Issues
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

### Connection Issues
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
  <summary><strong>SSL certificate not trusted (P4 connection)</strong></summary>

**Symptoms**: SSL trust errors when connecting to the P4 server
**Solutions**:
1. Trust the server: `p4 trust -f -y`
2. Check trust status: `p4 trust -l`
3. For persistent issues, verify the SSL configuration.

</details>

<details>
  <summary><strong>SSL certificate errors for P4 Code Review API (reviews)</strong></summary>

**Symptoms**: `CERTIFICATE_VERIFY_FAILED` errors when using review tools
**Solutions**:
1. **System trust store**: By default, the server uses the OS trust store via `truststore`. Ensure your corporate CA is installed in the OS certificate store.
2. **Custom CA bundle**: To use a custom CA certificate, you must **first** set `P4MCP_TLS_CA_MODE=certifi` (to disable `truststore`), then provide the CA path via `--ca-bundle /path/to/ca.pem` or `P4MCP_CA_BUNDLE`. In the default `system` mode, `truststore` overrides custom CA bundles and they are silently ignored.
3. **Disable verification**: Use `--ssl-no-verify` or set `P4MCP_SSL_VERIFY=false` (not recommended for production). This works in both TLS modes.

> **Note:** These SSL settings only apply when the Swarm URL uses HTTPS. If Swarm is configured with an `http://` URL, SSL verification is not performed and these settings have no effect.

</details>

### Authentication Problems
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
1. Reset the password through a P4 administrator.
2. Use ticket-based authentication: `p4 login -a`
3. Verify the username is correct: `p4 info`

</details>

### Workspace Issues
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

### Permission Errors
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

### Performance Issues
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

### Tool Execution
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


### Common Error Patterns

1. **Authentication**: Ensure valid login before MCP operations.
2. **Workspace mapping**: Verify client views include target files.
3. **Permissions**: Check user and file permissions for write operations.
4. **Network**: Verify connectivity for remote P4 Servers.

### Getting Help

1. **Check the logs**: Always check `logs/p4mcp.log` first.
2. **Test P4**: Ensure `p4 info` works before troubleshooting MCP.
3. **Report issues to the community**: Report issues with log excerpts and environment details.

## Support

Perforce P4 MCP Server is a community supported project and is not officially supported by Perforce.
Pull requests and issues are the responsibility of the project's moderator(s); this may be a vetted individual or team with members outside of the Perforce organization.
All issues should be reported and managed via GitHub (not via Perforce's standard support process).

## Contributions

We welcome contributions to the P4 MCP Server project.


## License
This project is licensed under the MIT License. See [LICENSE](LICENSE.txt) for details.

### Third-Party Notices
This project includes third-party components. Their licenses and attributions are listed in [THIRD-PARTY-NOTICES](THIRD-PARTY-NOTICES.txt).