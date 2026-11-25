# Building Nearshelf on Windows (PowerShell)

## 1. Install once

- **Git for Windows**: https://git-scm.com/download/win
- **Android Studio**: https://developer.android.com/studio. It brings Java (JDK 21) and the Android SDK. Open it once and finish the setup wizard (this installs the SDK and accepts its licences).
  - Without Android Studio: install Temurin JDK 21 (https://adoptium.net) and the Android command-line tools, then run `sdkmanager --licenses`.

The project uses Gradle 9.8 through the wrapper (`gradlew.bat`); it downloads itself and every library on the first build (a few minutes, internet needed).

## 2. Put the code on GitHub (github.com/mar-devl)

Create an **empty** repository named `Nearshelf` on GitHub (no README, no .gitignore, no licence), then in PowerShell:

```powershell
Expand-Archive .\Nearshelf.zip -DestinationPath C:\dev
cd C:\dev\Nearshelf
git init -b main
git add .
git commit -m "Nearshelf 1.0.0"
git remote add origin https://github.com/mar-devl/Nearshelf.git
git push -u origin main
```

`local.properties`, keystores (`*.jks`, `*.keystore`) and build output are in `.gitignore`, so your passwords and keys never reach GitHub.

## 3. Allow the scripts in this PowerShell window

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

(This only affects the current window.)

## 4. Create your upload keystore (once)

```powershell
.\tools\windows\create-keystore.ps1
```

It asks for a name (default MAR Dev), a two-letter country code and a password, creates
`%USERPROFILE%\nearshelf-keys\nearshelf-upload.jks`, and writes the signing settings into `local.properties`.

**Back up the .jks file and its password** (e.g. a password manager plus an offline copy). Do not commit them.

The same thing by hand, if you prefer:

```powershell
keytool -genkeypair -v -keystore "$HOME\nearshelf-keys\nearshelf-upload.jks" -storetype PKCS12 -alias upload -keyalg RSA -keysize 2048 -validity 10000
```

and in `local.properties`:

```properties
release.storeFile=C:/Users/YOU/nearshelf-keys/nearshelf-upload.jks
release.storePassword=YOUR_PASSWORD
release.keyAlias=upload
release.keyPassword=YOUR_PASSWORD
```

## 5. Your AdMob IDs (for the real ads)

Add to `local.properties` (from AdMob › Apps › Nearshelf):

```properties
admob.appId=ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX
admob.nativeUnitId=ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX
admob.testAds=false
```

**Test ads on/off:** `admob.testAds=true` makes the release build show Google's test ads too (for a release you want to try on your own phone); set it back to `false` before building the version you upload to Play. The build log and `build-release.ps1` say which ads the release contains.

Only **release** builds use these IDs. Debug builds always show Google's test ads, so testing on your own phone never touches your live ads (AdMob can suspend an account whose owner taps its own ads). The build stops with a clear message if an ID is in the wrong place (the app ID has `~`, the unit ID has `/`).

## 6. Build

```powershell
.\tools\windows\build-release.ps1
```

Results:

- `app\build\outputs\bundle\release\app-release.aab`: upload this to Google Play.
- `app\build\outputs\apk\release\app-release.apk`: to install on your phone.

Add `-SkipTests` to build faster once tests have passed.

## 7. Google Play

1. Play Console › Create app › Nearshelf: Library Book Finder.
2. Setup › App integrity: keep **Play App Signing** on (Google holds the app signing key; yours is the upload key).
3. Testing › Internal testing › Create release › upload `app-release.aab`.
4. App content › Privacy policy: `https://mar-devl.github.io/Nearshelf-legal/`
5. Store listing, Data safety and content rating: see `docs/play-store.md`.

Before each new release, raise `versionCode` (and `versionName`) in `app/build.gradle.kts`.
