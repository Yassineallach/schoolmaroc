# Building Nearshelf on GitHub (no build tools on your PC)

GitHub Actions builds the signed Play bundle (`.aab`) and an installable APK in the cloud.
Workflow: `.github/workflows/release.yml`. Your PC is only needed once, to create the upload key.

## 1. Put the project on GitHub

The project has about 300 files; GitHub's web upload takes 100 at a time, so use
**GitHub Desktop** (desktop.github.com):

1. File › Add local repository › choose the `Nearshelf` folder › "create a repository" if asked.
2. Publish repository › name `Nearshelf` › keep **Private** ticked.
3. Check that the `.github` folder is in the repository on github.com.

`local.properties` and `*.jks` are in `.gitignore`, so your passwords, IDs and key never upload.

## 2. Create the upload key (once, keep it forever)

Needs only Java (you have Amazon Corretto), not Gradle:

```powershell
.\tools\windows\create-keystore.ps1
```

It saves the key to `C:\Users\<you>\nearshelf-keys\nearshelf-upload.jks` (outside the project).
Back up that file and its password somewhere safe (password manager + a USB stick).
Every update you ever publish must be signed with this same key.

Copy the key as text to the clipboard:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("$HOME\nearshelf-keys\nearshelf-upload.jks")) | Set-Clipboard
```

## 3. Add the secrets

github.com › your repository › **Settings › Secrets and variables › Actions › New repository secret**:

| Name | Value |
|---|---|
| `KEYSTORE_BASE64` | paste the clipboard from step 2 |
| `KEYSTORE_PASSWORD` | the keystore password |
| `KEY_ALIAS` | `upload` |
| `KEY_PASSWORD` | the key password (the script uses the same one as the keystore) |
| `ADMOB_APP_ID` | your AdMob app ID (with `~`) |
| `ADMOB_NATIVE_UNIT_ID` | your native ad unit ID (with `/`) |

Secrets are encrypted, hidden in logs, and not given to builds from forks.

## 4. Build

**Actions › Build release › Run workflow.** Two options:

- **Show Google's TEST ads**: off for the version you upload to Play; on for a build to try on your own phone.
- **Run the unit tests first**: leave on.

It takes about 10–15 minutes. When the run is green, open it and download
**nearshelf-release-N** under *Artifacts* (a zip with `app-release.aab`, `app-release.apk`
and `mapping.txt`).

- Upload `app-release.aab` to Play Console.
- Upload `mapping.txt` too (Play Console › the release › App bundle explorer › Downloads › ReProguard
  mapping file) so crash reports are readable.
- `app-release.apk` installs directly on a phone.

Pushing a tag such as `v1.0.0` also starts a build (with real ads).

## If a run fails

Open the red step: the error is near the end of its log. A failed test also uploads
**test-reports-N** with the details. The yellow warnings at the top of the run say whether
the build is unsigned or uses test ads.

## Before each Play update

Raise `versionCode` (and `versionName`) in `app/build.gradle.kts`; Play rejects a bundle whose
versionCode it has already seen.
