import inspect
import logging

from . import changelist_handlers
from . import file_handlers
from . import job_handlers
from . import review_handlers
from . import server_handlers
from . import shelve_handlers
from . import stream_handlers
from . import workspace_handlers

logger = logging.getLogger(__name__)

# Explicit list of handler modules – pkgutil.iter_modules cannot discover
# modules inside a PyInstaller binary, so we enumerate them here.
_HANDLER_MODULES = [
    changelist_handlers,
    file_handlers,
    job_handlers,
    review_handlers,
    server_handlers,
    shelve_handlers,
    stream_handlers,
    workspace_handlers,
]


class Handlers:
    """Main handler class that registers per-resource handler modules.

    Every ``<resource>_handlers`` module listed in ``_HANDLER_MODULES`` is
    inspected.  Its handler class (ending with ``Handlers``) is instantiated
    with the matching ``<resource>_services`` kwarg, and any
    ``_handle_query_<resource>`` / ``_handle_modify_<resource>`` methods are
    registered in the dispatch table.
    """

    def __init__(self, **services):
        self.dispatch = {}

        for module in _HANDLER_MODULES:

            # Find the handler class: any class defined in this module
            # whose name ends with "Handlers"
            handler_cls = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if name.endswith("Handlers") and obj.__module__ == module.__name__:
                    handler_cls = obj
                    break
            if handler_cls is None:
                continue

            # Derive the service kwarg from the handler __init__ signature
            sig = inspect.signature(handler_cls.__init__)
            svc_param_names = [
                p for p in sig.parameters if p != "self" and p.endswith("_services")
            ]
            if not svc_param_names:
                continue

            svc_name = svc_param_names[0]          # e.g. "workspace_services"
            svc_instance = services.get(svc_name)
            if svc_instance is None:
                continue

            handler_instance = handler_cls(svc_instance)

            # Register _handle_query_* and _handle_modify_* methods
            for attr_name in dir(handler_instance):
                if attr_name.startswith("_handle_query_"):
                    resource = attr_name[len("_handle_query_"):]
                    self.dispatch[("query", resource)] = getattr(handler_instance, attr_name)
                elif attr_name.startswith("_handle_modify_"):
                    resource = attr_name[len("_handle_modify_"):]
                    self.dispatch[("modify", resource)] = getattr(handler_instance, attr_name)

        logger.debug(
            "Handler dispatch table: %s",
            sorted(self.dispatch.keys()),
        )

    async def handle(self, operation, sub_operation, params):
        handler = self.dispatch.get((operation, sub_operation))
        if not handler:
            logger.error(f"Unknown operation: {operation}/{sub_operation}")
            return {"status": "error", "message": f"Unknown operation: {operation}/{sub_operation}"}
        return await handler(params)