@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
set "TCL_LIBRARY=%ROOT%python\tcl\tcl8.6"
set "TK_LIBRARY=%ROOT%python\tcl\tk8.6"
set "PATH=%ROOT%python;%ROOT%python\DLLs;%PATH%"
cd /d "%ROOT%"
"%ROOT%python\python.exe" "%ROOT%MYAPI单图模式.py"
if errorlevel 1 pause
