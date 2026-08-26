# bootstrap.ps1
# Lance a chaque ouverture de session via HKLM\...\Run (pose par le MSI).
# Role : s'assurer que la tache planifiee SYSTEM/gMSA C2AgentBeacon existe.
#
# Logique de creation (pour NE JAMAIS bloquer un utilisateur standard) :
#   - Tache deja presente                 -> ne fait rien.
#   - Deja eleve (admin)                  -> cree la tache directement (aucun UAC).
#   - Pas eleve + machine DU DOMAINE      -> ne fait RIEN : la creation est
#                                            deleguee au GPO (script de demarrage
#                                            en SYSTEM). => Aucune invite UAC pour
#                                            les utilisateurs standard.
#   - Pas eleve + machine HORS domaine    -> s'auto-eleve (1 invite UAC) : cas de
#                                            l'installation manuelle par un admin.

$ErrorActionPreference = 'SilentlyContinue'

$log = Join-Path $env:TEMP 'c2-bootstrap.log'
function W([string]$m) {
    "{0} {1}" -f [DateTime]::Now.ToString('s'), $m | Out-File -FilePath $log -Append -Encoding utf8
}

$taskName       = 'C2AgentBeacon'
$registerScript = Join-Path $PSScriptRoot 'register-task.ps1'

# 1. La tache existe deja ? -> rien a faire
if (Get-ScheduledTask -TaskName $taskName -TaskPath '\' -ErrorAction SilentlyContinue) {
    W "Task already exists -> nothing to do"
    exit 0
}

# 2. Sommes-nous eleves (administrateur) ?
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    # Contexte deja eleve -> creation directe, sans UAC
    W "Elevated -> creation directe de la tache"
    & $registerScript
    Start-ScheduledTask -TaskName $taskName -TaskPath '\' -ErrorAction SilentlyContinue
    W "Bootstrap done (elevated)"
    exit 0
}

# 3. Pas eleve : on ne s'auto-eleve (UAC) QUE si la machine est CONFIRMEE hors
#    domaine. En cas de doute (detection qui echoue) -> on SUPPOSE le domaine ->
#    PAS d'UAC. Un utilisateur standard du domaine ne doit jamais voir d'invite ;
#    la tache est de toute facon creee par le GPO (script de demarrage SYSTEM).
$partOfDomain = $true
try {
    $cs = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
    $partOfDomain = [bool]$cs.PartOfDomain
}
catch {
    W ("Detection domaine (CIM) echouee: {0} -> suppose domaine (pas d'UAC)" -f $_.Exception.Message)
    $partOfDomain = $true
}
W ("PartOfDomain = {0}" -f $partOfDomain)

if ($partOfDomain) {
    W "Domain-joined (ou incertain) + not elevated -> creation deleguee au GPO (SYSTEM), pas d'UAC"
    exit 0
}

# 4. Hors domaine (install manuelle) : s'auto-elever -> 1 invite UAC
W "Hors domaine + not elevated -> relaunch eleve (UAC)"
try {
    Start-Process -FilePath 'powershell.exe' -Verb RunAs -WindowStyle Hidden -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`""
    )
}
catch {
    W ("Elevation refusee/echouee: {0}" -f $_.Exception.Message)
}
exit 0
