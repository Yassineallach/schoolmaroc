# PrintScale AuraSR: batch upscaling of artwork for print-on-demand.
# Model: fal/AuraSR-v2 (GigaGAN-based 4x upscaler for AI-generated images), licence CC BY-SA 4.0.
# This file is embedded verbatim in the Colab and Kaggle notebooks.

import io
import json
import math
import os
import time
import zipfile
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageDraw, ImageOps

Image.MAX_IMAGE_PIXELS = None  # print files are large on purpose

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

# Short side x long side in inches.
PRESETS = {
    "5x7": (5, 7), "8x10": (8, 10), "8x12": (8, 12), "10x12": (10, 12),
    "11x14": (11, 14), "12x16": (12, 16), "12x18": (12, 18), "16x20": (16, 20),
    "18x24": (18, 24), "20x24": (20, 24), "20x30": (20, 30), "24x36": (24, 36),
    "30x40": (30, 40), "36x48": (36, 48),
    # ISO 216 paper, from exact millimetres (A4 at 300 DPI = 2480 x 3508 px)
    "A5": (148 / 25.4, 210 / 25.4), "A4": (210 / 25.4, 297 / 25.4), "A3": (297 / 25.4, 420 / 25.4),
    "A2": (420 / 25.4, 594 / 25.4), "A1": (594 / 25.4, 841 / 25.4),
}
ETSY_FILE_LIMIT = 20_000_000  # bytes; fits whether Etsy's "20 MB" means 10^6 or 2^20


def describe_size(w_in, h_in):
    """'A4' for ISO sizes in either orientation, otherwise '8x10 in'."""
    for k, (a, b) in PRESETS.items():
        if k.startswith("A") and abs(min(w_in, h_in) - a) < 0.01 and abs(max(w_in, h_in) - b) < 0.01:
            return k
    return f"{round(w_in, 2):g}x{round(h_in, 2):g} in"


# ----------------------------------------------------------------------------- model

def load_aurasr(model_id="fal/AuraSR-v2"):
    """Loads AuraSR on the GPU if there is one, otherwise on the CPU (very slow)."""
    import torch
    from aura_sr import AuraSR
    from huggingface_hub import snapshot_download
    from safetensors.torch import load_file

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        torch.backends.cudnn.benchmark = True  # tiles are all 64 px, so cuDNN can pick the fastest kernels once
    path = snapshot_download(model_id, allow_patterns=["config.json", "model.safetensors"])
    with open(os.path.join(path, "config.json")) as f:
        config = json.load(f)
    model = AuraSR(config, device=device)  # the package's from_pretrained always assumes CUDA
    model.upsampler.load_state_dict(load_file(os.path.join(path, "model.safetensors")), strict=True)
    model.upsampler.eval()
    return model, device


def _ai_block(model, rgb: Image.Image, seed: int, batch: int = 8) -> np.ndarray:
    """4x one block. Pads to whole 64 px tiles with edge pixels so small or odd sizes work."""
    import torch
    tile = model.input_image_size
    w, h = rgb.size
    pw = math.ceil(w / tile) * tile
    ph = math.ceil(h / tile) * tile
    arr = np.asarray(rgb)
    if (pw, ph) != (w, h):
        arr = np.pad(arr, ((0, ph - h), (0, pw - w), (0, 0)), mode="edge")
    torch.manual_seed(seed)  # the GAN takes a noise vector; fixed seed = repeatable output
    out = model.upscale_4x_overlapped(Image.fromarray(arr), max_batch_size=batch)
    return np.asarray(out, dtype=np.float32)[: h * 4, : w * 4]


def default_batch():
    """Tiles per GPU call. AuraSR's own default of 8 leaves a T4 mostly idle."""
    import torch
    if not torch.cuda.is_available():
        return 8
    gb = torch.cuda.get_device_properties(0).total_memory / 2**30
    return 64 if gb >= 20 else 32 if gb >= 12 else 16


def _blocks(w, h, block, overlap):
    if w <= block and h <= block:
        return [(0, 0, w, h)]
    step = block - overlap
    xs = list(range(0, max(w - overlap, 1), step))
    ys = list(range(0, max(h - overlap, 1), step))
    return [(x0, y0, min(x0 + block, w), min(y0 + block, h)) for y0 in ys for x0 in xs]


def _batches_for(bw, bh, tile, batch):
    """GPU calls AuraSR makes for one block: a normal pass plus a half-tile-offset pass."""
    pw, ph = math.ceil(bw / tile) * tile, math.ceil(bh / tile) * tile
    t1 = (pw // tile) * (ph // tile)
    t2 = ((pw + tile) // tile) * ((ph + tile) // tile)
    return math.ceil(t1 / batch) + math.ceil(t2 / batch)


def ai_upscale_4x(model, rgb: Image.Image, block=1024, overlap=64, seed=0, progress=None, batch=8,
                  cancelled=None) -> Image.Image:
    """
    4x a whole image in overlapping blocks and feather them together, so memory stays bounded
    for any input size (AuraSR keeps its whole output as float tensors). progress(done, total)
    is called after every GPU batch; cancelled() is checked at the same points.
    """
    w, h = rgb.size
    tile = model.input_image_size
    # Keep every block on AuraSR's own 64 px tile grid so blocks match whole-image inference.
    overlap = max(tile, round(overlap / tile) * tile)
    block = max(overlap + tile, round(block / tile) * tile)
    blocks = _blocks(w, h, block, overlap)
    total = sum(_batches_for(x1 - x0, y1 - y0, tile, batch) for x0, y0, x1, y1 in blocks)
    count = [0]

    def on_batch(*_):
        count[0] += 1
        if cancelled is not None and cancelled():
            raise InterruptedError("cancelled")
        if progress:
            progress(min(count[0], total), total)

    hook = model.upsampler.register_forward_hook(on_batch)
    try:
        if len(blocks) == 1:
            out = _ai_block(model, rgb, seed, batch)
            return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))

        acc = np.zeros((h * 4, w * 4, 3), np.float32)
        wsum = np.zeros((h * 4, w * 4, 1), np.float32)
        ramp = overlap * 4
        for x0, y0, x1, y1 in blocks:
            part = _ai_block(model, rgb.crop((x0, y0, x1, y1)), seed, batch)
            bh, bw = part.shape[:2]

            def axis(n, at_start, at_end):
                # linear cross-fade over the overlap; edges of the image keep full weight
                v = np.ones(n, np.float32)
                r = min(ramp, n // 2)
                if r > 0:
                    up = (np.arange(r, dtype=np.float32) + 0.5) / r
                    if not at_start:
                        v[:r] = up
                    if not at_end:
                        v[n - r:] = np.minimum(v[n - r:], up[::-1])
                return v

            wt = (axis(bh, y0 == 0, y1 == h)[:, None] * axis(bw, x0 == 0, x1 == w)[None, :])[..., None]
            acc[y0 * 4: y0 * 4 + bh, x0 * 4: x0 * 4 + bw] += part * wt
            wsum[y0 * 4: y0 * 4 + bh, x0 * 4: x0 * 4 + bw] += wt
        out = acc / np.maximum(wsum, 1e-6)
        return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))
    finally:
        hook.remove()


# ----------------------------------------------------------------------------- framing

@dataclass
class Settings:
    mode: str = "print"            # "print" (inches at a DPI) or "scale" (factor)
    print_size: str = "auto"       # a PRESETS key, "auto" (largest preset matching the image ratio), or "WxH" like "16x20"
    unit: str = "in"               # "in" or "cm" for a custom WxH
    dpi: int = 300
    scale: float = 4.0             # used in "scale" mode
    framing: str = "fill"          # "fill" (crop to the print ratio), "fit" (add margin), "keep" (no crop, largest print that fits)
    crop_anchor: str = "center"    # "center", "top", "bottom", "left", "right"
    margin: str = "white"          # "fit" margin: "white", "black", "transparent", "edge"
    output_format: str = "png"     # "png", "jpg", or "etsy" (JPEG at the best quality under Etsy's 20 MB per-file limit)
    jpeg_quality: int = 95
    seed: int = 0
    block: int = 1024              # source pixels per AI block; lower it if the GPU runs out of memory
    batch: int = 0                 # 64 px tiles per GPU call; 0 = pick from GPU memory
    comparison: bool = True


@dataclass
class Plan:
    name: str
    src_w: int
    src_h: int
    crop_box: tuple
    canvas_w: int
    canvas_h: int
    target_w: int
    target_h: int
    print_w_in: float = None
    print_h_in: float = None
    notes: list = field(default_factory=list)

    @property
    def needed_scale(self):
        return max(self.target_w / self.canvas_w, self.target_h / self.canvas_h)

    @property
    def uses_ai(self):
        return self.target_w > self.canvas_w or self.target_h > self.canvas_h

    def ai_detail_dpi(self):
        if self.print_w_in is None:
            return None
        return min(self.canvas_w * 4 / self.print_w_in, self.canvas_h * 4 / self.print_h_in)


def load_image(path):
    """Opens with camera orientation applied; returns (image in RGB or RGBA, ICC profile bytes or None)."""
    img = Image.open(path)
    icc = img.info.get("icc_profile")
    img = ImageOps.exif_transpose(img)
    has_alpha = img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)
    if img.mode in ("I;16", "I;16B", "I", "F"):
        arr = np.asarray(img, dtype=np.float32)
        img = Image.fromarray((arr / max(arr.max(), 1) * 255).astype(np.uint8))
    img = img.convert("RGBA" if has_alpha else "RGB")
    if has_alpha and img.getextrema()[3][0] == 255:
        img = img.convert("RGB")  # alpha channel present but fully opaque
    return img, icc


def _parse_size(text, unit):
    w, h = (float(v) for v in text.lower().replace(" ", "").split("x"))
    if unit == "cm":
        w, h = w / 2.54, h / 2.54
    return w, h


def plan_for(name, img, s: Settings) -> Plan:
    w, h = img.size
    notes = []
    if s.mode == "scale":
        tw, th = round(w * s.scale), round(h * s.scale)
        return Plan(name, w, h, (0, 0, w, h), w, h, tw, th, notes=notes)

    ratio = min(w, h) / max(w, h)
    if s.print_size == "auto":
        matches = [k for k, (a, b) in PRESETS.items() if abs(a / b - ratio) < 0.02 and b <= 36]
        key = max(matches, key=lambda k: PRESETS[k][1]) if matches else "16x20"
        if not matches:
            notes.append(f"No preset matches the {w}x{h} ratio; using 16x20 with {s.framing}.")
        short, long_ = PRESETS[key]
    elif s.print_size in PRESETS:
        short, long_ = PRESETS[s.print_size]
    else:
        a, b = _parse_size(s.print_size, s.unit)
        short, long_ = min(a, b), max(a, b)
    landscape = w > h
    pw_in, ph_in = (long_, short) if landscape else (short, long_)

    if s.framing == "keep":
        # largest print of that size class that fits without cropping
        k = min(pw_in / w, ph_in / h)
        pw_in, ph_in = w * k, h * k
        plan = Plan(name, w, h, (0, 0, w, h), w, h, round(pw_in * s.dpi), round(ph_in * s.dpi), pw_in, ph_in, notes)
        _warn_soft(plan, s)
        return plan

    target_ratio = pw_in / ph_in
    if s.framing == "fill":
        if w / h > target_ratio:
            cw, ch = round(h * target_ratio), h
        else:
            cw, ch = w, round(w / target_ratio)
        ax = {"left": 0.0, "right": 1.0}.get(s.crop_anchor, 0.5)
        ay = {"top": 0.0, "bottom": 1.0}.get(s.crop_anchor, 0.5)
        x0 = round((w - cw) * ax)
        y0 = round((h - ch) * ay)
        box = (x0, y0, x0 + cw, y0 + ch)
        if (cw, ch) != (w, h):
            lost = 100 * (1 - cw * ch / (w * h))
            notes.append(f"Crops {lost:.0f}% of the image to fit {describe_size(pw_in, ph_in)}.")
    else:  # fit
        if w / h > target_ratio:
            cw, ch = w, round(w / target_ratio)
        else:
            cw, ch = round(h * target_ratio), h
        box = (0, 0, w, h)
    tw, th = round(pw_in * s.dpi), round(ph_in * s.dpi)
    plan = Plan(name, w, h, box, cw, ch, tw, th, pw_in, ph_in, notes)
    _warn_soft(plan, s)
    return plan


def _warn_soft(plan, s):
    """Says plainly when most of the print's pixels will come from interpolation, not the AI."""
    dpi = plan.ai_detail_dpi()
    if plan.uses_ai and dpi is not None and dpi < s.dpi * 0.5:
        plan.notes.append(f"WARNING: AI detail is only about {round(dpi)} DPI at this size; "
                          f"expect a soft print up close. A smaller print or a larger source works better.")


def prepare_canvas(img, plan: Plan, s: Settings) -> Image.Image:
    if s.framing == "fit" and s.mode == "print" and (plan.canvas_w, plan.canvas_h) != (plan.src_w, plan.src_h):
        if s.margin == "transparent":
            canvas = Image.new("RGBA", (plan.canvas_w, plan.canvas_h), (0, 0, 0, 0))
        else:
            if s.margin == "edge":
                a = np.asarray(img.convert("RGB"))
                border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
                color = tuple(int(v) for v in border.mean(axis=0))
            else:
                color = (255, 255, 255) if s.margin == "white" else (0, 0, 0)
            canvas = Image.new(img.mode, (plan.canvas_w, plan.canvas_h), color + ((255,) if img.mode == "RGBA" else ()))
        canvas.paste(img, ((plan.canvas_w - plan.src_w) // 2, (plan.canvas_h - plan.src_h) // 2))
        return canvas
    return img.crop(plan.crop_box)


def bleed_transparent(rgba: Image.Image) -> Image.Image:
    """Gives fully transparent pixels the colour of the nearest visible pixel (avoids dark halos)."""
    from scipy.ndimage import distance_transform_edt
    a = np.asarray(rgba)
    alpha = a[..., 3]
    if alpha.min() > 0 or alpha.max() == 0:
        return rgba.convert("RGB")
    _, (iy, ix) = distance_transform_edt(alpha == 0, return_indices=True)
    return Image.fromarray(a[..., :3][iy, ix])


# ----------------------------------------------------------------------------- run

def output_name(name, plan: Plan, s: Settings):
    base = "".join(c if c.isalnum() or c in "-_" else "_" for c in os.path.splitext(name)[0]).strip("_")[:48] or "Artwork"
    f = round(plan.needed_scale, 1)
    factor = f"{int(f)}x" if f == int(f) else f"{f}x"
    dpi = f"_{s.dpi}DPI" if s.mode == "print" else ""
    ext = "jpg" if s.output_format in ("jpg", "etsy") else "png"
    if s.output_format == "etsy":
        base += "_Etsy"
    return f"{base}_{factor}_{plan.target_w}x{plan.target_h}{dpi}.{ext}"


def process(model, path, out_dir, s: Settings, log=print):
    """Upscales one image to its print target. Returns a result dict for the summary table."""
    t0 = time.time()
    name = os.path.basename(path)
    img, icc = load_image(path)
    plan = plan_for(name, img, s)
    canvas = prepare_canvas(img, plan, s)
    has_alpha = canvas.mode == "RGBA"
    rgb = bleed_transparent(canvas) if has_alpha else canvas

    if plan.uses_ai:
        last = [0.0]

        def prog(d, t):
            if time.time() - last[0] > 5 or d == t:
                last[0] = time.time()
                log(f"   AI {100 * d // t}%")
        ai = ai_upscale_4x(model, rgb, block=s.block, seed=s.seed, progress=prog, batch=s.batch or default_batch())
        method = "AuraSR 4x"
        if (ai.width, ai.height) != (plan.target_w, plan.target_h):
            ai = ai.resize((plan.target_w, plan.target_h), Image.LANCZOS)
            beyond = plan.needed_scale / 4
            method += f", then Lanczos {beyond:.2f}x" if beyond > 1.01 else ", then downsampled"
        out = ai
    else:
        out = rgb.resize((plan.target_w, plan.target_h), Image.LANCZOS)
        method = "Lanczos only (no enlargement needed)"

    if has_alpha:
        alpha = canvas.getchannel("A").resize((plan.target_w, plan.target_h), Image.LANCZOS)
        out = out.convert("RGBA")
        out.putalpha(alpha)

    fname = output_name(name, plan, s)
    dst = os.path.join(out_dir, fname)
    save_kw = {"dpi": (s.dpi, s.dpi)}
    if icc:
        save_kw["icc_profile"] = icc
    quality_note = ""
    if s.output_format == "etsy":
        if out.mode == "RGBA":
            flat = Image.new("RGB", out.size, (255, 255, 255))
            flat.paste(out, mask=out.getchannel("A"))
            out = flat
        q, sub, data = save_jpeg_under(out, ETSY_FILE_LIMIT, save_kw)
        with open(dst, "wb") as f:
            f.write(data)
        quality_note = f" JPEG quality {q}%{'' if sub == 0 else ', 4:2:0 colour'} to fit Etsy's 20 MB limit."
    elif s.output_format == "jpg":
        if out.mode == "RGBA":
            flat = Image.new("RGB", out.size, (255, 255, 255))
            flat.paste(out, mask=out.getchannel("A"))
            out = flat
        out.save(dst, "JPEG", quality=s.jpeg_quality, subsampling=0, optimize=True, **save_kw)
    else:
        out.save(dst, "PNG", compress_level=6, **save_kw)

    compare_path = None
    if s.comparison:
        compare_path = os.path.join(out_dir, "compare", os.path.splitext(fname)[0] + "_compare.jpg")
        os.makedirs(os.path.dirname(compare_path), exist_ok=True)
        comparison_sheet(rgb, out, plan).save(compare_path, quality=92)

    ai_dpi = plan.ai_detail_dpi() if plan.uses_ai else None
    res = {
        "file": name, "output": fname, "source": f"{plan.src_w}x{plan.src_h}",
        "output_px": f"{plan.target_w}x{plan.target_h}",
        "print": f"{describe_size(plan.print_w_in, plan.print_h_in)} @ {s.dpi} DPI" if plan.print_w_in else "-",
        "ai_detail_dpi": round(ai_dpi) if ai_dpi else "-",
        "method": method, "size_mb": round(os.path.getsize(dst) / 2**20, 1),
        "seconds": round(time.time() - t0, 1), "notes": (" ".join(plan.notes) + quality_note).strip(), "compare": compare_path,
    }
    return res


def save_jpeg_under(img, limit, save_kw, min_quality=70):
    """
    Highest JPEG quality (70 to 100) whose file is at most `limit` bytes. Tries full colour
    resolution (4:4:4) first, then standard 4:2:0. Raises with a clear reason if nothing fits.
    """
    for sub in (0, 2):
        lo, hi, best = min_quality, 100, None
        while lo <= hi:
            q = (lo + hi) // 2
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=q, subsampling=sub, optimize=True, **save_kw)
            if buf.tell() <= limit:
                best, lo = (q, buf.getvalue()), q + 1
            else:
                hi = q - 1
        if best:
            return best[0], sub, best[1]
    raise ValueError(f"Even at {min_quality}% JPEG quality this file is over {limit // 1_000_000} MB, Etsy's limit per file. "
                     "Use a smaller print size or lower DPI, or deliver this size through a download link.")


def comparison_sheet(src_rgb: Image.Image, out: Image.Image, plan: Plan, side=640) -> Image.Image:
    """100% crop from the centre of the output, next to the same area enlarged with Lanczos."""
    out_rgb = out.convert("RGB")
    W, H = out_rgb.size
    side = min(side, W, H)
    l, t = (W - side) // 2, (H - side) // 2
    after = out_rgb.crop((l, t, l + side, t + side))
    sx, sy = src_rgb.width / W, src_rgb.height / H
    box = (l * sx, t * sy, (l + side) * sx, (t + side) * sy)
    before = src_rgb.resize((side, side), Image.LANCZOS, box=box)
    sheet = Image.new("RGB", (side * 2 + 12, side + 36), (18, 17, 16))
    sheet.paste(before, (0, 36))
    sheet.paste(after, (side + 12, 36))
    d = ImageDraw.Draw(sheet)
    d.text((8, 8), "ORIGINAL, Lanczos enlargement (100% crop)", fill=(242, 238, 230), font=_font(18))
    d.text((side + 20, 8), "AURASR OUTPUT (100% crop)", fill=(242, 238, 230), font=_font(18))
    return sheet


def _font(size):
    from PIL import ImageFont
    try:
        return ImageFont.load_default(size=size)  # Pillow 10.1+
    except TypeError:
        return ImageFont.load_default()


def find_images(folder):
    found = []
    for root, _, files in os.walk(folder):
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() in IMAGE_EXTS and not f.startswith("."):
                found.append(os.path.join(root, f))
    return found


def preview_plans(paths, s: Settings, max_side=360):
    """Contact sheet of every image with the crop/fit frame drawn on, before any processing."""
    tiles = []
    for p in paths:
        img, _ = load_image(p)
        plan = plan_for(os.path.basename(p), img, s)
        k = max_side / max(img.size)
        thumb = img.convert("RGB").resize((max(1, round(img.width * k)), max(1, round(img.height * k))))
        d = ImageDraw.Draw(thumb)
        if s.framing == "fill" and s.mode == "print":
            x0, y0, x1, y1 = (v * k for v in plan.crop_box)
            dim = Image.new("RGB", thumb.size, (0, 0, 0))
            mask = Image.new("L", thumb.size, 150)
            ImageDraw.Draw(mask).rectangle((x0, y0, x1 - 1, y1 - 1), fill=0)
            thumb = Image.composite(dim, thumb, mask)
            ImageDraw.Draw(thumb).rectangle((x0, y0, x1 - 1, y1 - 1), outline=(234, 100, 64), width=3)
        label = f"{plan.target_w}x{plan.target_h}px" + (f" | AI detail {round(plan.ai_detail_dpi())} DPI" if plan.uses_ai and plan.print_w_in else "")
        cell = Image.new("RGB", (max_side, max_side + 44), (18, 17, 16))
        cell.paste(thumb, ((max_side - thumb.width) // 2, (max_side - thumb.height) // 2))
        cd = ImageDraw.Draw(cell)
        cd.text((6, max_side + 4), os.path.basename(p)[:44], fill=(242, 238, 230), font=_font(15))
        cd.text((6, max_side + 23), label, fill=(184, 177, 166), font=_font(14))
        tiles.append((cell, plan))
    cols = min(3, max(1, len(tiles)))
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * (max_side + 8), rows * (max_side + 52)), (10, 10, 10))
    for i, (cell, _) in enumerate(tiles):
        sheet.paste(cell, ((i % cols) * (max_side + 8), (i // cols) * (max_side + 52)))
    return sheet, [p for _, p in tiles]


def zip_folder(folder, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as z:  # PNG/JPEG are already compressed
        for root, _, files in os.walk(folder):
            for f in files:
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, folder))
    return zip_path


CREDIT = ("Upscaled with AuraSR v2 by fal.ai (https://huggingface.co/fal/AuraSR-v2), "
          "licensed CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/).")
