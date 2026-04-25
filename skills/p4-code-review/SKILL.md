---
name: p4-code-review
description: P4 code review workflows — discover, create, vote, comment, transition, and manage reviews via P4 MCP tools. Use when: creating reviews, voting, commenting, transitioning review states, managing participants, or tracking review activity in P4.
---

# Code Review Workflows

Use the `query_reviews` and `modify_reviews` tools to manage P4 Code Review code reviews.

## Querying Reviews

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `list` | List reviews with filters | `review_fields`, `max_results` |
| `dashboard` | Get review dashboard for current user | — |
| `get` | Get full review details | `review_id` |
| `transitions` | Get available state transitions | `review_id` |
| `files` | List files in a review | `review_id` |
| `files_readby` | Check which files have been read by reviewers | `review_id` |
| `comments` | Get all comments on a review | `review_id` |
| `activity` | Get review activity log | `review_id` |

## Modifying Reviews

### Lifecycle

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `create` | Create a new review from a changelist | `change_id`, `description` |
| `transition` | Move review to a new state | `review_id`, `transition` |
| `archive_inactive` | Archive stale reviews | `not_updated_since`, `max_reviews` |
| `obliterate` | Permanently remove a review (requires approval) | `review_id` |

### Voting & Participation

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `vote` | Vote on a review (up/down/clear) | `review_id`, `vote_value` |
| `append_participants` | Add reviewers | `review_id`, `users`, `groups` |
| `replace_participants` | Replace all reviewers | `review_id`, `users`, `groups` |
| `delete_participants` | Remove reviewers | `review_id`, `users`, `groups` |
| `join` | Join a review as participant | `review_id` |
| `leave` | Leave a review | `review_id` |

### Comments

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `add_comment` | Add a new comment | `review_id`, `body`, `context` |
| `reply_comment` | Reply to an existing comment | `review_id`, `comment_id`, `body` |
| `mark_comment_read` | Mark a comment as read | `review_id`, `comment_id` |
| `mark_comment_unread` | Mark a comment as unread | `review_id`, `comment_id` |
| `mark_all_comments_read` | Mark all comments as read | `review_id` |
| `mark_all_comments_unread` | Mark all comments as unread | `review_id` |

### Changelist Management

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `append_change` | Add a changelist to a review | `review_id`, `change_id` |
| `replace_with_change` | Replace review content with a new changelist | `review_id`, `change_id` |

### Metadata

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `update_author` | Change the review author | `review_id`, `new_author` |
| `update_description` | Update review description | `review_id`, `new_description` |
| `refresh_projects` | Refresh project associations | `review_id` |

## Common Workflows

### Submit code for review

1. `modify_changelists` → `create` a pending changelist with your edits
2. `modify_shelves` → `shelve` the changelist
3. `modify_reviews` → `create` a review from the changelist
4. `modify_reviews` → `append_participants` to add reviewers

### Review code

1. `query_reviews` → `dashboard` to see reviews assigned to you
2. `query_reviews` → `get` to see review details
3. `query_reviews` → `files` to see changed files
4. `query_reviews` → `comments` to see existing discussion
5. `modify_reviews` → `add_comment` to provide feedback
6. `modify_reviews` → `vote` to approve or request changes
7. `query_reviews` → `transitions` to see available state changes
8. `modify_reviews` → `transition` to approve/reject

### Update a review

1. Make edits and shelve the updated changelist
2. `modify_reviews` → `replace_with_change` to update review content
3. Review comments and address feedback

## Best Practices

- Check `transitions` before calling `transition` to verify the target state is valid.
- Use `files_readby` to track which reviewers have seen the latest changes.
- Always `shelve` changes before creating a review so reviewers can see the diff.
- Use `append_participants` rather than `replace_participants` to avoid removing existing reviewers.
