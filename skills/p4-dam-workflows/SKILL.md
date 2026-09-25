---
name: p4-dam-workflows
description: P4 DAM (Digital Asset Management) workflows — search, browse, tag, review, and manage digital assets via P4 MCP tools. Use when discovering, searching, filtering, reviewing, or managing assets stored in P4 DAM.
---

# P4 DAM Workflows

## Prerequisites

- The P4 server must have the `P4.HTH.URL` property set (points at the P4 DAM instance).
- The server must be started with a P4 DAM API key via the `P4DAM_API_KEY` environment variable. Without a key, P4 DAM tools are not registered at all — a warning is logged at startup.
- Write tools (create, update, delete, sync) require the server to be started without `--readonly`.

## Tool Reference

### Discovery & Navigation

| Tool | Purpose |
|------|---------|
| `query_p4dam_projects` | List projects. Accepts `search_term` (matches name, short name, or description). |
| `query_p4dam_repositories` | List repositories in a project. Accepts `search_term` (matches short name). |
| `query_p4dam_helix_classic_branches` | List Helix Classic branches in a helix_classic repository. |

### Asset Search

| Tool | Purpose |
|------|---------|
| `query_p4dam_assets` | Search assets by keyword/filters — use when you don't have a depot path yet. |
| `query_p4dam_asset` | Fetch full metadata for a single known asset by depot path. |
| `fetch_p4dam_media` | Fetch and render a thumbnail, preview, or file image. |
| `regenerate_p4dam_preview` | Trigger async regeneration of thumbnail and preview for an asset revision. |

**`query_p4dam_assets` filters:** `search_term`, `project_ids` (UUIDs), `repository_ids` (UUIDs), `path` (wildcard depot path patterns, e.g. `//depot/art/*.png`), `name` (filename wildcard), `tag`, `file_extension`, `exclude_file_extension`, `user`, `from_size` / `to_size` (bytes), `from_date` / `to_date` (ISO 8601), `all_revisions`, `max_results`, `offset`.

**`query_p4dam_asset` params:** `depot_path` (required), `identifier` (changeset), `project_id` (short name or UUID), `repository_id` (UUID, or short name if `project_id` is also provided), `include`.

**`query_p4dam_asset` include values:**
- Default set: `commit`, `latest_commit`, `custom_attributes`, `weblinks`, `asset_bundle`, `asset_bundle_origin`, `parent_asset_bundles`, `helix_classic_branch_matches`, `stream_view_matches`, `sprite`
- Require project/repository/stream or branch context: `file_review`, `comments`, `all_comments`
- Extras: `file_count`, `scene_refs`

**`fetch_p4dam_media`:** Pass `thumbnail_url`, `preview_url`, `sprite_url`, or `file_url` from search/asset results. `thumbnail_url`, `preview_url`, and `sprite_url` are only present for image files (nil for non-image assets). Returns the image directly for visual display.

**`regenerate_p4dam_preview`:** Trigger P4Search to regenerate the thumbnail and preview for a specific asset revision. Params: `depot_path` (required), `commit_id` (changeset number, required). Returns `accepted` immediately — regeneration is async. Requires `P4.P4Search.URL` and `P4.P4Search.AUTH_TOKEN` on the P4 server.

### Asset Bundles

| Tool | Purpose |
|------|---------|
| `create_p4dam_asset_bundle` | Create a named collection of depot files scoped for review. |
| `update_p4dam_asset_bundle` | Update description, view_paths, or hero_file_path. |
| `delete_p4dam_asset_bundle` | Delete an asset bundle (prompts for confirmation). |
| `sync_p4dam_asset_bundle` | Sync bundle's depot files to local P4CLIENT workspace. |

**Create flow:** `query_p4dam_projects` → `query_p4dam_repositories` → (if helix_classic: `query_p4dam_helix_classic_branches`) → `create_p4dam_asset_bundle`.

### File Reviews

| Tool | Purpose |
|------|---------|
| `query_p4dam_file_reviews` | List file reviews in a project. Filter by `depot_path`. |
| `query_p4dam_file_review` | Fetch single review with full detail including `download_url`. |
| `create_p4dam_file_review` | Create a file review (single-file or asset bundle). |
| `update_p4dam_file_review` | Update state, name, view_paths, description, position. |
| `delete_p4dam_file_review` | Delete a review (prompts for confirmation). |

**`query_p4dam_file_reviews` include:** `weblinks`.

### Workflows

| Tool | Purpose |
|------|---------|
| `query_p4dam_workflows` | List workflows. `include` accepts `states`, `transition_rules`, `projects`. |
| `query_p4dam_workflow` | Fetch a single workflow by short name or UUID. |
| `query_p4dam_workflow_states` | List states for a workflow (name, short_name, kind, color, position). |

State kinds: `open` (initial), `review` (under review), `done` (terminal).

### Comments

| Tool | Purpose |
|------|---------|
| `create_p4dam_comment` | Post a comment on a file review, a file within a review, a committed file, or as a reply. |

**`create_p4dam_comment` types and required fields:**

| `type` | Required | Use case |
|--------|----------|----------|
| `file_review` | `project`, `repository`, `file_review` | Comment on an asset bundle file review |
| `file_review_file` | `project`, `repository`, `file_review`, `path` | Comment on a specific file inside a file review |
| `commit_file` | `project`, `repository`, `commit`, `path` | Comment on a committed file or asset bundle without a review |
| `comment` | `comment` | Reply to an existing comment |

`path` is a relative path within the repository (e.g. `renders/hero.png`), not a full depot path.
For `commit_file` on helix_stream repos: also pass `stream_path`. For helix_classic: also pass `helix_classic_branch`.

### Custom Attributes

| Tool | Purpose |
|------|---------|
| `query_p4dam_custom_attribute_templates` | List available custom attribute templates for a project (name, type, allowed values). |
| `update_p4dam_asset_custom_attributes` | Set or remove custom attribute values on one or more assets. |

**Flow:** `query_p4dam_custom_attribute_templates(project_id=...)` → pick template UUID → `update_p4dam_asset_custom_attributes(paths=[...], create=[{uuid, value}])`.

**Attribute types:** `text` (any string), `single-select` (one of `available_values`), `multi-select` (list of `available_values`), `checkbox` (`"true"` / `"false"`).

### Tags

| Tool | Purpose |
|------|---------|
| `update_p4dam_asset_tags` | Add/remove user tags and auto-tags on one or more assets in one call. |

**Tag operations:** `create` (add tags), `delete` (remove user tags), `delete_auto` (remove auto-generated tags). Supports individual files, specific revisions (`identifier` in path), recursive folders (`//depot/folder/...`), and `propagatable` for future revisions.

---

## Response Fields

### `query_p4dam_assets` — each result item

| Field | Notes |
|-------|-------|
| `depot_path` | Full depot path — pass to `query_p4dam_asset` or `fetch_p4dam_media(file_url)` |
| `name` | Filename only |
| `commit` | Changeset number |
| `rev` | Revision number |
| `size` | File size in bytes |
| `mime` | MIME type (e.g. `image/png`) |
| `file_type` | Perforce file type |
| `user` | Last modifier username |
| `updated_at` | ISO 8601 timestamp |
| `tags` | User-applied tags (array of strings) |
| `auto_tags` | Auto-generated tags (array of strings) |
| `blurhash` | Present only for image files |
| `thumbnail_url` | Pass to `fetch_p4dam_media` — image files only, nil otherwise |
| `preview_url` | Pass to `fetch_p4dam_media` — image files only, nil otherwise |
| `file_url` | Pass to `fetch_p4dam_media` for the raw file |
| `sprite` | `{ sprite_url, metadata }` — animation sprite sheet, image files only |

The response wrapper also contains `total_count`, `more_results`, and `next_offset` for pagination.

### `query_p4dam_asset` — top-level fields

| Field | Notes |
|-------|-------|
| `depot_path` | Full depot path |
| `thumbnail_url` | Pass to `fetch_p4dam_media` — present only for image files |
| `preview_url` | Pass to `fetch_p4dam_media` — present only for image files |
| `file_url` | Raw file download URL |
| `asset_bundle.uuid` | Pass as `bundle_id` to `update_p4dam_asset_bundle` / `delete_p4dam_asset_bundle` |
| `asset_bundle.view_paths` | Pass directly to `sync_p4dam_asset_bundle` |
| `asset_bundle.depot_path` | Depot path of the `.p4bundle` file |
| `weblinks` | Array of weblinks (included by default) |
| `custom_attributes` | Custom metadata fields |
| `commit` | Changeset object (included by default) |
| `latest_commit` | Latest commit object (included by default) |
| `helix_classic_branch_matches` | Matching Helix Classic branches (included by default) |
| `stream_view_matches` | Matching stream views (included by default) |

### `query_p4dam_repositories` — each result item

| Field | Notes |
|-------|-------|
| `uuid` | Pass as `repository_id` to other tools |
| `short_name` | Pass as `repository_id` to other tools (also accepted) |
| `type` | `helix_stream` or `helix_classic` — determines which additional param is required for bundles/reviews |
| `linked_streams` | Array of stream paths — use `stream` value as `stream_path` when creating bundles/reviews for helix_stream repos |
| `default_identifier` | Default branch/stream identifier |

### `query_p4dam_file_reviews` — each result item

| Field | Notes |
|-------|-------|
| `uuid` | Pass as `review_id` to `query_p4dam_file_review`, `update_p4dam_file_review`, `delete_p4dam_file_review` |
| `name` | Review name |
| `state` | Current workflow state object (`short_name`, `kind`) |
| `depot_path` | File or bundle being reviewed |
| `view_paths` | Scope of the review |
| `asset_bundle` | Linked asset bundle (if bundle review) |
| `thumbnail_url` | Pass to `fetch_p4dam_media` — present only for image files |
| `preview_url` | Pass to `fetch_p4dam_media` — present only for image files |
| `download_url` | Bundle download URL — only present when `asset_bundle` is set |
| `creator` | Creator account object |

### `query_p4dam_workflow_states` — each result item

| Field | Notes |
|-------|-------|
| `short_name` | **Pass as `state` when creating or updating a file review** (not `name`) |
| `name` | Human-readable display name |
| `kind` | `open`, `review`, or `done` |
| `color` | Hex color string |
| `position` | Ordering within the workflow |

---

## Common Workflows

### 1. Search and filter assets

```
# By keyword (filename, tags, or custom attributes):
query_p4dam_assets(search_term="monocycle")

# Narrow by project or file type:
query_p4dam_assets(project_ids=["proj-uuid"], file_extension=["png", "svg"])

# By date range or size:
query_p4dam_assets(search_term="hero", from_date="2024-01-01", to_date="2024-12-31")
query_p4dam_assets(from_size=1048576, to_size=52428800)  # 1 MB – 50 MB

# By depot path pattern:
query_p4dam_assets(path=["//depot/art/characters/..."])
query_p4dam_assets(path=["//depot/renders/*.png"])
```

### 2. Fetch full metadata for a known asset

```
query_p4dam_asset(depot_path="//stream/images/logo.png")
```

To include `file_review`, `comments`, or `all_comments`, pass `project_id` and `repository_id`. Find them in `stream_view_matches` or `helix_classic_branch_matches` from the initial result:

```
query_p4dam_asset(depot_path="//stream/images/logo.png", project_id="proj-uuid", repository_id="repo-uuid", include=["file_review", "all_comments"])
```

### 3. View a thumbnail or preview

```
# From query_p4dam_assets result:
fetch_p4dam_media(url=<result.thumbnail_url>)

# From query_p4dam_asset result (higher resolution):
fetch_p4dam_media(url=<result.preview_url>)
```

### 4. Create an asset bundle (helix_stream repo)

```
query_p4dam_projects(search_term="characters")
query_p4dam_repositories(project_id="proj-uuid")
create_p4dam_asset_bundle(
    depot_path="//stream/bundles/q3-chars.p4bundle",
    project="proj-uuid",
    repository="repo-uuid",
    view_paths=["//stream/renders/...", "//stream/textures/..."],
    stream_path="//stream/mainline",
    description="Q3 character renders"
)
```

### 5. Sync a bundle to local workspace

```
# Get view_paths from asset_bundle section:
query_p4dam_asset(depot_path="//stream/bundles/q3-chars.p4bundle", include=["asset_bundle"])
sync_p4dam_asset_bundle(view_paths=<asset_bundle.view_paths>)
```

### 6. Create a file review

```
# Discover the state short_name first:
query_p4dam_workflows(include=["states"])
create_p4dam_file_review(
    project_id="my-project",
    name="Q3 hero renders — art director pass",
    depot_path="//stream/bundles/q3-chars.p4bundle",
    view_paths=["//stream/renders/..."],
    state="open"
)
```

### 7. Transition a review to a new state

```
query_p4dam_workflow_states(workflow_id="default_workflow")
update_p4dam_file_review(project_id="my-project", review_id="review-uuid", state="in-review")
```

### 8. Tag assets

```
# Tag a single file:
update_p4dam_asset_tags(paths=[{"path": "//stream/renders/hero.png"}], create=["hero", "q3-final"])

# Tag an entire folder recursively:
update_p4dam_asset_tags(paths=[{"path": "//stream/renders/..."}], create=["q3"])

# Remove a tag:
update_p4dam_asset_tags(paths=[{"path": "//stream/renders/hero.png"}], delete=["wip"])

# Propagate to future revisions:
update_p4dam_asset_tags(paths=[{"path": "//stream/renders/hero.png"}], create=["hero"], propagatable=true)
```

---

## Best Practices

- Use `query_p4dam_assets` first to discover assets; switch to `query_p4dam_asset` for full metadata on a known depot path.
- After showing `query_p4dam_asset` results, indicate which extra data can be fetched by re-calling with additional `include` values: `comments` (comments on the queried revision only), `all_comments` (comments across all revisions), `file_count` (number of files in a bundle), `scene_refs` (referenced files).
- Leave `all_revisions=false` (default) in asset searches unless you need history — latest-only is faster.
- When `query_p4dam_asset` results include `thumbnail_url`, `preview_url`, or `sprite_url`, the asset is an image — render it via `fetch_p4dam_media`. These fields are only present for image files.
- When `query_p4dam_asset` returns `commit`, always show "Submitted on {date} by {author} (#{changeset})" followed by the commit description truncated to 512 characters. If `latest_commit` is present and differs from `commit`, also show "You're viewing changeset #{commit.number}, latest is #{latest_commit.number} from {date}".
- When `query_p4dam_asset` returns a non-empty `scene_refs`, indicate that this file has referenced files, and list each by `depot_path`. Mark entries where `exists` is false as missing. Render `thumbnail_url` via `fetch_p4dam_media` if present.
Applies to both `query_p4dam_assets` and `query_p4dam_asset`.
- When `query_p4dam_asset` returns `custom_attributes`, list them as "**{name}**: {value}", skipping entries where `template.hidden` is true.
- When `query_p4dam_asset` returns `weblinks`, list them as markdown links: `[{text}]({url})`, falling back to the URL as text if `text` is blank.
- When `query_p4dam_asset` returns `file_reviews`, show each as: **"{name}"** — state `{state.short_name}`, created by `{creator}`.
- When `query_p4dam_asset` returns an `asset_bundle` object, indicate that this asset is an asset bundle.
- When `query_p4dam_asset` returns an `asset_bundle_origin` object (but no `asset_bundle`), indicate that this is a `.p4bundle` file derived from a bundle at a different depot path (e.g. branched or integrated).
- When `query_p4dam_asset` returns a `parent_asset_bundles` object, indicate that this asset is part of an asset bundle.
- `project_id` and `repository_id` accept either UUID or short name in all tools.
- For helix_stream repos, `stream_path` is required when creating bundles or reviews. Find it in `linked_streams` from `query_p4dam_repositories`.
- For helix_classic repos, `helix_classic_branch` is required. Use `query_p4dam_helix_classic_branches` to discover it.
- When creating a file review, the `state` field value is ignored by the backend — new reviews always start in the project's first open state.
- `sync_p4dam_asset_bundle` requires `P4CLIENT` to be set in the environment.
- When results include a non-empty `helix_classic_branch_matches`, list each entry as "{short_name} ({project.short_name} / {repository.short_name})", marking the default branch. Applies to both `query_p4dam_assets` and `query_p4dam_asset`.
- When results include a non-empty `stream_view_matches`, list each entry as "{stream_path} ({project.short_name} / {repository.short_name})". 