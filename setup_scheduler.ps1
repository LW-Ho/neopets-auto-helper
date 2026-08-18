<#
  setup_scheduler.ps1
  Registers a Windows Scheduled Task that runs run_all_accounts.bat:
    - once AT LOGON  -> resumes automatically after a reboot + auto-login
    - then EVERY N HOURS, indefinitely
  Runs only while you are logged on (Docker Desktop needs your session), which
  matches your "auto-return to desktop on boot" setup.

  Usage (run once, in PowerShell, from the repo folder):
    powershell -ExecutionPolicy Bypass -File .\setup_scheduler.ps1
    powershell -ExecutionPolicy Bypass -File .\setup_scheduler.ps1 -IntervalHours 4
  Remove it later with:
    Unregister-ScheduledTask -TaskName "NeopetsAutoHelper" -Confirm:$false
#>
param(
    [int]$IntervalHours = 6,
    [string]$TaskName   = "NeopetsAutoHelper"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat = Join-Path $scriptDir "run_all_accounts.bat"
if (-not (Test-Path $bat)) { throw "Cannot find $bat" }

$user = "$env:USERDOMAIN\$env:USERNAME"

# Run the .bat via cmd.exe so exit codes / redirection behave normally.
$action = New-ScheduledTaskAction -Execute "cmd.exe" `
    -Argument "/c `"$bat`"" -WorkingDirectory $scriptDir

# Trigger 1: at this user's logon (fires after reboot + auto-login).
$atLogon = New-ScheduledTaskTrigger -AtLogOn -User $user

# Trigger 2: starting now, repeat every N hours ~forever.
$repeat = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Hours $IntervalHours) `
    -RepetitionDuration  (New-TimeSpan -Days 3650)

$principal = New-ScheduledTaskPrincipal -UserId $user `
    -LogonType Interactive -RunLevel Limited

# IgnoreNew -> if a run is still going when the next trigger fires, skip it
#              (accounts never overlap). StartWhenAvailable -> catch up if the
#              PC was off at a scheduled time. 12h cap is a safety net.
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 12)

Register-ScheduledTask -TaskName $TaskName -Action $action `
    -Trigger $atLogon, $repeat -Principal $principal -Settings $settings -Force

Write-Host ""
Write-Host "Registered scheduled task '$TaskName':" -ForegroundColor Green
Write-Host "  - runs at logon (resumes after reboot)"
Write-Host "  - repeats every $IntervalHours hour(s)"
Write-Host ""
Write-Host "Test it now with:  Start-ScheduledTask -TaskName `"$TaskName`""
Write-Host "Watch the log at:  $scriptDir\logs\run.log"
