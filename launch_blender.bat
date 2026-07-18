@echo off
rem ------------------------------------------------------------------
rem Development launcher for this add-on.
rem Starts Blender through the package-aware development bootstrap
rem (dev_loader.py), which imports this folder as a proper Python
rem package and registers it - no zip, no install needed, and
rem relative imports (from . import ...) work in multi-file add-ons.
rem
rem The production zip does NOT use this file: an installed extension
rem is loaded by Blender through __init__.py in the normal way.
rem
rem %~dp0 expands to the folder that contains this .bat file
rem (including the trailing backslash), so the script works no matter
rem where it is launched from.
rem ------------------------------------------------------------------

set "BLENDER_EXE=C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"

if not exist "%BLENDER_EXE%" (
    echo [ERROR] Blender not found: "%BLENDER_EXE%"
    echo Edit BLENDER_EXE in this .bat to match your install path.
    pause
    exit /b 1
)

"%BLENDER_EXE%" --python "%~dp0dev_loader.py"
