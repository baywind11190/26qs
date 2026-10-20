param([Parameter(Mandatory=$true)][string]$Root,[Parameter(Mandatory=$true)][string]$Instance,[Parameter(Mandatory=$true)][int]$ParentPid)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path -LiteralPath $Root).Path
if (-not $taskRoot.StartsWith('D:\codex\0000_26qs\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Collector workspace outside authorized project' }
if ($Instance -notmatch '^PMUX_CPU_[a-f0-9]{32}$') { throw 'Invalid private trace instance' }
$taskWpr=Join-Path $env:SystemRoot 'System32\wpr.exe'
$taskProfile=Join-Path $PSScriptRoot 'cpu_diagnostic.wprp'
$taskOwned=$false
$taskParentStart=(Get-Process -Id $ParentPid).StartTime
function Write-Reply($name,$object) {
    $taskText=$object | ConvertTo-Json -Depth 5
    [IO.File]::WriteAllText((Join-Path $taskRoot $name),$taskText,[Text.UTF8Encoding]::new($false))
}
$taskIdentity=[Security.Principal.WindowsIdentity]::GetCurrent()
$taskAdmin=[Security.Principal.WindowsPrincipal]::new($taskIdentity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Write-Reply 'collector_ready.json' @{pid=$PID;administrator=$taskAdmin;instance=$Instance}
if (-not $taskAdmin) { exit 3 }
$taskDeadline=[DateTime]::UtcNow.AddHours(1)
$taskSequence=0
try {
    while ([DateTime]::UtcNow -lt $taskDeadline) {
        $taskParent=Get-Process -Id $ParentPid -ErrorAction SilentlyContinue
        if (-not $taskParent -or $taskParent.StartTime -ne $taskParentStart) { break }
        $taskRequestPath=Join-Path $taskRoot 'collector_request.json'
        if (-not (Test-Path -LiteralPath $taskRequestPath)) { Start-Sleep -Milliseconds 100;continue }
        try { $taskRequest=Get-Content -Raw -LiteralPath $taskRequestPath | ConvertFrom-Json } catch { Start-Sleep -Milliseconds 100;continue }
        if ($taskRequest.instance -ne $Instance -or $taskRequest.sequence -le $taskSequence) { Start-Sleep -Milliseconds 100;continue }
        $taskSequence=[int]$taskRequest.sequence
        $taskCode=3;$taskOutput='invalid operation'
        if ($taskRequest.action -eq 'start' -and -not $taskOwned) {
            $taskOutput=(& $taskWpr -start "$taskProfile!PMUXCPU" -filemode -instancename $Instance 2>&1 | Out-String)
            $taskCode=$LASTEXITCODE
            if ($taskCode -eq 0) {$taskOwned=$true}
        } elseif ($taskRequest.action -in @('stop','abort') -and $taskOwned -and $taskRequest.name -match '^[a-zA-Z0-9_-]+$') {
            $taskTrace=Join-Path $taskRoot ($taskRequest.name+'.etl')
            if (Test-Path -LiteralPath $taskTrace) { $taskOutput='refusing to overwrite ETL' } else {
                $taskOutput=(& $taskWpr -stop $taskTrace 'PMUX CPU qualification' -skipPdbGen -instancename $Instance 2>&1 | Out-String)
                $taskCode=$LASTEXITCODE
                if ($taskCode -eq 0) {$taskOwned=$false}
            }
        } elseif ($taskRequest.action -eq 'abort' -and -not $taskOwned) { $taskCode=0;$taskOutput='no owned recording' }
        elseif ($taskRequest.action -eq 'finish' -and -not $taskOwned) { $taskCode=0;$taskOutput='finished' }
        Write-Reply ('collector_response_'+$taskSequence+'.json') @{sequence=$taskSequence;rc=$taskCode;output=$taskOutput;owned=$taskOwned;instance=$Instance}
        if ($taskRequest.action -eq 'finish' -and -not $taskOwned) { break }
    }
} finally {
    if ($taskOwned) { & $taskWpr -cancel -instancename $Instance 2>&1 | Out-File -LiteralPath (Join-Path $taskRoot 'owned_session_cleanup.log') -Encoding utf8 }
}
