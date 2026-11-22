"""Builds the Colab and Kaggle notebooks from notebooks/printscale_aurasr.py.

Run after editing the module:  python tools/build_notebooks.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB_DIR = os.path.join(ROOT, "notebooks")
CORE = open(os.path.join(NB_DIR, "printscale_aurasr.py")).read()
SERVER = open(os.path.join(NB_DIR, "printscale_server.py")).read()


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text, form=False):
    meta = {"cellView": "form"} if form else {}
    return {"cell_type": "code", "metadata": meta, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


def notebook(cells, colab):
    for i, c in enumerate(cells):
        c["id"] = f"cell-{i:02d}"
    meta = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"}}
    if colab:
        meta["accelerator"] = "GPU"
        meta["colab"] = {"provenance": [], "gpuType": "T4"}
    return {"cells": cells, "metadata": meta, "nbformat": 4, "nbformat_minor": 5}


INTRO = """
# PrintScale AuraSR: print-size upscaling for Etsy artwork

Upscales a folder of AI-generated artwork with **AuraSR v2** (a GigaGAN-based 4× upscaler trained for AI-generated images), then sizes each file for a real print and embeds the DPI.

**What you get per image:** a PNG or JPEG at exact print pixels (inches × DPI), the DPI tag and original colour profile kept, transparency kept in PNG. You also get a 100% crop comparison against plain Lanczos enlargement, and one zip of everything.

**Honest limits:**
* AuraSR enlarges **4× per pass**. Bigger prints (for example 24 × 36 in from a 1024 px image) are 4× AI plus Lanczos interpolation for the rest. The summary table reports the *AI detail DPI* so you can see how much detail is real.
* It is a GAN: it sharpens edges and removes JPEG blur, but it can add faint texture to smooth gradients. Check the comparison images before you list.
* Nothing leaves this notebook's machine except what you download. The model is downloaded from Hugging Face and runs locally here. Your images are not sent to fal.ai or Hugging Face.

**Licence:** AuraSR v2 weights are CC BY-SA 4.0. Commercial use is allowed with credit; `CREDITS.txt` in the zip contains the attribution.
"""

GPU_CHECK = """
#@title 1. Check the GPU
import os, subprocess, torch
if torch.cuda.is_available():
    props = torch.cuda.get_device_properties(0)
    print(f"GPU: {props.name}, {props.total_memory / 2**30:.0f} GB. AuraSR will run on it.")
elif os.environ.get("PRINTSCALE_ALLOW_CPU") == "1":
    print("No GPU: running on CPU (test mode, very slow).")
else:
    raise RuntimeError(__GPU_HELP__)
"""

INSTALL = """
#@title 2. Install AuraSR (about 1 minute)
# torch and torchvision are already in the image; this adds the AuraSR package only.
%pip install -q aura-sr==0.0.4 einops safetensors
"""

CORE_CELL = "%%writefile printscale_aurasr.py\n" + CORE  # cell magic must be the first line

IMPORT_CELL = """
import importlib, sys
sys.path.insert(0, os.getcwd())
import printscale_aurasr as ps
importlib.reload(ps)
print("ready")
"""

SETTINGS_COLAB = """
#@title 4. Settings
#@markdown **Output size**
MODE = "print"  #@param ["print", "scale"]
#@markdown `auto` picks the largest common print (up to 24×36 in) that matches each image's ratio.
PRINT_SIZE = "auto"  #@param ["auto", "5x7", "8x10", "8x12", "10x12", "11x14", "12x16", "12x18", "16x20", "18x24", "20x24", "20x30", "24x36", "30x40", "36x48", "custom"]
CUSTOM_SIZE = "16x20"  #@param {type:"string"}
UNIT = "in"  #@param ["in", "cm"]
DPI = 300  #@param [300, 240, 200, 150] {type:"raw"}
SCALE = 4  #@param [2, 4, 8] {type:"raw"}
#@markdown **Framing** (fill crops to the print ratio, fit adds a margin, keep never crops)
FRAMING = "fill"  #@param ["fill", "fit", "keep"]
CROP_ANCHOR = "center"  #@param ["center", "top", "bottom", "left", "right"]
MARGIN = "white"  #@param ["white", "black", "transparent", "edge"]
#@markdown **File**
OUTPUT_FORMAT = "png"  #@param ["png", "jpg"]
JPEG_QUALITY = 95  #@param [90, 95, 100] {type:"raw"}
COMPARISON_IMAGES = True  #@param {type:"boolean"}

settings = ps.Settings(
    mode=MODE, print_size=CUSTOM_SIZE if PRINT_SIZE == "custom" else PRINT_SIZE, unit=UNIT, dpi=int(DPI),
    scale=float(SCALE), framing=FRAMING, crop_anchor=CROP_ANCHOR, margin=MARGIN,
    output_format=OUTPUT_FORMAT, jpeg_quality=int(JPEG_QUALITY), comparison=COMPARISON_IMAGES,
)
print(settings)
"""

SETTINGS_KAGGLE = """
# 4. Settings: edit the values, then run the cell.
MODE = "print"          # "print" (inches at a DPI) or "scale" (factor)
PRINT_SIZE = "auto"     # "auto", a preset like "8x10", "16x20", "24x36", or a custom "WxH"
UNIT = "in"             # "in" or "cm" (for custom sizes)
DPI = 300               # 300, 240, 200 or 150
SCALE = 4               # used when MODE = "scale": 2, 4 or 8
FRAMING = "fill"        # "fill" crops to the print ratio, "fit" adds a margin, "keep" never crops
CROP_ANCHOR = "center"  # "center", "top", "bottom", "left", "right"
MARGIN = "white"        # for "fit": "white", "black", "transparent", "edge"
OUTPUT_FORMAT = "png"   # "png" or "jpg"
JPEG_QUALITY = 95       # 90, 95 or 100
COMPARISON_IMAGES = True

settings = ps.Settings(
    mode=MODE, print_size=PRINT_SIZE, unit=UNIT, dpi=int(DPI), scale=float(SCALE), framing=FRAMING,
    crop_anchor=CROP_ANCHOR, margin=MARGIN, output_format=OUTPUT_FORMAT, jpeg_quality=int(JPEG_QUALITY),
    comparison=COMPARISON_IMAGES,
)
print(settings)
"""

INPUT_COLAB = """
#@title 5. Choose your images
#@markdown `upload` opens a file picker. `drive` reads a Google Drive folder (path below, relative to *My Drive*).
SOURCE = "upload"  #@param ["upload", "drive"]
DRIVE_FOLDER = "Etsy/to_upscale"  #@param {type:"string"}
SAVE_COPY_TO_DRIVE = False  #@param {type:"boolean"}
DRIVE_OUTPUT_FOLDER = "Etsy/upscaled"  #@param {type:"string"}

import shutil
INPUT_DIR = os.environ.get("PRINTSCALE_INPUT") or "/content/printscale_input"
OUTPUT_DIR = os.environ.get("PRINTSCALE_OUTPUT") or "/content/printscale_output"
if not os.environ.get("PRINTSCALE_INPUT"):
    if SOURCE == "drive" or SAVE_COPY_TO_DRIVE:
        from google.colab import drive
        drive.mount("/content/drive")
    if SOURCE == "drive":
        INPUT_DIR = os.path.join("/content/drive/MyDrive", DRIVE_FOLDER)
    else:
        from google.colab import files
        shutil.rmtree(INPUT_DIR, ignore_errors=True)
        os.makedirs(INPUT_DIR)
        for name, data in files.upload().items():
            with open(os.path.join(INPUT_DIR, os.path.basename(name)), "wb") as f:
                f.write(data)
images = ps.find_images(INPUT_DIR)
print(f"{len(images)} image(s) in {INPUT_DIR}")
if not images:
    raise RuntimeError("No PNG, JPEG, WebP or TIFF images found. Upload some or check the Drive folder path.")
"""

INPUT_KAGGLE = """
# 5. Find your images
# Add them first: right panel > Input > Upload > New Dataset (drag in your images), then run this cell.
INPUT_DIR = os.environ.get("PRINTSCALE_INPUT") or "/kaggle/input"
OUTPUT_DIR = os.environ.get("PRINTSCALE_OUTPUT") or "/kaggle/working/printscale_output"
images = ps.find_images(INPUT_DIR)
print(f"{len(images)} image(s) under {INPUT_DIR}")
for p in images[:20]:
    print("  ", p)
if not images:
    raise RuntimeError("No images found. Add a dataset with your artwork (Input > Upload > New Dataset).")
"""

PREVIEW = """
#@title 6. Preview the framing (nothing is processed yet)
# The orange frame is what will be kept. Change FRAMING or CROP_ANCHOR in step 4 if a crop is wrong.
from IPython.display import display
sheet, plans = ps.preview_plans(images, settings)
display(sheet)
for pl in plans:
    detail = f", AI detail about {round(pl.ai_detail_dpi())} DPI" if pl.uses_ai and pl.print_w_in else ""
    print(f"{pl.name}: {pl.src_w}x{pl.src_h} -> {pl.target_w}x{pl.target_h} px ({pl.needed_scale:.2f}x){detail}. {' '.join(pl.notes)}")
"""

LOAD_MODEL = """
#@title 7. Load AuraSR v2 (downloads 2.5 GB the first time)
model, device = ps.load_aurasr()
print("AuraSR v2 loaded on", device.upper(), f"| {ps.default_batch()} tiles per GPU batch" if device == "cuda" else "")
"""

RUN = """
#@title 8. Upscale everything
import gc, shutil, time, pandas as pd
from IPython.display import display
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
os.makedirs(OUTPUT_DIR)
results, t_all = [], time.time()
for i, path in enumerate(images, 1):
    print(f"[{i}/{len(images)}] {os.path.basename(path)}")
    block, batch = settings.block, ps.default_batch()
    for attempt in range(4):
        try:
            settings.block, settings.batch = block, batch
            r = ps.process(model, path, OUTPUT_DIR, settings, log=print)
            results.append(r)
            print(f"   saved {r['output']} ({r['size_mb']} MB, {r['seconds']} s, {r['method']})")
            break
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache(); gc.collect()
            if batch > 4:
                batch //= 2
            else:
                block //= 2
            print(f"   GPU memory full; retrying with batch {batch}, blocks of {block} px")
        except Exception as e:
            print(f"   skipped: {type(e).__name__}: {e}")
            results.append({"file": os.path.basename(path), "output": "FAILED", "notes": str(e)})
            break
    settings.block, settings.batch = 1024, 0
    torch.cuda.empty_cache(); gc.collect()
with open(os.path.join(OUTPUT_DIR, "CREDITS.txt"), "w") as f:
    f.write(ps.CREDIT + "\\n")
print(f"Done in {time.time() - t_all:.0f} s")
summary = pd.DataFrame(results).drop(columns=["compare"], errors="ignore")
summary.to_csv(os.path.join(OUTPUT_DIR, "summary.csv"), index=False)
display(summary)
"""

COMPARE = """
#@title 9. Check the results at 100%
# Left: the original enlarged with Lanczos. Right: AuraSR. Look at edges, text and smooth gradients.
from PIL import Image
for r in results:
    if r.get("compare"):
        print(r["output"])
        display(Image.open(r["compare"]))
"""

DOWNLOAD_COLAB = """
#@title 10. Download
zip_path = ps.zip_folder(OUTPUT_DIR, os.path.join(os.path.dirname(OUTPUT_DIR), "printscale_upscaled.zip"))
print(f"{zip_path}: {os.path.getsize(zip_path) / 2**20:.0f} MB")
if SAVE_COPY_TO_DRIVE:
    dst = os.path.join("/content/drive/MyDrive", DRIVE_OUTPUT_FOLDER)
    shutil.copytree(OUTPUT_DIR, dst, dirs_exist_ok=True)
    print("Copied to Google Drive:", dst)
if not os.environ.get("PRINTSCALE_INPUT"):
    from google.colab import files
    files.download(zip_path)  # large zips can take a while to start; Drive is faster for big batches
"""

DOWNLOAD_KAGGLE = """
# 10. Download
zip_path = ps.zip_folder(OUTPUT_DIR, os.path.join(os.path.dirname(OUTPUT_DIR), "printscale_upscaled.zip"))
print(f"{zip_path}: {os.path.getsize(zip_path) / 2**20:.0f} MB")
print("Download it from the right panel: Output > printscale_upscaled.zip (refresh the panel if it is not listed).")
print("Files in /kaggle/working disappear when the session ends unless you use Save Version.")
"""

COLAB_GPU = '"No GPU. In Colab: Runtime > Change runtime type > T4 GPU, then run all cells again."'
KAGGLE_GPU = '"No GPU. In Kaggle: Settings (right panel) > Accelerator > GPU T4 x2. Also turn Internet on."'

colab_cells = [
    md(INTRO + "\n**Steps:** Runtime > Change runtime type > **T4 GPU**, then run the cells in order. Settings are in step 4.\n"),
    code(GPU_CHECK.replace("__GPU_HELP__", COLAB_GPU), form=True),
    code(INSTALL, form=True),
    md("**3. Upscaling code.** No changes needed: run the next two cells."),
    code(CORE_CELL),
    code(IMPORT_CELL),
    code(SETTINGS_COLAB, form=True),
    code(INPUT_COLAB, form=True),
    code(PREVIEW, form=True),
    code(LOAD_MODEL, form=True),
    code(RUN, form=True),
    code(COMPARE, form=True),
    code(DOWNLOAD_COLAB, form=True),
]

kaggle_cells = [
    md(INTRO + """
**Before you start (right panel):** Settings > Accelerator > **GPU T4 x2** and Settings > **Internet on** (needed to install AuraSR and download the model). If you pick P100 and see a "CUDA capability" warning, switch to T4.

Then add your images: Input > Upload > New Dataset. Run the cells in order; settings are in step 4.
"""),
    code(GPU_CHECK.replace("__GPU_HELP__", KAGGLE_GPU).replace("#@title ", "# ")),
    code(INSTALL.replace("#@title ", "# ")),
    md("**3. Upscaling code.** No changes needed: run the next two cells."),
    code(CORE_CELL),
    code(IMPORT_CELL),
    code(SETTINGS_KAGGLE),
    code(INPUT_KAGGLE),
    code(PREVIEW.replace("#@title ", "# ")),
    code(LOAD_MODEL.replace("#@title ", "# ")),
    code(RUN.replace("#@title ", "# ")),
    code(COMPARE.replace("#@title ", "# ")),
    code(DOWNLOAD_KAGGLE),
]

# ----------------------------------------------------------------------------- server notebooks

SERVER_INTRO = """
# PrintScale cloud GPU server (AuraSR v2)

Turns this notebook into a private upscaling server for the **PrintScale Android app**. The app sends its prepared artwork here, AuraSR v2 upscales it 4× on this GPU, and the app downloads the result. Print sizing, DPI, colour profile, history and export all happen in the app.

**How to connect:** run every cell. The last cell shows a link and a QR code. Scan the QR code with your phone's camera and tap **Open in the PrintScale app**, or copy the link into the app (Home > Cloud GPU > paste link).

* The link is new each time the notebook starts and contains a private key; anyone with the full link can use your GPU, so do not share it.
* Keep this tab open while you work. The server stops when the notebook stops or the session ends.
* Uploads are kept only while a job runs and are deleted after download (or after one hour).
* **Free-tier rules:** Colab's free tier may disconnect notebooks that serve outside traffic; Kaggle sessions stop after 12 hours. If the app says it cannot reach the server, restart this notebook and connect with the new link.
* AuraSR v2 weights are CC BY-SA 4.0 (commercial use allowed with credit: "Upscaled with AuraSR v2 by fal.ai").
"""

SERVER_INSTALL = """
#@title 2. Install AuraSR and the QR code helper (about 1 minute)
%pip install -q aura-sr==0.0.4 einops safetensors qrcode
"""

SERVER_START = """
#@title 5. Start the server and show the link (keep this running)
import time
import qrcode
from IPython.display import display, clear_output
import printscale_server as srv
importlib.reload(srv)

model, device = ps.load_aurasr()
server = srv.PrintScaleServer(model, device, port=int(os.environ.get("PRINTSCALE_PORT", 8765))).start()
if os.environ.get("PRINTSCALE_NO_TUNNEL") == "1":
    print("Test mode: no tunnel, local link only.")
else:
    print("Opening a Cloudflare tunnel...")
    server.start_tunnel()
connect_page = server.link.replace("/?key=", "/connect?key=")

def show():
    clear_output(wait=True)
    print("PrintScale cloud GPU is running on", (server.gpu or device).upper())
    print()
    print("Paste this link in the app (Home > Cloud GPU):")
    print(server.link)
    print()
    print("Or scan with your phone's camera, then tap 'Open in the PrintScale app':")
    display(qrcode.make(connect_page).resize((280, 280)))
    print(server.status_line())

show()
if os.environ.get("PRINTSCALE_NO_TUNNEL") != "1":
    try:
        while True:          # keeps the cell busy so the notebook stays alive; stop it to shut the server down
            time.sleep(30)
            show()
    except KeyboardInterrupt:
        print("Server stopped.")
"""

SERVER_CELL = "%%writefile printscale_server.py\n" + SERVER

server_colab = [
    md(SERVER_INTRO + "\n**Steps:** Runtime > Change runtime type > **T4 GPU**, then Runtime > Run all.\n"),
    code(GPU_CHECK.replace("__GPU_HELP__", COLAB_GPU), form=True),
    code(SERVER_INSTALL, form=True),
    md("**3. Server code.** No changes needed: run the next cells."),
    code(CORE_CELL),
    code(SERVER_CELL),
    code(IMPORT_CELL),
    code(SERVER_START, form=True),
]
server_kaggle = [
    md(SERVER_INTRO + "\n**Before you start (right panel):** Settings > Accelerator > **GPU T4 x2** and Settings > **Internet on**. Then Run All.\n"),
    code(GPU_CHECK.replace("__GPU_HELP__", KAGGLE_GPU).replace("#@title ", "# ")),
    code(SERVER_INSTALL.replace("#@title ", "# ")),
    md("**3. Server code.** No changes needed: run the next cells."),
    code(CORE_CELL),
    code(SERVER_CELL),
    code(IMPORT_CELL),
    code(SERVER_START.replace("#@title ", "# ")),
]

for name, cells, colab in (("PrintScale_AuraSR_Colab.ipynb", colab_cells, True),
                           ("PrintScale_AuraSR_Kaggle.ipynb", kaggle_cells, False),
                           ("PrintScale_Server_Colab.ipynb", server_colab, True),
                           ("PrintScale_Server_Kaggle.ipynb", server_kaggle, False)):
    with open(os.path.join(NB_DIR, name), "w") as f:
        json.dump(notebook(cells, colab), f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote", name)
