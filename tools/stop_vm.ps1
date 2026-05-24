#requires -Version 5.1
<#
.SYNOPSIS
    hyperv-mcp tool wrapper — stop a VM (graceful / force / save-state).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Name,
    [switch]$Force,
    [switch]$Save,
    [switch]$Live
)

if ($Force -and $Save) {
    @{ ok = $false; error = @{ code = 'invalid_arg'; message = 'force and save are mutually exclusive' } } |
        ConvertTo-Json -Depth 3 -Compress
    exit 2
}

function stop_vm-WrapMock {
    [CmdletBinding()]
    param([string]$Name, [switch]$Force, [switch]$Save)
    $mode = if ($Save) { 'saved' } elseif ($Force) { 'force' } else { 'graceful' }
    $newState = if ($Save) { 'Saved' } else { 'Off' }
    return @{
        previous_state = 'Running'
        current_state  = $newState
        mode           = $mode
        elapsed_sec    = 0.0
    }
}

function stop_vm-WrapLive {
    [CmdletBinding()]
    param([string]$Name, [switch]$Force, [switch]$Save)
    $vm = Get-VM -Name $Name -ErrorAction Stop
    $previous = $vm.State.ToString()
    $newState = if ($Save) { 'Saved' } else { 'Off' }
    if ($previous -eq $newState) {
        return @{ previous_state = $previous; current_state = $newState; note = "already $newState, no action taken" }
    }
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    if     ($Save)  { Save-VM -Name $Name -ErrorAction Stop }
    elseif ($Force) { Stop-VM -Name $Name -TurnOff -Force -ErrorAction Stop }
    else            { Stop-VM -Name $Name -Force -ErrorAction Stop }
    $sw.Stop()
    return @{
        previous_state = $previous
        current_state  = $newState
        mode           = (if ($Save) { 'saved' } elseif ($Force) { 'force' } else { 'graceful' })
        elapsed_sec    = [math]::Round($sw.Elapsed.TotalSeconds, 2)
    }
}

try {
    $res = if ($Live) {
        stop_vm-WrapLive -Name $Name -Force:$Force -Save:$Save
    } else {
        stop_vm-WrapMock -Name $Name -Force:$Force -Save:$Save
    }
    $payload = @{ ok = $true; name = $Name }
    foreach ($k in $res.Keys) { $payload[$k] = $res[$k] }
    $payload | ConvertTo-Json -Depth 4 -Compress
    exit 0
} catch {
    $msg  = $_.Exception.Message
    $code = if ($msg -like '*not found*') { 'vm_not_found' } else { 'internal' }
    @{ ok = $false; error = @{ code = $code; message = $msg } } | ConvertTo-Json -Depth 4 -Compress
    exit 1
}
