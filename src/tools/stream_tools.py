"""Stream query and modify tools."""

from __future__ import annotations

from typing import Annotated, Optional, List, Literal, TYPE_CHECKING

from fastmcp import Context
from pydantic import Field

from ..models import stream_models as stream_m
from .common import handle_with_logging, handle_modify_with_delete_gate

if TYPE_CHECKING:
    from ..server import P4MCPServer


def register(server: "P4MCPServer") -> None:
    if "streams" not in server.toolsets:
        return

    @server.mcp.tool(tags=["read", "streams"])
    async def query_streams(
        action: Annotated[Literal[
            "list", "get", "children", "parent", "graph",
            "integration_status", "get_workspace", "list_workspaces",
            "validate_file", "validate_submit", "check_resolve", "interchanges"
        ], Field(
            description=(
                "Stream query action: "
                "'list' streams, 'get' stream spec, 'children'/'parent'/'graph' of a stream, "
                "'integration_status' (p4 istat), 'get_workspace'/'list_workspaces', "
                "'validate_file'/'validate_submit' against stream view, "
                "'check_resolve' for pending spec conflicts, 'interchanges' between streams"
            )
        )],
        ctx: Context,
        stream_name: Annotated[Optional[str], Field(
            default=None,
            description="Stream depot path (e.g. '//depot/main'). Required for most actions.",
            examples=["//depot/main", "//depot/dev"],
        )] = None,
        stream_path: Annotated[Optional[List[str]], Field(
            default=None,
            description="Stream path pattern(s) for 'list' (e.g. ['//depot/...'])",
            examples=[["//depot/..."]],
        )] = None,
        filter: Annotated[Optional[str], Field(
            default=None,
            description="Filter expression string for 'list' (-F flag). Supports &, |, and parentheses. E.g. 'Parent=//Ace/MAIN&(Type=development|Type=release)'",
            examples=["Type=development", "Parent=//depot/main&Type=release", "Owner=alice|(Type=development&Parent=//depot/main)"],
        )] = None,
        fields: Annotated[Optional[List[str]], Field(
            default=None,
            description="Fields to return for 'list' (e.g. ['Stream', 'Owner', 'Name', 'Type'])",
            examples=[["Stream", "Owner", "Name", "Type"]],
        )] = None,
        unloaded: Annotated[bool, Field(
            default=False,
            description="Include unloaded streams/workspaces",
        )] = False,
        all_streams: Annotated[bool, Field(
            default=False,
            description="Include virtual streams in 'list' results",
        )] = False,
        viewmatch: Annotated[Optional[str], Field(
            default=None,
            description="Single depot file path to filter streams whose views contain this path",
            examples=["//depot/main/src/file.txt"],
        )] = None,
        view_without_edit: Annotated[bool, Field(
            default=False,
            description="View locked stream without opening for edit (-v flag)",
        )] = False,
        at_change: Annotated[Optional[str], Field(
            default=None,
            description="Changelist number for historical stream spec",
            examples=["12345"],
        )] = None,
        both_directions: Annotated[bool, Field(
            default=False,
            description="Show integration status in both directions (-a flag for integration_status)",
        )] = False,
        force_refresh: Annotated[bool, Field(
            default=False,
            description="Force istat to assume cache is stale and search for pending integrations (-c flag)",
        )] = False,
        workspace: Annotated[Optional[str], Field(
            default=None,
            description="Workspace name for get_workspace, validate_file, validate_submit",
            examples=["my_workspace"],
        )] = None,
        template: Annotated[Optional[str], Field(
            default=None,
            description="Template workspace for get_workspace",
            examples=["template_workspace"],
        )] = None,
        user: Annotated[Optional[str], Field(
            default=None,
            description="Filter workspaces by user (list_workspaces)",
            examples=["alice", "bob"],
        )] = None,
        file_paths: Annotated[Optional[List[str]], Field(
            default=None,
            description="File paths for validate_file or interchanges",
            examples=[["//depot/main/src/file.txt", "//depot/dev/src/file.txt"]],
        )] = None,
        changelist: Annotated[Optional[str], Field(
            default=None,
            description="Changelist for validate_submit",
            examples=["12345"],
        )] = None,
        reverse: Annotated[bool, Field(
            default=False,
            description="Reverse comparison direction (interchanges)",
        )] = False,
        long_output: Annotated[bool, Field(
            default=False,
            description="Full changelist descriptions (interchanges)",
        )] = False,
        limit: Annotated[Optional[int], Field(
            default=None,
            description="Max changelists (interchanges)",
            examples=[10, 50],
        )] = None,
        max_results: Annotated[int, Field(
            default=50,
            ge=1,
            le=1000,
            description="Maximum number of results to return",
        )] = 50,
    ) -> dict:
        """Query streams: list, get spec, children/parent/graph, integration status, workspaces, validate files, check resolve, interchanges (READ permission)"""
        params = stream_m.QueryStreamsParams(
            action=action, stream_name=stream_name, stream_path=stream_path,
            filter=filter, fields=fields, unloaded=unloaded, all_streams=all_streams,
            viewmatch=viewmatch, view_without_edit=view_without_edit,
            at_change=at_change,
            both_directions=both_directions, force_refresh=force_refresh,
            workspace=workspace, template=template, user=user,
            file_paths=file_paths, changelist=changelist,
            reverse=reverse, long_output=long_output,
            limit=limit, max_results=max_results,
        )
        return await handle_with_logging(server, "query", "streams", params, "query_streams", ctx)

    if not server.readonly:
        @server.mcp.tool(tags=["write", "streams"])
        async def modify_streams(
            action: Annotated[Literal[
                "create", "update", "delete",
                "edit_spec", "resolve_spec", "revert_spec", "shelve_spec", "unshelve_spec",
                "copy", "merge", "integrate", "populate",
                "switch", "create_workspace"
            ], Field(
                description=(
                    "Stream modification action: "
                    "'create'/'update'/'delete' a stream, "
                    "'edit_spec'/'resolve_spec'/'revert_spec'/'shelve_spec'/'unshelve_spec' for spec editing, "
                    "'copy'/'merge'/'integrate'/'populate' for propagation, "
                    "'switch' workspace stream, 'create_workspace' for a stream"
                )
            )],
            ctx: Context,
            stream_name: Annotated[Optional[str], Field(
                default=None,
                description="Stream depot path (e.g. '//depot/main'). Also used as -S flag for propagation.",
                examples=["//depot/main", "//depot/dev"],
            )] = None,
            stream_type: Annotated[Optional[str], Field(
                default=None,
                description="Stream type (required for create): mainline, development, sparsedev, release, sparserel, task, virtual",
                examples=["mainline", "development", "release", "task"],
            )] = None,
            parent: Annotated[Optional[str], Field(
                default=None,
                description="Parent stream (required for non-mainline create)",
                examples=["//depot/main"],
            )] = None,
            name: Annotated[Optional[str], Field(
                default=None,
                description="Short display name for the stream",
                examples=["Main", "Dev Branch"],
            )] = None,
            description: Annotated[Optional[str], Field(
                default=None,
                description="Stream or workspace description",
                examples=["Main development stream", "Feature branch for project X"],
            )] = None,
            options: Annotated[Optional[str], Field(
                default=None,
                description="Stream options: 'allsubmit/ownersubmit unlocked/locked toparent/notoparent fromparent/nofromparent'",
                examples=["allsubmit unlocked toparent fromparent", "ownersubmit locked notoparent nofromparent"],
            )] = None,
            parent_view: Annotated[Optional[str], Field(
                default=None,
                description="Parent view treatment: 'inherit' or 'noinherit'",
                examples=["inherit", "noinherit"],
            )] = None,
            paths: Annotated[Optional[List[str]], Field(
                default=None,
                description="Stream view paths (e.g. ['share ...', 'isolate dir/...'])",
                examples=[["share ...", "isolate dir/..."]],
            )] = None,
            remapped: Annotated[Optional[List[str]], Field(
                default=None,
                description="Remapped paths",
                examples=[["src/... new_src/..."]],
            )] = None,
            ignored: Annotated[Optional[List[str]], Field(
                default=None,
                description="Ignored paths",
                examples=[["build/...", "tmp/..."]],
            )] = None,
            changelist: Annotated[Optional[str], Field(
                default=None,
                description="Changelist for edit_spec, shelve_spec, unshelve_spec, or propagation, 'default' not allowed for edit_spec/shelve_spec/unshelve_spec",
                examples=["12345"],
            )] = None,
            resolve_mode: Annotated[Optional[str], Field(
                default=None,
                description="Resolve mode for resolve_spec: 'auto', 'accept_theirs', 'accept_yours'",
                examples=["auto", "accept_theirs", "accept_yours"],
            )] = None,
            target_changelist: Annotated[Optional[str], Field(
                default=None,
                description="Target changelist for unshelve_spec",
                examples=["12345"],
            )] = None,
            parent_stream: Annotated[Optional[str], Field(
                default=None,
                description="Override parent stream for propagation (-P flag)",
                examples=["//depot/main", "//depot/release"],
            )] = None,
            branch: Annotated[Optional[str], Field(
                default=None,
                description="Branch spec name for integrate/populate (-b flag)",
                examples=["my_branch_spec"],
            )] = None,
            file_paths: Annotated[Optional[List[str]], Field(
                default=None,
                description="File paths for propagation",
                examples=[["//depot/dev/...", "//depot/dev/src/file.txt"]],
            )] = None,
            preview: Annotated[bool, Field(
                default=False,
                description="Preview only, don't make changes (-n flag)",
            )] = False,
            force: Annotated[bool, Field(
                default=False,
                description="Force operation",
            )] = False,
            reverse: Annotated[bool, Field(
                default=False,
                description="Reverse direction (-r flag)",
            )] = False,
            quiet: Annotated[bool, Field(
                default=False,
                description="Suppress informational messages (-q flag)",
            )] = False,
            max_files: Annotated[Optional[int], Field(
                default=None,
                description="Limit number of files processed (-m flag)",
                examples=[100, 500],
            )] = None,
            output_base: Annotated[bool, Field(
                default=False,
                description="Show base revision with each scheduled resolve (-Ob flag for merge/integrate) or display list of files created (-o flag for populate)",
            )] = False,
            virtual: Annotated[bool, Field(
                default=False,
                description="Copy using virtual stream (-v flag, copy only)",
            )] = False,
            schedule_branch_resolve: Annotated[bool, Field(
                default=False,
                description="Schedule 'branch resolves' instead of branching new target files automatically (-Rb flag)",
            )] = False,
            integrate_around_deleted: Annotated[bool, Field(
                default=False,
                description="Integrate around deleted revisions (-Di flag)",
            )] = False,
            skip_cherry_picked: Annotated[bool, Field(
                default=False,
                description="Skip cherry-picked revisions already integrated (-Rs flag)",
            )] = False,
            source_path: Annotated[Optional[str], Field(
                default=None,
                description="Source path for populate",
                examples=["//depot/main/..."],
            )] = None,
            target_path: Annotated[Optional[str], Field(
                default=None,
                description="Target path for populate",
                examples=["//depot/dev/..."],
            )] = None,
            workspace: Annotated[Optional[str], Field(
                default=None,
                description="Workspace name for switch",
                examples=["my_workspace"],
            )] = None,
            workspace_name: Annotated[Optional[str], Field(
                default=None,
                description="Workspace name to create (create_workspace)",
                examples=["new_stream_workspace"],
            )] = None,
            root: Annotated[Optional[str], Field(
                default=None,
                description="Workspace root directory (create_workspace)",
                examples=["/home/user/perforce/workspace"],
            )] = None,
            host: Annotated[Optional[str], Field(
                default=None,
                description="Host restriction (create_workspace)",
                examples=["workstation01"],
            )] = None,
            alt_roots: Annotated[Optional[List[str]], Field(
                default=None,
                description="Alternate root paths (create_workspace)",
                examples=[["/home/user/alt_root", "/mnt/shared/workspace"]],
            )] = None,
        ) -> dict:
            """Create/update/delete streams, edit/resolve/revert/shelve stream specs, copy/merge/integrate/populate between streams, switch workspace, create stream workspace (WRITE permission)"""
            params = stream_m.ModifyStreamsParams(
                action=action, stream_name=stream_name, stream_type=stream_type,
                parent=parent, name=name, description=description,
                options=options, parent_view=parent_view, paths=paths,
                remapped=remapped, ignored=ignored,
                changelist=changelist, resolve_mode=resolve_mode,
                target_changelist=target_changelist, parent_stream=parent_stream,
                branch=branch, file_paths=file_paths,
                preview=preview, force=force, reverse=reverse, quiet=quiet,
                max_files=max_files, output_base=output_base, virtual=virtual,
                schedule_branch_resolve=schedule_branch_resolve,
                integrate_around_deleted=integrate_around_deleted,
                skip_cherry_picked=skip_cherry_picked,
                source_path=source_path, target_path=target_path,
                workspace=workspace, workspace_name=workspace_name,
                root=root, host=host, alt_roots=alt_roots,
            )
            return await handle_modify_with_delete_gate(
                server, "streams", params, "modify_streams", ctx,
                f"Requires approval to delete stream: {stream_name}",
            )
