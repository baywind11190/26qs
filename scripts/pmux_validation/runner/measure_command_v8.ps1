param([Parameter(Mandatory=$true)][string]$RequestPath)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$req = Get-Content -Raw -Encoding UTF8 -LiteralPath $RequestPath | ConvertFrom-Json
$worker = $null; $client = $null; $reader = $null; $writer = $null
$metrics = $null; $measurement = $null; $hostError = $null
$token = [Guid]::NewGuid().ToString('N')
$ready = Join-Path $req.cwd 'worker_ready.json'
try {
    if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) {
        throw 'Windows PowerShell 5.1 required'
    }
    foreach ($path in @($ready,$req.result_path)) {
        if (Test-Path -LiteralPath $path) { throw ('Refusing overwrite: ' + $path) }
    }
    $workerScript = Join-Path $PSScriptRoot 'measure_worker_v8.py'
    $arguments = '"{0}" "{1}" "{2}" "{3}"' -f $workerScript,$req.runner,$ready,$token
    $worker = Start-Process -FilePath $req.python -ArgumentList $arguments -PassThru -WindowStyle Hidden `
        -WorkingDirectory $req.cwd -RedirectStandardOutput (Join-Path $req.cwd 'worker.stdout.log') `
        -RedirectStandardError (Join-Path $req.cwd 'worker.stderr.log')
    $deadline = [DateTime]::UtcNow.AddSeconds(20)
    while (-not (Test-Path -LiteralPath $ready) -and [DateTime]::UtcNow -lt $deadline) {
        if ($worker.HasExited) { throw 'Measurement worker exited before readiness' }
        Start-Sleep -Milliseconds 20
    }
    if (-not (Test-Path -LiteralPath $ready)) { throw 'Measurement worker readiness timeout' }
    $info = Get-Content -Raw -Encoding UTF8 -LiteralPath $ready | ConvertFrom-Json
    if ($info.token -ne $token -or $info.memory_method -ne 'windows-root-exit-event-v1') {
        throw 'Measurement worker identity mismatch'
    }
    $client = New-Object System.Net.Sockets.TcpClient
    $client.NoDelay = $true
    $client.Connect([string]$info.host,[int]$info.port)
    $stream = $client.GetStream()
    $reader = New-Object System.IO.StreamReader($stream,[System.Text.Encoding]::UTF8,$false,4096,$true)
    $writer = New-Object System.IO.StreamWriter($stream,$utf8,4096,$true)
    $writer.AutoFlush = $true
    $request = [ordered]@{token=$token; action='run'; request_id=[Guid]::NewGuid().ToString('N');
        cmd=@($req.command); cwd=$req.cwd; log_path=$req.log_path; timeout_s=$req.timeout_s; env=$null}
    $wire = $request | ConvertTo-Json -Compress -Depth 12
    $script:responseLine = $null
    $measurement = Microsoft.PowerShell.Utility\Measure-Command -Expression {
        $writer.WriteLine($wire)
        $script:responseLine = $reader.ReadLine()
    }
    if ([string]::IsNullOrWhiteSpace($script:responseLine)) { throw 'No worker response' }
    [System.IO.File]::WriteAllText((Join-Path $req.cwd 'worker_response.json'),$script:responseLine,$utf8)
    $response = $script:responseLine | ConvertFrom-Json
    if (-not $response.ok) { throw ('Worker error: ' + $response.error) }
    $metrics = $response.metrics
    $writer.WriteLine((@{token=$token; action='shutdown'; request_id='shutdown'} | ConvertTo-Json -Compress))
    $null = $reader.ReadLine()
    if (-not $worker.WaitForExit(10000)) { throw 'Measurement worker shutdown timeout' }
}
catch { $hostError = $_.Exception.ToString() }
finally {
    if ($reader) { $reader.Dispose() }
    if ($writer) { $writer.Dispose() }
    if ($client) { $client.Dispose() }
    if ($worker -and -not $worker.HasExited) { $worker.Kill(); $worker.WaitForExit() }
}
$result = [ordered]@{}
if ($metrics) { foreach ($property in $metrics.PSObject.Properties) { $result[$property.Name] = $property.Value } }
$result.schema = 2
$result.performance_scheme = [string]$req.performance_scheme
$result.wall_time_method = [string]$req.method
$result.measure_command_module = 'Microsoft.PowerShell.Utility'
$result.wall_time_semantics = 'Request dispatch through same Yosys debug-exit capture, process exit, and log/output completion; local transport and debugger overhead included'
$result.time_span_ticks = if ($measurement) { [long]$measurement.Ticks } else { $null }
$result.total_milliseconds = if ($measurement) { [double]$measurement.TotalMilliseconds } else { $null }
$result.yosys_pid = if ($metrics) { $metrics.main_pid } else { $null }
$result.time_pid = if ($metrics) { $metrics.main_pid } else { $null }
$result.process_exit_observed = [bool]($metrics -and $metrics.memory_exit_event_observed -and $metrics.memory_capture_complete)
$result.output_capture_complete = [bool]($metrics -and $metrics.rc -ne $null -and (Test-Path -LiteralPath $req.log_path))
$result.powershell_major = [int]$PSVersionTable.PSVersion.Major
$result.powershell_minor = [int]$PSVersionTable.PSVersion.Minor
$result.powershell_version = [string]$PSVersionTable.PSVersion.ToString()
$psExe = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
$result.powershell_path = $psExe
$hashStream = [System.IO.File]::OpenRead($psExe)
$hasher = [System.Security.Cryptography.SHA256]::Create()
try {
    $result.powershell_sha256 = [System.BitConverter]::ToString($hasher.ComputeHash($hashStream)).Replace('-','').ToLowerInvariant()
}
finally { $hashStream.Dispose(); $hasher.Dispose() }
if ($hostError) { $result.measurement_error = $hostError; $result.metrics_valid = $false }
[System.IO.File]::WriteAllText($req.result_path,($result | ConvertTo-Json -Depth 14),$utf8)
if ($hostError) { exit 2 }
exit 0
