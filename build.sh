#!/usr/bin/env bash

set -e

# This script must be executed, not sourced: it relies on an EXIT trap to
# restore p4mcp/_version.py, and EXIT traps do not fire in a sourcing shell.
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    echo "❌ build.sh must be executed, not sourced." >&2
    return 1
fi

command="${1:-build}"

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
EXECUTABLE_PATH="$SCRIPT_DIR/dist/p4-mcp-server/p4-mcp-server"
PYTHON_CMD="python3"

# --- Version configuration ---
# pyproject.toml's [project] version is the single source of truth.
VERSION_FILE="$SCRIPT_DIR/p4mcp/_version.py"
if [ -z "$RELEASE_VERSION" ]; then
    PYPROJECT_FILE="$SCRIPT_DIR/pyproject.toml"

    if [ ! -f "$PYPROJECT_FILE" ]; then
        echo "❌ Version file not found: $PYPROJECT_FILE" >&2
        exit 1
    fi

    # Take the first `version = "x.y.z"` line (the [project] version) and
    # strip the key, quotes and surrounding whitespace.
    RELEASE_VERSION=$(grep -E '^version *= *' "$PYPROJECT_FILE" | head -n1 \
        | cut -d '=' -f2- | tr -d " '\"" | cut -d'#' -f1)

    # Fail loudly rather than baking a stale default: a malformed pyproject.toml
    # or a missing version key must stop the build, not produce a wrong-version
    # binary. Set RELEASE_VERSION in the environment to override the source.
    if [ -z "$RELEASE_VERSION" ]; then
        echo "❌ Could not parse version from pyproject.toml" >&2
        exit 1
    fi
fi

# Version baked into the frozen binary. Defaults to RELEASE_VERSION, but CI
# (buildtools/buildscripts/compile.sh) overrides it with a build-number-qualified
# value while keeping RELEASE_VERSION for archive naming and p4python matching.
BAKE_VERSION="${BAKE_VERSION:-$RELEASE_VERSION}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_usage() {
    echo "Usage: $0 [build|run|clean|setup|package]"
    echo ""
    echo "Commands:"
    echo "  build    Setup venv, install deps, and build executable"
    echo "  run      Run the built executable (builds first if needed)"
    echo "  clean    Clean build artifacts and virtual environment"
    echo "  setup    Only setup virtual environment and install dependencies"
    echo "  package  Build and create versioned zip archive (cleans build/dist/.venv after successful packaging)"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 run"
    echo "  $0 setup"
    echo "  $0 clean"
    echo "  $0 package"
}

log_info()    { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error()   { echo -e "${RED}❌ $1${NC}"; }

check_python() {
    if ! command -v $PYTHON_CMD &> /dev/null; then
        log_error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    log_info "Using Python $PYTHON_VERSION"
    echo "Using Python $PYTHON_VERSION"
    log_info "Building version: $VERSION"
}

setup_venv() {
    log_info "Setting up virtual environment..."
    # Remove existing venv if it exists
    if [ -d "$VENV_DIR" ]; then
        log_warning "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
    fi
    # Create new virtual environment
    $PYTHON_CMD -m venv "$VENV_DIR"
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip
    log_success "Virtual environment created and activated"
}

install_dependencies() {
    log_info "Installing dependencies from requirements.txt..."
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt file not found in current directory"
        exit 1
    fi
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Set default p4python version to latest if not specified
    REL_VERSION="${RELEASE_VERSION:-$(pip index versions p4python 2>/dev/null | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | cut -d. -f1,2 | sort -V | tail -1)}"
    P4PYTHON_VERSION=$(pip index versions p4python 2>/dev/null | grep -Eo "${REL_VERSION}\.[0-9]+" | sort -V | tail -1)

    echo "Release version: ${REL_VERSION}"
    echo "P4Python version: ${P4PYTHON_VERSION}"
    echo "P4Python version test string: $P4PYTHON_VERSION"

    # Version configuration
    VERSION="${VERSION:-${REL_VERSION}}"
    ARCHIVE_NAME="p4-mcp-server-${VERSION}.tgz"

    echo "Package name will be: $ARCHIVE_NAME"

    # Install dependencies
    pip install -r requirements.txt
    if [ -z "$P4PYTHON_VERSION" ]; then
        log_warning "Could not determine P4Python version. Skipping p4python installation."
    else
        pip install p4python==$P4PYTHON_VERSION
    fi
    # Install PyInstaller if not already in requirements.txt
    if ! pip show pyinstaller &> /dev/null; then
        log_info "Installing PyInstaller..."
        pip install pyinstaller
    fi
    log_success "Dependencies installed successfully"
}

build_executable() {
    log_info "Building p4-mcp-server with PyInstaller..."
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    # Check if the spec file exists
    if [ ! -f "p4-mcp-server.spec" ]; then
        log_error "p4-mcp-server.spec file not found in current directory"
        exit 1
    fi
    # Clean previous build artifacts (but keep venv)
    log_info "Cleaning previous build artifacts..."
    rm -rf build/ dist/

    # Remove the "P4MCP.spec" and binary if they exist
    if [ -f "P4MCP.spec" ]; then
        log_info "Removing existing P4MCP.spec..."
        rm -f "P4MCP.spec"
    fi
    if [ -f "p4mcp/telemetry/P4MCP" ]; then
        log_info "Removing existing P4MCP binary..."
        rm -f "p4mcp/telemetry/P4MCP"
    fi

    # Build standalone binary for consent_ui.py
    log_info "Building standalone binary for consent_ui.py..."
    pyinstaller --onefile --distpath p4mcp/telemetry --name "P4MCP" p4mcp/telemetry/consent_ui.py
    if [ -f "p4mcp/telemetry/P4MCP" ]; then
        log_success "Standalone P4MCP binary created at p4mcp/telemetry/P4MCP"
    else
        log_error "Failed to build consent_ui binary"
        exit 1
    fi

    # Bake the version into _version.py so the frozen binary reports the right
    # version (importlib.metadata can't see package metadata inside a PyInstaller
    # bundle). Restore the importlib.metadata form on EXIT — success or failure —
    # via a trap.
    if [ -f "$VERSION_FILE" ]; then
        # A leftover .bak from a previously interrupted run means _version.py is
        # already baked; restore it first so we back up the canonical form, not
        # a stale baked one.
        if [ -f "$VERSION_FILE.bak" ]; then
            mv -f "$VERSION_FILE.bak" "$VERSION_FILE"
        fi
        log_info "Baking version $BAKE_VERSION into $VERSION_FILE for the frozen build..."
        cp "$VERSION_FILE" "$VERSION_FILE.bak"
        trap 'if [ -f "$VERSION_FILE.bak" ]; then mv -f "$VERSION_FILE.bak" "$VERSION_FILE"; fi' EXIT
        chmod u+w "$VERSION_FILE"
        cat > "$VERSION_FILE" <<EOF
"""Single source of truth for the package version.

This file was rewritten by build.sh to bake the static version into the frozen
PyInstaller binary. build.sh restores the importlib.metadata form (a try/except
around importlib.metadata.version) once the build completes.
"""
__version__ = "$BAKE_VERSION"
EOF
    fi

    # Run PyInstaller for main app
    log_info "Running PyInstaller for main app..."
    pyinstaller p4-mcp-server.spec
    # Check if build was successful and command is not package
    if [ "${command}" != "package" ]; then
        if [ -f "$EXECUTABLE_PATH" ]; then
            log_success "Build successful!"
            log_info "Executable created at: $EXECUTABLE_PATH"
            echo ""
            log_info "To run the server:"
            echo "  ./dist/p4-mcp-server [arguments]"
            echo ""
        else
            log_error "Build failed!"
            exit 1
        fi
    fi
}

create_package() {
    log_info "Creating package: $ARCHIVE_NAME"
    if [ ! -f "$EXECUTABLE_PATH" ]; then
        log_error "Executable not found. Please build first."
        exit 1
    fi
    # Remove existing package if it exists
    if [ -f "$SCRIPT_DIR/$ARCHIVE_NAME" ]; then
        log_warning "Removing existing package: $ARCHIVE_NAME"
        rm -f "$SCRIPT_DIR/$ARCHIVE_NAME"
    fi
    # Create tar.gz package with only the executable
    tar -czf "$ARCHIVE_NAME" -C "$SCRIPT_DIR/dist" p4-mcp-server
    if [ -f "$ARCHIVE_NAME" ]; then
        log_success "Package $ARCHIVE_NAME created successfully!"
        log_info "Package path: $SCRIPT_DIR/$ARCHIVE_NAME"
        # Show package contents
        # log_info "Package contents:"
        # tar -tzf "$ARCHIVE_NAME"
        # Show file size
        ARCHIVE_SIZE=$(ls -lh "$ARCHIVE_NAME" | awk '{print $5}')
        log_info "Package size: $ARCHIVE_SIZE"
        # Clean up build, dist directories and P4MCP.spec and P4MCP binary after successful packaging
        rm -rf build/ dist/ "$VENV_DIR"
        rm -f "P4MCP.spec" "p4mcp/telemetry/P4MCP"
        log_info "build/dist and .venv directories cleaned up after packaging!"
    else
        log_error "Failed to create package!"
        exit 1
    fi
}

run_executable() {
    if [ ! -f "$EXECUTABLE_PATH" ]; then
        log_warning "Executable not found. Building first..."
        full_build
    fi
    log_info "Running p4-mcp-server with arguments: $@"
    "$EXECUTABLE_PATH" "$@"
}

clean_all() {
    log_info "Cleaning all build artifacts and virtual environment..."
    rm -rf build/ dist/ "$VENV_DIR"
    # Also remove any existing archives
    rm -f "$SCRIPT_DIR"/p4-mcp-server-*.tgz
    log_success "Clean complete!"
}

full_build() {
    check_python
    setup_venv
    install_dependencies
    build_executable
}

setup_only() {
    check_python
    setup_venv
    install_dependencies
    log_success "Setup complete! Virtual environment ready at: $VENV_DIR"
    echo ""
    log_info "To activate the virtual environment manually, run:"
    echo "  source $VENV_DIR/bin/activate"
}

package_build() {
    full_build
    create_package
}

# Main script logic
case "${1:-build}" in
    "build")
        full_build
        ;;
    "run")
        shift
        if [ "$1" = "--" ]; then
            shift
        fi
        run_executable "$@"
        ;;
    "clean")
        clean_all
        ;;
    "setup")
        setup_only
        ;;
    "package")
        package_build
        ;;
    "-h"|"--help"|"help")
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac