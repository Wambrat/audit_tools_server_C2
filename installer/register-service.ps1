# Installe l'agent comme SERVICE Windows via le wrapper WinSW (agent-service.exe).
# Compte de service auto-adaptatif :
#   - Machine JOINTE au domaine + gMSA configure -> service sous gMSA,
#     avec repli LocalSystem si le demarrage sous gMSA echoue.
#   - Sinon (hors domaine / gMSA absent)         -> service sous LocalSystem.
# S'auto-localise via $PSScriptRoot. Appele par bootstrap.ps1 (hors domaine, UAC)
# ou par le script de demarrage GPO en SYSTEM (machines du domaine).
# Journalise dans %windir%\Temp\jadus-register-service.log.

$ErrorActionPreference = 'SilentlyContinue'

# Compte gMSA injecte au build (voir register-task.ps1 pour le meme mecanisme).
$GmsaAccount = '__GMSA_ACCOUNT__'

$serviceName = 'JadusAgent'
$log = Join-Path $env:windir 'Temp\jadus-register-service.log'
function Write-Log([string]$m) {
    "{0} {1}" -f [DateTime]::Now.ToString('s'), $m | Out-File -FilePath $log -Append -Encoding utf8
}

Write-Log "=== register-service START ==="
Write-Log ("PSScriptRoot = {0}" -f $PSScriptRoot)
Write-Log ("whoami       = {0}" -f (whoami))
Write-Log ("gMSA config  = '{0}'" -f $GmsaAccount)

$wrapper = Join-Path $PSScriptRoot 'agent-service.exe'
Write-Log ("wrapper      = {0} (exists={1})" -f $wrapper, (Test-Path $wrapper))
if (-not (Test-Path $wrapper)) { Write-Log "wrapper introuvable -> abandon"; exit 1 }

# Service deja present ?
if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) {
    Write-Log "Service deja present -> exit 0"
    Write-Log "=== register-service END ==="
    exit 0
}

# 1) Installer le service (WinSW lit agent-service.xml, meme basename)
Write-Log "Installation du service (WinSW install)..."
& $wrapper install 2>&1 | ForEach-Object { Write-Log "  winsw: $_" }
Start-Sleep -Seconds 2

# 2) Determiner le compte : gMSA si domaine + configure, sinon LocalSystem
$placeholder = '__GMSA' + '_ACCOUNT__'   # reconstruit pour ne pas etre remplace au build
$account = 'LocalSystem'
if ($GmsaAccount -and $GmsaAccount -ne $placeholder) {
    $partOfDomain = $false
    try { $partOfDomain = [bool](Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop).PartOfDomain } catch {}
    Write-Log ("PartOfDomain = {0}" -f $partOfDomain)
    if ($partOfDomain) { $account = $GmsaAccount }
}
Write-Log ("Compte de service choisi = {0}" -f $account)

# 3) Positionner le compte (gMSA : mot de passe vide, gere par l'OS)
#    NB : la syntaxe sc.exe exige un espace apres 'obj=' et 'password='.
if ($account -eq 'LocalSystem') {
    & sc.exe config $serviceName obj= "LocalSystem" 2>&1 | ForEach-Object { Write-Log "  sc: $_" }
} else {
    & sc.exe config $serviceName obj= "$account" password= "" 2>&1 | ForEach-Object { Write-Log "  sc: $_" }
}

# 4) Recuperation automatique sur echec (restart apres 60s, 3 fois)
& sc.exe failure $serviceName reset= 86400 actions= restart/60000/restart/60000/restart/60000 2>&1 |
    ForEach-Object { Write-Log "  sc-failure: $_" }

# 5) Demarrer
Start-Service -Name $serviceName -ErrorAction SilentlyContinue
$svc = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
Write-Log ("Etat du service = {0}" -f ($svc.Status))

# 6) Repli LocalSystem si le demarrage sous gMSA a echoue
if ($account -ne 'LocalSystem' -and $svc -and $svc.Status -ne 'Running') {
    Write-Log "Demarrage sous gMSA KO -> repli LocalSystem"
    & sc.exe config $serviceName obj= "LocalSystem" 2>&1 | ForEach-Object { Write-Log "  sc: $_" }
    Start-Service -Name $serviceName -ErrorAction SilentlyContinue
    Write-Log ("Etat du service (repli) = {0}" -f (Get-Service -Name $serviceName -EA SilentlyContinue).Status)
}

Write-Log "=== register-service END ==="
exit 0
