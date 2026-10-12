#!/usr/bin/env python3
"""Quality checks for a rendered MP4.

  python3 scripts/validate_video.py output/final_video.mp4 [--expect 282.5] [--sheet out.png]

Checks: container/codec/resolution/fps, durations of video & audio, black frames,
audio peak / loudness / clipping, frozen (static) stretches, and writes a contact sheet.
"""
import json, re, subprocess, sys
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    path = Path(sys.argv[1])
    args = sys.argv[2:]
    expect = float(args[args.index("--expect") + 1]) if "--expect" in args else None
    sheet = args[args.index("--sheet") + 1] if "--sheet" in args else str(path.with_suffix(".sheet.png"))
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + msg)
        ok &= bool(cond)

    j = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    fps = eval(v["r_frame_rate"])
    vdur, fdur = float(v.get("duration", 0)), float(j["format"]["duration"])
    check(v["codec_name"] == "h264", f"video codec {v['codec_name']} ({v.get('profile')}, {v['pix_fmt']})")
    check((v["width"], v["height"]) == (1920, 1080), f"resolution {v['width']}x{v['height']} (16:9)")
    check(abs(fps - 30) < 0.01, f"frame rate {fps:.3f}")
    check(a is not None and a["codec_name"] == "aac", f"audio codec {a and a['codec_name']} {a and a['sample_rate']}Hz ch={a and a['channels']}")
    adur = float(a["duration"]) if a else 0
    check(abs(vdur - adur) < 0.2, f"durations video {vdur:.2f}s audio {adur:.2f}s container {fdur:.2f}s")
    if expect:
        check(abs(fdur - expect) < 0.3, f"expected duration {expect:.2f}s")

    bd = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vf", "blackdetect=d=0.5:pix_th=0.06", "-an", "-f", "null", "-"]).stderr
    blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bd)
    inner = [b for b in blacks if float(b[0]) > 1.5 and float(b[1]) < fdur - 1.5]
    check(not inner, f"no black stretches inside the programme (found {len(blacks)} total, {len(inner)} inside: {inner[:5]})")

    fr = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vf", "freezedetect=n=0.0008:d=4", "-an", "-f", "null", "-"]).stderr
    frozen = re.findall(r"freeze_start: ([\d.]+)", fr)
    check(len(frozen) == 0, f"no frozen stretches >4s (found {frozen[:6]})")

    vol = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vn", "-af", "volumedetect,ebur128=peak=true", "-f", "null", "-"]).stderr
    peak = float(re.search(r"max_volume: (-?[\d.]+) dB", vol).group(1))
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", vol)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", vol)
    check(peak < -0.3, f"audio sample peak {peak} dBFS (no clipping)")
    print(f"INFO integrated loudness {lufs[-1] if lufs else '?'} LUFS, true peak {tp[-1] if tp else '?'} dBFS")

    n = 24
    times = [fdur * (i + 0.5) / n for i in range(n)]
    sel = "+".join(f"eq(n\\,{int(t * fps)})" for t in times)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-vf", f"select='{sel}',scale=480:270,tile=4x6", "-vsync", "vfr", "-frames:v", "1", sheet])
    print(f"INFO contact sheet: {sheet}")
    print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
