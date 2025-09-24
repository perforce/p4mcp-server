@echo off
setlocal enabledelayedexpansion

REM Enhanced build script for p4-mcp-server (Windows Batch)
REM Creates virtual environment, installs dependencies, and builds executable

REM Parse command line arguments first
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=build

REM Check for help commands immediately
if /i "%COMMAND%"=="help" goto :show_usage
if /i "%COMMAND%"=="-h" goto :show_usage
if /i "%COMMAND%"=="--help" goto :show_usage

REM Detect available Python command
set PYTHON_CMD=
where py >nul 2>&1 && set PYTHON_CMD=py
if not defined PYTHON_CMD (
    where python >nul 2>&1 && set PYTHON_CMD=python
)
if not defined PYTHON_CMD (
    where python3 >nul 2>&1 && set PYTHON_CMD=python3
)
if not defined PYTHON_CMD (
    echo [ERROR] Python 3 is not installed or not in PATH
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"

REM REM Version configuration
if "%RELEASE_VERSION%"=="" (
    
    set CONNECTION_FILE=%SCRIPT_DIR%src\core\connection.py
    
    if exist "!CONNECTION_FILE!" (
        set "VER_RAW="
        for /f "usebackq tokens=1* delims==" %%A in (`findstr /r /c:"^__version__ *= *" "!CONNECTION_FILE!"`) do (
            set VER_RAW=%%B
        )
        if defined VER_RAW (
            set "VER_STR=!VER_RAW: =!"
            set "VER_STR=!VER_STR:'=!"
            set "VER_STR=!VER_STR:"=!"
            for /f "tokens=1 delims=#;" %%V in ("!VER_STR!") do set "RELEASE_VERSION=%%V"
        ) else (
            call :log_warning "Could not parse __version__ from connection.py"
        )
    ) else (
        call :log_warning "Version file not found: !CONNECTION_FILE!"
    )
)

if "%RELEASE_VERSION%"=="" set RELEASE_VERSION=2025.1.0
set VERSION=%RELEASE_VERSION%
set ARCHIVE_NAME=p4-mcp-server-%VERSION%.zip
set VENV_DIR=%SCRIPT_DIR%.venv
set EXECUTABLE_PATH=%SCRIPT_DIR%dist\p4-mcp-server\p4-mcp-server.exe
set ARCHIVE_NAME=p4-mcp-server-%VERSION%.zip

REM Shift to get remaining arguments for executable
shift
set EXECUTABLE_ARGS=
:parse_args
if "%1"=="" goto :args_done
if "%1"=="--" (
    shift
    goto :parse_args
)
set EXECUTABLE_ARGS=%EXECUTABLE_ARGS% %1
shift
goto :parse_args
:args_done

REM Main script logic with improved logging
if /i "%COMMAND%"=="build" (
    call :log_info "Selected command: build"
    goto :full_build
)
if /i "%COMMAND%"=="run" (
    call :log_info "Selected command: run"
    goto :run_executable
)
if /i "%COMMAND%"=="clean" (
    call :log_info "Selected command: clean"
    goto :clean_all
)
if /i "%COMMAND%"=="setup" (
    call :log_info "Selected command: setup"
    goto :setup_only
)
if /i "%COMMAND%"=="package" (
    call :log_info "Selected command: package"
    goto :package_build
)

echo [91m❌ Unknown command: %COMMAND%[0m
goto :show_usage

:show_usage
echo Usage: build.bat [build^|run^|clean^|setup^|package]
echo.
echo Commands:
echo   build    Setup venv, install deps, and build executable
echo   run      Run the built executable (builds first if needed)
echo   clean    Clean build artifacts and virtual environment
echo   setup    Only setup virtual environment and install dependencies
echo   package  Build and create versioned zip archive (cleans build/dist/.venv after successful packaging)
echo.
echo Examples:
echo   build.bat build
echo   build.bat run
echo   build.bat setup
echo   build.bat clean
echo   build.bat package
goto :eof

:log_info
echo [INFO] %~1
goto :eof

:log_success
echo [SUCCESS] %~1
goto :eof

:log_warning
echo [WARNING] %~1
goto :eof

:log_error
echo [ERROR] %~1
goto :eof

:check_python
call :log_info "Checking Python installation..."
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    call :log_error "Python 3 is not installed or not in PATH"
    exit /b 1
)

for /f "tokens=2" %%i in ('"%PYTHON_CMD% --version 2>&1"') do set PYTHON_VERSION=%%i
call :log_info "Using Python %PYTHON_VERSION%"
call :log_info "Building version: %VERSION%"
goto :eof

:setup_venv
call :log_info "Setting up virtual environment..."

REM Remove existing venv if it exists
if exist "%VENV_DIR%" (
    call :log_warning "Removing existing virtual environment..."
    rmdir /s /q "%VENV_DIR%"
)

REM Create new virtual environment
call :log_info "Creating virtual environment..."
%PYTHON_CMD% -m venv "%VENV_DIR%"
if errorlevel 1 (
    call :log_error "Failed to create virtual environment"
    exit /b 1
)

REM Upgrade pip
call :log_info "Upgrading pip..."
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    call :log_error "Failed to upgrade pip"
    exit /b 1
)

call :log_success "Virtual environment created and activated"
goto :eof

:install_dependencies
call :log_info "Installing dependencies from requirements.txt..."

REM Determine latest p4python version matching RELEASE_VERSION
set REL_VERSION=%RELEASE_VERSION%
if "%REL_VERSION%"=="" set REL_VERSION=2025.1

if not exist "requirements.txt" (
    call :log_error "requirements.txt file not found in current directory"
    exit /b 1
)

REM Install dependencies
"%VENV_DIR%\Scripts\pip.exe" install -r requirements.txt
if errorlevel 1 (
    call :log_error "Failed to install dependencies"
    exit /b 1
)

set PYTHON_EXE=%VENV_DIR%\Scripts\python.exe
set PIP_EXE=%VENV_DIR%\Scripts\pip.exe

REM Check if pip exists before trying to use it
if not exist "%PIP_EXE%" (
    call :log_warning "Pip not found in virtual environment. Skipping p4python version detection."
    set P4PYTHON_VERSION=
) else (
    REM Try to get p4python versions - use a simpler approach
    "%PIP_EXE%" index versions p4python >temp_pip_output.txt 2>nul
    if errorlevel 1 (
        call :log_warning "Could not query p4python versions. Skipping version detection."
        set P4PYTHON_VERSION=
        if exist temp_pip_output.txt del temp_pip_output.txt
    ) else (
        REM Parse the output to find matching version
        "%PYTHON_EXE%" -c "import re; rel='%REL_VERSION%'; content=open('temp_pip_output.txt').read(); vers=re.findall(r'([0-9]+\.[0-9]+\.[0-9]+)', content); match=[v for v in vers if v.startswith(rel)]; result=sorted(match)[-1] if match else ''; print(result)" > temp_version.txt 2>nul
        if errorlevel 1 (
            call :log_warning "Could not parse p4python versions. Skipping version detection."
            set P4PYTHON_VERSION=
        ) else (
            set /p P4PYTHON_VERSION=<temp_version.txt
        )
        if exist temp_pip_output.txt del temp_pip_output.txt
        if exist temp_version.txt del temp_version.txt
    )
)

echo Release version: %REL_VERSION%
echo P4Python version: %P4PYTHON_VERSION%

REM Install p4python if version found
if "%P4PYTHON_VERSION%"=="" (
    call :log_warning "Could not determine P4Python version from release. Building with latest p4python version"
) else (
    "%VENV_DIR%\Scripts\pip.exe" install p4python==%P4PYTHON_VERSION%
    if errorlevel 1 (
        call :log_error "Failed to install p4python"
        exit /b 1
    )
)

REM Check if PyInstaller is installed
"%VENV_DIR%\Scripts\pip.exe" list | findstr /i "pyinstaller" >nul
if errorlevel 1 (
    call :log_info "Installing PyInstaller..."
    "%VENV_DIR%\Scripts\pip.exe" install pyinstaller
    if errorlevel 1 (
        call :log_error "Failed to install PyInstaller"
        exit /b 1
    )
)

call :log_success "Dependencies installed successfully"
goto :eof

:build_executable
call :log_info "Building p4-mcp-server with PyInstaller..."

REM Check if the spec file exists
if not exist "p4-mcp-server.spec" (
    call :log_error "p4-mcp-server.spec file not found in current directory"
    exit /b 1
)

REM Clean previous build artifacts (but keep venv)
call :log_info "Cleaning previous build artifacts..."
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Remove the "P4MCP.spec" and binary if they exist
if exist "P4MCP.spec" (
    call :log_info "Removing existing P4MCP.spec..."
    del "P4MCP.spec"
)
if exist "src\telemetry\P4MCP.exe" (
    call :log_info "Removing existing P4MCP binary..."
    del "src\telemetry\P4MCP.exe"
)

REM Build standalone binary for consent_ui.py
call :log_info "Building standalone binary for consent_ui.py..."
"%VENV_DIR%\Scripts\pyinstaller.exe" --onefile --noconsole --distpath src\telemetry --name "P4MCP" src\telemetry\consent_ui.py 
if errorlevel 1 (
    call :log_error "Failed to build consent_ui binary"
    exit /b 1
)

if exist "src\telemetry\P4MCP.exe" (
    call :log_success "Standalone P4MCP binary created at src\telemetry\P4MCP.exe"
) else (
    call :log_error "Failed to build consent_ui binary"
    exit /b 1
)

REM Run PyInstaller for main app
call :log_info "Running PyInstaller for main app..."
"%VENV_DIR%\Scripts\pyinstaller.exe" p4-mcp-server.spec
if errorlevel 1 (
    call :log_error "PyInstaller build failed"
    exit /b 1
)

call :log_info "PyInstaller build completed. Checking for executable..."

REM Check if build was successful
if exist "%EXECUTABLE_PATH%" (
    call :log_success "Build successful!"
    
    REM Only show this message if not packaging
    if /i not "%COMMAND%"=="package" (
        call :log_info "Executable created at: %EXECUTABLE_PATH%"
        echo.
        call :log_info "To run the server:"
        echo   .\dist\p4-mcp-server\p4-mcp-server.exe [arguments]
        echo.
    )
) else (
    call :log_error "Build failed!"
    exit /b 1
)
goto :eof

:create_package
call :log_info "Creating versioned zip archive %ARCHIVE_NAME% ..."

if not exist "%EXECUTABLE_PATH%" (
    call :log_error "Executable not found. Please build first."
    exit /b 1
)

set ARCHIVE_PATH=%SCRIPT_DIR%%ARCHIVE_NAME%

REM Remove existing archive if it exists
if exist "%ARCHIVE_PATH%" (
    call :log_warning "Removing existing archive: %ARCHIVE_NAME%"
    del /f "%ARCHIVE_PATH%"
)

REM Create zip archive with only the executable
powershell -Command "Compress-Archive -Path '%SCRIPT_DIR%dist\p4-mcp-server' -DestinationPath '%ARCHIVE_PATH%' -Force"
if errorlevel 1 (
    call :log_error "Failed to create package"
    exit /b 1
)

if exist "%ARCHIVE_PATH%" (
    call :log_success "Package %ARCHIVE_NAME% created successfully!"
    call :log_info "Package Path: %ARCHIVE_PATH%"
    
    REM Show file size (avoid 'Missing operand')
    for %%i in ("%ARCHIVE_PATH%") do set "ARCHIVE_SIZE=%%~zi"
    
    if defined ARCHIVE_SIZE (
        set /a ARCHIVE_SIZE_KB=!ARCHIVE_SIZE!/1024
        call :log_info "Package size: !ARCHIVE_SIZE_KB! KB"
    ) else (
        call :log_warning "Could not determine package size."
    )
    
    REM Clean up build, dist, .venv directories and P4MCP.spec and P4MCP binary after successful packaging
    if exist "build" rmdir /s /q "build"
    if exist "dist" rmdir /s /q "dist"
    if exist ".venv" rmdir /s /q ".venv"
    if exist "P4MCP.spec" del "P4MCP.spec"
    if exist "src\telemetry\P4MCP.exe" del "src\telemetry\P4MCP.exe"
    call :log_info "build/dist and .venv directories cleaned up after packaging!"
) else (
    call :log_error "Failed to create package!"
    exit /b 1
)
goto :eof

:run_executable
if not exist "%EXECUTABLE_PATH%" (
    call :log_warning "Executable not found. Building first..."
    call :full_build
    if errorlevel 1 exit /b 1
)

call :log_info "Running p4-mcp-server with arguments:%EXECUTABLE_ARGS%"
echo [INFO] Command: "%EXECUTABLE_PATH%" %EXECUTABLE_ARGS%
"%EXECUTABLE_PATH%" %EXECUTABLE_ARGS%
goto :eof

:clean_all
call :log_info "Cleaning all build artifacts and virtual environment..."
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"

REM Also remove any existing archives
for %%f in ("%SCRIPT_DIR%p4-mcp-server-*.zip") do del /f "%%f"

call :log_success "Clean complete!"
goto :eof

:full_build
call :check_python
if errorlevel 1 exit /b 1
call :setup_venv
if errorlevel 1 exit /b 1
call :install_dependencies
if errorlevel 1 exit /b 1
call :build_executable
if errorlevel 1 exit /b 1
goto :eof

:setup_only
call :check_python
if errorlevel 1 exit /b 1
call :setup_venv
if errorlevel 1 exit /b 1
call :install_dependencies
if errorlevel 1 exit /b 1
call :log_success "Setup complete! Virtual environment ready at: %VENV_DIR%"
echo.
call :log_info "To activate the virtual environment manually, run:"
echo   %VENV_DIR%\Scripts\activate.bat
goto :eof

:package_build
call :full_build
if errorlevel 1 exit /b 1
call :create_package
if errorlevel 1 exit /b 1
goto :eof