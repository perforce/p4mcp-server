import logging
from .utils import handle_errors

logger = logging.getLogger(__name__)


class StreamHandlers:
    """Handlers for stream query and modify operations."""

    def __init__(self, stream_services):
        self.stream_services = stream_services

    # -----------------------------------------------------------------
    # QUERY
    # -----------------------------------------------------------------
    @handle_errors
    async def _handle_query_streams(self, params):
        action = params.action

        if action == "list":
            result = await self.stream_services.list_streams(
                stream_path=getattr(params, "stream_path", None),
                filter=getattr(params, "filter", None),
                fields=getattr(params, "fields", None),
                limit=getattr(params, "max_results", 50),
                unloaded=getattr(params, "unloaded", False),
                all_streams=getattr(params, "all_streams", False),
                viewmatch=getattr(params, "viewmatch", None),
            )

        elif action == "get":
            result = await self.stream_services.get_stream(
                stream_name=params.stream_name,
                view_without_edit=getattr(params, "view_without_edit", False),
                at_change=getattr(params, "at_change", None),
            )

        elif action == "children":
            result = await self.stream_services.get_stream_children(params.stream_name)

        elif action == "parent":
            result = await self.stream_services.get_stream_parent(params.stream_name)

        elif action == "graph":
            result = await self.stream_services.get_stream_graph(params.stream_name)

        elif action == "integration_status":
            result = await self.stream_services.get_stream_integration_status(
                stream_name=getattr(params, "stream_name", None),
                both_directions=getattr(params, "both_directions", False),
                force_refresh=getattr(params, "force_refresh", False),
            )

        elif action == "get_workspace":
            result = await self.stream_services.get_stream_workspace(
                workspace=getattr(params, "workspace", None),
                stream_name=getattr(params, "stream_name", None),
                template=getattr(params, "template", None),
            )

        elif action == "list_workspaces":
            result = await self.stream_services.list_stream_workspaces(
                stream_name=getattr(params, "stream_name", None),
                user=getattr(params, "user", None),
                limit=getattr(params, "max_results", 50),
                unloaded=getattr(params, "unloaded", False),
            )

        elif action == "validate_file":
            result = await self.stream_services.validate_file_against_stream(
                file_paths=params.file_paths,
                workspace=getattr(params, "workspace", None),
            )

        elif action == "validate_submit":
            result = await self.stream_services.validate_submit_against_stream(
                changelist=getattr(params, "changelist", None),
                workspace=getattr(params, "workspace", None),
            )

        elif action == "check_resolve":
            result = await self.stream_services.check_stream_spec_resolve_needed(
                stream_name=params.stream_name,
            )

        elif action == "interchanges":
            result = await self.stream_services.interchanges_stream(
                stream=params.stream_name,
                reverse=getattr(params, "reverse", False),
                file_paths=getattr(params, "file_paths", None),
                long_output=getattr(params, "long_output", False),
                limit=getattr(params, "limit", None),
            )

        else:
            logger.error(f"Unknown stream query action: {action}")
            raise ValueError(f"Unknown stream query action: {action}")

        return {
            "status": result.get("status", "success") if isinstance(result, dict) else "success",
            "action": action,
            "data": result,
        }

    # -----------------------------------------------------------------
    # MODIFY
    # -----------------------------------------------------------------
    @handle_errors
    async def _handle_modify_streams(self, params):
        action = params.action

        # --- Stream CRUD ---
        if action == "create":
            result = await self.stream_services.create_stream(
                stream_name=params.stream_name,
                stream_type=params.stream_type,
                parent=getattr(params, "parent", None),
                name=getattr(params, "name", None),
                description=getattr(params, "description", None),
                options=getattr(params, "options", None),
                parent_view=getattr(params, "parent_view", None),
                paths=getattr(params, "paths", None),
                remapped=getattr(params, "remapped", None),
                ignored=getattr(params, "ignored", None),
            )

        elif action == "update":
            result = await self.stream_services.update_stream(
                stream_name=params.stream_name,
                name=getattr(params, "name", None),
                description=getattr(params, "description", None),
                options=getattr(params, "options", None),
                parent_view=getattr(params, "parent_view", None),
                paths=getattr(params, "paths", None),
                remapped=getattr(params, "remapped", None),
                ignored=getattr(params, "ignored", None),
            )

        elif action == "delete":
            result = await self.stream_services.delete_stream(
                stream_name=params.stream_name
            )

        # --- Spec editing ---
        elif action == "edit_spec":
            result = await self.stream_services.edit_stream_spec(
                stream_name=params.stream_name,
                changelist=getattr(params, "changelist", None),
            )

        elif action == "resolve_spec":
            result = await self.stream_services.resolve_stream_spec(
                stream_name=params.stream_name,
                resolve_mode=getattr(params, "resolve_mode", "auto") or "auto",
            )

        elif action == "revert_spec":
            result = await self.stream_services.revert_stream_spec(
                stream_name=params.stream_name,
            )

        elif action == "shelve_spec":
            result = await self.stream_services.shelve_stream_spec(
                changelist=params.changelist,
            )

        elif action == "unshelve_spec":
            result = await self.stream_services.unshelve_stream_spec(
                changelist=params.changelist,
                target_changelist=getattr(params, "target_changelist", None),
            )

        # --- Propagation ---
        elif action == "copy":
            result = await self.stream_services.copy_stream(
                stream=getattr(params, "stream_name", None),
                parent_stream=getattr(params, "parent_stream", None),
                file_paths=getattr(params, "file_paths", None),
                changelist=getattr(params, "changelist", None),
                preview=getattr(params, "preview", False),
                force=getattr(params, "force", False),
                virtual=getattr(params, "virtual", False),
                reverse=getattr(params, "reverse", False),
                quiet=getattr(params, "quiet", False),
                max_files=getattr(params, "max_files", None),
            )

        elif action == "merge":
            result = await self.stream_services.merge_stream(
                stream=getattr(params, "stream_name", None),
                parent_stream=getattr(params, "parent_stream", None),
                file_paths=getattr(params, "file_paths", None),
                changelist=getattr(params, "changelist", None),
                preview=getattr(params, "preview", False),
                force=getattr(params, "force", False),
                reverse=getattr(params, "reverse", False),
                quiet=getattr(params, "quiet", False),
                max_files=getattr(params, "max_files", None),
                output_base=getattr(params, "output_base", False),
            )

        elif action == "integrate":
            result = await self.stream_services.integrate_stream(
                stream=getattr(params, "stream_name", None),
                parent_stream=getattr(params, "parent_stream", None),
                file_paths=getattr(params, "file_paths", None),
                changelist=getattr(params, "changelist", None),
                branch=getattr(params, "branch", None),
                preview=getattr(params, "preview", False),
                force=getattr(params, "force", False),
                reverse=getattr(params, "reverse", False),
                quiet=getattr(params, "quiet", False),
                max_files=getattr(params, "max_files", None),
                schedule_branch_resolve=getattr(params, "schedule_branch_resolve", False),
                output_base=getattr(params, "output_base", False),
                integrate_around_deleted=getattr(params, "integrate_around_deleted", False),
                skip_cherry_picked=getattr(params, "skip_cherry_picked", False),
            )

        elif action == "populate":
            result = await self.stream_services.populate_stream(
                stream=getattr(params, "stream_name", None),
                parent_stream=getattr(params, "parent_stream", None),
                branch=getattr(params, "branch", None),
                source_path=getattr(params, "source_path", None),
                target_path=getattr(params, "target_path", None),
                description=getattr(params, "description", None),
                preview=getattr(params, "preview", False),
                force=getattr(params, "force", False),
                reverse=getattr(params, "reverse", False),
                max_files=getattr(params, "max_files", None),
                show_files=getattr(params, "output_base", False),
            )

        # --- Workspace ---
        elif action == "switch":
            result = await self.stream_services.switch_stream(
                stream_name=params.stream_name,
                workspace=getattr(params, "workspace", None),
                preview=getattr(params, "preview", False),
            )

        elif action == "create_workspace":
            result = await self.stream_services.create_stream_workspace(
                workspace_name=params.workspace_name,
                stream_name=params.stream_name,
                root=params.root,
                description=getattr(params, "description", None),
                options=getattr(params, "options", None),
                host=getattr(params, "host", None),
                alt_roots=getattr(params, "alt_roots", None),
            )

        else:
            logger.error(f"Unknown stream modify action: {action}")
            raise ValueError(f"Unknown stream modify action: {action}")

        return {
            "status": result.get("status", "success") if isinstance(result, dict) else "success",
            "action": action,
            "message": result,
        }
