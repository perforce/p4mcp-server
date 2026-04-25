"""
P4 stream services layer

Read service for tools:
- list_streams : List streams with filtering and field selection
- get_stream : Get stream spec with optional alias conversion
- get_stream_children : Get child streams of a given stream
- get_stream_parent : Get parent stream of a given stream
- get_stream_graph : Get stream graph (parents/children)
- get_stream_integration_status : Get stream integration status (p4 istat)
- get_stream_workspace : Get workspace spec with optional stream association
- list_stream_workspaces : List workspaces filtered by stream (p4 clients -S)

Validation service for tools:
- validate_file_against_stream : Validate file paths against stream view rules before edit/add
- validate_submit_against_stream : Validate opened files belong to the current stream before submit
- check_stream_spec_resolve_needed : Detect pending stream spec conflicts (p4 stream resolve -n)

Write service for tools:
- create_stream : Create a new stream
- update_stream : Update an existing stream (with validation for bound workspaces and open files)
- delete_stream : Delete a stream
- edit_stream_spec : Open stream spec for private editing (p4 edit -So)
- resolve_stream_spec : Resolve pending private stream spec edits (p4 resolve -So)
- revert_stream_spec : Revert pending private stream spec edits (p4 revert -So)
- shelve_stream_spec : Shelve an open stream spec (p4 shelve -As)
- unshelve_stream_spec : Unshelve a shelved stream spec (p4 unshelve -As)
- copy_stream : Copy/promote files between streams (p4 copy -S)
- merge_stream : Merge changes between streams (p4 merge -S)
- integrate_stream : Integrate changes between streams/branches (p4 integrate)
- populate_stream : Branch files without workspace (p4 populate)
- interchanges_stream : List outstanding changes between streams (p4 interchanges -S)
- switch_stream : Switch workspace to a different stream
- create_stream_workspace : Create a new workspace associated with a stream

"""

import logging
from typing import List, Dict, Any, Optional
from P4 import P4Exception

from ..core.connection import P4ConnectionManager

logger = logging.getLogger(__name__)

class StreamServices:
    """Stream services for stream operations"""
    
    def __init__(self, connection_manager: P4ConnectionManager):
        self.connection_manager = connection_manager

    async def list_streams(
        self,
        stream_path: Optional[List[str]] = None,
        filter: Optional[str] = None,
        fields: Optional[List[str]] = None,
        limit: int = 50,
        unloaded: bool = False,
        all_streams: bool = False,
        viewmatch: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List streams
        
        Args:
            stream_path: Stream path pattern(s) to match (e.g., ['//depot/...'])
            filter: Filter expression string (-F flag). Supports &, |, and parentheses.
                    E.g., "Parent=//Ace/MAIN&(Type=development|Type=release)"
                    Supported fields: Stream, Owner, Name, Parent, Type, Description, Options,
                    firmerThanParent, changeFlowsToParent, changeFlowsFromParent, IntegHub
            fields: List of fields to return (e.g., ['Stream', 'Owner', 'Name', 'Type'])
            limit: Maximum number of streams to return (default: 50)
            unloaded: If True, list unloaded streams (-U flag)
            all_streams: If True, include all streams including deleted streams (-a flag)
            viewmatch: Single depot file path to filter streams whose views contain this path
                       (e.g., 'foo.c' or '//depot/path/...'). Supports optional revRange.
        
        Returns:
            Dict with status and list of streams
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["streams"]
                
                # Add unloaded flag
                if unloaded:
                    args.append("-U")
                
                # Add all streams flag
                if all_streams:
                    args.append("-a")
                
                # Add filter expression
                if filter:
                    args.append("-F")
                    args.append(filter)
                
                # Add fields to return
                if fields:
                    args.append("-T")
                    args.append(",".join(fields))
                
                # Add max results limit
                args.append(f"-m{limit}")
                
                # Add viewmatch file
                if viewmatch:
                    args.append("--viewmatch")
                    args.append(viewmatch)
                
                # Add stream path pattern(s)
                if stream_path:
                    args.extend(stream_path)
                
                streams = p4.run(*args)
                return {"status": "success", "message": [{k: v for k, v in stream.items()} for stream in streams]}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to list streams: {e}")
                return {"status": "error", "message": str(e)}

    async def get_stream(
        self,
        stream_name: Optional[str] = None,
        view_without_edit: bool = False,
        at_change: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stream spec
        
        Args:
            stream_name: Stream name (e.g., '//depot/main'). If None, uses current workspace stream.
            view_without_edit: If True, allow admins to view a locked stream without opening for edit (-v flag)
            at_change: Changelist number to retrieve historical stream spec (e.g., '12345' for stream@12345)
        
        Returns:
            Dict with status and stream spec
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Resolve the effective stream name
                effective_stream = stream_name
                if not effective_stream:
                    ws_spec = p4.run("client", "-o")[0]
                    effective_stream = ws_spec.get("Stream")
                    if not effective_stream:
                        return {"status": "error", "message": "No stream specified and current workspace is not stream-based"}
                
                # Verify stream exists before fetching spec
                # (p4 stream -o always returns a template, even for nonexistent streams)
                if not at_change:
                    existing = p4.run("streams", "-F", f"Stream={effective_stream}")
                    if len(existing) == 0:
                        # Also check deleted streams
                        all_streams = p4.run("streams", "-a", "-F", f"Stream={effective_stream}")
                        if len(all_streams) == 0:
                            return {"status": "error", "message": f"Stream '{effective_stream}' does not exist"}
                
                args = ["stream", "-o"]
                
                if view_without_edit:
                    args.append("-v")
                
                # Build stream specifier with optional @change
                stream_specifier = effective_stream
                if at_change:
                    stream_specifier = f"{effective_stream}@{at_change}"
                args.append(stream_specifier)
                
                stream_spec = p4.run(*args)[0]
                return {"status": "success", "message": {k: v for k, v in stream_spec.items()}}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get stream '{stream_name}': {e}")
                return {"status": "error", "message": str(e)}

    async def get_stream_children(self, stream_name: str) -> List[Dict[str, Any]]:
        """Get child streams of a given stream
        
        Args:
            stream_name: Parent stream name (e.g., '//depot/main')
        
        Returns:
            Dict with status and list of child streams
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Verify stream exists
                existing = p4.run("streams", "-F", f"Stream={stream_name}")
                if not existing:
                    all_streams = p4.run("streams", "-a", "-F", f"Stream={stream_name}")
                    if not all_streams:
                        return {"status": "error", "message": f"Stream '{stream_name}' does not exist"}

                children = p4.run("streams", "-F", f"Parent={stream_name}")
                if not children:
                    return {"status": "success", "message": "No child streams found"}
                return {"status": "success", "message": [{k: v for k, v in child.items()} for child in children]}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get children of stream '{stream_name}': {e}")
                return {"status": "error", "message": str(e)}

    async def get_stream_parent(self, stream_name: str) -> Dict[str, Any]:
        """Get parent stream of a given stream
        
        Args:
            stream_name: Stream name (e.g., '//depot/dev')
        
        Returns:
            Dict with status and parent stream name
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Verify stream exists
                existing = p4.run("streams", "-F", f"Stream={stream_name}")
                if not existing:
                    all_streams = p4.run("streams", "-a", "-F", f"Stream={stream_name}")
                    if not all_streams:
                        return {"status": "error", "message": f"Stream '{stream_name}' does not exist"}

                stream_spec = p4.run("stream", "-o", stream_name)[0]
                if stream_spec.get("Parent") in (None, "none"):
                    return {"status": "success", "message": "No parent stream (this is a mainline stream)"}
                parent = stream_spec.get("Parent")
                return {"status": "success", "message": parent}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get parent of stream '{stream_name}': {e}")
                return {"status": "error", "message": str(e)}
            
    async def get_stream_graph(self, stream_name: str) -> Dict[str, Any]:
        """Get stream graph (parents/children)
        
        Args:
            stream_name: Stream name (e.g., '//depot/main')
        
        Returns:
            Dict with status and stream graph containing stream, parent, and children
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Verify stream exists
                existing = p4.run("streams", "-F", f"Stream={stream_name}")
                if not existing:
                    all_streams = p4.run("streams", "-a", "-F", f"Stream={stream_name}")
                    if not all_streams:
                        return {"status": "error", "message": f"Stream '{stream_name}' does not exist"}

                stream_spec = p4.run("stream", "-o", stream_name)[0]
                parent = stream_spec.get("Parent")
                children = p4.run("streams", "-F", f"Parent={stream_name}")
                return {
                    "status": "success",
                    "message": {
                        "stream": stream_name,
                        "parent": parent,
                        "children": [{k: v for k, v in child.items()} for child in children]
                    }
                }
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get stream graph for '{stream_name}': {e}")
                return {"status": "error", "message": str(e)}      
            

    async def get_stream_integration_status(
        self,
        stream_name: Optional[str] = None,
        both_directions: bool = False,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get stream integration status using 'p4 istat'
        
        Args:
            stream_name: Stream name (e.g., '//depot/dev'). If None, uses current workspace stream.
            both_directions: If True, show integration status in both directions
                            (to parent and from parent) (-a flag)
            force_refresh: If True, force istat to assume cache is stale and
                          search for pending integrations (-c flag)
        
        Returns:
            Dict with status and integration status info
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["istat"]
                
                if both_directions:
                    args.append("-a")
                
                if force_refresh:
                    args.append("-c")
                
                if stream_name:
                    args.append(stream_name)
                
                result = p4.run(*args)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get integration status for stream '{stream_name}': {e}")
                return {"status": "error", "message": str(e)}


    # Valid stream types for v1
    VALID_STREAM_TYPES = {"mainline", "development", "sparsedev", "release", "sparserel", "task", "virtual"}

    async def create_stream(
        self,
        stream_name: str,
        stream_type: str,
        parent: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        options: Optional[str] = None,
        parent_view: Optional[str] = None,
        paths: Optional[List[str]] = None,
        remapped: Optional[List[str]] = None,
        ignored: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new stream
        
        Validates all inputs before creation:
        - Stream type must be valid
        - Stream name must not already exist
        - Parent stream must exist and not be deleted (for non-mainline types)
        
        Args:
            stream_name: Stream depot path (e.g., '//depot/main')
            stream_type: Stream type - 'mainline', 'development', 'sparsedev', 'release', 'sparserel', 'task', 'virtual'
            parent: Parent stream (required for non-mainline streams, e.g., '//depot/main')
            name: Short name for the stream (defaults to last component of stream_name)
            description: Stream description text
            options: Stream options - combination of:
                     'allsubmit/ownersubmit', 'unlocked/locked', 
                     'toparent/notoparent', 'fromparent/nofromparent',
                     'mergedown/mergeany'
            parent_view: How to treat parent view - 'inherit' or 'noinherit'
            paths: List of view paths (e.g., ['share ...', 'isolate dir/...'])
            remapped: List of remapped paths (e.g., ['dir/... other_dir/...'])
            ignored: List of ignored paths (e.g., ['*.tmp', 'temp/...'])
        
        Returns:
            Dict with status and result message
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Step 1: Validate stream type
                if stream_type not in self.VALID_STREAM_TYPES:
                    return {
                        "status": "error",
                        "message": f"Invalid stream type '{stream_type}'. Must be one of: {', '.join(sorted(self.VALID_STREAM_TYPES))}"
                    }
                
                # Step 2: Check for duplicate stream name
                existing = p4.run("streams", "-F", f"Stream={stream_name}")
                if len(existing) > 0:
                    return {
                        "status": "error",
                        "message": f"Stream '{stream_name}' already exists"
                    }
                
                # Step 3: Validate parent stream for non-mainline types
                if stream_type != "mainline":
                    if not parent:
                        return {
                            "status": "error",
                            "message": f"Parent stream is required for '{stream_type}' stream type"
                        }
                    
                    # Check if parent exists in active streams
                    active_parent = p4.run("streams", "-F", f"Stream={parent}")
                    parent_exists = len(active_parent) > 0
                    parent_deleted = False
                    
                    if not parent_exists:
                        # Check if parent exists but is deleted
                        all_parent = p4.run("streams", "-a", "-F", f"Stream={parent}")
                        if len(all_parent) > 0:
                            parent_exists = True
                            parent_deleted = True
                    
                    if not parent_exists:
                        return {
                            "status": "error",
                            "message": f"Parent stream '{parent}' does not exist"
                        }
                    
                    if parent_deleted:
                        return {
                            "status": "error",
                            "message": f"Parent stream '{parent}' has been deleted. Cannot create a child of a deleted stream."
                        }
                
                # Step 4: Create the stream
                stream_spec = p4.fetch_stream(stream_name)
                
                # Set required fields
                stream_spec["Stream"] = stream_name
                stream_spec["Type"] = stream_type
                
                # Set parent (required for non-mainline)
                if parent:
                    stream_spec["Parent"] = parent
                elif stream_type == "mainline":
                    stream_spec["Parent"] = "none"
                
                # Set optional fields
                if name:
                    stream_spec["Name"] = name
                
                if description:
                    stream_spec["Description"] = description
                
                if options:
                    stream_spec["Options"] = options
                elif stream_type == "virtual":
                    # Virtual streams default to notoparent nofromparent
                    default_opts = stream_spec.get("Options", "")
                    default_opts = default_opts.replace("toparent", "notoparent").replace("fromparent", "nofromparent")
                    stream_spec["Options"] = default_opts
                
                if parent_view:
                    stream_spec["ParentView"] = parent_view
                
                if paths:
                    stream_spec["Paths"] = paths
                
                if remapped:
                    stream_spec["Remapped"] = remapped
                
                if ignored:
                    stream_spec["Ignored"] = ignored
                
                result = p4.save_stream(stream_spec)
                return {"status": "success", "message": result}
            except P4Exception as e:
                error_str = str(e)
                # Handle permission errors with a clear message
                if "don't have permission" in error_str.lower() or "openstreamspec" in error_str.lower() or "you don't have" in error_str.lower():
                    logger.error(f"P4Error: Permission denied creating stream '{stream_name}': {e}")
                    return {
                        "status": "error",
                        "message": f"Permission denied: you lack the required permission to create stream '{stream_name}'. Contact your Perforce administrator.",
                        "detail": error_str
                    }
                logger.error(f"P4Error: Failed to create stream '{stream_name}': {e}")
                return {"status": "error", "message": error_str}
    
    async def update_stream(
        self,
        stream_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        options: Optional[str] = None,
        parent_view: Optional[str] = None,
        paths: Optional[List[str]] = None,
        remapped: Optional[List[str]] = None,
        ignored: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Update an existing stream
        
        Validates before saving:
        - Stream must exist
        - Stream must not be locked (force/-f is not allowed in v1)
        - Warns when workspaces are bound to the stream
        - Blocks destructive changes (Paths/Remapped/Ignored) when open files exist
          in bound workspaces
        
        Note: Force update (-f) is not supported in v1.
        
        Args:
            stream_name: Stream depot path (e.g., '//depot/main')
            name: Short name for the stream
            description: Stream description text
            options: Stream options - combination of:
                     'allsubmit/ownersubmit', 'unlocked/locked', 
                     'toparent/notoparent', 'fromparent/nofromparent',
                     'mergedown/mergeany'
            parent_view: How to treat parent view - 'inherit' or 'noinherit'
            paths: List of view paths (e.g., ['share ...', 'isolate dir/...'])
            remapped: List of remapped paths
            ignored: List of ignored paths
        
        Returns:
            Dict with status and result message
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Step 1: Verify stream exists
                existing = p4.run("streams", "-F", f"Stream={stream_name}")
                if len(existing) == 0:
                    return {
                        "status": "error",
                        "message": f"Stream '{stream_name}' does not exist"
                    }
                
                # Step 2: Fetch current stream spec
                stream_spec = p4.fetch_stream(stream_name)
                
                # Step 3: Check if stream is locked
                current_options = stream_spec.get("Options", "")
                if "locked" in current_options.lower() and "unlocked" not in current_options.lower():
                    return {
                        "status": "error",
                        "message": f"Stream '{stream_name}' is locked. Force update (-f) is not allowed in v1. Contact the stream owner or an administrator."
                    }
                
                # Step 3.5: Check if stream spec requires resolve before editing
                try:
                    resolve_preview = p4.run("stream", "resolve", "-n", stream_name)
                    if resolve_preview:
                        return {
                            "status": "error",
                            "message": f"Stream '{stream_name}' has pending spec conflicts that must be resolved before editing. Use resolve_stream_spec() or 'p4 resolve -So' first. MCP will not auto-resolve.",
                            "resolve_preview": resolve_preview
                        }
                except P4Exception:
                    # stream resolve -n may fail if no resolve is needed; that's fine
                    pass
                
                # Step 4: Check for bound workspaces
                bound_workspaces = p4.run("clients", "-S", stream_name)
                has_bound_workspaces = len(bound_workspaces) > 0
                
                # Step 5: Determine if this is a view-affecting (destructive) change
                is_view_change = any([
                    paths is not None,
                    remapped is not None,
                    ignored is not None,
                    parent_view is not None
                ])
                
                # Step 6: If view-affecting change with bound workspaces, check for open files
                if is_view_change and has_bound_workspaces:
                    all_open_files = []
                    for ws in bound_workspaces:
                        ws_name = ws.get("client", ws.get("Client", ""))
                        if ws_name:
                            opened = p4.run("opened", "-C", ws_name)
                            if opened:
                                all_open_files.extend([
                                    {"workspace": ws_name, "file": f.get("depotFile", f.get("clientFile", "unknown"))}
                                    for f in opened
                                ])
                    
                    if all_open_files:
                        return {
                            "status": "error",
                            "message": f"Cannot modify stream view (Paths/Remapped/Ignored/ParentView): {len(all_open_files)} file(s) are open in bound workspaces. Submit or revert changes first.",
                            "open_files": all_open_files[:20],
                            "open_file_count": len(all_open_files),
                            "bound_workspace_count": len(bound_workspaces)
                        }
                
                # Step 7: Apply updates
                if name:
                    stream_spec["Name"] = name
                
                if description:
                    stream_spec["Description"] = description
                
                if options:
                    stream_spec["Options"] = options
                
                if paths:
                    stream_spec["Paths"] = paths
                
                if remapped:
                    stream_spec["Remapped"] = remapped
                
                if ignored:
                    stream_spec["Ignored"] = ignored
                
                # Step 8: Save (no -f flag in v1)
                result = p4.save_stream(stream_spec)
                
                # Step 9: ParentView can only be changed via 'p4 stream parentview';
                # Perforce rejects ParentView changes through spec save.
                pv_result = None
                if parent_view:
                    try:
                        pv_result = p4.run("stream", "parentview", f"--{parent_view}", stream_name)
                    except P4Exception as pv_err:
                        return {
                            "status": "error",
                            "message": f"Stream saved, but failed to change ParentView to '{parent_view}': {pv_err}"
                        }
                
                response = {"status": "success", "message": result}
                if pv_result:
                    response["parent_view_result"] = pv_result
                if has_bound_workspaces:
                    response["warning"] = f"{len(bound_workspaces)} workspace(s) are bound to this stream and may be affected by this change."
                    response["bound_workspaces"] = [ws.get("client", ws.get("Client", "")) for ws in bound_workspaces]
                return response
            except P4Exception as e:
                error_str = str(e)
                if "don't have permission" in error_str.lower() or "openstreamspec" in error_str.lower() or "you don't have" in error_str.lower():
                    logger.error(f"P4Error: Permission denied updating stream '{stream_name}': {e}")
                    return {
                        "status": "error",
                        "message": f"Permission denied: you lack the required permission to update stream '{stream_name}'. Contact your Perforce administrator.",
                        "detail": error_str
                    }
                if "resolve" in error_str.lower() or "must resolve" in error_str.lower():
                    logger.error(f"P4Error: Stream '{stream_name}' has unresolved changes: {e}")
                    return {
                        "status": "error",
                        "message": f"Stream '{stream_name}' has newer submitted changes that require resolve before editing. Use 'p4 resolve -So' or resolve_stream_spec() first.",
                        "detail": error_str
                    }
                logger.error(f"P4Error: Failed to update stream '{stream_name}': {e}")
                return {"status": "error", "message": error_str}

    async def edit_stream_spec(
        self,
        stream_name: str,
        changelist: Optional[str] = None
    ) -> Dict[str, Any]:
        """Open stream spec for private editing
        
        Opens the stream spec in private edit mode using 'p4 edit -So'.
        The stream spec is opened like a file and can be shelved, resolved,
        or reverted before being submitted.
        
        Blocks if the stream spec has pending conflicts requiring resolve.
        
        Args:
            stream_name: Stream depot path (e.g., '//depot/main')
            changelist: Pending changelist to open the spec in (-c flag). If None, uses default changelist.
        
        Returns:
            Dict with status and result message
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Check if stream spec requires resolve before opening for edit
                # Note: 'p4 stream resolve -n' operates on the workspace's stream,
                # no stream_name argument is accepted.
                try:
                    resolve_preview = p4.run("stream", "resolve", "-n")
                    if resolve_preview:
                        return {
                            "status": "error",
                            "message": f"Stream '{stream_name}' has pending spec conflicts that must be resolved before opening for edit. Use resolve_stream_spec() or 'p4 resolve -So' first. MCP will not auto-resolve.",
                            "resolve_preview": resolve_preview
                        }
                except P4Exception:
                    pass
                
                # 'p4 edit -So' opens the workspace's stream spec for edit.
                # It does not take a stream name argument.
                args = ["edit", "-So"]
                
                if changelist:
                    args.append("-c")
                    args.append(changelist)
                
                result = p4.run(*args)
                return {"status": "success", "message": result}
            except P4Exception as e:
                error_str = str(e)
                if "don't have permission" in error_str.lower() or "openstreamspec" in error_str.lower():
                    logger.error(f"P4Error: Permission denied opening stream spec '{stream_name}': {e}")
                    return {
                        "status": "error",
                        "message": f"Permission denied: you lack the required permission to open stream spec '{stream_name}'. Contact your Perforce administrator.",
                        "detail": error_str
                    }
                logger.error(f"P4Error: Failed to open stream spec '{stream_name}' for edit: {e}")
                return {"status": "error", "message": error_str}

    async def resolve_stream_spec(
        self,
        stream_name: str,
        resolve_mode: str = "auto"
    ) -> Dict[str, Any]:
        """Resolve pending private stream spec edits
        
        Resolves conflicts on a privately-opened stream spec using 'p4 resolve -So'.
        
        Args:
            stream_name: Stream depot path (e.g., '//depot/main')
            resolve_mode: Resolve strategy:
                - 'auto' (-am): Automatic merge
                - 'accept_theirs' (-at): Accept theirs (server version)
                - 'accept_yours' (-ay): Accept yours (your edits)
                - 'accept_safe' (-as): Accept safe (only non-conflicting)
        
        Returns:
            Dict with status and resolve result
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                resolve_flags = {
                    "auto": "-am",
                    "accept_theirs": "-at",
                    "accept_yours": "-ay",
                    "accept_safe": "-as"
                }
                
                if resolve_mode not in resolve_flags:
                    return {
                        "status": "error",
                        "message": f"Invalid resolve mode '{resolve_mode}'. Must be one of: {', '.join(resolve_flags.keys())}"
                    }
                
                # 'p4 resolve -So' operates on the workspace's stream spec.
                # It does not take a stream name argument.
                args = ["resolve", "-So", resolve_flags[resolve_mode]]
                result = p4.run(*args)
                return {"status": "success", "message": result}
            except P4Exception as e:
                error_str = str(e)
                # "not opened" means no spec is open for resolve — treat as success
                if "not opened" in error_str.lower():
                    return {
                        "status": "success",
                        "message": f"Stream '{stream_name}' has no open spec to resolve"
                    }
                logger.error(f"P4Error: Failed to resolve stream spec '{stream_name}': {e}")
                return {"status": "error", "message": error_str}

    async def revert_stream_spec(
        self,
        stream_name: str
    ) -> Dict[str, Any]:
        """Revert pending private stream spec edits
        
        Reverts a privately-opened stream spec using 'p4 revert -So',
        discarding any pending changes.
        
        Args:
            stream_name: Stream depot path (e.g., '//depot/main')
        
        Returns:
            Dict with status and result message
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # 'p4 revert -So' operates on the workspace's stream spec.
                # It does not take a stream name argument.
                result = p4.run("revert", "-So")
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to revert stream spec '{stream_name}': {e}")
                return {"status": "error", "message": str(e)}

    async def shelve_stream_spec(
        self,
        changelist: str
    ) -> Dict[str, Any]:
        """Shelve an open stream spec
        
        Shelves a privately-opened stream spec using 'p4 shelve -As'.
        The stream spec must already be open for edit (via edit_stream_spec).
        
        Args:
            changelist: Changelist containing the open stream spec (-c flag)
        
        Returns:
            Dict with status and result message
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                result = p4.run("shelve", "-As", "-c", changelist)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to shelve stream spec in changelist '{changelist}': {e}")
                return {"status": "error", "message": str(e)}

    async def unshelve_stream_spec(
        self,
        changelist: str,
        target_changelist: Optional[str] = None
    ) -> Dict[str, Any]:
        """Unshelve a shelved stream spec
        
        Restores a shelved stream spec using 'p4 unshelve -As'.
        
        Args:
            changelist: Changelist containing the shelved stream spec (-s flag)
            target_changelist: Target changelist to unshelve into (-c flag). If None, uses default.
        
        Returns:
            Dict with status and result message
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["unshelve", "-As", "-s", changelist]
                
                if target_changelist:
                    args.append("-c")
                    args.append(target_changelist)
                
                result = p4.run(*args)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to unshelve stream spec from changelist '{changelist}': {e}")
                return {"status": "error", "message": str(e)}
    
    async def delete_stream(
        self,
        stream_name: str
    ) -> Dict[str, Any]:
        """Delete a stream with safety validations
        
        Validates before deletion:
        - Stream must exist and not already be deleted
        - No child streams may reference the stream
        - No client workspaces may be bound to the stream
        
        Note: Force delete (-f) is not supported in v1.
        Deleted streams can be reported afterwards using list_streams(all_streams=True).
        
        Args:
            stream_name: Stream depot path (e.g., '//depot/dev')
        
        Returns:
            Dict with status, validation results, and result message
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Step 1: Verify stream exists and is not already deleted
                active_streams = p4.run("streams", "-F", f"Stream={stream_name}")
                stream_exists = len(active_streams) > 0
                already_deleted = False
                
                if not stream_exists:
                    # Check if it was already deleted
                    all_streams = p4.run("streams", "-a", "-F", f"Stream={stream_name}")
                    if len(all_streams) > 0:
                        already_deleted = True
                
                if already_deleted:
                    return {
                        "status": "error",
                        "message": f"Stream '{stream_name}' has already been deleted"
                    }
                
                if not stream_exists:
                    return {
                        "status": "error",
                        "message": f"Stream '{stream_name}' does not exist"
                    }
                
                # Step 2: Check for child streams
                child_streams = p4.run("streams", "-F", f"Parent={stream_name}")
                if len(child_streams) > 0:
                    child_names = [c.get("Stream", "unknown") for c in child_streams]
                    return {
                        "status": "error",
                        "message": f"Cannot delete stream '{stream_name}': {len(child_streams)} child stream(s) reference it as parent. Reparent or delete child streams first.",
                        "child_streams": child_names
                    }
                
                # Step 3: Check for bound workspaces
                bound_workspaces = p4.run("clients", "-S", stream_name)
                if len(bound_workspaces) > 0:
                    ws_names = [ws.get("client", ws.get("Client", "unknown")) for ws in bound_workspaces]
                    return {
                        "status": "error",
                        "message": f"Cannot delete stream '{stream_name}': {len(bound_workspaces)} workspace(s) are bound to it. Switch or delete bound workspaces first.",
                        "bound_workspaces": ws_names
                    }
                
                # Step 4: Execute deletion (no -f flag in v1)
                result = p4.run("stream", "-d", stream_name)
                return {
                    "status": "success",
                    "message": f"Stream '{stream_name}' has been deleted. Use list_streams(all_streams=True) to see deleted streams.",
                    "result": result
                }
            except P4Exception as e:
                error_str = str(e)
                if "don't have permission" in error_str.lower() or "you don't have" in error_str.lower():
                    logger.error(f"P4Error: Permission denied deleting stream '{stream_name}': {e}")
                    return {
                        "status": "error",
                        "message": f"Permission denied: you lack the required permission to delete stream '{stream_name}'. Contact your Perforce administrator.",
                        "detail": error_str
                    }
                logger.error(f"P4Error: Failed to delete stream '{stream_name}': {e}")
                return {"status": "error", "message": error_str}
            
    async def copy_stream(
        self,
        stream: Optional[str] = None,
        parent_stream: Optional[str] = None,
        file_paths: Optional[List[str]] = None,
        changelist: Optional[str] = None,
        preview: bool = False,
        force: bool = False,
        virtual: bool = False,
        reverse: bool = False,
        quiet: bool = False,
        max_files: Optional[int] = None
    ) -> Dict[str, Any]:
        """Copy/promote files between streams (branch without integration history)
        
        Typically used to promote changes to a more stable stream.
        When used with streams (-S), copies from the specified stream to the workspace stream.
        Use --from semantics by setting reverse=True to copy FROM the workspace stream
        TO the parent/specified stream.
        
        Validates:
        - Workspace must be stream-based when using stream mode
        - Target stream must exist
        
        Note: Does not auto-resolve conflicts.
        
        Args:
            stream: Source stream for stream-based copy (-S flag). If None, uses file paths.
            parent_stream: Override parent stream when using -S (-P flag)
            file_paths: Source and target file paths for non-stream copy (e.g., ['//from/...', '//to/...'])
            changelist: Open files in the specified pending changelist (-c flag)
            preview: Preview only, don't actually open files for branch (-n flag)
            force: Force copying against stream's expected flow (-F flag).
                   Allows using an arbitrary view to copy into a stream.
            virtual: Open target files without transferring content (-v flag)
            reverse: Reverse the copy direction when using streams (-r flag)
            quiet: Suppress informational messages (-q flag)
            max_files: Limit the number of files processed (-m flag)
        
        Returns:
            Dict with status and list of files scheduled for copy
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                current_stream = None
                # Validate workspace is stream-based when using stream mode
                if stream:
                    ws_spec = p4.run("client", "-o")
                    if not ws_spec or not ws_spec[0].get("Stream"):
                        return {
                            "status": "error",
                            "message": "Current workspace is not stream-based. Stream copy requires a stream workspace."
                        }
                    current_stream = ws_spec[0].get("Stream")
                    
                    # Validate target stream exists
                    existing = p4.run("streams", "-F", f"Stream={stream}")
                    if len(existing) == 0:
                        return {
                            "status": "error",
                            "message": f"Stream '{stream}' does not exist"
                        }
                    
                    # Refresh workspace view: re-save the client spec so the
                    # server regenerates the view mapping from the stream.
                    # This is critical when the workspace was switched to a
                    # different stream (vs. originally created for it).
                    try:
                        p4.save_client(ws_spec[0])
                    except P4Exception:
                        pass  # best-effort; view may already be current
                    
                    # Ensure the have-table is populated.  Stream-aware
                    # commands (copy/merge) need the intersection of the
                    # client view and the branch view, which requires a
                    # non-empty have-table.  A bare 'sync -k' marks all
                    # head revisions as "have" without transferring content.
                    try:
                        have = p4.run("have", "-m1", f"{current_stream}/...")
                    except P4Exception:
                        have = []
                    if not have:
                        try:
                            p4.run("sync", "-k", f"{current_stream}/...")
                        except P4Exception:
                            pass  # best-effort
                
                args = ["copy"]
                
                # Add preview flag
                if preview:
                    args.append("-n")
                
                # Add force flag
                if force:
                    args.append("-F")
                
                # Add virtual flag
                if virtual:
                    args.append("-v")
                
                # Add quiet flag
                if quiet:
                    args.append("-q")
                
                # Add changelist
                if changelist:
                    args.append("-c")
                    args.append(changelist)
                
                # Add max files
                if max_files:
                    args.append(f"-m{max_files}")
                
                # Stream-based copy
                if stream:
                    args.append("-S")
                    args.append(stream)
                    
                    if parent_stream:
                        args.append("-P")
                        args.append(parent_stream)
                    
                    if reverse:
                        args.append("-r")
                
                # File path based copy
                if file_paths:
                    args.extend(file_paths)
                
                result = p4.run(*args)
                
                if not result:
                    return {
                        "status": "success",
                        "message": "No files to copy. Streams are already in sync.",
                        "files": []
                    }
                
                return {"status": "success", "message": result}
            except P4Exception as e:
                error_str = str(e)
                logger.error(f"P4Error: Failed to copy: {e}")
                # Provide actionable fallback when copy fails due to
                # client/branch view mismatch (common after stream switch).
                if "no target file" in error_str.lower() or "client and branch view" in error_str.lower():
                    ws_info = f" (workspace stream: {current_stream})" if current_stream else ""
                    return {
                        "status": "error",
                        "message": error_str,
                        "hint": (
                            f"'p4 copy -S' could not find overlapping files in the client and branch views{ws_info}. "
                            "This often happens when the workspace was switched to a stream rather than "
                            "originally created for it. Workaround: use the 'integrate' action with "
                            "stream and reverse flags instead, which is more permissive about view mapping."
                        )
                    }
                return {"status": "error", "message": error_str}
            
    async def merge_stream(
        self,
        stream: Optional[str] = None,
        parent_stream: Optional[str] = None,
        file_paths: Optional[List[str]] = None,
        changelist: Optional[str] = None,
        preview: bool = False,
        force: bool = False,
        reverse: bool = False,
        quiet: bool = False,
        max_files: Optional[int] = None,
        output_base: bool = False
    ) -> Dict[str, Any]:
        """Merge changes from a more stable stream into the current workspace stream
        
        When used with streams (-S), merges from the specified stream to the workspace stream.
        Unlike integrate, merge automatically determines the direction based on stream relationships.
        
        Use parent_stream (-P) for one-off propagation between non-parent streams.
        
        Validates:
        - Workspace must be stream-based when using stream mode
        - Source stream must exist
        
        Note: MCP does not auto-resolve conflicts. After merge, use 'p4 resolve' to
        resolve any conflicts, then 'p4 submit' to complete the merge.
        
        Args:
            stream: Source stream for stream-based merge (-S flag, e.g., '//depot/main')
            parent_stream: Override parent for non-parent stream merge (-P flag).
                          Enables one-off propagation between streams that are not
                          direct parent/child (e.g., merge between two sibling dev streams).
            file_paths: File paths to merge (optional, defaults to all files in stream)
            changelist: Open files in the specified pending changelist (-c flag)
            preview: Preview only, don't actually schedule merge (-n flag).
                    Use this to see what would be merged before executing.
            force: Force merging against stream's expected flow (-F flag).
                   Allows using an arbitrary view to merge into a stream.
            reverse: Reverse the merge direction when using streams (-r flag)
            quiet: Suppress informational messages (-q flag)
            max_files: Limit the number of files processed (-m flag)
            output_base: Show the base revision for the merge with each scheduled resolve (-Ob flag)
        
        Returns:
            Dict with status, list of files scheduled for merge, and next-step guidance
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                current_stream = None
                # Validate workspace is stream-based when using stream mode
                if stream:
                    ws_spec = p4.run("client", "-o")
                    if not ws_spec or not ws_spec[0].get("Stream"):
                        return {
                            "status": "error",
                            "message": "Current workspace is not stream-based. Stream merge requires a stream workspace."
                        }
                    current_stream = ws_spec[0].get("Stream")
                    
                    # Validate source stream exists
                    existing = p4.run("streams", "-F", f"Stream={stream}")
                    if len(existing) == 0:
                        return {
                            "status": "error",
                            "message": f"Source stream '{stream}' does not exist"
                        }
                    
                    # Validate parent_stream override if specified
                    if parent_stream:
                        parent_existing = p4.run("streams", "-F", f"Stream={parent_stream}")
                        if len(parent_existing) == 0:
                            return {
                                "status": "error",
                                "message": f"Parent override stream '{parent_stream}' does not exist"
                            }
                    
                    # Refresh workspace view (see copy_stream for rationale)
                    try:
                        p4.save_client(ws_spec[0])
                    except P4Exception:
                        pass
                    
                    # Ensure have-table is populated for stream-aware merge
                    try:
                        have = p4.run("have", "-m1", f"{current_stream}/...")
                    except P4Exception:
                        have = []
                    if not have:
                        try:
                            p4.run("sync", "-k", f"{current_stream}/...")
                        except P4Exception:
                            pass
                
                args = ["merge"]
                
                # Add preview flag
                if preview:
                    args.append("-n")
                
                # Add force flag (must be uppercase -F for p4 merge)
                if force:
                    args.append("-F")
                
                # Add quiet flag
                if quiet:
                    args.append("-q")
                
                # Add output base flag (-Ob shows base revision with each resolve)
                if output_base:
                    args.append("-Ob")
                
                # Add changelist
                if changelist:
                    args.append("-c")
                    args.append(changelist)
                
                # Add max files
                if max_files:
                    args.append(f"-m{max_files}")
                
                # Stream-based merge
                if stream:
                    args.append("-S")
                    args.append(stream)
                    
                    if parent_stream:
                        args.append("-P")
                        args.append(parent_stream)
                    
                    if reverse:
                        args.append("-r")
                
                # File paths
                if file_paths:
                    args.extend(file_paths)
                
                result = p4.run(*args)
                
                if not result:
                    return {
                        "status": "success",
                        "message": "No files to merge. Streams are already in sync.",
                        "files": []
                    }
                
                response = {"status": "success", "message": result}
                
                if not preview:
                    response["next_steps"] = (
                        "Files have been scheduled for merge. "
                        "Next: 1) Use 'p4 resolve' to resolve any conflicts (MCP will not auto-resolve). "
                        "2) Use 'p4 submit' to complete the merge."
                    )
                
                return response
            except P4Exception as e:
                error_str = str(e)
                logger.error(f"P4Error: Failed to merge: {e}")
                if "no target file" in error_str.lower() or "client and branch view" in error_str.lower():
                    ws_info = f" (workspace stream: {current_stream})" if current_stream else ""
                    return {
                        "status": "error",
                        "message": error_str,
                        "hint": (
                            f"'p4 merge -S' could not find overlapping files in the client and branch views{ws_info}. "
                            "This often happens when the workspace was switched to a stream rather than "
                            "originally created for it. Workaround: use the 'integrate' action with "
                            "stream and reverse flags instead, which is more permissive about view mapping."
                        )
                    }
                return {"status": "error", "message": error_str}
            
    async def integrate_stream(
        self,
        stream: Optional[str] = None,
        parent_stream: Optional[str] = None,
        file_paths: Optional[List[str]] = None,
        changelist: Optional[str] = None,
        branch: Optional[str] = None,
        preview: bool = False,
        force: bool = False,
        reverse: bool = False,
        quiet: bool = False,
        max_files: Optional[int] = None,
        schedule_branch_resolve: bool = False,
        output_base: bool = False,
        integrate_around_deleted: bool = False,
        skip_cherry_picked: bool = False
    ) -> Dict[str, Any]:
        """Integrate changes from one set of files to another
        
        When used with streams (-S), integrates from the specified stream to the workspace stream.
        
        Args:
            stream: Source stream for stream-based integration (-S flag)
            parent_stream: Override parent stream when using -S (-P flag)
            file_paths: Source and target file paths for file-based integration
            changelist: Open files in the specified pending changelist (-c flag)
            branch: Use branch spec for integration (-b flag)
            preview: Preview only, don't actually schedule integration (-n flag)
            force: Force integration to ignore integration history and treat
                   all source revisions as unintegrated (-f flag)
            reverse: Reverse the integration direction when using streams/branch (-r flag)
            quiet: Suppress informational messages (-q flag)
            max_files: Limit the number of files processed (-m flag)
            schedule_branch_resolve: Schedule 'branch resolves' instead of branching
                                     new target files automatically (-Rb flag)
            output_base: Show the base revision for the merge with each file opened (-Ob flag)
            integrate_around_deleted: If source file has been deleted and re-added,
                                     treat revisions before deletion as part of same file (-Di flag)
            skip_cherry_picked: Skip cherry-picked revisions already integrated.
                               Can improve merge results but may cause multiple resolves
                               per file to be scheduled (-Rs flag)
        
        Returns:
            Dict with status and list of files scheduled for integration
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["integrate"]
                
                # Add preview flag
                if preview:
                    args.append("-n")
                
                # Add force flag
                if force:
                    args.append("-f")
                
                # Add quiet flag
                if quiet:
                    args.append("-q")
                
                # Add output base flag (-Ob shows base revision with each opened file)
                if output_base:
                    args.append("-Ob")
                
                # Add changelist
                if changelist:
                    args.append("-c")
                    args.append(changelist)
                
                # Add max files
                if max_files:
                    args.append(f"-m{max_files}")
                
                # Integrate around deleted revisions
                if integrate_around_deleted:
                    args.append("-Di")
                
                # Schedule branch resolves instead of auto-branching
                if schedule_branch_resolve:
                    args.append("-Rb")
                
                # Skip cherry-picked revisions already integrated
                if skip_cherry_picked:
                    args.append("-Rs")
                
                # Branch spec based integration
                if branch:
                    args.append("-b")
                    args.append(branch)
                    
                    if reverse:
                        args.append("-r")
                
                # Stream-based integration
                elif stream:
                    args.append("-S")
                    args.append(stream)
                    
                    if parent_stream:
                        args.append("-P")
                        args.append(parent_stream)
                    
                    if reverse:
                        args.append("-r")
                
                # File path based integration
                if file_paths:
                    args.extend(file_paths)
                
                result = p4.run(*args)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to integrate: {e}")
                return {"status": "error", "message": str(e)}
            
    async def populate_stream(
        self,
        stream: Optional[str] = None,
        parent_stream: Optional[str] = None,
        branch: Optional[str] = None,
        source_path: Optional[str] = None,
        target_path: Optional[str] = None,
        description: Optional[str] = None,
        preview: bool = False,
        force: bool = False,
        reverse: bool = False,
        max_files: Optional[int] = None,
        show_files: bool = False
    ) -> Dict[str, Any]:
        """Branch a set of files as a one-step operation (without using a client workspace)
        
        Populate is typically used to seed a new stream/branch with files from a parent.
        Unlike copy/merge/integrate, populate does not require a client workspace.
        
        Args:
            stream: Stream to populate from (-S flag). Branches from parent stream.
            parent_stream: Override parent stream when using -S (-P flag)
            branch: Use branch spec to determine source and target (-b flag)
            source_path: Source file path for direct file-to-file populate (-s flag)
            target_path: Target file path for direct file-to-file populate (required with source_path)
            description: Description for the submitted changelist (-d flag)
            preview: Preview only, don't actually create files (-n flag)
            force: Force operation, populate files even if target is not empty.
                   By default deleted files are skipped; -f forces them to be branched.
            reverse: Reverse the direction of populate (-r flag)
            max_files: Limit the number of files processed (-m flag)
            show_files: Display list of files created by the populate command (-o flag)
        
        Returns:
            Dict with status and list of files populated
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["populate"]
                
                # Add preview flag
                if preview:
                    args.append("-n")
                
                # Add force flag
                if force:
                    args.append("-f")
                
                # Add show files flag
                if show_files:
                    args.append("-o")
                
                # Add max files
                if max_files:
                    args.append(f"-m{max_files}")
                
                # Add description
                if description:
                    args.append("-d")
                    args.append(description)
                
                # Branch spec based populate
                if branch:
                    args.append("-b")
                    args.append(branch)
                    
                    if reverse:
                        args.append("-r")
                
                # Stream-based populate
                elif stream:
                    args.append("-S")
                    args.append(stream)
                    
                    if parent_stream:
                        args.append("-P")
                        args.append(parent_stream)
                    
                    if reverse:
                        args.append("-r")
                
                # File path based populate: p4 populate [flags] from to
                elif source_path and target_path:
                    args.append(source_path)
                    args.append(target_path)
                
                result = p4.run(*args)
                return {"status": "success", "message": result}
            except P4Exception as e:
                error_str = str(e)
                logger.error(f"P4Error: Failed to populate: {e}")
                # Provide a clearer message when target already has files
                if "already exist" in error_str.lower() or "can't branch" in error_str.lower():
                    return {
                        "status": "error",
                        "message": error_str,
                        "hint": (
                            "'p4 populate' is designed for initial branching only — it fails "
                            "when target files already exist in the depot.  Use 'integrate' "
                            "(or 'merge'/'copy') instead to propagate subsequent changes "
                            "between streams that already share files.  To force-populate "
                            "over existing files, set force=True (-f flag).  Note: when "
                            "populating a child stream from its parent (the most common case), "
                            "set reverse=True so the direction is parent → child."
                        )
                    }
                return {"status": "error", "message": error_str}
            
    async def switch_stream(
        self,
        stream_name: str,
        workspace: Optional[str] = None,
        preview: bool = False
    ) -> Dict[str, Any]:
        """Switch a workspace to a different stream
        
        Switches the current or specified workspace to use a different stream.
        The workspace view is automatically updated to match the new stream's view.
        
        Validation checks performed:
        - Workspace must be stream-based (not classic)
        - Target stream must exist and not be deleted
        - No files can be open in the workspace
        
        Note: Force switch (-f) is not supported in v1.
        
        Args:
            stream_name: Target stream to switch to (e.g., '//depot/dev')
            workspace: Workspace name to switch. If None, uses current workspace.
            preview: Preview only, show what would happen without making changes
        
        Returns:
            Dict with status, validation results, and result message
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Get workspace name (use current if not specified)
                ws_name = workspace or p4.client
                
                # Step 1: Validate workspace is stream-based
                ws_spec = p4.run("client", "-o", ws_name)
                if not ws_spec:
                    return {"status": "error", "message": f"Workspace '{ws_name}' not found"}
                
                # p4 client -o returns a template for nonexistent workspaces.
                # Real workspaces have an 'Update' or 'Access' field.
                if not ws_spec[0].get("Update") and not ws_spec[0].get("Access"):
                    return {"status": "error", "message": f"Workspace '{ws_name}' does not exist"}
                
                current_stream = ws_spec[0].get("Stream")
                if not current_stream:
                    return {
                        "status": "error", 
                        "message": f"Workspace '{ws_name}' is not stream-based. Cannot switch streams on a classic workspace."
                    }
                
                # Step 2: Validate target stream exists and is not deleted
                # First check active streams
                active_streams = p4.run("streams", "-F", f"Stream={stream_name}")
                stream_exists = len(active_streams) > 0
                stream_deleted = False
                
                if not stream_exists:
                    # Check if stream exists but is deleted (using -a flag)
                    all_streams = p4.run("streams", "-a", "-F", f"Stream={stream_name}")
                    if len(all_streams) > 0:
                        stream_exists = True
                        stream_deleted = True
                
                if not stream_exists:
                    return {
                        "status": "error",
                        "message": f"Target stream '{stream_name}' does not exist"
                    }
                
                if stream_deleted:
                    return {
                        "status": "error",
                        "message": f"Target stream '{stream_name}' has been deleted. Cannot switch to a deleted stream."
                    }
                
                # Step 3: Check for open files in workspace
                opened_files = p4.run("opened", "-C", ws_name)
                has_open_files = len(opened_files) > 0
                
                if has_open_files:
                    open_file_list = [f.get("depotFile", f.get("clientFile", "unknown")) for f in opened_files[:10]]
                    return {
                        "status": "error",
                        "message": f"Cannot switch stream: workspace '{ws_name}' has {len(opened_files)} open file(s). Revert or submit changes before switching.",
                        "open_files": open_file_list,
                        "open_file_count": len(opened_files)
                    }
                
                # Step 4: Preview mode - show what would happen
                if preview:
                    # Get the target stream spec to show what the workspace would switch to.
                    # Note: 'p4 client -o -S stream ws_name' errors on existing clients,
                    # so we preview using the stream spec itself.
                    target_spec = p4.run("stream", "-o", stream_name)
                    return {
                        "status": "success",
                        "message": {
                            "preview": True,
                            "current_stream": current_stream,
                            "target_stream": stream_name,
                            "workspace": ws_name,
                            "target_stream_type": target_spec[0].get("Type") if target_spec else None,
                            "target_stream_parent": target_spec[0].get("Parent") if target_spec else None
                        }
                    }
                
                # Step 5: Execute the switch (without -f flag, not allowed in v1)
                args = ["client", "-s", "-S", stream_name]
                if workspace:
                    args.append(workspace)
                
                result = p4.run(*args)
                
                # Step 6: Initialize the have-table for the new stream.
                # After a stream switch the workspace view is regenerated but
                # the have-table is empty.  Stream-aware commands like
                # 'p4 copy -S' and 'p4 merge -S' need the have-table to
                # intersect with the branch view.  'sync -k' marks all head
                # revisions as "have" without transferring file content.
                sync_note = None
                try:
                    p4.run("sync", "-k", f"{stream_name}/...")
                except P4Exception as sync_err:
                    sync_note = f"Have-table sync after switch failed (non-fatal): {sync_err}"
                    logger.warning(sync_note)
                
                response = {
                    "status": "success", 
                    "message": f"Workspace '{ws_name}' switched from '{current_stream}' to stream '{stream_name}'",
                    "result": result
                }
                if sync_note:
                    response["warning"] = sync_note
                return response
            except P4Exception as e:
                logger.error(f"P4Error: Failed to switch workspace to stream '{stream_name}': {e}")
                return {"status": "error", "message": str(e)}

    async def create_stream_workspace(
        self,
        workspace_name: str,
        stream_name: str,
        root: str,
        description: Optional[str] = None,
        options: Optional[str] = None,
        host: Optional[str] = None,
        alt_roots: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new workspace associated with a stream
        
        Creates a stream-associated workspace. The workspace view is automatically
        generated based on the stream's Paths, Remapped, and Ignored fields.
        
        Args:
            workspace_name: Name for the new workspace
            stream_name: Stream to associate with (e.g., '//depot/main')
            root: Local root directory for the workspace
            description: Workspace description
            options: Workspace options - combination of:
                     'allwrite/noallwrite', 'clobber/noclobber',
                     'compress/nocompress', 'locked/unlocked',
                     'modtime/nomodtime', 'rmdir/normdir'
            host: Host restriction for the workspace
            alt_roots: List of alternate root directories
        
        Returns:
            Dict with status and result message
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Check if workspace already exists
                existing_spec = p4.run("client", "-o", workspace_name)
                if existing_spec and existing_spec[0].get("Update"):
                    return {
                        "status": "error",
                        "message": f"Workspace '{workspace_name}' already exists. Use a different name."
                    }

                # Fetch template workspace spec with stream association
                workspace_spec = p4.fetch_client("-S", stream_name, workspace_name)
                
                # Set required fields
                workspace_spec["Client"] = workspace_name
                workspace_spec["Root"] = root
                workspace_spec["Stream"] = stream_name
                
                # Set optional fields
                if description:
                    workspace_spec["Description"] = description
                
                if options:
                    workspace_spec["Options"] = options
                
                if host:
                    workspace_spec["Host"] = host
                
                if alt_roots:
                    workspace_spec["AltRoots"] = alt_roots
                
                result = p4.save_client(workspace_spec)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to create stream workspace '{workspace_name}': {e}")
                return {"status": "error", "message": str(e)}

    async def get_stream_workspace(
        self,
        workspace: Optional[str] = None,
        stream_name: Optional[str] = None,
        template: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get workspace spec, optionally with stream association
        
        Retrieves a workspace specification. Can also be used to preview
        what a workspace would look like if associated with a stream.
        
        Args:
            workspace: Workspace name. If None, uses current workspace.
            stream_name: Stream to associate for preview (-S flag)
            template: Template workspace to use (-t flag)
        
        Returns:
            Dict with status and workspace spec
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["client", "-o"]
                
                if stream_name:
                    args.append("-S")
                    args.append(stream_name)
                
                if template:
                    args.append("-t")
                    args.append(template)
                
                if workspace:
                    args.append(workspace)
                
                result = p4.run(*args)
                if not result:
                    return {"status": "error", "message": f"Workspace '{workspace or 'current'}' not found"}
                
                spec = result[0]
                # p4 client -o returns a template for nonexistent workspaces.
                # Real workspaces have an 'Update' or 'Access' field.
                if workspace and not spec.get("Update") and not spec.get("Access"):
                    return {"status": "error", "message": f"Workspace '{workspace}' does not exist"}

                return {"status": "success", "message": {k: v for k, v in spec.items()}}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get workspace: {e}")
                return {"status": "error", "message": str(e)}

    async def list_stream_workspaces(
        self,
        stream_name: Optional[str] = None,
        user: Optional[str] = None,
        name_filter: Optional[str] = None,
        limit: int = 50,
        unloaded: bool = False
    ) -> Dict[str, Any]:
        """List workspaces, optionally filtered by stream
        
        Args:
            stream_name: Stream to filter workspaces by (-S flag)
            user: Filter by user (-u flag)
            name_filter: Filter workspaces by name pattern (-e flag, e.g., 'svr-dev-rel*')
            limit: Maximum number of workspaces to return (-m flag, default: 50)
            unloaded: If True, list unloaded workspaces (-U flag)
        
        Returns:
            Dict with status and list of workspaces
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["clients"]
                
                # Add stream filter
                if stream_name:
                    # Verify stream exists before querying workspaces
                    existing = p4.run("streams", "-F", f"Stream={stream_name}")
                    if len(existing) == 0:
                        # Also check deleted streams
                        all_streams = p4.run("streams", "-a", "-F", f"Stream={stream_name}")
                        if len(all_streams) == 0:
                            return {"status": "error", "message": f"Stream '{stream_name}' does not exist"}
                    args.append("-S")
                    args.append(stream_name)
                
                # Add user filter
                if user:
                    args.append("-u")
                    args.append(user)
                
                # Add unloaded flag
                if unloaded:
                    args.append("-U")
                
                # Add name filter
                if name_filter:
                    args.append("-e")
                    args.append(name_filter)
                
                # Add max results limit
                args.append(f"-m{limit}")
                
                result = p4.run(*args)
                return {"status": "success", "message": [{k: v for k, v in ws.items()} for ws in result]}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to list workspaces: {e}")
                return {"status": "error", "message": str(e)}

    # -------------------------------------------------------------------------
    # Stream spec resolve detection
    # -------------------------------------------------------------------------

    async def check_stream_spec_resolve_needed(
        self,
        stream_name: str
    ) -> Dict[str, Any]:
        """Detect whether a stream spec has pending conflicts requiring resolve
        
        Uses 'p4 stream resolve -n' (preview mode) to check if the stream spec
        has conflicts from newer submitted changes. This is a read-only check
        that does NOT perform any resolve.
        
        Args:
            stream_name: Stream depot path (e.g., '//depot/main')
        
        Returns:
            Dict with status, resolve_needed flag, and conflict details
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Verify stream exists
                existing = p4.run("streams", "-F", f"Stream={stream_name}")
                if not existing:
                    all_streams = p4.run("streams", "-a", "-F", f"Stream={stream_name}")
                    if not all_streams:
                        return {"status": "error", "message": f"Stream '{stream_name}' does not exist"}

                # Preview resolve to detect pending conflicts.
                # 'p4 stream resolve -n' operates on the workspace's stream.
                # It does not take a stream name argument.
                resolve_preview = p4.run("stream", "resolve", "-n")
                
                if resolve_preview:
                    return {
                        "status": "success",
                        "resolve_needed": True,
                        "stream": stream_name,
                        "message": (
                            f"Stream '{stream_name}' has pending spec conflicts that require resolve. "
                            "Use resolve_stream_spec() or 'p4 resolve -So' to resolve. "
                            "Edit and submit operations will be blocked until conflicts are resolved. "
                            "MCP will not automatically resolve conflicts."
                        ),
                        "conflicts": resolve_preview
                    }
                else:
                    return {
                        "status": "success",
                        "resolve_needed": False,
                        "stream": stream_name,
                        "message": f"Stream '{stream_name}' has no pending spec conflicts"
                    }
            except P4Exception as e:
                error_str = str(e)
                # "No stream spec to resolve" or "not opened" means no conflicts
                if "no stream" in error_str.lower() or "nothing to resolve" in error_str.lower() or "no file" in error_str.lower() or "not opened" in error_str.lower():
                    return {
                        "status": "success",
                        "resolve_needed": False,
                        "stream": stream_name,
                        "message": f"Stream '{stream_name}' has no pending spec conflicts"
                    }
                logger.error(f"P4Error: Failed to check resolve status for stream '{stream_name}': {e}")
                return {"status": "error", "message": error_str}

    # -------------------------------------------------------------------------
    # Stream view validation helpers
    # -------------------------------------------------------------------------

    def _classify_path_against_stream(self, file_path: str, stream_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a file path against stream Paths/Remapped/Ignored rules.
        
        Checks the stream spec's Paths and Ignored fields to determine
        whether a file path is writable, read-only (import), isolated, or excluded.
        
        Args:
            file_path: Depot or relative path to classify
            stream_spec: Stream spec dict from p4 stream -o
        
        Returns:
            Dict with 'allowed' (bool), 'rule' (str), and 'detail' (str)
        """
        stream_root = stream_spec.get("Stream", "")
        paths = stream_spec.get("Paths", [])
        ignored = stream_spec.get("Ignored", [])
        remapped = stream_spec.get("Remapped", [])

        # Normalise file_path for comparison
        normalised = file_path

        # Check Ignored first – these are always blocked
        for pattern in ignored:
            pattern = pattern.strip()
            if not pattern:
                continue
            # Simple suffix / prefix matching for common patterns
            if pattern.endswith("/..."):
                prefix = pattern[:-4]  # strip /...
                if prefix in normalised:
                    return {
                        "allowed": False,
                        "rule": "ignored",
                        "detail": f"File matches ignored pattern '{pattern}' in stream spec"
                    }
            elif normalised.endswith(pattern.lstrip("*")):
                return {
                    "allowed": False,
                    "rule": "ignored",
                    "detail": f"File matches ignored pattern '{pattern}' in stream spec"
                }

        # Walk Paths entries – order matters, last match wins in Perforce
        # but for safety we record the most specific match
        best_match: Optional[Dict[str, Any]] = None
        for path_entry in paths:
            entry = path_entry.strip()
            if not entry:
                continue
            parts = entry.split(None, 1)
            if len(parts) < 2:
                continue
            path_type = parts[0].lower()   # share, isolate, import, import+, exclude
            path_pattern = parts[1]

            # Very lightweight glob: check if the depot path falls under this mapping
            # Convert stream-relative patterns to depot form for comparison
            depot_pattern = path_pattern
            if not depot_pattern.startswith("//"):
                depot_pattern = f"{stream_root}/{depot_pattern.lstrip('/')}"

            # Strip trailing /... for prefix comparison
            depot_prefix = depot_pattern.replace("/...", "")

            if normalised.startswith(depot_prefix) or normalised.startswith(path_pattern.replace("/...", "")):
                best_match = {"type": path_type, "pattern": entry}

        if best_match:
            ptype = best_match["type"]
            pattern = best_match["pattern"]

            if ptype == "exclude":
                return {
                    "allowed": False,
                    "rule": "excluded",
                    "detail": f"File is excluded by stream path rule '{pattern}'"
                }
            if ptype == "import":
                return {
                    "allowed": False,
                    "rule": "import_readonly",
                    "detail": f"File is imported as read-only by stream path rule '{pattern}'. Import paths cannot be edited."
                }
            if ptype in ("share", "isolate", "import+"):
                return {
                    "allowed": True,
                    "rule": ptype,
                    "detail": f"File is writable under stream path rule '{pattern}'"
                }

        # No matching path rule – the file is outside the stream view
        return {
            "allowed": False,
            "rule": "outside_view",
            "detail": f"File '{file_path}' is not mapped in the stream view"
        }

    async def validate_file_against_stream(
        self,
        file_paths: List[str],
        workspace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate file paths against stream view rules before edit or add
        
        Checks whether file paths are writable, read-only (import), excluded,
        or ignored according to the workspace's stream spec (p4 stream -o -v).
        
        Fails gracefully if the workspace is not stream-based.
        
        Args:
            file_paths: List of depot file paths to validate
            workspace: Workspace name. If None, uses current workspace.
        
        Returns:
            Dict with status, overall allowed flag, and per-file results
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Step 1: Get workspace spec and verify it is stream-based
                ws_name = workspace or p4.client
                ws_spec = p4.run("client", "-o", ws_name)
                if not ws_spec:
                    return {"status": "error", "message": f"Workspace '{ws_name}' not found"}
                
                # p4 client -o returns a template for nonexistent workspaces.
                # Real workspaces have an 'Update' or 'Access' field.
                if not ws_spec[0].get("Update") and not ws_spec[0].get("Access"):
                    return {"status": "error", "message": f"Workspace '{ws_name}' does not exist"}
                
                current_stream = ws_spec[0].get("Stream")
                if not current_stream:
                    return {
                        "status": "error",
                        "message": f"Workspace '{ws_name}' is not stream-based. Stream view validation does not apply to classic workspaces."
                    }
                
                # Step 2: Get stream spec with view (-v to see effective view)
                stream_spec = p4.run("stream", "-o", "-v", current_stream)
                if not stream_spec:
                    return {"status": "error", "message": f"Could not retrieve stream spec for '{current_stream}'"}
                
                spec = stream_spec[0]
                
                # Step 3: Validate each file path
                results = []
                all_allowed = True
                for fp in file_paths:
                    classification = self._classify_path_against_stream(fp, spec)
                    classification["file"] = fp
                    results.append(classification)
                    if not classification["allowed"]:
                        all_allowed = False
                
                return {
                    "status": "success",
                    "all_allowed": all_allowed,
                    "stream": current_stream,
                    "workspace": ws_name,
                    "file_count": len(file_paths),
                    "blocked_count": sum(1 for r in results if not r["allowed"]),
                    "results": results
                }
            except P4Exception as e:
                logger.error(f"P4Error: Failed to validate files against stream: {e}")
                return {"status": "error", "message": str(e)}

    async def validate_submit_against_stream(
        self,
        changelist: Optional[str] = None,
        workspace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate that opened files belong to the current stream before submit
        
        Checks all opened files (or those in a specific changelist) against
        the workspace's stream view. Any file outside the stream view or in a
        read-only / excluded / ignored path is flagged.
        
        Fails gracefully if the workspace is not stream-based.
        
        Args:
            changelist: Pending changelist to validate. If None, checks all opened files.
            workspace: Workspace name. If None, uses current workspace.
        
        Returns:
            Dict with status, overall submittable flag, and per-file results
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Step 1: Get workspace spec and verify it is stream-based
                ws_name = workspace or p4.client
                ws_spec = p4.run("client", "-o", ws_name)
                if not ws_spec:
                    return {"status": "error", "message": f"Workspace '{ws_name}' not found"}
                
                # p4 client -o returns a template for nonexistent workspaces.
                # Real workspaces have an 'Update' or 'Access' field.
                if not ws_spec[0].get("Update") and not ws_spec[0].get("Access"):
                    return {"status": "error", "message": f"Workspace '{ws_name}' does not exist"}
                
                current_stream = ws_spec[0].get("Stream")
                if not current_stream:
                    return {
                        "status": "error",
                        "message": f"Workspace '{ws_name}' is not stream-based. Stream view validation does not apply to classic workspaces."
                    }
                
                # Step 2: Get opened files
                opened_args = ["opened"]
                if changelist:
                    opened_args.extend(["-c", changelist])
                opened_args.extend(["-C", ws_name])
                
                opened_files = p4.run(*opened_args)
                if not opened_files:
                    return {
                        "status": "success",
                        "submittable": True,
                        "stream": current_stream,
                        "workspace": ws_name,
                        "message": "No opened files to validate",
                        "file_count": 0,
                        "blocked_count": 0,
                        "results": []
                    }
                
                # Step 3: Get stream spec with view
                stream_spec = p4.run("stream", "-o", "-v", current_stream)
                if not stream_spec:
                    return {"status": "error", "message": f"Could not retrieve stream spec for '{current_stream}'"}
                
                spec = stream_spec[0]
                
                # Step 4: Also get workspace view for cross-checking
                ws_view = ws_spec[0].get("View", [])
                
                # Step 5: Validate each opened file
                results = []
                all_submittable = True
                for f in opened_files:
                    depot_file = f.get("depotFile", f.get("clientFile", ""))
                    action = f.get("action", "unknown")
                    
                    # Classify against stream rules
                    classification = self._classify_path_against_stream(depot_file, spec)
                    classification["file"] = depot_file
                    classification["action"] = action
                    
                    if not classification["allowed"]:
                        all_submittable = False
                        classification["submittable"] = False
                    else:
                        classification["submittable"] = True
                    
                    results.append(classification)
                
                blocked = [r for r in results if not r["submittable"]]
                
                response = {
                    "status": "success",
                    "submittable": all_submittable,
                    "stream": current_stream,
                    "workspace": ws_name,
                    "file_count": len(results),
                    "blocked_count": len(blocked),
                    "results": results
                }
                
                if not all_submittable:
                    response["message"] = (
                        f"Submit blocked: {len(blocked)} file(s) violate stream rules. "
                        "See 'results' for per-file details with the specific stream rule that caused rejection."
                    )
                else:
                    response["message"] = "All opened files are valid for submit within the current stream view."
                
                return response
            except P4Exception as e:
                logger.error(f"P4Error: Failed to validate submit against stream: {e}")
                return {"status": "error", "message": str(e)}

    async def interchanges_stream(
        self,
        stream: str,
        reverse: bool = False,
        file_paths: Optional[List[str]] = None,
        long_output: bool = False,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """List outstanding changes between streams that have not yet been propagated
        
        Uses 'p4 interchanges -S' to show changelists that need to be merged or copied
        between the specified stream and the workspace stream.
        
        By default, shows changes in the source stream that have not been merged
        into the workspace stream. Use reverse=True to see changes in the workspace
        stream that have not been propagated to the source stream.
        
        Validates:
        - Workspace must be stream-based
        - Target stream must exist
        
        Args:
            stream: Stream to compare against (-S flag, e.g., '//depot/main')
            reverse: If True, reverse the comparison direction (-r flag).
                    Without reverse: shows changes in <stream> not yet in workspace stream.
                    With reverse: shows changes in workspace stream not yet in <stream>.
            file_paths: Optional file paths to limit the comparison
            long_output: If True, include full changelist descriptions (-l flag)
            limit: Maximum number of changelists to return (-m flag)
        
        Returns:
            Dict with status and list of outstanding changelists
        """
        async with self.connection_manager.get_connection() as p4:
            try:
                # Validate workspace is stream-based
                ws_spec = p4.run("client", "-o")
                if not ws_spec or not ws_spec[0].get("Stream"):
                    return {
                        "status": "error",
                        "message": "Current workspace is not stream-based. Interchanges requires a stream workspace."
                    }
                
                workspace_stream = ws_spec[0].get("Stream")
                
                # Validate target stream exists
                existing = p4.run("streams", "-F", f"Stream={stream}")
                if len(existing) == 0:
                    return {
                        "status": "error",
                        "message": f"Stream '{stream}' does not exist"
                    }
                
                args = ["interchanges", "-S", stream]
                
                if reverse:
                    args.append("-r")
                
                if long_output:
                    args.append("-l")
                
                # Note: p4 interchanges does not support the -m flag.
                # The limit parameter is applied client-side after fetching results.
                
                if file_paths:
                    args.extend(file_paths)
                
                result = p4.run(*args)
                
                # Apply client-side limit since p4 interchanges doesn't support -m
                if limit and result:
                    result = result[:limit]
                
                if not result:
                    direction = (
                        f"from '{workspace_stream}' to '{stream}'" if reverse
                        else f"from '{stream}' to '{workspace_stream}'"
                    )
                    return {
                        "status": "success",
                        "message": f"No outstanding changes {direction}. Streams are in sync.",
                        "changelists": [],
                        "count": 0
                    }
                
                direction_desc = (
                    f"in '{workspace_stream}' not yet propagated to '{stream}'" if reverse
                    else f"in '{stream}' not yet merged into '{workspace_stream}'"
                )
                
                return {
                    "status": "success",
                    "message": f"{len(result)} outstanding changelist(s) {direction_desc}",
                    "changelists": result,
                    "count": len(result),
                    "source_stream": stream,
                    "workspace_stream": workspace_stream,
                    "direction": "reverse" if reverse else "forward"
                }
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get interchanges for stream '{stream}': {e}")
                return {"status": "error", "message": str(e)}
