@echo off
REM Set the path to Blender
set BLENDER_PATH="C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"
REM Set the path to your Python script
set SCRIPT_PATH="H:\f\Fnaf_mod_tool\scripts\bulk_export_new.py"

REM Run Blender in background mode with the Python script
%BLENDER_PATH% --background --python %SCRIPT_PATH%

REM Pause to keep the window open in case of errors

pause
REM Relaunch the batch script after processing (if needed)
call "%~f0"
