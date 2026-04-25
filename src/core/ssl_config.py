import sys
import os
import logging

logger = logging.getLogger(__name__)


def configure_tls_ca_mode() -> None:
    """Configure TLS certificate source based on P4MCP_TLS_CA_MODE.

    Supported values:
    - system (default): use OS certificate store via truststore
    - certifi: disable truststore injection and use default Python behavior
    """
    raw_mode = os.getenv("P4MCP_TLS_CA_MODE", "system")
    mode = raw_mode.strip().lower() or "system"

    if mode == "certifi":
        logger.info(
            "TLS CA mode: certifi (truststore injection disabled; "
            "using default Python TLS certificate behavior)"
        )
        return

    if mode != "system":
        logger.warning("Unrecognized P4MCP_TLS_CA_MODE=%r; defaulting to system", raw_mode)

    try:
        import truststore
        truststore.inject_into_ssl()
        logger.info("TLS CA mode: system (using OS trust store via truststore)")
    except ImportError:
        logger.warning(
            "truststore is not installed; "
            "continuing with default Python TLS certificate behavior"
        )


def resolve_ssl_verify(args) -> object:
    """Determine SSL verify setting from parsed CLI args.

    Priority: --ca-bundle > --ssl-no-verify > None (let Config/env decide).

    Returns:
        str path, False, or None.

    Raises:
        SystemExit: if --ca-bundle path does not exist.
    """
    if args.ca_bundle:
        if not os.path.isfile(args.ca_bundle):
            logger.error("--ca-bundle path does not exist: %s", args.ca_bundle)
            sys.exit(1)
        return args.ca_bundle
    if args.ssl_no_verify:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return False
    return None  # let Config/env decide
