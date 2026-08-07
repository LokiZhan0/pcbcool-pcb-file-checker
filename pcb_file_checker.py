#!/usr/bin/env python3
"""PCBCool PCB File Checker.

A lightweight, dependency-free preflight tool that scans a folder or ZIP archive
for common PCB manufacturing and assembly files.

This tool checks file presence and naming only. It does not parse Gerber geometry,
perform DRC, verify stackups, or replace a manufacturer DFM review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable

VERSION = "1.0.0"

GERBER_EXTENSIONS = {
    ".gbr", ".ger", ".pho",
    ".gtl", ".gbl", ".gts", ".gbs", ".gto", ".gbo", ".gtp", ".gbp",
    ".gko", ".gml", ".gm1", ".gm2",
}
DRILL_EXTENSIONS = {".drl", ".xln", ".exc", ".ncd"}
BOM_EXTENSIONS = {".csv", ".tsv", ".xls", ".xlsx", ".ods", ".txt"}
PLACEMENT_EXTENSIONS = {".csv", ".tsv", ".txt", ".pos", ".mnt", ".xy", ".xlsx", ".xls"}

CATEGORY_LABELS = {
    "top_copper": "Top copper",
    "bottom_copper": "Bottom copper",
    "inner_copper": "Inner copper",
    "generic_copper": "Generic Gerber / copper",
    "top_mask": "Top solder mask",
    "bottom_mask": "Bottom solder mask",
    "top_silkscreen": "Top silkscreen",
    "bottom_silkscreen": "Bottom silkscreen",
    "top_paste": "Top paste",
    "bottom_paste": "Bottom paste",
    "outline": "Board outline / mechanical",
    "drill": "Drill / Excellon",
    "bom": "Bill of materials",
    "placement": "Pick-and-place / centroid",
    "drawing": "Fabrication / assembly drawing",
    "readme": "Readme / instructions",
    "other": "Other files",
}


def natural_key(path: Path) -> list[object]:
    parts = re.split(r"(\d+)", path.name.lower())
    return [int(p) if p.isdigit() else p for p in parts]


def classify_file(path: Path) -> str:
    name = path.name.lower()
    stem = path.stem.lower()
    ext = path.suffix.lower()

    # Exact, widely used Gerber extension mappings.
    exact = {
        ".gtl": "top_copper",
        ".gbl": "bottom_copper",
        ".gts": "top_mask",
        ".gbs": "bottom_mask",
        ".gto": "top_silkscreen",
        ".gbo": "bottom_silkscreen",
        ".gtp": "top_paste",
        ".gbp": "bottom_paste",
        ".gko": "outline",
        ".gml": "outline",
        ".gm1": "outline",
        ".gm2": "outline",
    }
    if ext in exact:
        return exact[ext]

    if ext in DRILL_EXTENSIONS:
        return "drill"

    # Common KiCad inner-layer extensions such as .g1, .g2, .g10.
    if re.fullmatch(r"\.g\d+", ext):
        return "inner_copper"

    # File-name heuristics for generic Gerber names.
    if ext in GERBER_EXTENSIONS:
        if any(k in stem for k in ("edge", "outline", "profile", "board", "dimension", "contour", "route")):
            return "outline"
        if any(k in stem for k in ("drill", "excellon", "pth", "npth")):
            return "drill"
        if any(k in stem for k in ("top", "front", "f_cu", "f-cu")) and any(k in stem for k in ("copper", "signal", "layer", "cu")):
            return "top_copper"
        if any(k in stem for k in ("bottom", "back", "b_cu", "b-cu")) and any(k in stem for k in ("copper", "signal", "layer", "cu")):
            return "bottom_copper"
        if any(k in stem for k in ("inner", "in1", "in2", "in3", "in4", "mid", "plane")):
            return "inner_copper"
        if "mask" in stem:
            if any(k in stem for k in ("top", "front", "f_")):
                return "top_mask"
            if any(k in stem for k in ("bottom", "back", "b_")):
                return "bottom_mask"
        if any(k in stem for k in ("silk", "legend", "overlay")):
            if any(k in stem for k in ("top", "front", "f_")):
                return "top_silkscreen"
            if any(k in stem for k in ("bottom", "back", "b_")):
                return "bottom_silkscreen"
        if "paste" in stem:
            if any(k in stem for k in ("top", "front", "f_")):
                return "top_paste"
            if any(k in stem for k in ("bottom", "back", "b_")):
                return "bottom_paste"
        return "generic_copper"

    # Drill files are sometimes exported as .txt.
    if ext == ".txt" and any(k in stem for k in ("drill", "excellon", "pth", "npth")):
        return "drill"

    # Assembly documents.
    if ext in BOM_EXTENSIONS and any(k in stem for k in ("bom", "bill_of_material", "bill-of-material", "materials")):
        return "bom"

    if ext in PLACEMENT_EXTENSIONS and any(
        k in stem
        for k in (
            "pick", "place", "pnp", "centroid", "position", "positions",
            "cpl", "mount", "placement", "xy", "coordinates",
        )
    ):
        return "placement"

    if ext in {".pdf", ".dwg", ".dxf", ".step", ".stp"} and any(
        k in stem for k in ("fab", "fabrication", "assembly", "drawing", "mechanical", "outline")
    ):
        return "drawing"

    if name in {"readme", "readme.txt", "readme.md", "instructions.txt", "notes.txt"}:
        return "readme"

    return "other"


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and not path.name.startswith("."):
            yield path


def inspect_directory(root: Path, assembly: bool) -> dict[str, object]:
    categories: dict[str, list[str]] = defaultdict(list)

    for path in sorted(iter_files(root), key=natural_key):
        category = classify_file(path)
        try:
            display_path = str(path.relative_to(root))
        except ValueError:
            display_path = str(path)
        categories[category].append(display_path)

    copper_categories = ("top_copper", "bottom_copper", "inner_copper", "generic_copper")
    has_copper = any(categories.get(c) for c in copper_categories)
    has_outline = bool(categories.get("outline"))
    has_drill = bool(categories.get("drill"))
    has_mask = bool(categories.get("top_mask") or categories.get("bottom_mask"))
    has_bom = bool(categories.get("bom"))
    has_placement = bool(categories.get("placement"))

    issues: list[dict[str, str]] = []

    if not has_copper:
        issues.append({
            "severity": "ERROR",
            "message": "No copper Gerber files were recognized.",
        })
    if not has_outline:
        issues.append({
            "severity": "ERROR",
            "message": "No board outline or mechanical profile file was recognized.",
        })
    if not has_drill:
        issues.append({
            "severity": "WARNING",
            "message": "No Excellon or drill file was recognized. This may be valid only for a board with no drilled features.",
        })
    if not has_mask:
        issues.append({
            "severity": "NOTICE",
            "message": "No solder mask file was recognized. Confirm whether the board is intentionally maskless.",
        })

    if assembly:
        if not has_bom:
            issues.append({
                "severity": "ERROR",
                "message": "Assembly mode is enabled, but no BOM file was recognized.",
            })
        if not has_placement:
            issues.append({
                "severity": "WARNING",
                "message": "Assembly mode is enabled, but no pick-and-place or centroid file was recognized.",
            })

    recognized = sum(len(v) for k, v in categories.items() if k != "other")
    total = sum(len(v) for v in categories.values())

    return {
        "tool": "PCBCool PCB File Checker",
        "version": VERSION,
        "source": str(root),
        "assembly_mode": assembly,
        "summary": {
            "total_files": total,
            "recognized_files": recognized,
            "unclassified_files": len(categories.get("other", [])),
            "has_copper": has_copper,
            "has_outline": has_outline,
            "has_drill": has_drill,
            "has_solder_mask": has_mask,
            "has_bom": has_bom,
            "has_placement": has_placement,
        },
        "categories": {k: v for k, v in categories.items() if v},
        "issues": issues,
        "disclaimer": (
            "Presence and naming check only. This tool does not parse Gerber geometry, "
            "run DRC, verify impedance or stackup data, or replace a PCB manufacturer DFM review."
        ),
    }


def print_human(report: dict[str, object]) -> None:
    print(f"PCBCool PCB File Checker v{report['version']}")
    print("=" * 48)
    print(f"Source: {report['source']}")
    print(f"Assembly checks: {'enabled' if report['assembly_mode'] else 'disabled'}")
    print()

    categories = report["categories"]
    assert isinstance(categories, dict)

    if not categories:
        print("No files found.")
    else:
        print("Detected files")
        print("--------------")
        ordered_keys = [k for k in CATEGORY_LABELS if k in categories]
        for key in ordered_keys:
            files = categories[key]
            print(f"\n{CATEGORY_LABELS.get(key, key)} ({len(files)}):")
            for filename in files:
                print(f"  - {filename}")

    print("\nPreflight result")
    print("----------------")
    issues = report["issues"]
    assert isinstance(issues, list)
    if issues:
        for issue in issues:
            print(f"[{issue['severity']}] {issue['message']}")
    else:
        print("[PASS] No missing-file warnings were detected by this basic naming check.")

    print("\nNote")
    print("----")
    print(report["disclaimer"])


def inspect_input(input_path: Path, assembly: bool) -> dict[str, object]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    if input_path.is_dir():
        return inspect_directory(input_path, assembly)

    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory(prefix="pcb-file-checker-") as temp_dir:
            temp_path = Path(temp_dir)
            with zipfile.ZipFile(input_path) as archive:
                # Prevent ZIP path traversal.
                for member in archive.infolist():
                    target = (temp_path / member.filename).resolve()
                    if temp_path.resolve() not in target.parents and target != temp_path.resolve():
                        raise ValueError(f"Unsafe path in ZIP archive: {member.filename}")
                archive.extractall(temp_path)
            report = inspect_directory(temp_path, assembly)
            report["source"] = str(input_path)
            return report

    raise ValueError("Input must be a directory or a .zip archive.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check a PCB package for common Gerber, drill, BOM, and pick-and-place files. "
            "The default container path is /data."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="/data",
        help="Directory or ZIP archive to inspect (default: /data)",
    )
    parser.add_argument(
        "--assembly",
        action="store_true",
        help="Also require a BOM and check for a pick-and-place file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of the human-readable report.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = inspect_input(Path(args.path), args.assembly)
    except (FileNotFoundError, ValueError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_human(report)

    issues = report["issues"]
    assert isinstance(issues, list)
    return 1 if any(issue["severity"] == "ERROR" for issue in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
