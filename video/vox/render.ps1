<#
.SYNOPSIS
  Renders the Red Rising explainer at full quality and joins the eight acts into one film.

.EXAMPLE
  .\render.ps1                         # full quality: CRF 12, slow preset, 320k audio
  .\render.ps1 -Crf 16 -Preset medium  # faster, still high quality
  .\render.ps1 -Acts 3,4               # re-render only some acts, then rejoin

  Requires Python 3.10+ and ffmpeg on PATH. Output goes to .\out\
#>
param(
    [int]$Crf = 12,
    [ValidateSet('ultrafast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow')]
    [string]$Preset = 'slow',
    [string]$AudioBitrate = '320k',
    [int]$Parallel = [Math]::Max(1, [int]([Environment]::ProcessorCount / 2)),
    [int[]]$Acts = @(1, 2, 3, 4, 5, 6, 7, 8),
    [string]$OutDir = (Join-Path $PSScriptRoot 'out')
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$ActFiles = @{
    1 = 'Act1_The_Mines.mp4'
    2 = 'Act2_The_Author.mp4'
    3 = 'Act3_A_World_Ruled_by_Color.mp4'
    4 = 'Act4_Eo_and_the_Lie.mp4'
    5 = 'Act5_The_Institute.mp4'
    6 = 'Act6_Rome_and_the_Cost.mp4'
    7 = 'Act7_Allies_and_Enemies.mp4'
    8 = 'Act8_Legacy.mp4'
}

# --- tools ---------------------------------------------------------------
$Py = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' }
      elseif (Get-Command py -ErrorAction SilentlyContinue) { 'py' }
      else { throw 'Python not found. Install Python 3.10+ from python.org and tick "Add to PATH".' }
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    throw 'ffmpeg not found. Install it (e.g. "winget install Gyan.FFmpeg") and reopen PowerShell.'
}

Write-Host "Installing Python packages..." -ForegroundColor Cyan
& $Py -m pip install --quiet --upgrade -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'pip install failed.' }

New-Item -ItemType Directory -Force $OutDir | Out-Null
$env:VOX_CRF = "$Crf"
$env:VOX_PRESET = $Preset
$env:VOX_ABR = $AudioBitrate

# --- render acts in parallel ---------------------------------------------
Write-Host "Rendering acts $($Acts -join ', ') with CRF $Crf, preset $Preset, $Parallel at a time..." -ForegroundColor Cyan
$queue = [System.Collections.Queue]::new()
$Acts | ForEach-Object { $queue.Enqueue($_) }
$running = @()
$started = Get-Date

while ($queue.Count -gt 0 -or $running.Count -gt 0) {
    while ($running.Count -lt $Parallel -and $queue.Count -gt 0) {
        $n = $queue.Dequeue()
        $out = Join-Path $OutDir $ActFiles[$n]
        $p = Start-Process -FilePath $Py -NoNewWindow -PassThru `
            -ArgumentList @("act${n}_vox.py", 'video', "`"$out`"") `
            -RedirectStandardOutput (Join-Path $OutDir "act$n.log") `
            -RedirectStandardError (Join-Path $OutDir "act$n.err.log")
        $null = $p.Handle  # keeps ExitCode available after the process ends
        $running += [pscustomobject]@{ Proc = $p; Act = $n }
        Write-Host "  started act $n"
    }
    Start-Sleep -Seconds 2
    foreach ($r in @($running)) {
        if ($r.Proc.HasExited) {
            if ($r.Proc.ExitCode -ne 0) {
                Get-Content (Join-Path $OutDir "act$($r.Act).err.log") -Tail 20
                throw "Act $($r.Act) failed (exit $($r.Proc.ExitCode)). See $OutDir\act$($r.Act).err.log"
            }
            Write-Host ("  finished act {0}  ({1:mm\:ss} elapsed)" -f $r.Act, ((Get-Date) - $started)) -ForegroundColor Green
            $running = @($running | Where-Object { $_.Act -ne $r.Act })
        }
    }
}

# --- join all eight acts into one film -----------------------------------
$missing = 1..8 | Where-Object { -not (Test-Path (Join-Path $OutDir $ActFiles[$_])) }
if ($missing) {
    Write-Host "Acts not rendered yet: $($missing -join ', '). Skipping the full film." -ForegroundColor Yellow
    exit 0
}
$list = Join-Path $OutDir 'acts.txt'
$lines = 1..8 | ForEach-Object { "file '" + ((Join-Path $OutDir $ActFiles[$_]) -replace '\\', '/') + "'" }
[System.IO.File]::WriteAllLines($list, $lines)  # UTF-8 without BOM, which ffmpeg's concat reader needs

$full = Join-Path $OutDir 'Red_Rising_Full.mp4'
ffmpeg -y -v error -f concat -safe 0 -i $list -c copy -movflags +faststart $full
if ($LASTEXITCODE -ne 0) { throw 'Joining the acts failed.' }

$dur = & ffprobe -v error -show_entries format=duration -of csv=p=0 $full
Write-Host ("Done: {0}  ({1:N1} s, {2:N0} MB, total {3:mm\:ss})" -f $full, [double]$dur, ((Get-Item $full).Length / 1MB), ((Get-Date) - $started)) -ForegroundColor Green
