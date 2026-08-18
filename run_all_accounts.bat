@echo off
REM ============================================================================
REM  run_all_accounts.bat
REM  Runs every accounts\*.json SEQUENTIALLY, one throwaway Docker container each.
REM  - Waits for the Docker engine to be ready (important right after a reboot).
REM  - Reuses cookies via the shared sessions\ folder (fewer NeoPass re-logins).
REM  - Never overlaps accounts; STAGGER seconds between them spreads logins out.
REM  - Appends output to logs\run.log.
REM  Point Windows Task Scheduler at this file (see setup_scheduler.ps1).
REM ============================================================================
setlocal enabledelayedexpansion

REM ===== Config (edit these) =================================================
REM  x86/amd64 hosts: neopets-playwright-helper-x86:latest
REM  arm64 hosts:     neopets-playwright-helper-arm64:latest
set "IMAGE=neopets-playwright-helper-x86:latest"
REM  Seconds to wait between accounts.
set "STAGGER=20"
REM  Rotate logs\run.log once it passes this many MB (keeps one .old backup),
REM  so the log can't grow without bound across months of scheduled runs.
set "LOGMAXMB=5"
REM ==========================================================================

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR:~0,-1%"
set "LOGDIR=%ROOT%\logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set "LOG=%LOGDIR%\run.log"
set "DEBUGDIR=%ROOT%\debug"
if not exist "%DEBUGDIR%" mkdir "%DEBUGDIR%"

REM  Keep logs\run.log bounded (see LOGMAXMB) before appending this run.
call :rotate_log

>>"%LOG%" echo(
>>"%LOG%" echo ====================================================================
>>"%LOG%" echo [%date% %time%] Batch start (image=%IMAGE%)
echo [%date% %time%] Batch start

call :wait_docker
if errorlevel 1 exit /b 1

call :check_image
if errorlevel 1 exit /b 1

for %%A in ("%ROOT%\accounts\*.json") do (
    call :run_one "%%~nxA" "%%~nA"
    timeout /t %STAGGER% /nobreak >nul
)

>>"%LOG%" echo [%date% %time%] Batch done.
echo [%date% %time%] Batch done.
endlocal
exit /b 0

REM ---------------------------------------------------------------------------
:rotate_log
REM  If run.log is bigger than LOGMAXMB, move it aside to run.log.old (one
REM  backup only) and start a fresh run.log. Total log on disk stays ~2x LOGMAXMB.
if not exist "%LOG%" exit /b 0
set /a _maxbytes=%LOGMAXMB% * 1048576
set "_logsize=0"
for %%A in ("%LOG%") do set "_logsize=%%~zA"
if %_logsize% GEQ %_maxbytes% (
    if exist "%LOG%.old" del /q "%LOG%.old"
    move /y "%LOG%" "%LOG%.old" >nul
    >>"%LOG%" echo [%date% %time%] (rotated previous log to run.log.old, was !_logsize! bytes)
)
exit /b 0

REM ---------------------------------------------------------------------------
:wait_docker
REM  After a reboot Docker Desktop may still be starting; poll up to 5 minutes.
set /a _tries=0
:__wd_loop
docker info >nul 2>&1
if not errorlevel 1 (
    >>"%LOG%" echo [%date% %time%] Docker engine ready.
    exit /b 0
)
set /a _tries+=1
if %_tries% GEQ 60 (
    >>"%LOG%" echo [%date% %time%] Docker engine NOT ready after 5 min, aborting.
    echo Docker engine not ready, aborting.
    exit /b 1
)
timeout /t 5 /nobreak >nul
goto :__wd_loop

REM ---------------------------------------------------------------------------
:check_image
docker image inspect %IMAGE% >nul 2>&1
if not errorlevel 1 exit /b 0
>>"%LOG%" echo [%date% %time%] Image %IMAGE% not found. Build it first.
echo Image %IMAGE% not found. Build with:
echo    docker buildx build --load --platform linux/amd64 -t %IMAGE% .
exit /b 1

REM ---------------------------------------------------------------------------
:run_one
REM  %1 = file name with extension (account_0.json)   %2 = base name (account_0)
set "ACC=%~1"
set "NAME=%~2"
>>"%LOG%" echo [%date% %time%] ---- Running !ACC! ----
echo Running !ACC! ...
REM  Remove a leftover container from a previous crashed run, if any.
docker rm -f neo-!NAME! >nul 2>&1
docker run --rm --name neo-!NAME! ^
    -v "%ROOT%\accounts:/usr/src/app/accounts:ro" ^
    -v "%ROOT%\sessions:/usr/src/app/sessions" ^
    -v "%ROOT%\debug:/usr/src/app/debug" ^
    -e ACCOUNT_FILE=/usr/src/app/accounts/!ACC! ^
    %IMAGE% >>"%LOG%" 2>&1
>>"%LOG%" echo [%date% %time%] ---- !ACC! finished (exit !errorlevel!) ----
exit /b 0
