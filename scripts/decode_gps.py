# -*- coding: utf-8 -*-
"""Diagnose GPS time decode for the 4 LAS tiles."""
import laspy, numpy as np, glob, os
from datetime import datetime, timedelta

SRC = r"D:\GIS_Portfolio\Lidar_demo\raw_data\export\new-zealand-coastal-lidar-point-cloud"
files = sorted(glob.glob(os.path.join(SRC, "*.las")))

# ASPRS: GPS time = seconds since 1980-01-06 00:00:00 UTC (GPS standard)
# Adjusted Standard GPS Time: same epoch, but leap seconds removed -> UTC-based
GPS_EPOCH = datetime(1980, 1, 6)

for f in files[:1]:  # just first tile
    las = laspy.read(f, laz_backend=laspy.LazBackend.Laszip)
    gt = np.asarray(las.gps_time)
    print(f"File: {os.path.basename(f)}")
    print(f"  raw gps_time min/max: {gt.min():.3f} / {gt.max():.3f}")
    print(f"  header gps_time_type: {las.header.global_encoding.gps_time_type}")
    # Standard decode
    t0 = GPS_EPOCH + timedelta(seconds=float(gt.min()))
    t1 = GPS_EPOCH + timedelta(seconds=float(gt.max()))
    print(f"  decode (epoch 1980-01-06): {t0.isoformat()} .. {t1.isoformat()}")
    # Try: maybe values are in milliseconds?
    s_min = float(gt.min()) / 1000.0
    s_max = float(gt.max()) / 1000.0
    print(f"  if milliseconds: {GPS_EPOCH + timedelta(seconds=s_min)} .. {GPS_EPOCH + timedelta(seconds=s_max)}")
    # Try: 1993 epoch (sometimes vendors use a recent epoch)
    for epoch_year in [1970, 1980, 1990, 1993, 2000]:
        ep = datetime(epoch_year, 1, 1)
        d0 = ep + timedelta(seconds=float(gt.min()))
        d1 = ep + timedelta(seconds=float(gt.max()))
        print(f"  epoch {epoch_year}-01-01: {d0.isoformat()} .. {d1.isoformat()}")
    # What value would 2025-01-28 be?
    target = datetime(2025, 1, 28)
    offset = (target - GPS_EPOCH).total_seconds()
    print(f"  expected seconds for 2025-01-28 from 1980 epoch: {offset:.0f}")
    print(f"  observed min: {gt.min():.0f}, diff: {gt.min()-offset:.0f}")
