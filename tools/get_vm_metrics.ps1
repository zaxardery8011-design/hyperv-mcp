#requires -Version 5.1
<#
.SYNOPSIS
    hyperv-mcp tool wrapper — return CPU / memory / disk / network metrics.

.DESCRIPTION
    Per-VM if -Name supplied; host aggregate otherwise.
#>
[CmdletBinding()]
param(
    [string]$Name,
    [string[]]$Include = @('cpu','memory'),
    [switch]$Live
)

function get_vm_metrics-WrapMockVm {
    [CmdletBinding()]
    param([string]$Name, [string[]]$Include)
    $base = @{ name = $Name; captured_at = (Get-Date -Format 'o') }
    if ($Include -contains 'cpu')     { $base['cpu']     = @{ usage_pct = 12; vcpu_count = 4 } }
    if ($Include -contains 'memory')  { $base['memory']  = @{ assigned_mb = 4096; demand_mb = 2410; available_mb = 1686 } }
    if ($Include -contains 'disk')    { $base['disk']    = @(@{ path = "C:\Hyper-V\$Name\disk.vhdx"; size_gb = 60; used_gb = 22 }) }
    if ($Include -contains 'network') { $base['network'] = @(@{ adapter = 'Default Switch'; tx_bps = 124000; rx_bps = 89000 }) }
    return $base
}

function get_vm_metrics-WrapMockHost {
    return @{
        host             = $env:COMPUTERNAME
        captured_at      = (Get-Date -Format 'o')
        vm_count_running = 1
        vm_count_total   = 3
        cpu              = @{ logical_processors = 16; total_usage_pct = 24 }
        memory           = @{ total_mb = 65536; assigned_to_vms_mb = 4096; free_mb = 38400 }
    }
}

function get_vm_metrics-WrapLiveVm {
    [CmdletBinding()]
    param([string]$Name, [string[]]$Include)
    $vm = Get-VM -Name $Name -ErrorAction Stop
    $base = @{ name = $Name; captured_at = (Get-Date -Format 'o') }
    if ($Include -contains 'cpu')    { $base['cpu']    = @{ usage_pct = [int]$vm.CPUUsage; vcpu_count = [int]$vm.ProcessorCount } }
    if ($Include -contains 'memory') {
        $base['memory'] = @{
            assigned_mb  = [int]($vm.MemoryAssigned / 1MB)
            demand_mb    = [int]($vm.MemoryDemand   / 1MB)
            available_mb = [int](($vm.MemoryAssigned - $vm.MemoryDemand) / 1MB)
        }
    }
    if ($Include -contains 'network') {
        $base['network'] = @(Get-VMNetworkAdapter -VMName $Name | ForEach-Object {
            @{
                adapter = $_.SwitchName
                tx_bps  = 0  # filled by perf counter pull in v0.3
                rx_bps  = 0
            }
        })
    }
    return $base
}

try {
    $payload = @{ ok = $true }
    if ($Name) {
        $m = if ($Live) {
            get_vm_metrics-WrapLiveVm -Name $Name -Include $Include
        } else {
            get_vm_metrics-WrapMockVm -Name $Name -Include $Include
        }
        foreach ($k in $m.Keys) { $payload[$k] = $m[$k] }
    } else {
        $m = get_vm_metrics-WrapMockHost
        foreach ($k in $m.Keys) { $payload[$k] = $m[$k] }
    }
    $payload | ConvertTo-Json -Depth 6 -Compress
    exit 0
} catch {
    $msg  = $_.Exception.Message
    $code = if ($msg -like '*not found*') { 'vm_not_found' } else { 'internal' }
    @{ ok = $false; error = @{ code = $code; message = $msg } } | ConvertTo-Json -Depth 4 -Compress
    exit 1
}
