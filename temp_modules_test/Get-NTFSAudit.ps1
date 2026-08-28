function Get-NTFSAudit {
    [CmdletBinding()]
    param(
        [parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [string]$Path,

        [parameter(Mandatory=$false)]
        [string]$User
    )

    process {
        # 1. Recuperation de l'ACL
        $ACL = Get-Acl -Path $Path -ErrorAction SilentlyContinue

        if (-not $ACL) {
            Write-Warning "Impossible d'acceder a : $Path"
            return $null
        }

        # 2. Recuperer et cumuler les droits (Bitwise OR)
        $Rules = $ACL.Access | Where-Object { 
            ($_.IdentityReference.Value -match $User) -and  
            ($_.AccessControlType -eq 'Allow') 
        }

        [int]$CumulativeRights = 0
        if ($Rules) {
            foreach ($Rule in $Rules) {
                $CumulativeRights = $CumulativeRights -bor [int]$Rule.FileSystemRights
            }
        }

        # 3. Calcul des booleens (Vrai/Faux)
        $FullControlMask = [int][System.Security.AccessControl.FileSystemRights]::FullControl
        $WriteMask       = [int][System.Security.AccessControl.FileSystemRights]::Write
        $ReadMask        = [int][System.Security.AccessControl.FileSystemRights]::ReadAndExecute

        $IsFullControl = ($CumulativeRights -band $FullControlMask) -eq $FullControlMask
        $CanWrite      = ($CumulativeRights -band $WriteMask) -eq $WriteMask
        $CanRead       = ($CumulativeRights -band $ReadMask)  -eq $ReadMask

        # 4. Determination du label de niveau d'acces (lecture humaine rapide)
        $AccessLevel = "None"
        if ($IsFullControl) { $AccessLevel = "FullControl" }
        elseif ($CanWrite -and $CanRead) { $AccessLevel = "Read/Write" }
        elseif ($CanWrite) { $AccessLevel = "WriteOnly" }
        elseif ($CanRead) { $AccessLevel = "ReadOnly" }
        elseif ($CumulativeRights -ne 0) { $AccessLevel = "Custom" }

        # 4b. Statut de conformite : droits trop larges pour cet utilisateur = a corriger.
        #     FullControl = FAIL, Write = WARNING, sinon PASS.
        $Status = if ($IsFullControl) { 'FAIL' } elseif ($CanWrite) { 'WARNING' } else { 'PASS' }

        # 5. RETOUR DE L'OBJET
        [PSCustomObject]@{
            Path          = $Path
            User          = $User
            Status        = $Status         # Conformite : PASS / WARNING / FAIL
            AccessLevel   = $AccessLevel     # Resume textuel du niveau d'acces
            IsFullControl = $IsFullControl  # Booleen
            CanWrite      = $CanWrite       # Booleen
            CanRead       = $CanRead        # Booleen
            RawRights     = $CumulativeRights # Valeur numerique (debug)
        }
    }
}

Get-NTFSAudit
