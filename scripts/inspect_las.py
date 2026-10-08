# -*- coding: utf-8 -*-
"""Inspect LAS headers for the 3DCM Tauranga Harbour export."""
import laspy, glob, os, json

files = sorted(glob.glob(r"D:\GIS_Portfolio\Lidar_demo\raw_data\export\new-zealand-coastal-lidar-point-cloud\*.las"))
print("files:", len(files))
for f in files:
    las = laspy.read(f, laz_backend=laspy.LazBackend.Laszip)
    h = las.header
    with open(f, "rb") as fh:
        sig = fh.read(4)
    compressed = sig in (b"LAZ", b"laz ") or sig[:3] == b"LAZ"
    print("=" * 70)
    print(os.path.basename(f))
    print(f"  point_format: {h.point_format.id}  compressed: {compressed}  version: {h.version}")
    print(f"  points: {h.point_count:,}")
    print(f"  scales: {h.scales}  offsets: {h.offsets}")
    print(f"  mins: {h.mins}  maxs: {h.maxs}")
    # CRS via VLR
    wkt = None
    for vlr in las.header.vlrs:
        if vlr.record_id in (2111, 2112) or "WKT" in str(vlr):
            wkt = str(vlr)[:120]
    print(f"  vlr_count: {len(las.header.vlrs)}  crs_hint: {wkt}")
    # dims
    dims = [d.name for d in las.point_format.dimensions]
    print(f"  dims: {dims}")
    # sample class counts
    cls, cnt = las.classification.copy(), None
    import numpy as np
    vals, counts = np.unique(cls, return_counts=True)
    print(f"  classes: {dict(zip(vals.tolist(), counts.tolist()))}")
    print(f"  flags: synthetic={int((cls >> 5) & 1).__bool__() if False else 'n/a'}")
    for fld in ("synthetic", "withheld", "key_point", "overlap"):
        try:
            arr = getattr(las, fld)
            print(f"  {fld}: {int(arr.sum())}")
        except Exception as e:
            print(f"  {fld}: err")
    print(f"  z range: {las.z.min():.3f} .. {las.z.max():.3f}")
