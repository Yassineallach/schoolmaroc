<#
.SYNOPSIS
  Creates Nearshelf's upload keystore and writes the signing settings to local.properties.

.DESCRIPTION
  - Asks for the keystore password once (hidden) and passes it to keytool through a
    temporary environment variable, so it never appears on the command line.
  - Creates a PKCS12 keystore with one RSA 2048 key valid for about 27 years
    (Google Play requires validity beyond 22 October 2033).
  - Updates local.properties (never committed: it is in .gitignore) with
    release.storeFile / storePassword / keyAlias / keyPassword, keeping other lines.

  Keep the keystore file and its password safe and backed up: with Play App Signing you
  can ask Google to reset a lost upload key, but it takes time.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\tools\windows\create-keystore.ps1
.EXAMPLE
  .\tools\windows\create-keystore.ps1 -KeystorePath "D:\keys\nearshelf-upload.jks"
#>
param(
    [string]$KeystorePath = (Join-Path $HOME "nearshelf-keys\nearshelf-upload.jks"),
    [string]$Alias = "upload"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")

function Find-Keytool {
    if ($env:JAVA_HOME -and (Test-Path (Join-Path $env:JAVA_HOME "bin\keytool.exe"))) {
        return (Join-Path $env:JAVA_HOME "bin\keytool.exe")
    }
    $onPath = Get-Command keytool -ErrorAction SilentlyContinue
    if ($onPath) { return $onPath.Source }
    $studio = "C:\Program Files\Android\Android Studio\jbr\bin\keytool.exe"
    if (Test-Path $studio) { return $studio }
    throw "keytool not found. Install JDK 21 (or Android Studio) and set JAVA_HOME, then run this again."
}

function Read-Plain([string]$prompt) {
    $secure = Read-Host -Prompt $prompt -AsSecureString
    return [System.Net.NetworkCredential]::new("", $secure).Password
}

# Values inside a distinguished name: escape the characters keytool treats specially.
function Escape-Dn([string]$value) { return ($value -replace '([,+="\\<>;])', '\$1') }

$keytool = Find-Keytool
Write-Host "Using keytool: $keytool"

if (Test-Path $KeystorePath) {
    throw "A keystore already exists at $KeystorePath. Choose another -KeystorePath; never overwrite an upload key."
}
New-Item -ItemType Directory -Force -Path (Split-Path $KeystorePath) | Out-Null

# Who the certificate names (shown to nobody but you and Google).
$name = Read-Host "Your name or the developer name [MAR Dev]"
if ([string]::IsNullOrWhiteSpace($name)) { $name = "MAR Dev" }
$org = Read-Host "Organization [MAR Dev]"
if ([string]::IsNullOrWhiteSpace($org)) { $org = "MAR Dev" }
do { $country = (Read-Host "Two-letter country code (e.g. MA, US, FR)").Trim().ToUpper() } until ($country -match '^[A-Z]{2}$')
$dname = "CN=$(Escape-Dn $name), O=$(Escape-Dn $org), C=$country"

do {
    $pass = Read-Plain "Keystore password (at least 6 characters, hidden)"
    $again = Read-Plain "Type it again"
    if ($pass -ne $again) { Write-Host "The passwords don't match. Try again." -ForegroundColor Yellow }
    elseif ($pass.Length -lt 6) { Write-Host "Use at least 6 characters." -ForegroundColor Yellow }
} until ($pass -eq $again -and $pass.Length -ge 6)

# PKCS12 keystores use one password for the store and the key.
$env:NEARSHELF_KS_PASS = $pass
try {
    & $keytool -genkeypair -v `
        -keystore $KeystorePath -storetype PKCS12 `
        -alias $Alias -keyalg RSA -keysize 2048 -validity 10000 `
        -dname $dname `
        -storepass:env NEARSHELF_KS_PASS -keypass:env NEARSHELF_KS_PASS
    if ($LASTEXITCODE -ne 0) { throw "keytool failed (exit code $LASTEXITCODE)." }
} finally {
    Remove-Item Env:\NEARSHELF_KS_PASS -ErrorAction SilentlyContinue
}

# local.properties: replace the release.* lines, keep everything else (sdk.dir, admob.*).
$propsPath = Join-Path $ProjectRoot "local.properties"
$lines = @()
if (Test-Path $propsPath) { $lines = @(Get-Content $propsPath | Where-Object { $_ -notmatch '^\s*release\.' }) }
$storeFile = ($KeystorePath -replace '\\', '/')      # forward slashes need no escaping
$escapedPass = ($pass -replace '\\', '\\')           # a backslash must be doubled in .properties
$lines += "release.storeFile=$storeFile"
$lines += "release.storePassword=$escapedPass"
$lines += "release.keyAlias=$Alias"
$lines += "release.keyPassword=$escapedPass"
# WriteAllLines writes UTF-8 without a byte-order mark, which Java's Properties reads correctly.
[System.IO.File]::WriteAllLines($propsPath, [string[]]$lines)

Write-Host ""
Write-Host "Keystore created: $KeystorePath" -ForegroundColor Green
Write-Host "Signing settings written to: $propsPath"
Write-Host ""
Write-Host "Back up the keystore file and its password somewhere safe (not in Git)." -ForegroundColor Yellow
Write-Host "Certificate fingerprint (for your records):"
$env:NEARSHELF_KS_PASS = $pass
try { & $keytool -list -keystore $KeystorePath -storepass:env NEARSHELF_KS_PASS -alias $Alias } finally { Remove-Item Env:\NEARSHELF_KS_PASS -ErrorAction SilentlyContinue }
