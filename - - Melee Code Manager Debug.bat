@echo off

python "%~dp0Melee Code Manager.py" %*

:: If there are no errors, exit. Otherwise, pause so that the errors can be read.
if [%ERRORLEVEL%]==[0] goto eof

pause