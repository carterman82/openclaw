<#
.SYNOPSIS
    Phase 4 wrapper for the openclaw agent. Invoked by Windows Task Scheduler
    daily at 07:00 America/Denver.

.DESCRIPTION
    Reads scheduled-sites.json at the project root, iterates over every entry
    where enabled=true, and runs `python -m openclaw post --site <slug>` for
    each. Per-site retry policy: up to 2 retries (total 3 attempts) with a
    60-second wait after attempt 1 and a 300-second wait after attempt 2.

    Every attempt appends stdout+stderr to
    `logs/openclaw-YYYY-MM-DD-<slug>.log` in the project root.

    Phase 8 Step 8.6: `python -m openclaw post` returns a distinct exit code 2
    when the article published successfully but the Phase 5 static-export/
    git-push deploy step failed (see openclaw/main.py). That case is NOT
    retried here — retrying would generate and publish a whole new duplicate
    article just to redo a git push. Instead it's recorded separately as a
    "deploy failure" and surfaced via a `deploy_failed=<slugs>` line in the
    flag payload, distinct from genuine generation failures (any other
    non-zero exit code, which IS retried).

    After the run, if any site had a generation failure and/or a deploy
    failure, `logs/last-run-failed.flag` is written containing both failure
    lists and the last 50 lines of the most recent failing log. On a fully
    clean run (no generation failures, no deploy failures), that flag file is
    removed. Exit code is the number of sites with a genuine generation
    failure after retries (0 = all generations succeeded; deploy-only
    failures don't affect the exit code but still drop the flag file).

.PARAMETER Sites
    Optional list of site slugs to override the scheduled-sites.json set.
    Useful for manual test runs: `.\scripts\run-openclaw.ps1 -Sites localhost`.

.PARAMETER Draft
    If specified, appends --draft to every `python -m openclaw post` call.
    Handy for a manual dry run that doesn't publish live.

.EXAMPLE
    .\scripts\run-openclaw.ps1
    .\scripts\run-openclaw.ps1 -Sites localhost -Draft
#>
[CmdletBinding()]
param(
    [string[]]$Sites,
    [switch]$Draft
)

# Do NOT set $ErrorActionPreference = 'Stop'. In PS 5.1, native command stderr
# is wrapped as NativeCommandError records; combined with Stop, the wrapper
# would terminate on Python's first `logging.INFO` line before the real work
# ran. We check $LASTEXITCODE explicitly instead.

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$PythonExe = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $PythonExe)) {
    throw "Missing venv Python at $PythonExe. Create .venv per README.md before scheduling."
}

# Task Scheduler's PATH doesn't include user-profile installs (e.g. Git for
# Windows under %LOCALAPPDATA%\Programs\Git). openclaw/deploy.py needs git.exe
# to push each subsite's Staatic export to GitHub Pages — without this
# prepend, every scheduled deploy fails with `FileNotFoundError: [WinError 2]`
# and the post is published locally but never reaches the live URL. Prepend
# each candidate directory that actually exists so a machine-wide install
# (Program Files) is preferred over a user-profile one when both are present.
$GitCandidates = @(
    (Join-Path $env:ProgramFiles 'Git\cmd'),
    (Join-Path ${env:ProgramFiles(x86)} 'Git\cmd'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Git\cmd'),
    (Join-Path $env:USERPROFILE 'AppData\Local\Programs\Git\cmd')
) | Where-Object { $_ -and (Test-Path (Join-Path $_ 'git.exe')) } | Select-Object -Unique
foreach ($gitDir in $GitCandidates) {
    if (-not ($env:PATH -split ';' | Where-Object { $_ -eq $gitDir })) {
        $env:PATH = "$gitDir;$env:PATH"
    }
}

$SitesConfigPath = Join-Path $ProjectRoot 'scheduled-sites.json'
$LogsDir = Join-Path $ProjectRoot 'logs'
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
}
$FailFlag = Join-Path $LogsDir 'last-run-failed.flag'

if ($Sites -and $Sites.Count -gt 0) {
    $siteSlugs = $Sites
} else {
    if (-not (Test-Path $SitesConfigPath)) {
        throw "Missing $SitesConfigPath. Create it with an array of {slug, enabled} entries."
    }
    $siteConfig = Get-Content $SitesConfigPath -Raw | ConvertFrom-Json
    $siteSlugs = @($siteConfig | Where-Object { $_.enabled } | ForEach-Object { $_.slug })
    if ($siteSlugs.Count -eq 0) {
        throw "No enabled sites in $SitesConfigPath. Nothing to do."
    }
}

$DateStamp = Get-Date -Format 'yyyy-MM-dd'
$RunStart = Get-Date

Write-Output "[$($RunStart.ToString('u'))] run-openclaw.ps1 starting; sites: $($siteSlugs -join ', ')"

# Retry cadence: N=2 retries = 3 attempts. Waits are applied AFTER a failing
# attempt only if there is a retry left.
$RetryWaits = @(60, 300)

$Failures = @{}
$DeployFailures = @{}
$LastFailingLog = $null

foreach ($slug in $siteSlugs) {
    $logPath = Join-Path $LogsDir ("openclaw-{0}-{1}.log" -f $DateStamp, $slug)
    $siteExit = 1
    $attempt = 0

    while ($attempt -le $RetryWaits.Count) {
        $attempt++
        $attemptHeader = "[{0}] === {1} attempt {2}/{3} ===" -f (Get-Date -Format 'u'), $slug, $attempt, ($RetryWaits.Count + 1)
        Add-Content -Path $logPath -Value $attemptHeader -Encoding utf8
        Write-Output $attemptHeader

        $argList = @('-m', 'openclaw', 'post', '--site', $slug, '--verbose')
        if ($Draft) { $argList += '--draft' }

        # Start-Process with file redirection sidesteps PS 5.1's native-command
        # stderr wrapping (which turns Python `logging` output into ErrorRecords
        # and can spuriously trip $ErrorActionPreference). Both streams land in
        # temp files, are appended in order to the log, and the exit code comes
        # from the process object.
        $stdoutTmp = [System.IO.Path]::GetTempFileName()
        $stderrTmp = [System.IO.Path]::GetTempFileName()
        try {
            $proc = Start-Process -FilePath $PythonExe -ArgumentList $argList `
                -NoNewWindow -Wait -PassThru `
                -RedirectStandardOutput $stdoutTmp `
                -RedirectStandardError $stderrTmp
            $siteExit = $proc.ExitCode
            if (Test-Path $stdoutTmp) {
                Get-Content $stdoutTmp | Add-Content -Path $logPath -Encoding utf8
            }
            if (Test-Path $stderrTmp) {
                Get-Content $stderrTmp | Add-Content -Path $logPath -Encoding utf8
            }
        } finally {
            Remove-Item -ErrorAction SilentlyContinue $stdoutTmp, $stderrTmp
        }

        $tailHeader = "[{0}] --- exit={1} attempt={2} ---" -f (Get-Date -Format 'u'), $siteExit, $attempt
        Add-Content -Path $logPath -Value $tailHeader -Encoding utf8

        if ($siteExit -eq 0) {
            Write-Output "${slug}: PASS on attempt $attempt"
            break
        }

        if ($siteExit -eq 2) {
            # Published successfully, only the deploy (static export + git push)
            # failed. Do NOT retry: a retry here would generate and publish an
            # entirely new duplicate article just to redo a git push. Record it
            # separately and move on to the next site.
            Write-Output "${slug}: PUBLISHED but deploy failed (exit=2) on attempt $attempt -- not retrying"
            break
        }

        Write-Output "${slug}: FAIL exit=$siteExit on attempt $attempt"
        if ($attempt -le $RetryWaits.Count) {
            $wait = $RetryWaits[$attempt - 1]
            Write-Output "${slug}: waiting ${wait}s before retry"
            Start-Sleep -Seconds $wait
        }
    }

    if ($siteExit -eq 2) {
        $DeployFailures[$slug] = @{ log = $logPath }
        $LastFailingLog = $logPath
    } elseif ($siteExit -ne 0) {
        $Failures[$slug] = @{ exit = $siteExit; log = $logPath }
        $LastFailingLog = $logPath
    }
}

$RunEnd = Get-Date
$Elapsed = $RunEnd - $RunStart
Write-Output "[$($RunEnd.ToString('u'))] run-openclaw.ps1 finished in $([int]$Elapsed.TotalSeconds)s"

if ($Failures.Count -gt 0 -or $DeployFailures.Count -gt 0) {
    $flagLines = @(
        "openclaw run: $($Failures.Count) generation failure(s), $($DeployFailures.Count) deploy failure(s) of $($siteSlugs.Count) site(s)."
        "Run started : $($RunStart.ToString('u'))"
        "Run finished: $($RunEnd.ToString('u'))"
        ""
    )
    if ($Failures.Count -gt 0) {
        $flagLines += "Failed sites (generation):"
        foreach ($slug in $Failures.Keys) {
            $flagLines += "  - $slug (exit=$($Failures[$slug].exit), log=$($Failures[$slug].log))"
        }
        $flagLines += ""
    }
    if ($DeployFailures.Count -gt 0) {
        # Grep-friendly single line (Step 8.6) alongside the human-readable list.
        $flagLines += "deploy_failed=$(($DeployFailures.Keys) -join ',')"
        $flagLines += "Deploy-failed sites (published locally; GitHub Pages push failed):"
        foreach ($slug in $DeployFailures.Keys) {
            $flagLines += "  - $slug (log=$($DeployFailures[$slug].log))"
        }
        $flagLines += ""
    }
    if ($LastFailingLog -and (Test-Path $LastFailingLog)) {
        $flagLines += "Last 50 lines of $LastFailingLog :"
        $flagLines += (Get-Content $LastFailingLog -Tail 50)
    }
    Set-Content -Path $FailFlag -Value $flagLines -Encoding utf8
    Write-Output "Wrote failure flag: $FailFlag"
    exit $Failures.Count
} else {
    if (Test-Path $FailFlag) {
        Remove-Item $FailFlag
        Write-Output "Cleared previous failure flag: $FailFlag"
    }
    exit 0
}
