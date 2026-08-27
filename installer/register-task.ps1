# Enregistre la tache planifiee JadusAgentBeacon.
# Principal auto-adaptatif :
#   - Machine JOINTE au domaine + gMSA configure -> tentative sous gMSA, avec
#     repli SYSTEM si l'enregistrement gMSA echoue.
#   - Sinon (hors domaine / gMSA absent)         -> tache sous SYSTEM.
# Protege par un MUTEX global : si deux instances demarrent en meme temps
# (ex. deux scripts de demarrage), une seule enregistre, l'autre voit la tache
# deja creee et sort -> plus de "course" qui ecrase le gMSA par du SYSTEM.
# S'auto-localise via $PSScriptRoot. Journalise dans %windir%\Temp\jadus-register-task.log.

$ErrorActionPreference = 'SilentlyContinue'

# Compte gMSA injecte au build depuis config.json (scheduled_task.gmsaAccount).
$GmsaAccount = '__GMSA_ACCOUNT__'

$log = Join-Path $env:windir 'Temp\jadus-register-task.log'
function Write-Log([string]$m) {
    $line = "{0} {1}" -f [DateTime]::Now.ToString('s'), $m
    for ($i = 0; $i -lt 6; $i++) {
        try { $line | Out-File -FilePath $log -Append -Encoding utf8 -ErrorAction Stop; return }
        catch { Start-Sleep -Milliseconds 120 }
    }
}

# --- Serialisation : un seul enregistrement a la fois ---
$mutex = New-Object System.Threading.Mutex($false, 'Global\JadusAgentRegisterTask')
$owned = $false
try { $owned = $mutex.WaitOne([TimeSpan]::FromSeconds(90)) }
catch [System.Threading.AbandonedMutexException] { $owned = $true }

try {
    Write-Log "=== register-task START ==="
    Write-Log ("PSScriptRoot = {0}" -f $PSScriptRoot)
    Write-Log ("whoami       = {0}" -f (whoami))
    Write-Log ("gMSA config  = '{0}'" -f $GmsaAccount)

    $taskName     = 'JadusAgentBeacon'
    $launcherPath = Join-Path $PSScriptRoot 'launcher.ps1'
    Write-Log ("launcherPath = {0} (exists={1})" -f $launcherPath, (Test-Path $launcherPath))

    if (Get-ScheduledTask -TaskName $taskName -TaskPath '\' -ErrorAction SilentlyContinue) {
        Write-Log "Task already exists -> rien a faire"
    }
    else {
        # --- Action / declencheur / parametres ---
        $action = New-ScheduledTaskAction `
            -Execute 'powershell.exe' `
            -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$launcherPath`""

        $trigger = New-ScheduledTaskTrigger -AtStartup
        try { $trigger.Delay = 'PT1M' } catch { }

        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -MultipleInstances IgnoreNew

        # --- Doit-on tenter le gMSA ? ---
        # Placeholder reconstruit par morceaux pour que l'injection au build ne
        # remplace QUE la ligne d'affectation plus haut, pas cette comparaison.
        $placeholder = '__GMSA' + '_ACCOUNT__'
        $tryGmsa = $false
        if ($GmsaAccount -and $GmsaAccount -ne $placeholder) {
            $partOfDomain = $false
            try { $partOfDomain = [bool](Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop).PartOfDomain }
            catch { Write-Log ("Detection domaine (CIM) KO: {0}" -f $_.Exception.Message) }
            Write-Log ("PartOfDomain = {0}" -f $partOfDomain)

            if ($partOfDomain) {
                $tryGmsa = $true
                # Validation purement informative (ne bloque pas la tentative).
                $sam = (($GmsaAccount -replace '^.*\\', '') -replace '\$$', '')
                try {
                    Import-Module ActiveDirectory -ErrorAction Stop
                    $t = Test-ADServiceAccount -Identity $sam -ErrorAction SilentlyContinue
                    Write-Log ("Test-ADServiceAccount({0}) = {1} (informatif)" -f $sam, $t)
                }
                catch {
                    Write-Log ("Module ActiveDirectory indisponible (info): {0}" -f $_.Exception.Message)
                }
            }
        }
        Write-Log ("tryGmsa = {0}" -f $tryGmsa)

        # --- Enregistrement : gMSA d'abord, repli SYSTEM si echec ---
        $registered = $false
        if ($tryGmsa) {
            Write-Log ("Tentative enregistrement sous gMSA {0}" -f $GmsaAccount)
            try {
                $principal = New-ScheduledTaskPrincipal -UserId $GmsaAccount -LogonType Password -RunLevel Highest
                Register-ScheduledTask -TaskName $taskName -TaskPath '\' `
                    -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
                    -Description 'Jadus Agent - Beacon execution' -Force -ErrorAction Stop | Out-Null
                Write-Log ("Principal = gMSA {0} (OK)" -f $GmsaAccount)
                $registered = $true
            }
            catch {
                Write-Log ("Enregistrement gMSA KO: {0} -> repli SYSTEM" -f $_.Exception.Message)
            }
        }

        if (-not $registered) {
            Write-Log "Tentative enregistrement sous SYSTEM"
            try {
                $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
                Register-ScheduledTask -TaskName $taskName -TaskPath '\' `
                    -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
                    -Description 'Jadus Agent - Beacon execution' -Force -ErrorAction Stop | Out-Null
                Write-Log "Principal = SYSTEM (OK)"
                $registered = $true
            }
            catch {
                Write-Log ("Enregistrement SYSTEM KO: {0}" -f $_.Exception.Message)
            }
        }
        Write-Log ("registered = {0}" -f $registered)
    }

    Write-Log "=== register-task END ==="
}
finally {
    if ($owned) { try { $mutex.ReleaseMutex() } catch { } }
    $mutex.Dispose()
}

exit 0
