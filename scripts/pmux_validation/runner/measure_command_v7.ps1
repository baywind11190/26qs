param(
    [Parameter(Mandatory = $true)]
    [string]$RequestPath
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$requestFullPath = [System.IO.Path]::GetFullPath($RequestPath)
$request = [System.IO.File]::ReadAllText($requestFullPath, [System.Text.Encoding]::UTF8) |
    ConvertFrom-Json
$resultPath = [System.IO.Path]::GetFullPath([string]$request.result_path)
$stdoutPath = [System.IO.Path]::GetFullPath([string]$request.stdout_path)
$stderrPath = [System.IO.Path]::GetFullPath([string]$request.stderr_path)
$commandInfo = Get-Command -Name 'Microsoft.PowerShell.Utility\Measure-Command' -CommandType Cmdlet
if ($commandInfo.ModuleName -ne 'Microsoft.PowerShell.Utility') {
    throw 'Measure-Command is not provided by Microsoft.PowerShell.Utility'
}
if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) {
    throw 'V7 requires Windows PowerShell 5.1'
}
if (-not [System.IO.Directory]::Exists([string]$request.working_directory)) {
    throw 'Native working directory is missing'
}
if ([int]$request.timeout_ms -le 0) {
    throw 'Native timeout must be a positive number of milliseconds'
}

$process = New-Object System.Diagnostics.Process
$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = [string]$request.executable
$startInfo.Arguments = [string]$request.argument_string
$startInfo.WorkingDirectory = [string]$request.working_directory
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$process.StartInfo = $startInfo

$stdoutFile = New-Object System.IO.FileStream(
    $stdoutPath, [System.IO.FileMode]::CreateNew,
    [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
$stderrFile = New-Object System.IO.FileStream(
    $stderrPath, [System.IO.FileMode]::CreateNew,
    [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
$stdoutTask = $null
$stderrTask = $null
$timedOut = $false
$exitObserved = $false
$stdoutComplete = $false
$stderrComplete = $false
$nativeExitCode = $null
$nativePid = $null
$measurement = $null
$measurementError = $null

try {
    $measurement = Microsoft.PowerShell.Utility\Measure-Command -Expression {
        $null = $process.Start()
        $script:nativePid = $process.Id
        $stdoutTask = $process.StandardOutput.BaseStream.CopyToAsync($stdoutFile)
        $stderrTask = $process.StandardError.BaseStream.CopyToAsync($stderrFile)

        if (-not $process.WaitForExit([int]$request.timeout_ms)) {
            $script:timedOut = $true
            $killerInfo = New-Object System.Diagnostics.ProcessStartInfo
            $killerInfo.FileName = Join-Path $env:SystemRoot 'System32\taskkill.exe'
            $killerInfo.Arguments = '/PID ' + $process.Id + ' /T /F'
            $killerInfo.UseShellExecute = $false
            $killerInfo.CreateNoWindow = $true
            $killer = [System.Diagnostics.Process]::Start($killerInfo)
            if (-not $killer.WaitForExit(10000)) {
                throw 'taskkill did not finish within 10 seconds'
            }
            $process.WaitForExit()
        }
        else {
            $process.WaitForExit()
            $script:exitObserved = $true
            $script:nativeExitCode = $process.ExitCode
        }

        $tasks = @($stdoutTask, $stderrTask)
        if (-not [System.Threading.Tasks.Task]::WaitAll(
                [System.Threading.Tasks.Task[]]$tasks, 30000)) {
            throw 'Native output streams did not drain within 30 seconds'
        }
        $stdoutTask.GetAwaiter().GetResult()
        $stderrTask.GetAwaiter().GetResult()
        $stdoutFile.Flush()
        $stderrFile.Flush()
        $script:stdoutComplete = $true
        $script:stderrComplete = $true
    }
}
catch {
    $measurementError = $_.Exception.ToString()
}
finally {
    if ($stdoutFile) { $stdoutFile.Dispose() }
    if ($stderrFile) { $stderrFile.Dispose() }
    if ($process) { $process.Dispose() }
}

$result = [ordered]@{
    schema = 1
    performance_scheme = [string]$request.performance_scheme
    wall_time_method = [string]$request.method
    measure_command_module = [string]$commandInfo.ModuleName
    measure_command_source = [string]$commandInfo.Source
    powershell_version = [string]$PSVersionTable.PSVersion.ToString()
    powershell_major = [int]$PSVersionTable.PSVersion.Major
    powershell_minor = [int]$PSVersionTable.PSVersion.Minor
    executable = [string]$request.executable
    actual_command = @([string]$request.executable) + @($request.arguments)
    working_directory = [string]$request.working_directory
    native_pid = $nativePid
    rc = $nativeExitCode
    timed_out = [bool]$timedOut
    process_exit_observed = [bool]$exitObserved
    stdout_capture_complete = [bool]$stdoutComplete
    stderr_capture_complete = [bool]$stderrComplete
    stdout_path = $stdoutPath
    stderr_path = $stderrPath
    time_span_ticks = if ($measurement) { [long]$measurement.Ticks } else { $null }
    total_milliseconds = if ($measurement) { [double]$measurement.TotalMilliseconds } else { $null }
    measurement_error = $measurementError
}
[System.IO.File]::WriteAllText(
    $resultPath, ($result | ConvertTo-Json -Depth 8), $utf8NoBom)
if ($measurementError) { exit 2 }
exit 0
