#!/usr/bin/env python3
"""Checks libraries.json: schema, unique libraries, https URLs, coordinates in range.
Exit code 1 on any problem. The Kotlin test RegistryAssetTest runs the same checks in CI."""
import json
import os
import re
import sys

PROVIDERS = {"BIBLIOCOMMONS", "KOHA", "EVERGREEN", "ASPEN", "POLARIS", "SIERRA_ENCORE", "SIERRA_VEGA"}
HERE = os.path.dirname(os.path.abspath(__file__))
PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "app", "src", "main", "assets", "libraries.json")


def main():
    doc = json.load(open(PATH, encoding="utf-8"))
    errors = []
    if doc.get("version") != 1:
        errors.append("version must be 1")
    seen = set()
    for i, lib in enumerate(doc.get("libraries", [])):
        where = f"#{i} {lib.get('name')!r}"
        if not lib.get("name") or not re.fullmatch(r"[A-Z]{2}", lib.get("country", "")):
            errors.append(f"{where}: name and 2-letter country required")
        ident = (lib.get("name", "").lower(), lib.get("country"))
        if ident in seen:
            errors.append(f"{where}: duplicate")
        seen.add(ident)
        if not (lib.get("catalog") or lib.get("overdrive") or lib.get("hoopla")):
            errors.append(f"{where}: no service")
        cat = lib.get("catalog")
        if cat and (cat.get("provider") not in PROVIDERS or not cat.get("baseUrl", "").startswith("https://")):
            errors.append(f"{where}: bad catalog {cat}")
        if lib.get("overdrive") and not re.fullmatch(r"[A-Za-z0-9_-]+", lib["overdrive"].get("key", "")):
            errors.append(f"{where}: bad Libby key")
        ids = set()
        for b in lib.get("branches", []):
            if not b.get("id") or not b.get("name") or b["id"] in ids:
                errors.append(f"{where}: branch needs a unique id and a name: {b}")
            ids.add(b.get("id"))
            lat, lng = b.get("latitude"), b.get("longitude")
            if (lat is None) != (lng is None) or (lat is not None and not (-90 <= lat <= 90 and -180 <= lng <= 180)):
                errors.append(f"{where}: bad coordinates on {b.get('name')}")
    for e in errors:
        print("ERROR", e)
    print(f"{len(doc.get('libraries', []))} libraries, {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
