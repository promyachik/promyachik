@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo PUSH_STATE_TO_GITHUB V2
echo Sends current diagnostic state to GitHub:
echo _chatgpt_state\latest
echo.
echo This does NOT change site pages.
echo.

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

python "%CD%\scripts\push_state_to_github.py" "%CD%"
if errorlevel 1 goto FAIL

echo.
echo DONE
echo State pushed to GitHub.
echo Now write in ChatGPT: запушил
goto END

:FAIL
echo.
echo FAILED
echo Copy this window text to ChatGPT.
goto END

:END
pause
endlocal
