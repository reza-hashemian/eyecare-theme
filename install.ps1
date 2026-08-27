# Install eyecare-theme on Windows: PATH entry + Scheduled Task for day/night switching.
# Run in PowerShell:  powershell -ExecutionPolicy Bypass -File .\install.ps1
$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$cmd = Join-Path $dir "eyecare-theme.cmd"

# --- 1. PATH ---
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$dir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$dir", "User")
    Write-Host "  added $dir to your user PATH (restart your terminal)"
} else {
    Write-Host "  $dir already on PATH"
}

# --- 2. Scheduled Task, every 5 minutes ---
$taskName = "EyeCareTheme"
$action  = New-ScheduledTaskAction -Execute $cmd -Argument "auto --quiet"
# A daily trigger repeating every 5 min for 24h is the form that works on
# every supported Windows build; [TimeSpan]::MaxValue is rejected by some.
$trigger = New-ScheduledTaskTrigger -Daily -At (Get-Date).Date
$trigger.Repetition = (New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Hours 24)).Repetition
$logon = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
             -DontStopIfGoingOnBatteries -StartWhenAvailable

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($trigger, $logon) `
    -Settings $settings -Description "Apply the eye-comfort theme for the current time of day" | Out-Null
Write-Host "  scheduled task '$taskName' created (checks every 5 min)"

Write-Host ""
Write-Host "  Done. Next step:  eyecare-theme pick"
