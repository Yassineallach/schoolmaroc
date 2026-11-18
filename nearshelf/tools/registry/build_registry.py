#!/usr/bin/env python3
"""Build app/src/main/assets/libraries.json from seed.csv.

For every seed row this script, politely (one request at a time, --delay seconds apart):
  1. checks each candidate catalog URL live and keeps the first one whose software is
     recognised AND whose page title names this library (so a guessed subdomain that
     belongs to someone else is never accepted);
  2. finds the library's Libby system on locate.libbyapp.com and its full branch list
     (names, addresses, coordinates) from locate.libbyapp.com/branches/{websiteId};
  3. finds the library on Hoopla's library autocomplete (never the single-library
     endpoint, which exposes credential-like fields).
Only the standard library is used. Usage:
  python3 tools/registry/build_registry.py [--only "Seattle"] [--delay 1.0]
"""
import argparse
import csv
import datetime
import gzip
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "app", "src", "main", "assets", "libraries.json")
REPORT = os.path.join(HERE, "report.md")
UA = "Nearshelf-registry-builder/1.0 (+https://github.com/yassineallach/nearshelf)"

NON_BRANCH = re.compile(r"\b(digital|online|virtual|e-?library|access cards?|web ?site|electronic|ecard|e-card)\b", re.I)


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"['’`]", "", s)
    return re.sub(r"[^\w]+", " ", s).strip()


# Mirrors Library.idFor in Kotlin. "county"/"city" are kept: San Diego County Library and
# San Diego Public Library are different libraries.
NOISE = re.compile(r"\b(the|public|library|libraries|system|district|of|and)\b")


def key(name):
    n = norm(re.sub(r"\s*\([A-Za-z .]{2,20}\)\s*$", "", name))
    k = re.sub(r"\s+", " ", NOISE.sub(" ", n)).strip()
    return k or n


class Http:
    def __init__(self, delay):
        self.delay, self.last = delay, 0.0

    def get(self, url, headers=None, want_json=False):
        wait = self.delay - (time.time() - self.last)
        if wait > 0:
            time.sleep(wait)
        self.last = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip", **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                body = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                text = body.decode("utf-8", "replace")
                return r.geturl(), (json.loads(text) if want_json else text)
        except (urllib.error.URLError, TimeoutError, ValueError, ConnectionError) as e:
            return None, str(e)


# --- catalog detection: mirrors core/.../registry/CatalogDetector.kt (the tested original) ---
def detect(final_url, html):
    u = urllib.parse.urlparse(final_url)
    host, path, origin = u.hostname or "", u.path or "", f"https://{(u.hostname or '').lower()}"
    if "Aspen Discovery" in html:
        return "ASPEN", origin
    if host.endswith(".bibliocommons.com"):
        return "BIBLIOCOMMONS", origin
    if host.endswith(".iiivega.com"):
        return "SIERRA_VEGA", origin
    if "/cgi-bin/koha/" in path:
        return "KOHA", origin
    if path.startswith("/eg/opac") or path.startswith("/eg2/"):
        return "EVERGREEN", origin
    if "/iii/encore" in path or re.match(r"^/search~S\d*", path):
        return "SIERRA_ENCORE", origin
    if path.lower().startswith("/polaris"):
        return "POLARIS", origin + "/polaris"
    if host.endswith(".polarislibrary.com"):
        return "POLARIS", origin
    if re.search(r'<meta name="generator" content="Koha', html, re.I) or "/cgi-bin/koha/opac-search.pl" in html:
        return "KOHA", origin
    if "Vega Discover" in html:
        return "SIERRA_VEGA", origin
    if "POLARIS.PAC" in html or re.search(r'(src|href)="[^"]*/polaris/', html, re.I):
        return "POLARIS", origin + "/polaris" if (origin + "/polaris/" in html or '"/polaris/' in html) else origin
    if re.search(r'(src|href)="(https?://[^"/]+)?/(eg/opac/|eg2/)', html):
        return "EVERGREEN", origin
    if "WebPAC PRO" in html:
        return "SIERRA_ENCORE", origin
    return None


def title_of(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def find_catalog(http, row, log):
    for cand in [c.strip() for c in row["catalog_candidates"].split("|") if c.strip()]:
        # A leading "!" marks a catalog verified by hand (its page title is generic, e.g.
        # "Vega Discover"); the software is still detected live, only the name check is skipped.
        manual = cand.startswith("!")
        cand = cand.lstrip("!")
        final, html = http.get(cand)
        if final is None:
            log.append(f"catalog {cand}: unreachable ({html[:80]})")
            continue
        d = detect(final, html)
        t = title_of(html)
        if not d:
            log.append(f"catalog {cand}: not recognised (title {t[:60]!r})")
            continue
        # BiblioCommons answers unknown subdomains with a placeholder page.
        if not manual and norm(t) == "bibliocommons inc":
            log.append(f"catalog {cand}: BiblioCommons placeholder (no such library)")
            continue
        # The page title must name the place. Only the title counts: a guessed address
        # always contains the name, so checking the URL would accept anything.
        # "county", "city" and "and" are often written differently ("&") or left out.
        words = [w for w in key(row["name"]).split() if len(w) > 2 and w not in ("county", "city", "and")]
        if not manual and words and not all(w in norm(t) for w in words):
            log.append(f"catalog {cand}: {d[0]} but title {t[:60]!r} doesn't name the library")
            continue
        log.append(f"catalog {cand}: {d[0]} at {d[1]}")
        return {"provider": d[0], "baseUrl": d[1]}
    return None


def queries(row):
    """The official name first; OverDrive and Hoopla sometimes only find a library by its city."""
    return [q for q in (row["name"], row["city"]) if q]


def find_overdrive(http, row, log):
    for q in queries(row):
        final, data = http.get("https://locate.libbyapp.com/autocomplete/" + urllib.parse.quote(q), want_json=True)
        if final is None or not isinstance(data, dict):
            continue
        found = match_overdrive(http, row, data, log)
        if found[0]:
            return found
    log.append("libby: no matching system")
    return None, []


def match_overdrive(http, row, data, log):
    want = key(row["name"])
    for b in data.get("branches", []):
        if (b.get("countryCode") or "").upper() != row["country"]:
            continue
        for s in b.get("systems", []):
            if key(s.get("name", "")) == want and s.get("fulfillmentId"):
                od = {"key": s["fulfillmentId"], "websiteId": s.get("websiteId")}
                branches = []
                if s.get("websiteId"):
                    _, full = http.get(f"https://locate.libbyapp.com/branches/{s['websiteId']}", want_json=True)
                    if isinstance(full, dict):
                        branches = clean_branches(full.get("branches", []), s.get("name", ""))
                log.append(f"libby: {od['key']} ({len(branches)} branches)")
                return od, branches
    return None, []


def clean_branches(raw, system_name):
    out, seen = [], set()
    for b in raw:
        name = re.sub(r"\s*\(" + re.escape(system_name) + r"\)\s*$", "", b.get("name", "")).strip()
        if not name or NON_BRANCH.search(name) or name.lower() in seen:
            continue
        seen.add(name.lower())
        lat, lng = b.get("latitude"), b.get("longitude")
        out.append({k: v for k, v in {
            "id": f"od:{b['id']}",
            "name": name,
            "address": b.get("address") or None,
            "city": b.get("city") or None,
            "latitude": lat if isinstance(lat, (int, float)) and lat != 0 else None,
            "longitude": lng if isinstance(lng, (int, float)) and lng != 0 else None,
        }.items() if v is not None})
    return sorted(out, key=lambda b: b["name"])


def find_hoopla(http, row, log):
    for q in queries(row):
        url = "https://patron-api-gateway.hoopladigital.com/core/libraries/autocomplete?query=" + urllib.parse.quote(q)
        final, data = http.get(url, headers={"app": "WWW", "ws-api": "2.1", "Accept": "application/json"}, want_json=True)
        if final is None or not isinstance(data, list):
            continue
        found = match_hoopla(row, data, log)
        if found:
            return found
    log.append("hoopla: none")
    return None


def match_hoopla(row, data, log):
    want = key(row["name"])
    for lib in data:
        if not lib.get("enabled", True) or lib.get("hideFromChooser"):
            continue
        if (lib.get("country") or "").upper() != row["country"]:
            continue
        if row["region"] and lib.get("state") and lib["state"].upper() != row["region"].upper():
            continue
        if key(lib.get("name", "")) == want:
            log.append(f"hoopla: {lib['id']}")
            return {"id": str(lib["id"]), "borrowLimitPerMonth": lib.get("circsPerPatronMonth")}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", default=os.path.join(HERE, "seed.csv"))
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--only", help="substring of library names to process (output not written)")
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--update", help="substring of names to rebuild and merge into the existing output")
    args = ap.parse_args()

    http = Http(args.delay)
    rows = list(csv.DictReader(open(args.seed, encoding="utf-8")))
    if args.only:
        rows = [r for r in rows if args.only.lower() in r["name"].lower()]
    if args.update:
        rows = [r for r in rows if args.update.lower() in r["name"].lower()]
    libraries, report = [], []
    for i, row in enumerate(rows, 1):
        row = {k: (v or "").strip() for k, v in row.items()}
        log = []
        catalog = find_catalog(http, row, log)
        od, branches = find_overdrive(http, row, log)
        hoopla = find_hoopla(http, row, log)
        entry = {k: v for k, v in {
            "name": row["name"], "country": row["country"], "region": row["region"] or None, "city": row["city"] or None,
            "catalog": catalog, "overdrive": od, "hoopla": hoopla, "branches": branches,
        }.items() if v not in (None, [])}
        print(f"[{i}/{len(rows)}] {row['name']}: " + "; ".join(log), flush=True)
        report.append((row["name"], row["country"], catalog, od, hoopla, len(branches), log))
        if catalog or od or hoopla:
            libraries.append(entry)

    if args.only:
        print(json.dumps(libraries, indent=1)[:3000])
        return
    if args.update:
        old = json.load(open(args.out, encoding="utf-8"))["libraries"]
        redone = {(r[0], r[1]) for r in report}
        libraries = [l for l in old if (l["name"], l["country"]) not in redone] + libraries
    libraries.sort(key=lambda l: (l["country"], l["name"]))
    doc = {"version": 1, "generatedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "libraries": libraries}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")
    if args.update:
        print(f"updated {len(report)} rows in {args.out} ({len(libraries)} libraries)")
        return
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(f"# Registry build report\n\nGenerated {doc['generatedAt']} from {len(rows)} seed rows; {len(libraries)} libraries kept.\n\n")
        f.write(f"- Physical catalog verified: {sum(1 for r in report if r[2])}\n- Libby: {sum(1 for r in report if r[3])}\n- Hoopla: {sum(1 for r in report if r[4])}\n- With branch list: {sum(1 for r in report if r[5])}\n\n")
        f.write("| Library | Country | Catalog | Libby | Hoopla | Branches |\n|---|---|---|---|---|---|\n")
        for name, country, cat, od, hp, nb, _ in report:
            f.write(f"| {name} | {country} | {cat['provider'] + ' ' + cat['baseUrl'] if cat else '-'} | {od['key'] if od else '-'} | {hp['id'] if hp else '-'} | {nb} |\n")
        f.write("\n## Log\n\n")
        for name, *_, log in report:
            f.write(f"- **{name}**: " + "; ".join(log) + "\n")
    print(f"wrote {args.out} ({len(libraries)} libraries) and {REPORT}")


if __name__ == "__main__":
    sys.exit(main())
