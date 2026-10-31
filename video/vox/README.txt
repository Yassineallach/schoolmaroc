RED RISING - EXPLAINER VIDEO PROJECT
====================================

HOW TO RENDER (Windows)
1. Unzip this folder anywhere (for example on your Desktop).
   Make sure the folder path has no special characters like ' or %.
2. Double-click RENDER.bat
3. Wait. The first run downloads Python and ffmpeg if you don't have them
   (about 100 MB), then renders the eight acts and joins them.
4. The finished film is:  out\Red_Rising_Full.mp4   (1080p, 30 fps, ~7:38)

Each act is also saved on its own in the "out" folder.

OPTIONS (run from PowerShell inside this folder)
  powershell -ExecutionPolicy Bypass -File .\render.ps1 -Crf 16 -Preset medium   (faster)
  powershell -ExecutionPolicy Bypass -File .\render.ps1 -Acts 3,4                (only some acts)

WHAT'S INSIDE
  act1_vox.py ... act8_vox.py   one script per act (scenes, timing on spoken words)
  vox.py                        shared engine: paper style, cut-outs, motion, audio mastering
  data\                         images, cut-outs, fonts, narration clips, word timings
  render.ps1 / RENDER.bat       the full-quality render

If something fails, the error log for each act is in out\actN.err.log
