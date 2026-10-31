<#
.SYNOPSIS
  Renders the Red Rising explainer at full quality and joins the eight acts into one film.

.EXAMPLE
  .\render.ps1                         # full quality: CRF 12, slow preset, 320k audio
  .\render.ps1 -Crf 16 -Preset medium  # faster, still high quality
  .\render.ps1 -Acts 3,4               # re-render only some acts, then rejoin
  .\render.ps1 -Parallel 4             # render four acts at once (faster on many-core PCs)

  Requires Python 3.10+ and ffmpeg on PATH. Output goes to .\out\
#>
param(
    [int]$Crf = 12,
    [ValidateSet('ultrafast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow')]
    [string]$Preset = 'slow',
    [string]$AudioBitrate = '320k',
    [int]$Parallel = 1,  # one act at a time; raise (e.g. -Parallel 4) to render several at once
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

# --- tools (installed automatically if missing) ---------------------------
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProgressPreference = 'SilentlyContinue'
$Tools = Join-Path $PSScriptRoot 'tools'
New-Item -ItemType Directory -Force $Tools | Out-Null

function Test-Python([string]$exe) {
    # The Windows "python" store alias exists but is not a real Python, so actually run it.
    try { & $exe -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null; return $LASTEXITCODE -eq 0 } catch { return $false }
}

$Py = $null
$localPy = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
foreach ($cand in @('python', 'py', $localPy)) { if (Test-Python $cand) { $Py = $cand; break } }
if (-not $Py) {
    Write-Host "Python not found - downloading and installing Python 3.12 (just for this user)..." -ForegroundColor Cyan
    $setup = Join-Path $Tools 'python-setup.exe'
    Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile $setup
    Start-Process $setup -ArgumentList '/quiet InstallAllUsers=0 PrependPath=1 Include_test=0' -Wait
    if (-not (Test-Python $localPy)) { throw "Python install failed. Install Python 3.12 from python.org (tick 'Add to PATH') and run again." }
    $Py = $localPy
}
Write-Host "Using Python: $Py"

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    $ffExe = Get-ChildItem $Tools -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $ffExe) {
        Write-Host "ffmpeg not found - downloading it into .\tools ..." -ForegroundColor Cyan
        $zip = Join-Path $Tools 'ffmpeg.zip'
        Invoke-WebRequest 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile $zip
        Expand-Archive $zip (Join-Path $Tools 'ffmpeg') -Force
        $ffExe = Get-ChildItem $Tools -Recurse -Filter ffmpeg.exe | Select-Object -First 1
    }
    $env:Path = "$($ffExe.DirectoryName);$env:Path"
}
Write-Host "Using ffmpeg: $((Get-Command ffmpeg).Source)"

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
