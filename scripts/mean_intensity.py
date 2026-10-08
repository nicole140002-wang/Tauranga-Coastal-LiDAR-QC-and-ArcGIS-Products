# -*- coding: utf-8 -*-
import laspy, numpy as np, glob, os
SRC = r"D:\GIS_Portfolio\Lidar_demo\raw_data\export\new-zealand-coastal-lidar-point-cloud"
files = sorted(glob.glob(os.path.join(SRC, "*.las")))
sum_int = 0
n_total = 0
n_no42 = 0
sum_no42 = 0
for f in files:
    las = laspy.read(f, laz_backend=laspy.LazBackend.Laszip)
    cls = np.asarray(las.classification)
    inten = np.asarray(las.intensity)
    n = len(inten)
    n_total += n
    sum_int += int(inten.sum())
    mask42 = cls == 42
    n_no42 += int((~mask42).sum())
    sum_no42 += int(inten[~mask42].sum())
    print(f"{os.path.basename(f)}: n={n}, sum={sum_int}")
print(f"\nTotal: {n_total}")
print(f"All-records mean intensity: {sum_int/n_total:.1f}")
print(f"Excl class 42: n={n_no42}, mean={sum_no42/n_no42:.1f}")
