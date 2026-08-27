# Script de DEMARRAGE GPO (Configuration ORDINATEUR).
# S'execute en SYSTEM au boot, avant l'ouverture de session -> aucun UAC.
# Il appelle register-task.ps1 (installe par le MSI) qui cree la tache
# jadusAgentBeacon sous le gMSA (machine du domaine) ou SYSTEM (repli).
#
# - Ne fait rien si le MSI n'est pas encore installe (la 1re application d'une
#   GPO d'installation logicielle peut necessiter un boot supplementaire :
#   la tache sera creee au boot suivant).
# - Ne fait rien si la tache existe deja (register-task.ps1 s'en charge).

$candidates = @(
    (Join-Path ${env:ProgramFiles(x86)} 'jadusAgent\register-task.ps1'),  # MSI 32 bits
    (Join-Path $env:ProgramFiles         'jadusAgent\register-task.ps1')   # MSI 64 bits
)

foreach ($p in $candidates) {
    if ($p -and (Test-Path $p)) {
        & $p
        break
    }
}
