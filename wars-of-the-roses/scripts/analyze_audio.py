#!/usr/bin/env python3
"""Analyse the narration and build transcript.json, audio_analysis.json and subtitles.srt.

Input:
  input/narration_main.wav      the full narration (authoritative timeline)
  input/narration_2.wav         a 5 s pickup / re-take of one sentence
  data/words_raw.json           word timestamps from ElevenLabs Scribe, transcribed from
                                main + 1 s silence + retake (concatenated)

Usage:  python3 scripts/analyze_audio.py
"""
import json, subprocess, re
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
INP, DATA, OUT = ROOT / "input", ROOT / "data", ROOT / "output"
MAIN, RETAKE = INP / "narration_main.wav", INP / "narration_2.wav"


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=sample_rate,channels,codec_name:format=duration",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True)
    j = json.loads(out.stdout)
    s = j["streams"][0]
    return {"file": path.name, "codec": s["codec_name"], "sample_rate": int(s["sample_rate"]),
            "channels": int(s["channels"]), "duration": float(j["format"]["duration"])}


def pcm(path, sr=16000):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", str(sr),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def levels(path):
    x = pcm(path, 44100)
    w = 4410
    n = len(x) // w
    rms = np.sqrt((x[:n * w].reshape(n, w) ** 2).mean(1))
    db = 20 * np.log10(rms + 1e-9)
    return {"peak_dbfs": round(float(20 * np.log10(np.abs(x).max() + 1e-9)), 2),
            "rms_dbfs_median": round(float(np.median(db)), 1),
            "noise_floor_dbfs_p1": round(float(np.percentile(db, 1)), 1),
            "background_music_detected": bool(np.percentile(db, 1) > -40)}


def pauses(path, min_len=0.3):
    x = pcm(path)
    w = 1600  # 100 ms
    n = len(x) // w
    db = 20 * np.log10(np.sqrt((x[:n * w].reshape(n, w) ** 2).mean(1)) + 1e-9)
    thr = np.percentile(db, 12)
    res, s = [], None
    for i, v in enumerate(db < thr):
        if v and s is None:
            s = i
        if not v and s is not None:
            if (i - s) / 10 >= min_len:
                res.append([round(s / 10, 2), round(i / 10, 2)])
            s = None
    return res


def sentences(words):
    out, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.!?؟]$", w["text"]):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [{"start": s[0]["start"], "end": s[-1]["end"], "text": " ".join(w["text"] for w in s),
             "words": s} for s in out]


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


DANGLING = {"ذات", "من", "في", "على", "بين", "عن", "إلى", "مع", "حتى", "بعد", "عبر", "ضد", "التي", "الذي", "كل"}


def subtitle_cues(sents, max_words=9, max_dur=4.6):
    cues = []
    for s in sents:
        chunk = []
        for i, w in enumerate(s["words"]):
            chunk.append(w)
            last = i == len(s["words"]) - 1
            punct = w["text"].endswith("،") and len(chunk) >= 4
            long = len(chunk) >= max_words or (w["end"] - chunk[0]["start"]) >= max_dur
            if long and not last and w["text"] in DANGLING:
                long = len(chunk) >= max_words + 3  # don't end a cue on a preposition
            if last or punct or long:
                cues.append([chunk[0]["start"], chunk[-1]["end"], " ".join(c["text"] for c in chunk)])
                chunk = []
    # extend each cue slightly into the following gap for readability
    for i, c in enumerate(cues):
        nxt = cues[i + 1][0] if i + 1 < len(cues) else c[1] + 1.0
        c[1] = min(c[1] + 0.35, nxt - 0.04)
    return cues


def main():
    raw = json.loads((DATA / "words_raw.json").read_text())["words"]
    info_main, info_re = probe(MAIN), probe(RETAKE)
    split = info_main["duration"] + 0.5  # retake begins after main + 1 s gap
    offset = info_main["duration"] + 1.0
    main_words = [{"text": w["text"], "start": w["start"], "end": w["end"]}
                  for w in raw if w.get("type", "word") == "word" and w["start"] < split]
    retake_words = [{"text": w["text"], "start": round(w["start"] - offset, 3), "end": round(w["end"] - offset, 3)}
                    for w in raw if w.get("type", "word") == "word" and w["start"] >= split]
    sents = sentences(main_words)
    for i, s in enumerate(sents):
        s["id"] = f"s{i + 1:02d}"
    transcript = {
        "source": "ElevenLabs Scribe v1 (word timestamps), language ara",
        "audio": info_main["file"], "duration": info_main["duration"],
        "full_text": " ".join(s["text"] for s in sents),
        "sentences": sents,
        "retakes": [{"file": info_re["file"], "text": " ".join(w["text"] for w in retake_words),
                     "words": retake_words,
                     "matches_sentence": next((s["id"] for s in sents
                                               if s["text"] == " ".join(w["text"] for w in retake_words)), None)}],
    }
    (DATA / "transcript.json").write_text(json.dumps(transcript, ensure_ascii=False, indent=1))

    analysis = {"main": {**info_main, **levels(MAIN), "pauses": pauses(MAIN)},
                "retake": {**info_re, **levels(RETAKE)}}
    (DATA / "audio_analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=1))

    OUT.mkdir(exist_ok=True)
    cues = subtitle_cues(sents)
    with open(OUT / "subtitles.srt", "w", encoding="utf-8") as f:
        for i, (a, b, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n\n")

    print(f"main: {info_main['duration']:.2f}s {info_main['sample_rate']}Hz ch={info_main['channels']} "
          f"peak={analysis['main']['peak_dbfs']}dBFS music={analysis['main']['background_music_detected']}")
    print(f"sentences: {len(sents)}  words: {len(main_words)}  subtitle cues: {len(cues)}")
    print(f"retake: {transcript['retakes'][0]['text']} -> {transcript['retakes'][0]['matches_sentence']}")
    for s in sents:
        print(f"{s['id']} {s['start']:7.2f}-{s['end']:7.2f} {s['text'][:70]}")


if __name__ == "__main__":
    main()
