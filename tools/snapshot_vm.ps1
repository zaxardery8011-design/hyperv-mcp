#requires -Version 5.1
<#
.SYNOPSIS
    hyperv-mcp tool wrapper — checkpoint (snapshot) a VM.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Name,
    [string]$SnapshotName,
    [switch]$Live
)

if (-not $SnapshotName) { $SnapshotName = (Get-Date -Format 'o') }

function snapshot_vm-WrapMock {
    [CmdletBinding()]
    param([string]$Name, [string]$SnapshotName)
    return @{
        id           = [Guid]::NewGuid().ToString()
        name         = $SnapshotName
        parent_id    = $null
        created_at   = (Get-Date -Format 'o')
        type         = 'Standard'
    }
}

function snapshot_vm-WrapLive {
    [CmdletBinding()]
    param([string]$Name, [string]$SnapshotName)
    $snap = Checkpoint-VM -Name $Name -SnapshotName $SnapshotName -PassThru -ErrorAction Stop
    return @{
        id           = $snap.Id.ToString()
        name         = $snap.Name
        parent_id    = if ($snap.ParentSnapshotId) { $snap.ParentSnapshotId.ToString() } else { $null }
        created_at   = $snap.CreationTime.ToString('o')
        type         = $snap.SnapshotType.ToString()
    }
}

try {
    $snap = if ($Live) {
        snapshot_vm-WrapLive -Name $Name -SnapshotName $SnapshotName
    } else {
        snapshot_vm-WrapMock -Name $Name -SnapshotName $SnapshotName
    }
    @{ ok = $true; name = $Name; snapshot = $snap } | ConvertTo-Json -Depth 5 -Compress
    exit 0
} catch {
    $msg  = $_.Exception.Message
    $code = if ($msg -like '*not found*') { 'vm_not_found' } else { 'internal' }
    @{ ok = $false; error = @{ code = $code; message = $msg } } | ConvertTo-Json -Depth 4 -Compress
    exit 1
}
