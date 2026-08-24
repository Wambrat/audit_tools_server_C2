# Enregistre la tache planifiee C2AgentBeacon.
# Appele par le MSI (CustomAction deferred/SYSTEM) via le chemin d'install
# resolu depuis le registre. S'auto-localise via $PSScriptRoot.
# Journalise dans %windir%\Temp\c2-register-task.log pour diagnostic.

$ErrorActionPreference = 'SilentlyContinue'

$log = Join-Path $env:windir 'Temp\c2-register-task.log'
function W([string]$m) {
    "{0} {1}" -f [DateTime]::Now.ToString('s'), $m | Out-File -FilePath $log -Append -Encoding utf8
}

W "=== register-task START ==="
W ("PSScriptRoot = {0}" -f $PSScriptRoot)
W ("whoami       = {0}" -f (whoami))

$taskName     = 'C2AgentBeacon'
$launcherPath = Join-Path $PSScriptRoot 'launcher.ps1'
W ("launcherPath = {0} (exists={1})" -f $launcherPath, (Test-Path $launcherPath))

$existing = Get-ScheduledTask -TaskName $taskName -TaskPath '\' -ErrorAction SilentlyContinue
if ($existing) {
    W "Task already exists -> exit 0"
    W "=== register-task END ==="
    exit 0
}

try {
    $action = New-ScheduledTaskAction `
        -Execute 'powershell.exe' `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$launcherPath`""

    $trigger = New-ScheduledTaskTrigger -AtStartup

    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -MultipleInstances IgnoreNew

    Register-ScheduledTask `
        -TaskName $taskName `
        -TaskPath '\' `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -RunLevel Highest `
        -User 'SYSTEM' `
        -Description 'C2 Autonomous Agent - Beacon execution' `
        -Force `
        -ErrorAction Stop | Out-Null

    W "Register-ScheduledTask OK"
}
catch {
    W ("ERROR: {0}" -f $_.Exception.Message)
}

W "=== register-task END ==="
exit 0
