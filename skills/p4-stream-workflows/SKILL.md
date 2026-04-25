---
name: p4-stream-workflows
description: P4 stream workflows — creation, branching, merging, copying, integration, switching, and spec management via P4 MCP tools. Use when: creating streams, branching, merging, copying between streams, integrating changes, switching workspaces, or managing stream specs in P4.
---

# Stream Workflows

Use the `query_streams` and `modify_streams` tools to manage P4 streams.

## Querying Streams

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `list` | List streams under a depot path | `stream_path`, `filter`, `fields`, `max_results` |
| `get` | Get a single stream spec | `stream_name` |
| `children` | List child streams | `stream_name` |
| `parent` | Get parent stream | `stream_name` |
| `graph` | Get full stream hierarchy | `stream_path` |
| `integration_status` | Check pending integrations between stream and parent | `stream_name`, `both_directions`, `force_refresh` |
| `get_workspace` | Get workspace bound to a stream | `stream_name`, `workspace` |
| `list_workspaces` | List all workspaces for a stream | `stream_name`, `user` |
| `validate_file` | Check if a file path is valid in a stream | `stream_name`, `file_paths`, `workspace` |
| `validate_submit` | Verify a changelist is ready to submit in stream context | `workspace`, `changelist` |
| `check_resolve` | Check if resolve is needed after integration | `stream_name` |
| `interchanges` | List changes not yet integrated between stream and parent | `stream_name`, `reverse`, `limit` |

## Modifying Streams

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `create` | Create a new stream | `stream_name`, `stream_type`, `parent`, `description` |
| `update` | Update stream spec fields | `stream_name`, updated fields |
| `delete` | Delete a stream (requires approval) | `stream_name` |
| `edit_spec` | Open stream spec for editing | `stream_name`, `changelist` |
| `resolve_spec` | Resolve spec conflicts | `stream_name`, `resolve_mode` |
| `revert_spec` | Revert spec changes | `stream_name` |
| `shelve_spec` | Shelve stream spec changes | `stream_name`, `changelist` |
| `unshelve_spec` | Unshelve stream spec changes | `stream_name`, `target_changelist` |

## Stream Propagation (Branching & Merging)

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `copy` | Copy changes between parent/child streams | `stream_name`, `changelist`, `parent_stream` |
| `merge` | Merge changes between parent/child streams | `stream_name`, `changelist`, `parent_stream` |
| `integrate` | Integrate with custom source/target (advanced) | `stream_name`, `changelist`, `parent_stream` |
| `populate` | Seed a new stream with files from parent | `stream_name` |
| `switch` | Switch a workspace to a different stream | `stream_name`, `workspace` |
| `create_workspace` | Create a workspace bound to a stream | `stream_name`, `workspace_name`, `root` |

## Common Workflows

### Create a feature branch

1. `modify_streams` → `create` a new development stream with parent = mainline
2. `modify_streams` → `populate` to seed the new stream with parent files
3. `modify_streams` → `create_workspace` bound to the new stream

### Propagate changes to main

1. `query_streams` → `interchanges` to see what hasn't been merged yet
2. `query_streams` → `integration_status` to check current state
3. `modify_streams` → `copy` from child to parent (copies up)
4. `query_streams` → `check_resolve` to see if resolves are needed
5. `modify_streams` → `resolve_spec` if needed

### Merge from parent to child

1. `query_streams` → `interchanges` to see pending changes
2. `modify_streams` → `merge` from parent to child (merges down)
3. Resolve any conflicts

### Switch workspace streams

1. `query_streams` → `list_workspaces` to find existing workspaces
2. `modify_streams` → `switch` the workspace to the target stream

## Best Practices

- Always check `interchanges` before merging or copying to understand what will be propagated.
- Use `copy` for upward propagation (child → parent) and `merge` for downward (parent → child).
- Use `validate_submit` before submitting to catch stream-related issues early.
- Use `check_resolve` after integration to ensure all conflicts are handled.
- `populate` should only be used once when seeding a newly created stream.
