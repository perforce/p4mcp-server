---
name: p4-file-operations
description: P4 file operations — query content, history, annotations, diffs, and modify files (add, edit, delete, move, sync, resolve) via P4 MCP tools. Use when: reading file content, viewing history, comparing revisions, adding or editing files, syncing, resolving conflicts, or reconciling workspace changes in P4.
---

# File Operations

Use the `query_files` and `modify_files` tools to work with files in P4 depots.

## Querying Files

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `content` | Get file content at a revision | `file_path` |
| `history` | Get revision history (filelog) | `file_path`, `max_results` |
| `info` | Get file metadata (type, size, head revision) | `file_path` |
| `metadata` | Get extended file metadata | `file_path` |
| `diff` | Compare file revisions or depot vs workspace | `file_path`, `file2`, `diff2` |
| `annotations` | Get per-line blame/annotation | `file_path` |

## Modifying Files

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `add` | Mark a new file for add | `file_paths`, `changelist` |
| `edit` | Open an existing file for edit | `file_paths`, `changelist` |
| `delete` | Mark a file for delete (requires approval) | `file_paths`, `changelist` |
| `move` | Move/rename a file | `source_paths`, `target_paths`, `changelist` |
| `revert` | Revert opened files to depot version | `file_paths` |
| `reconcile` | Reconcile workspace with depot (detect offline edits) | `file_paths` |
| `resolve` | Resolve file conflicts after integration | `file_paths`, `mode` |
| `sync` | Sync files from depot to workspace | `file_paths`, `force` |

## Common Workflows

### Edit and submit a file

1. `modify_changelists` → `create` a pending changelist
2. `modify_files` → `edit` to open the file in the changelist
3. Make your changes locally
4. `modify_changelists` → `submit` to commit

### Add new files

1. `modify_changelists` → `create` a pending changelist
2. Create the file(s) locally in your workspace
3. `modify_files` → `add` to mark them for add
4. `modify_changelists` → `submit`

### Investigate file history

1. `query_files` → `history` to see revision log
2. `query_files` → `diff` to compare specific revisions
3. `query_files` → `annotations` to see per-line authorship
4. `query_files` → `content` to read a specific revision

### Sync and resolve conflicts

1. `modify_files` → `sync` to get latest from depot
2. If conflicts exist, `modify_files` → `resolve` to handle them
3. `modify_changelists` → `submit` when resolved

### Reconcile offline edits

1. Make changes outside of P4 (e.g., IDE edits without opening files first)
2. `modify_files` → `reconcile` to detect and open changed files

## Best Practices

- Always open files for `edit` before modifying them so changes are tracked.
- Use `reconcile` if you forgot to open files first — it detects offline edits, adds, and deletes.
- Use `diff` to verify changes before submitting.
- Use `annotations` to understand who last changed each line (useful for debugging).
- Specify `changelist` when opening files to keep changes organized.
- When moving files, both source and target must be in the same changelist.
