---
name: p4-workspace-setup
description: P4 workspace setup and management — create, configure, sync, and switch workspaces via P4 MCP tools. Use when: creating workspaces, configuring client specs, syncing files, switching workspaces, or checking workspace status in P4.
---

# Workspace Setup & Management

Use the `query_workspaces` and `modify_workspaces` tools to manage P4 client workspaces.

## Querying Workspaces

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `list` | List workspaces with filters | `user`, `max_results` |
| `get` | Get full workspace spec | `workspace_name` |
| `type` | Check if workspace is stream or classic | `workspace_name` |
| `status` | Get workspace sync status | `workspace_name` |

## Modifying Workspaces

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `create` | Create a new workspace | `name`, `specs` |
| `update` | Update workspace spec fields | `name`, `specs` |
| `delete` | Delete a workspace (requires approval) | `name` |
| `switch` | Switch active workspace | `name` |

## Common Workflows

### Create a stream workspace

1. `query_streams` → `list` to find available streams
2. `modify_workspaces` → `create` with `specs` containing the stream depot path
3. `modify_files` → `sync` to populate the workspace

### Create a classic workspace

1. `modify_workspaces` → `create` with `specs` containing view mappings (depot-to-local paths)
2. `modify_files` → `sync` to populate the workspace

### Check workspace state

1. `query_workspaces` → `get` to see the current spec
2. `query_workspaces` → `type` to check if it's stream-bound or classic
3. `query_workspaces` → `status` to see sync state (have vs head revisions)

### Switch between workspaces

1. `query_workspaces` → `list` to see available workspaces
2. `modify_workspaces` → `switch` to set the active workspace

## Best Practices

- Use stream workspaces when working with P4 streams — they auto-configure the view mapping from the stream spec.
- Set the workspace `root` to a directory that exists and is writable.
- Use `query_workspaces` → `status` to check for out-of-date files before starting work.
- Delete workspaces only when you're sure no pending changelists reference them.
- Each workspace must have a unique name on the P4 server.
