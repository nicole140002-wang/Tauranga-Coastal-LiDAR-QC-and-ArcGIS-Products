# -*- coding: utf-8 -*-
"""
Corrected intensity QC — exclude synthetic class 42 points
==========================================================
Finding: class 42 (derived/synthetic water surface) points are all assigned
intensity = 65530 by the processing pipeline. They are NOT real laser returns.
Including them in the mean/p95 inflates the intensity stats and falsely suggests
"sensor saturation" or "near-IR absorbed by water".

This script recomputes:
  - per-class intensity median / p5 / p95 / n
  - overall intensity stats excluding class 42
  - comparison: with vs without class 42
"""
import laspy
import numpy as np
import json, os, glob

SRC = r"D:\GIS_Portfolio\Lidar_demo\raw_data\export\new-zealand-coastal-lidar-point-cloud"
OUT = r"D:\GIS_Portfolio\Lidar_demo\processed"
os.makedirs(OUT, exist_ok=True)

CLASS_NAMES = {
    1: "Unclassified", 2: "Ground", 3: "Low veg", 4: "Med veg", 5: "High veg",
    6: "Building", 7: "Low noise", 9: "Water surface (topo)", 17: "Bridge",
    18: "High noise", 40: "Seabed", 41: "Water surface (refraction)",
    42: "Derived water surface (SYNTHETIC)", 43: "Submerged object", 45: "Bathy noise",
}

files = sorted(glob.glob(os.path.join(SRC, "*.las")))

# accumulate per-class intensity arrays
per_class = {}
all_inten_with42 = []
all_inten_no42 = []

for f in files:
    las = laspy.read(f, laz_backend=laspy.LazBackend.Laszip)
    cls = np.asarray(las.classification)
    inten = np.asarray(las.intensity)
    all_inten_with42.append(inten)
    all_inten_no42.append(inten[cls != 42])
    for c in np.unique(cls):
        c = int(c)
        per_class.setdefault(c, []).append(inten[cls == c])
    del las

# combine
all_with = np.concatenate(all_inten_with42)
all_no = np.concatenate(all_inten_no42)

print("=" * 70)
print("INTENSITY QC — corrected (excluding synthetic class 42)")
print("=" * 70)
print(f"\nTotal points: {len(all_with):,}")
print(f"Class 42 (synthetic) points: {len(all_with) - len(all_no):,}")

print(f"\n--- Overall intensity ---")
print(f"  WITH class 42:    mean={all_with.mean():.0f}  p50={np.median(all_with):.0f}  p95={np.percentile(all_with,95):.0f}  max={all_with.max()}")
print(f"  WITHOUT class 42: mean={all_no.mean():.0f}  p50={np.median(all_no):.0f}  p95={np.percentile(all_no,95):.0f}  max={all_no.max()}")

print(f"\n--- Per-class intensity (median, p5, p95, n) ---")
results = {}
for c in sorted(per_class.keys()):
    arr = np.concatenate(per_class[c])
    name = CLASS_NAMES.get(c, f"class {c}")
    med = float(np.median(arr))
    p5 = float(np.percentile(arr, 5))
    p95 = float(np.percentile(arr, 95))
    mx = float(arr.max())
    n = len(arr)
    results[c] = {"name": name, "n": n, "median": round(med,1), "p5": round(p5,1), "p95": round(p95,1), "max": round(mx,1)}
    print(f"  class {c:2d} {name:35s} n={n:>10,}  median={med:>7.0f}  p5={p5:>7.0f}  p95={p95:>7.0f}  max={mx:>6.0f}")

# check: are class 42 points ALL 65530?
c42 = np.concatenate(per_class[42])
print(f"\n--- Class 42 sanity check ---")
print(f"  unique values in class 42: {np.unique(c42)[:10]}")
print(f"  fraction == 65530: {(c42 == 65530).mean():.2%}")

out = {
    "total_points": int(len(all_with)),
    "class42_points": int(len(all_with) - len(all_no)),
    "with_class42": {"mean": round(float(all_with.mean()),1), "p50": round(float(np.median(all_with)),1), "p95": round(float(np.percentile(all_with,95)),1), "max": int(all_with.max())},
    "without_class42": {"mean": round(float(all_no.mean()),1), "p50": round(float(np.median(all_no)),1), "p95": round(float(np.percentile(all_no,95)),1), "max": int(all_no.max())},
    "per_class": results,
    "class42_all_65530": bool((c42 == 65530).all()),
}
with open(os.path.join(OUT, "intensity_corrected.json"), "w") as fh:
    json.dump(out, fh, indent=2)
print(f"\nsaved: intensity_corrected.json")
