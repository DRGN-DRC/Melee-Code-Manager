@echo off
cls

echo. & echo.
echo Are you sure you'd like to compile (y/n)?

set /p confirmation=

:: Compile the program if "y" was entered
echo. & echo.
if [%confirmation%]==[y] (
    echo Deleting bin\tempFiles
    del /Q bin\tempFiles
    echo.
    python setup.py build
) else (
    goto:eof
)

echo. & echo.
echo Exit Code: %ERRORLEVEL%

if not [%ERRORLEVEL%]==[0] goto :Failed



:Success
echo.
echo      Build complete!  Press any key to exit.
pause > nul

:: Open the target build folder
"%SystemRoot%\explorer.exe" "%~dp0build"
goto :eof



:Failed
echo.
echo      Build failed.  Press any key to exit.
pause > nul