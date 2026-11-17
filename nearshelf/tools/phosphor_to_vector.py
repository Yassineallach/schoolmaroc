#!/usr/bin/env python3
"""Convert Phosphor icon SVGs (MIT, @phosphor-icons/core) to Android vector drawables.

Usage: phosphor_to_vector.py <phosphor assets dir> <res/drawable dir> <weight> name[:alias] ...
Writes ic_<alias>.xml for each icon. Phosphor SVGs are 256x256 single-colour paths.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

NS = "{http://www.w3.org/2000/svg}"


def convert(svg_path: str) -> str:
    root = ET.parse(svg_path).getroot()
    vb = root.get("viewBox", "0 0 256 256").split()
    w, h = vb[2], vb[3]
    paths = []
    for el in root.iter():
        tag = el.tag.replace(NS, "")
        if tag == "path":
            paths.append(el.get("d"))
        elif tag in ("rect", "circle", "line", "polyline", "polygon", "ellipse"):
            raise SystemExit(f"{svg_path}: unsupported element <{tag}>")
    body = "\n".join(
        f'    <path android:fillColor="@android:color/white" android:pathData="{d}" />' for d in paths
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<!-- Phosphor Icons (MIT), https://phosphoricons.com -->\n"
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:width="24dp"\n    android:height="24dp"\n'
        f'    android:viewportWidth="{w}"\n    android:viewportHeight="{h}"\n'
        '    android:autoMirrored="false"\n'
        '    android:tint="?android:attr/colorControlNormal">\n'
        f"{body}\n</vector>\n"
    )


def main() -> None:
    src, out, weight, *names = sys.argv[1:]
    for spec in names:
        name, _, alias = spec.partition(":")
        alias = (alias or name).replace("-", "_")
        suffix = "" if weight == "regular" else f"-{weight}"
        svg = os.path.join(src, weight, f"{name}{suffix}.svg")
        mirrored = alias.startswith("arrow_left") or alias.startswith("caret_left")
        xml = convert(svg)
        if mirrored:
            xml = xml.replace('android:autoMirrored="false"', 'android:autoMirrored="true"')
        with open(os.path.join(out, f"ic_{alias}.xml"), "w") as f:
            f.write(xml)
        print("ic_" + alias)


if __name__ == "__main__":
    main()
