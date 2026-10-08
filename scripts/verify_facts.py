# -*- coding: utf-8 -*-
"""Verify GPS time, scan angle, extreme Z class, and tile contiguity."""
import laspy, numpy as np, glob, os

SRC = r"D:\GIS_Portfolio\Lidar_demo\raw_data\export\new-zealand-coastal-lidar-point-cloud"
files = sorted(glob.glob(os.path.join(SRC, "*.las")))

for f in files:
    las = laspy.read(f, laz_backend=laspy.LazBackend.Laszip)
    h = las.header
    print(f"\n=== {os.path.basename(f)} ===")
    print(f"  global_encoding: {h.global_encoding}")
    # bit 0 = GPS time type: 0 = GPS Standard Time, 1 = Adjusted Standard GPS Time
    gps_bit = h.global_encoding.gps_time_type
    print(f"  GPS time type (0=GPS Standard, 1=Adjusted Standard): {gps_bit}")
    gt = np.asarray(las.gps_time)
    print(f"  GPS time range: {gt.min():.3f} .. {gt.max():.3f}")
    # Standard GPS time: seconds since 1980-01-06
    # Adjusted: same epoch but with leap seconds handling
    # Try decode as standard GPS time (seconds since 1980-01-06 00:00:00 UTC)
    from datetime import datetime, timedelta
    epoch = datetime(1980, 1, 6)
    try:
        t0 = epoch + timedelta(seconds=float(gt.min()))
        t1 = epoch + timedelta(seconds=float(gt.max()))
        print(f"  decoded (GPS Standard): {t0.isoformat()} .. {t1.isoformat()}")
    except Exception as e:
        print(f"  decode err: {e}")
    # scan angle
    sa = np.asarray(las.scan_angle)
    print(f"  scan angle min/max: {sa.min()} / {sa.max()}")
    # extreme Z class
    z = np.asarray(las.z)
    cls = np.asarray(las.classification)
    i_min = z.argmin()
    i_max = z.argmax()
    print(f"  z min {z.min():.2f} -> class {cls[i_min]}")
    print(f"  z max {z.max():.2f} -> class {cls[i_max]}")
    # bbox
    x = np.asarray(las.x); y = np.asarray(las.y)
    print(f"  bbox x: {x.min():.1f} .. {x.max():.1f}")
    print(f"  bbox y: {y.min():.1f} .. {y.max():.1f}")
    del las
