# Convention de conformité des modules d'audit (champ `Status`)

Pour que le serveur Jadus Audit évalue correctement la conformité (et n'affiche plus
tout en « Conforme » par défaut), **chaque module d'audit doit renvoyer un objet
contenant un champ `Status`** valant `PASS`, `WARNING` ou `FAIL`, calculé à partir des
constats réels du module.

## Règles

- `PASS`    : contrôle conforme.
- `WARNING` : conforme partiellement / à surveiller (durcissement recommandé mais pas critique).
- `FAIL`    : non conforme (action requise).
- Optionnel : `N/A` si le contrôle ne s'applique pas au contexte.

Le champ `Status` doit se trouver **dans l'objet de données** (celui qui porte aussi
`Recommendation`), pas seulement au sommet. Ex. si le module renvoie
`[PSCustomObject]@{ Value = <données>; Xml = <remédiations> }`, mettez `Status` **dans `Value`**.

## Modèle

```powershell
# ... calcul des constats ...

# 1) Déterminer le nombre de non-conformités réelles
$issues = 0
if (<condition_non_conforme_1>) { $issues++ }
if (<condition_non_conforme_2>) { $issues++ }

# 2) En déduire le statut
$Status = if ($issues -gt 0) { 'FAIL' } else { 'PASS' }
# (ou 'WARNING' pour des écarts non critiques)

# 3) Inclure Status dans l'objet de données
$Data = [pscustomobject]@{
    Status         = $Status
    # ... vos champs de données ...
    Recommendation = $reco -join ' | '
}

# 4) Retour habituel (Value + Xml de remédiation)
[PSCustomObject]@{ Value = $Data; Xml = $XmlList }
```

## Comment ça marche côté serveur

1. L'agent renvoie désormais la sortie **structurée en JSON** (`output_type = "json"`)
   au lieu d'un texte aplati — la structure (`Status`, `Recommendation`, `Xml`) est préservée.
2. `monitoring.py` (`evaluate_result_compliance`) parse ce JSON, lit le champ `Status`
   via `flatten_audit_controls`, puis calcule la conformité globale
   (`FAIL` → Non conforme, `WARNING` → Partiellement conforme, sinon Conforme).
3. **Si un module n'a pas encore de `Status`** : le résultat est marqué **« Non évalué »**
   (plus jamais « Conforme » par défaut).

## À faire

Ajoutez le champ `Status` à **chacun de vos modules** (`Get-FirewallAudit`,
`Get-IPv6Status`, `Get-LLMNRState`, `Get-NetBiosInfo`, `Get-VPNStatus`,
`Get-EventMonitor`, `Get-LogStatus`, etc.) en suivant le modèle ci-dessus.
Voir `Get-RDPAudit.ps1` pour un exemple complet.
