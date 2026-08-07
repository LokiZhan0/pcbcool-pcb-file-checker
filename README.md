# PCBCool PCB File Checker

A lightweight container that checks whether a PCB manufacturing package appears to include the common files needed for quotation and engineering review.

It recognizes common Gerber, Excellon drill, board outline, BOM, and pick-and-place naming patterns. The tool is intended as a quick packaging check before files are submitted to a PCB manufacturer.

## What it checks

- Top, bottom, inner, and generic copper Gerber files
- Board outline or mechanical profile files
- Excellon and commonly named drill files
- Top and bottom solder mask files
- Silkscreen and solder paste files
- BOM files
- Pick-and-place, centroid, or component-position files
- ZIP archives as well as normal folders

## Important limitation

This is a **file-presence and naming check only**. It does not parse Gerber geometry, perform DRC, verify controlled impedance or stackup data, inspect aperture definitions, or replace a PCB manufacturer's DFM review.

## Quick start

Replace `lokizhan` with your Docker Hub username if you registered a different Docker ID.

### Windows PowerShell

Run the following commands from the folder containing your Gerber files:

```powershell
$pcbFiles = (Get-Location).Path
docker run --rm -v "${pcbFiles}:/data:ro" lokizhan/pcb-file-checker:latest
```

### macOS or Linux

```bash
docker run --rm -v "$PWD:/data:ro" lokizhan/pcb-file-checker:latest
```

## Check a ZIP archive

Mount the folder containing the ZIP file and pass the ZIP path inside the container:

```powershell
$folder = (Get-Location).Path
docker run --rm -v "${folder}:/data:ro" lokizhan/pcb-file-checker:latest /data/gerber-package.zip
```

## Include PCB assembly checks

The `--assembly` option also checks for a BOM and a pick-and-place file:

```powershell
$pcbFiles = (Get-Location).Path
docker run --rm -v "${pcbFiles}:/data:ro" lokizhan/pcb-file-checker:latest /data --assembly
```

## JSON output

Use `--json` when the result needs to be consumed by another script or CI workflow:

```powershell
$pcbFiles = (Get-Location).Path
docker run --rm -v "${pcbFiles}:/data:ro" lokizhan/pcb-file-checker:latest /data --assembly --json
```

## Example output

```text
PCBCool PCB File Checker v1.0.0
================================================
Source: /data
Assembly checks: enabled

Detected files
--------------

Top copper (1):
  - demo-F_Cu.gtl

Bottom copper (1):
  - demo-B_Cu.gbl

Board outline / mechanical (1):
  - demo-Edge_Cuts.gm1

Drill / Excellon (1):
  - demo-PTH.drl

Bill of materials (1):
  - demo-bom.csv

Pick-and-place / centroid (1):
  - demo-pick-and-place.csv

Preflight result
----------------
[PASS] No missing-file warnings were detected by this basic naming check.
```

## Build the image locally

```bash
docker build -t lokizhan/pcb-file-checker:latest .
```

## Exit codes

- `0`: no required-file errors were found
- `1`: one or more required-file errors were found
- `2`: invalid path, invalid ZIP archive, or another input error

## About PCBCool

This open utility is maintained by [PCBCool](https://pcbcool.com/), an online platform for custom PCB manufacturing and PCB assembly. Gerber files can be configured and submitted through the [PCBCool online PCB quotation system](https://pcbcool.com/quote/).

## License

MIT License. See `LICENSE` for details.
