<#
.SYNOPSIS
  Builds Nearshelf's release bundle (.aab, for Google Play) and APK on Windows.

.DESCRIPTION
  Finds Java (JAVA_HOME, PATH, or Android Studio's bundled JDK) and the Android SDK
  (local.properties, ANDROID_HOME, or the default %LOCALAPPDATA%\Android\Sdk), runs the
  tests, then builds. Gradle downloads itself and every dependency on the first run.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\tools\windows\build-release.ps1
.EXAMPLE
  .\tools\windows\build-release.ps1 -SkipTests
#>
param([switch]$SkipTests)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $ProjectRoot
$propsPath = Join-Path $ProjectRoot "local.properties"
$props = @{}
if (Test-Path $propsPath) {
    foreach ($line in Get-Content $propsPath) {
        if ($line -match '^\s*([^#=\s]+)\s*=\s*(.*)$') { $props[$Matches[1]] = $Matches[2] }
    }
}

# --- Java (JDK 17 or newer; 21 recommended) ---
if (-not $env:JAVA_HOME) {
    $candidates = @("C:\Program Files\Android\Android Studio\jbr") +
        @(Get-ChildItem "C:\Program Files\Eclipse Adoptium" -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | ForEach-Object { $_.FullName })
    foreach ($c in $candidates) {
        if (Test-Path (Join-Path $c "bin\java.exe")) { $env:JAVA_HOME = $c; break }
    }
}
if (-not $env:JAVA_HOME -and -not (Get-Command java -ErrorAction SilentlyContinue)) {
    throw "No Java found. Install Android Studio or Temurin JDK 21 (https://adoptium.net), then run this again."
}
Write-Host "Java: $(if ($env:JAVA_HOME) { $env:JAVA_HOME } else { (Get-Command java).Source })"

# --- Android SDK ---
$sdk = $props["sdk.dir"]
# Android Studio writes it escaped (C\:\\Users\\...): undo that for Windows paths.
if ($sdk) { $sdk = ($sdk -replace '\\:', ':') -replace '\\\\', '\' }
if (-not $sdk) { $sdk = $env:ANDROID_HOME }
if (-not $sdk) { $sdk = $env:ANDROID_SDK_ROOT }
if (-not $sdk) {
    $default = Join-Path $env:LOCALAPPDATA "Android\Sdk"
    if (Test-Path $default) { $sdk = $default }
}
if (-not $sdk) { throw "No Android SDK found. Install Android Studio (it installs the SDK), open it once, then run this again." }
if (-not $props.ContainsKey("sdk.dir")) {
    # Forward slashes need no escaping in .properties.
    Add-Content -Path $propsPath -Value ("sdk.dir=" + ($sdk -replace '\\', '/')) -Encoding ascii
}
Write-Host "Android SDK: $sdk"
if (-not (Test-Path (Join-Path $sdk "licenses"))) {
    Write-Host "SDK licences not accepted yet. Run: & `"$sdk\cmdline-tools\latest\bin\sdkmanager.bat`" --licenses" -ForegroundColor Yellow
}

# --- What this build will contain ---
$signed = $props.ContainsKey("release.storeFile") -and $props.ContainsKey("release.storePassword")
if (-not $signed) { Write-Host "No upload key in local.properties: the release will be UNSIGNED. Run create-keystore.ps1 first." -ForegroundColor Yellow }
if ("$($props['admob.testAds'])".Trim() -ieq "true") { Write-Host "admob.testAds=true in local.properties: this release shows Google's TEST ads. Set it to false before uploading to Play." -ForegroundColor Yellow }
else { Write-Host "AdMob: this release shows your REAL ads." -ForegroundColor Green }

# --- Build ---
$tasks = @()
if (-not $SkipTests) { $tasks += "test" }
$tasks += ":app:bundleRelease", ":app:assembleRelease"
& .\gradlew.bat @tasks --console=plain
if ($LASTEXITCODE -ne 0) { throw "Build failed (exit code $LASTEXITCODE). Scroll up for the first error." }

$aab = Join-Path $ProjectRoot "app\build\outputs\bundle\release\app-release.aab"
$apk = Get-ChildItem (Join-Path $ProjectRoot "app\build\outputs\apk\release") -Filter "*.apk" -ErrorAction SilentlyContinue | Select-Object -First 1
Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Play bundle: $aab"
if ($apk) { Write-Host "APK:         $($apk.FullName)" }
if ($signed) { Write-Host "Signed with your upload key: upload the .aab to Play Console (Internal testing first)." }
