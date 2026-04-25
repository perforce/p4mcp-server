---
name: p4-changelist-management
description: P4 changelist workflows — create, list, submit, shelve, unshelve, and manage changelists and shelved files via P4 MCP tools. Use when: creating changelists, editing files, shelving, unshelving, submitting, organizing changes, or managing pending work in P4.
---

# Changelist Management

Use the `query_changelists`, `modify_changelists`, `query_shelves`, and `modify_shelves` tools to manage P4 changelists and shelved files.

## Querying Changelists

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `list` | List changelists with filters | `status`, `user`, `workspace_name`, `depot_path`, `max_results` |
| `get` | Get full changelist details | `changelist_id` |

## Modifying Changelists

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `create` | Create a new pending changelist | `description` |
| `update` | Update changelist description or fields | `changelist_id`, `description` |
| `submit` | Submit a pending changelist | `changelist_id` |
| `delete` | Delete an empty pending changelist (requires approval) | `changelist_id` |
| `move_files` | Move files to a target changelist | `changelist_id`, `file_paths` |

## Querying Shelves

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `list` | List shelved changelists | `user`, `max_results` |
| `diff` | View diff of shelved files | `changelist_id` |
| `files` | List files in a shelved changelist | `changelist_id` |

## Modifying Shelves

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `shelve` | Shelve files from a pending changelist | `changelist_id`, `file_paths` |
| `unshelve` | Unshelve files back to the same changelist | `changelist_id`, `file_paths` |
| `unshelve_to_changelist` | Unshelve files into a different changelist | `changelist_id`, `target_changelist`, `file_paths` |
| `update` | Update shelved files with new edits | `changelist_id`, `file_paths` |
| `delete` | Delete shelved files (requires approval) | `changelist_id`, `file_paths`, `force` |

## Common Workflows

### Make and submit a change

1. `modify_changelists` → `create` a pending changelist
2. `modify_files` → `edit` (or `add`/`delete`) to open files for edit in the changelist
3. `modify_changelists` → `submit` to commit the change

### Shelve work in progress

1. `modify_changelists` → `create` a pending changelist
2. `modify_files` → `edit` to open files
3. `modify_shelves` → `shelve` to store changes server-side
4. `modify_files` → `revert` local copies (shelve is preserved)

### Resume shelved work

1. `query_shelves` → `list` to find your shelved changelists
2. `modify_shelves` → `unshelve` to restore files to your workspace
3. Continue editing, then `modify_changelists` → `submit`

### Organize files across changelists

1. `query_changelists` → `list` with `status=pending` to see your open changelists
2. `modify_changelists` → `move_files` to reorganize files between changelists

## Best Practices

- Always provide a meaningful description when creating changelists.
- Shelve before sharing work with others (e.g., for code review).
- Use `query_shelves` → `diff` to verify shelved content before unshelving.
- Submit changelists promptly to avoid long-lived pending changes.
- Use `move_files` to keep changelists focused on a single logical change.
