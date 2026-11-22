# PrintScale AI

An Android app that turns small AI-generated artwork into print-size files for Etsy and print-on-demand products. You import an image, pick a print size and DPI (or a 2×/4×/8× factor), crop or fit it to the product's ratio, and run a real super-resolution model **on the phone**. Then you check the result at 100% against the original and export a PNG/JPEG/WebP with the DPI embedded.

Kotlin, Jetpack Compose and Material 3. By default inference runs on the device with ONNX Runtime and nothing leaves the phone; an optional Cloud GPU mode runs AuraSR v2 in your own Colab or Kaggle notebook (section 8). No account, no analytics.

## 1. Architecture decision

### Engine: on-device first, cloud deliberately not built

| Option | Verdict |
|---|---|
| **A. On-device ONNX Runtime** | **Chosen.** Private, free to run, works offline, no usage caps. Fast enough with a compact model and tiling. |
| B. Cloud inference | Not built. It needs a server, costs money per image, and means uploading artwork people intend to sell. The engine sits behind an `SrModel` interface, so a cloud model can be added as another implementation. |
| C. Hybrid | This is the shape of the code: `SrModel` is the seam. Only the on-device implementation exists today. |

### Model selection

| Model | Size | Mobile CPU cost | Licence | Verdict |
|---|---|---|---|---|
| **Real-ESRGAN General x4v3** (SRVGGNetCompact) | 4.8 MB, 1.2 M params | about 2.4 TFLOP per source megapixel, plain 3×3 convs | BSD-3-Clause | **Chosen.** Built for degraded "real-world" input (JPEG blocking, noise, softness), which is what generator output looks like. Its denoise checkpoint pair gives a real noise-reduction control. |
| Real-ESRGAN x4plus (RRDBNet) | 64 MB, 16.7 M params | about 15× heavier | BSD-3 | Better on some photos, but minutes per megapixel on a phone. Rejected. |
| SwinIR / HAT | 12 to 80 MB | Attention blocks, poor mobile kernels | Apache-2.0 | Quality is high, but too slow and memory-hungry on device. |
| waifu2x | small | fast | MIT | Tuned for anime/line art and weaker on painterly or photographic AI art. |
| GFPGAN / CodeFormer (face) | 350 MB+ | heavy | Apache / **non-commercial (CodeFormer)** | Not shipped (see Limitations). |

The weights are the official release from `xinntao/Real-ESRGAN` (v0.2.5.0). `tools/export_realesrgan_onnx.py` rebuilds the network in PyTorch and exports both checkpoints to ONNX (opset 17, dynamic H/W). It checks the export against PyTorch (max diff 5e-6) and writes `blend_map.json`, the byte ranges of the weights. At run time the app linearly blends the two checkpoints' weights for the chosen noise-reduction strength, exactly as Real-ESRGAN's own `--denoise_strength` does. The blended model was verified against a PyTorch model with blended state dicts (max diff 2e-6).

### Processing pipeline (`engine/`, pure Kotlin, testable on the JVM)

```
original file ─ImageDecoder (EXIF orientation, keeps colour space)─▶ work bitmap (≤ 24 MP)
   ─CropGeometry (fill/fit, 90° turns, straighten, zoom/pan)─▶ prepared canvas (1 px = 1 source px)
   ─AlphaBleed (stop black halos on cut-outs)─▶
   ─AiRowProducer: 256 px tiles + 24 px context, Real-ESRGAN 4×, detail blend, unsharp mask, alpha via bicubic─▶
   ─StreamingResizer: separable Lanczos-3, premultiplied alpha, exact target pixels─▶
   ─PngStreamWriter (adaptive filters, pHYs DPI, iCCP/sRGB) + PreviewSink─▶ master.png + preview
```

* **Never holds the full output in memory.** AI output is produced one strip of tiles at a time and streamed through the resizer into a row-by-row PNG encoder. A 24 × 36 in at 300 DPI file (7200 × 10800, 78 MP) never exists as an Android `Bitmap`.
* **Tile seams:** a 24 px context gives a maximum error of 1/255 against whole-image inference (measured in tests).
* **Honest scaling:** the model is 4× per pass. 2× runs 4× and then downsamples. Anything beyond 4× (8×, or a big print from a small crop) is 4× AI plus Lanczos interpolation, and the UI says so, including the "AI detail DPI" the print actually gets.
* **Planner** checks crop size (≤ 16.7 MP into the model), output size (≤ 20 000 px per side and 250 MP), free heap and free storage *before* starting. It blocks impractical jobs with a reason instead of crashing.
* **Background work:** a WorkManager `CoroutineWorker` running as a `dataSync` foreground service, with a progress notification. Progress is real (source pixels through the model), and the ETA appears only after measured throughput. Cancellation is checked between tiles and also interrupts ONNX Runtime. Partial files are deleted on cancel or failure.
* **Colour:** pixels are copied without conversion (`copyPixelsToBuffer`, not `getPixels`, which converts to sRGB). A non-sRGB source ICC profile is embedded in the PNG; otherwise the PNG is tagged sRGB.

## 2. Features

| Area | What is built |
|---|---|
| Import | Android photo picker, system file picker (PNG/JPEG/WebP and anything Android decodes), "Share to PrintScale" from other apps. Shows size, ratio, format, file size, transparency, EXIF rotation and colour profile. |
| Upscaling | Real-ESRGAN 4× on device; 2×, 4×, 8× factors; exact print-size targets. |
| Print calculator | Pixels = inches × DPI. 300/240/200/150 DPI with guidance, the 14 presets from 5 × 7 to 36 × 48 in, custom sizes in inches or cm. |
| Aspect ratio | Original, 1:1, 2:3, 3:4, 4:5, 5:7, 11:14, 16:9, custom. Fill (crop) or Fit (margin: transparent, white, black, edge colour). Interactive crop with drag, pinch zoom, 90° rotation, ±15° straighten and reset. Everything outside the frame stays visible but dimmed, so nothing is cropped unseen. |
| Enhancement | Low / Balanced / High, plus Advanced: detail recovery, sharpening, noise reduction (real checkpoint blend). |
| Result | Before/after split slider, Original/Enhanced toggle, pinch zoom, and **100% inspection** that decodes a real full-resolution region of the output next to the same area of the original. Shows resolution, file size, print size, method, largest print at each DPI and covered presets. |
| Export | PNG (lossless, DPI, profile), JPEG 90/95/100 (DPI written into JFIF; transparency flattened to white), WebP lossless or lossy. Auto names like `Artwork_4x_7200x10800_300DPI.png`, editable. Save to Pictures/PrintScale, save anywhere via Files, share, open with. Success screen lists resolution, size, print size, DPI, format and location. |
| History | Thumbnail, date, original → final size, factor, export location; reopen, delete, clear all. Storage use shown on Home and in Settings. |
| Themes | Dark by default (a neutral surround for judging colour) and a full light theme. |
| Monetisation seam | `FeatureGate` with everything unlocked. A billing-backed gate can replace it without touching screens. |

## 3. Limitations (what is deliberately not built)

* **"Extend" (AI outpainting):** not implemented. No outpainting model of usable quality runs on a phone CPU at print resolutions. The app offers Fit with a plain or edge-matched margin and says so in the editor.
* **Face enhancement:** not implemented. GFPGAN is about 350 MB and slow on device, CodeFormer's licence forbids commercial use, and both visibly change faces in artwork. That conflicts with "faithful enhancement". No toggle is shown rather than a toggle that does nothing.
* **8× and large prints** are 4× AI plus Lanczos interpolation, not a second AI pass. A second pass of this model over-sharpens and multiplies the time by 16.
* **JPEG/WebP export** needs the whole image as one bitmap. Very large outputs on low-memory phones can only be exported as PNG; the export sheet explains this.
* **WebP** is limited to 16 383 px per side by the format, and it carries no DPI tag.
* **Batch, cloud processing, mockups, bleed guides:** future work. The `SrModel`, `RowSink` and `FeatureGate` seams are where they plug in.

## 4. Build

Requirements: JDK 17+ and the Android SDK (platform 36, build-tools 36).

```bash
cd printscale-ai
echo "sdk.dir=/path/to/Android/sdk" > local.properties   # Android Studio writes this for you
./gradlew :app:assembleRelease      # app/build/outputs/apk/release/app-arm64-v8a-release.apk (~27 MB)
./gradlew :app:assembleDebug        # unminified debug build
```

Release APKs are split per ABI (arm64-v8a for phones, x86_64 for the emulator). The release build is signed with the debug key so it installs for testing. Replace `signingConfig` with your own keystore before publishing.

To regenerate the ONNX files from the original weights:

```bash
pip install torch onnx onnxruntime
python tools/export_realesrgan_onnx.py <dir with realesr-general-x4v3.pth and realesr-general-wdn-x4v3.pth> app/src/main/assets/models
```

## 5. Tests

```bash
./gradlew :engine:test :app:testDebugUnitTest
```

* **Engine (17 tests, JVM, real model through ONNX Runtime desktop):** print maths and presets, planner limits, crop geometry including straighten and turns, and streaming Lanczos with alpha. Also PNG round-trip with DPI and ICC, JPEG DPI patch, file naming and alpha bleed. Then the tiled AI output against whole-image inference (seams ≤ 1/255), the full pipeline to a print size, transparent artwork, cancellation and the weight blend. It writes a Lanczos-vs-AI comparison image to `engine/build/test-output/`.
* **Android (18 tests, Robolectric with native graphics):** import of transparent PNG and opaque PNG, EXIF-rotated JPEG, a non-image rejected. Pixel-exact crops and the colour-preserving pixel round trip. The real `UpscaleWorker` end to end (Lanczos path), cleanup after failure, JPEG/PNG/WebP export with DPI and white flattening. Then click-through UI tests for every screen in both themes, with screenshots in `app/build/screenshots/`.

**Not tested here:** the app has not run on a physical phone or emulator. This build environment has no KVM, so the ONNX Runtime **Android** native library and on-device speed are unverified. The same model and Java API were exercised on the JVM. The first real-device run should check processing time on a mid-range phone and memory headroom at 4096 × 4096 crops.

## 6. Design notes

* **Palette:** charcoal and paper neutrals with one vermilion accent taken from printers' proof and registration marks. The accent appears only on the primary action and the active state.
* **Type:** Instrument Serif for titles and the big resolution numbers (a gallery and print-catalogue voice); Manrope for everything else (open, legible figures, with tabular digits for pixel sizes). Both are OFL and bundled.
* **Motif:** printer's crop marks frame the artwork in the editor, processing and result screens, and form the logo.
* **Shape:** 10 dp radius on buttons and cards, 8 dp on chips. Nothing is pill-shaped.

## 7. High-quality upscaling on Colab or Kaggle (AuraSR v2)

For your own listings, two notebooks run **AuraSR v2** (`fal/AuraSR-v2`, a 600 M-parameter GigaGAN upscaler trained for AI-generated images) on a free cloud GPU. It's a much larger model than the one in the app, and it gives crisper edges and cleaner JPEG artefacts.

| Notebook | How to open |
|---|---|
| `notebooks/PrintScale_AuraSR_Colab.ipynb` | colab.research.google.com > File > Upload notebook (or Open notebook > GitHub). Runtime > Change runtime type > **T4 GPU**. |
| `notebooks/PrintScale_AuraSR_Kaggle.ipynb` | kaggle.com > Create > New Notebook > File > Import Notebook. Settings: Accelerator **GPU T4 x2**, **Internet on**. Add images as a dataset. |

Run the cells in order. You get a framing preview before anything is processed, then batch 4× upscaling and an exact resize to print pixels (presets, custom inches/cm, 150 to 300 DPI, fill/fit/keep). Files are PNG or JPEG with the DPI and colour profile embedded and transparency kept. You also get 100% comparison crops against Lanczos, a summary table with the *AI detail DPI*, and a zip with `CREDITS.txt`.

* **Licence:** the AuraSR v2 repo's `LICENSE.md` is **CC BY-SA 4.0**, even though its card metadata says Apache-2.0. Both allow commercial use; credit is required, and the credit text is written into the zip. This is a reading of the licence, not legal advice.
* **Not a backend for the app:** Colab and Kaggle free tiers are for interactive notebook use, not for serving an app. A cloud mode in the app would need a paid GPU endpoint.
* **Behaviour:** it is a GAN, so it sharpens edges strongly but can add faint texture to smooth gradients and slightly roughen perfectly clean edges. Check the comparison crops for flat or minimal designs.
* **Tested here:** both notebooks were executed top to bottom on a CPU with the real AuraSR v2 weights, including a full 7200 × 10800 output, transparency and JPEG with DPI and ICC. Processing large images in 64 px-aligned blocks matches whole-image output (99.9% of pixels within 5/255). They have not yet been run on an actual Colab or Kaggle GPU, so GPU speed is unmeasured.
* **GPU:** the notebooks always run AuraSR on the GPU when one is attached. Colab notebooks open with a T4 preselected; on Kaggle, choose the accelerator once in Settings. They send 16 to 64 tiles per GPU call, sized from GPU memory (AuraSR's own default is 8, which leaves a T4 mostly idle). If the GPU runs out of memory, they retry with smaller batches automatically.
* For using AuraSR from inside the app instead of in the notebook, see section 8. The app's notebook links point to the branch in `NOTEBOOK_REF` (`app/build.gradle.kts`); change it to `main` after merging.
* `notebooks/printscale_aurasr.py` is the shared code. After editing it, run `python tools/build_notebooks.py` to rebuild both notebooks.

## 8. Cloud GPU server: AuraSR inside the app

The app can use **your own Colab or Kaggle notebook as its AI engine**. You work entirely in the app; only the AI 4× step runs on the notebook's GPU.

1. In the app: Home > **Connect a cloud GPU** > *Open in Colab* (or Kaggle). This opens `notebooks/PrintScale_Server_Colab.ipynb` (or `_Kaggle`).
2. Choose a GPU (Colab preselects a T4; on Kaggle choose GPU T4 x2 and turn Internet on) and run all cells.
3. The last cell prints a link like `https://name.trycloudflare.com/?key=...` and a QR code. Scan the QR code with the phone camera and tap **Open in the PrintScale app**, or paste the link into the app.
4. In the editor choose **AI engine > Cloud GPU** and upscale as usual.

What happens per job: the app uploads its prepared crop as PNG and polls progress, which shows live in the app and the notification. It then downloads the 4× PNG and streams it through the same Lanczos print resize and PNG writer as the on-device engine. DPI, colour profile, transparency, history, comparison and export all work the same.

| Piece | Where |
|---|---|
| Server (stdlib HTTP, single GPU queue, private key, cancel, deletes files after download or 1 h) | `notebooks/printscale_server.py` |
| Tunnel | Cloudflare quick tunnel (`trycloudflare.com`), no account needed. Jobs are asynchronous because these tunnels drop requests that wait longer than about 100 s. |
| App client, streaming PNG reader | `engine/.../CloudClient.kt`, `PngStreamReader.kt` |
| App flow | `UpscaleWorker.runCloud`, the Cloud GPU sheet, the editor's engine switch, the `printscale://connect` deep link |

Honest limits:
* **Privacy:** with Cloud GPU the cropped artwork leaves the phone and goes to your notebook on Google's or Kaggle's servers. The app says so wherever the option appears. The on-device engine stays fully offline. The app now holds the INTERNET permission for this, and uses it only for the server you connect.
* **Free-tier rules:** Colab's free tier may disconnect notebooks used as servers, and Kaggle sessions end after 12 hours. When that happens the app reports that the server can't be reached; restart the notebook and connect with the new link (it changes every start).
* **Data:** about 1 MB up and 20 to 40 MB down for a typical 1024 × 1536 crop. The editor shows an estimate.
* **Tested here:** the server ran locally with the real AuraSR v2 weights on CPU. The engine client completed real round trips, including transparency and cancellation. The actual Android worker completed a real cloud job against it (29 s on CPU). The Cloudflare tunnel step could not be run in this sandbox, which does not allow opening public tunnels, so it is untested.

To run the cloud integration tests yourself, start the server notebook (or `printscale_server.py`) and set `PRINTSCALE_TEST_SERVER` to its link before `./gradlew :engine:test :app:testDebugUnitTest`.

## 9. Project layout

```
engine/                 pure Kotlin: planner, crop geometry, tiling, Lanczos, PNG writer, ONNX model, formats
app/src/main/java/com/printscale/ai/
  data/                 imports, history (JSON), settings, job spec
  imaging/              decode/orientation, crop rendering, pixel transfer
  processing/           WorkManager worker, controller, model loading
  export/               PNG/JPEG/WebP export, MediaStore, Files, share
  ui/                   home, editor (crop canvas), processing, result (compare viewer), history, settings
app/src/main/assets/models/   Real-ESRGAN ONNX checkpoints, blend map, licence
tools/export_realesrgan_onnx.py
notebooks/                    AuraSR v2 batch notebooks, server notebooks, shared code
tools/build_notebooks.py
```

Licences: Real-ESRGAN weights are BSD-3-Clause (© Xintao Wang); Manrope and Instrument Serif are SIL OFL 1.1. All three are viewable in Settings.
