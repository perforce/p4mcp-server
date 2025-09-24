# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import importlib.metadata

dist = importlib.metadata.distribution("fastmcp")
fastmcp_dist_info = dist._path

# Choose platform-specific consent_ui binary
if sys.platform.startswith("win"):
    consent_ui = "src/telemetry/P4MCP.exe"
else:
    consent_ui = "src/telemetry/P4MCP"

a = Analysis(
    ['src/main.py'],
    pathex=["."],
    binaries=[],
    datas=[
        (consent_ui, 'consent'),
        ('icons/logo-p4mcp-icon.png', 'icons'),
        ('icons/logo-p4mcp-reg.png', 'icons'),
        (fastmcp_dist_info, os.path.basename(fastmcp_dist_info)),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='p4-mcp-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='p4-mcp-server',
)
