@echo off
setlocal

:: Set the folder to scan (change this if you want it hardcoded)
set "FOLDER_TO_SCAN=%~1"

:: If no folder was passed as an argument, use the current directory
if "%FOLDER_TO_SCAN%"=="" set "FOLDER_TO_SCAN=%cd%"

:: Output file
set "OUTPUT_FILE=file_list.txt"

:: Delete the output file if it exists
if exist "%OUTPUT_FILE%" del "%OUTPUT_FILE%"

:: Recursively list all files and write to file_list.txt
for /R "%FOLDER_TO_SCAN%" %%F in (*) do (
    echo %%F >> "%OUTPUT_FILE%"
)

echo Done. File list written to "%OUTPUT_FILE%"
pause
