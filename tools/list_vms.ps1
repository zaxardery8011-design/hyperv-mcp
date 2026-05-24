#requires -Version 5.1
<#
.SYNOPSIS
    hyperv-mcp tool wrapper — list VMs as JSON.

.DESCRIPTION
    v0.1 emits canned mock JSON so server.py can subprocess it during local dev.
    v0.2 replaces the mock branch with real Get-VM calls.

.PARAMETER StateFilter
    any | Running | Off | Saved | Paused. Default: any.

.PARAMETER NamePattern
    Optional PowerShell -Like pattern (e.g. 'LINC-*').

.OUTPUTS
    JSON to stdout, schema per spec.md tool 1.
#>
[CmdletBinding()]
param(
    [ValidateSet('any','Running','Off','Saved','Paused')]
    [string]$StateFilter = 'any',
    [string]$NamePattern,
    [switch]$Live
)

function list_vms-WrapMock {
    [CmdletBinding()]
    param([string]$StateFilter, [string]$NamePattern)
    $mock = @(
        @{ name='LINC-01';       id='8c5a4f12-1ab2-4cde-90f1-0123456789ab'; state='Running'; cpu_usage_pct=12; memory_assigned_mb=4096; uptime_sec=3680; version='10.0'; generation=2; notes='' }
        @{ name='LINC-02';       id='9b6e5f23-2cd3-5def-a012-1234567890bc'; state='Off';     cpu_usage_pct=0;  memory_assigned_mb=0;    uptime_sec=0;    version='10.0'; generation=2; notes='' }
        @{ name='THUNDER-BASE';  id='ac7f6034-3de4-6ef0-b123-2345678901cd'; state='Saved';   cpu_usage_pct=0;  memory_assigned_mb=8192; uptime_sec=0;    version='10.0'; generation=2; notes='thunder v2.0 base image' }
    )
    $filtered = $mock
    if ($StateFilter -ne 'any') { $filtered = $filtered | Where-Object { $_.state -eq $StateFilter } }
    if ($NamePattern)            { $filtered = $filtered | Where-Object { $_.name -like $NamePattern } }
    return $filtered
}

function list_vms-WrapLive {
    [CmdletBinding()]
    param([string]$StateFilter, [string]$NamePattern)
    if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) {
        throw 'Hyper-V module not available (Get-VM missing).'
    }
    $vms = Get-VM
    if ($StateFilter -ne 'any') { $vms = $vms | Where-Object { $_.State.ToString() -eq $StateFilter } }
    if ($NamePattern)            { $vms = $vms | Where-Object { $_.Name -like $NamePattern } }
    return $vms | ForEach-Object {
        @{
            name                = $_.Name
            id                  = $_.Id.ToString()
            state               = $_.State.ToString()
            cpu_usage_pct       = [int]$_.CPUUsage
            memory_assigned_mb  = [int]($_.MemoryAssigned / 1MB)
            uptime_sec          = [int]$_.Uptime.TotalSeconds
            version             = $_.Version
            generation          = $_.Generation
            notes               = $_.Notes
        }
    }
}

try {
    $vms = if ($Live) {
        list_vms-WrapLive -StateFilter $StateFilter -NamePattern $NamePattern
    } else {
        list_vms-WrapMock -StateFilter $StateFilter -NamePattern $NamePattern
    }

    $payload = @{
        ok           = $true
        host         = $env:COMPUTERNAME
        captured_at  = (Get-Date -Format 'o')
        vm_count     = @($vms).Count
        vms          = @($vms)
    }
    $payload | ConvertTo-Json -Depth 6 -Compress
    exit 0
} catch {
    @{ ok = $false; error = @{ code = 'internal'; message = $_.Exception.Message } } |
        ConvertTo-Json -Depth 4 -Compress
    exit 1
}
