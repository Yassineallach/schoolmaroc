@echo off
cd /d "%~dp0"
echo Rendering the Red Rising video at full quality. This can take 10-40 minutes.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0render.ps1" %*
echo.
echo Finished. Your video is in the "out" folder: out\Red_Rising_Full.mp4
pause
