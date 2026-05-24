#requires -Version 5.1
<#
.SYNOPSIS
    hyperv-mcp tool wrapper — start a VM and optionally wait for heartbeat.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Name,
    [switch]$WaitForHeartbeat,
    [ValidateRange(1,600)][int]$TimeoutSec = 60,
    [switch]$Live
)

function start_vm-WrapMock {
    [CmdletBinding()]
    param([string]$Name, [switch]$WaitForHeartbeat)
    if ($Name -notmatch '^[A-Za-z0-9_\-\.]+$') { throw "vm_not_found: $Name" }
    return @{
        previous_state    = 'Off'
        current_state     = 'Running'
        heartbeat_received = [bool]$WaitForHeartbeat
        elapsed_sec       = 0.0
    }
}

function start_vm-WrapLive {
    [CmdletBinding()]
    param([string]$Name, [switch]$WaitForHeartbeat, [int]$TimeoutSec)
    $vm = Get-VM -Name $Name -ErrorAction Stop
    $previous = $vm.State.ToString()
    if ($previous -eq 'Running') {
        return @{ previous_state = $previous; current_state = 'Running'; note = 'already Running, no action taken' }
    }
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    Start-VM -Name $Name -ErrorAction Stop
    $hb = $false
    if ($WaitForHeartbeat) {
        try { Wait-VM -Name $Name -For Heartbeat -Timeout $TimeoutSec -ErrorAction Stop; $hb = $true } catch { $hb = $false }
    }
    $sw.Stop()
    return @{
        previous_state     = $previous
        current_state      = 'Running'
        heartbeat_received = $hb
        elapsed_sec        = [math]::Round($sw.Elapsed.TotalSeconds, 2)
    }
}

try {
    $res = if ($Live) {
        start_vm-WrapLive -Name $Name -WaitForHeartbeat:$WaitForHeartbeat -TimeoutSec $TimeoutSec
    } else {
        start_vm-WrapMock -Name $Name -WaitForHeartbeat:$WaitForHeartbeat
    }
    $payload = @{ ok = $true; name = $Name }
    foreach ($k in $res.Keys) { $payload[$k] = $res[$k] }
    $payload | ConvertTo-Json -Depth 4 -Compress
    exit 0
} catch {
    $msg  = $_.Exception.Message
    $code = if ($msg -like '*vm_not_found*' -or $msg -like '*not found*') { 'vm_not_found' } else { 'internal' }
    @{ ok = $false; error = @{ code = $code; message = $msg } } | ConvertTo-Json -Depth 4 -Compress
    exit 1
}
