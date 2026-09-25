#!/bin/sh
# docker-entrypoint.sh
#
# Normalizes a bind-mounted P4TICKETS file so the non-root mcpuser can read it,
# then drops privileges before running the server.
#
# Why this exists: the image runs the server as the non-root mcpuser (uid 1000),
# but a host .p4tickets file is typically owner-only (0600). On runtimes that
# preserve host ownership (native Linux Docker/podman, podman/krun on macOS),
# the mounted file is owned by a foreign uid, so mcpuser gets "Permission
# denied" and P4 auth fails. mcpuser cannot even read (let alone copy) that
# file, so the fix must run as root: start the container as root, copy the
# ticket to a mcpuser-owned runtime path, repoint P4TICKETS at it, then drop to
# mcpuser via gosu. Copy failures (read-only FS, missing/unreadable ticket) are
# non-fatal — we simply fall through and let P4 report a normal auth error.
set -e

TICKETS="${P4TICKETS:-/home/mcpuser/.p4tickets}"
RUNTIME_TICKETS=/home/mcpuser/.p4tickets-runtime

# Cache the uid once to avoid a TOCTOU gap between the check and the copy/exec.
CURRENT_UID=$(id -u)

if [ "$CURRENT_UID" = "0" ]; then
    # gosu needs mcpuser to exist; fail loudly instead of with a cryptic error.
    getent passwd mcpuser >/dev/null || { echo "Error: mcpuser not found in passwd database" >&2; exit 1; }

    if [ -f "$TICKETS" ] && [ ! -L "$TICKETS" ]; then
        # Remove any stale copy from a prior run so install cannot fail on an
        # existing (possibly wrong-owner) file and silently leave P4TICKETS unset.
        rm -f "$RUNTIME_TICKETS"
        if install -m 600 -o mcpuser -g mcpuser "$TICKETS" "$RUNTIME_TICKETS" 2>/dev/null; then
            export P4TICKETS="$RUNTIME_TICKETS"
        fi
    elif [ -e "$TICKETS" ]; then
        # Directory or symlink where a regular file was expected: warn, then let
        # P4 report a normal auth error rather than silently doing nothing.
        echo "Warning: P4TICKETS ($TICKETS) is not a regular file; leaving it unchanged" >&2
    fi
    exec gosu mcpuser "$@"
fi

# Already non-root (e.g. `docker run --user 1000`): run as-is; if the ticket is
# unreadable this degrades to a normal auth error rather than a startup crash.
exec "$@"
