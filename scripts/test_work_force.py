import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
from scipy.integrate import trapezoid

df = pd.read_csv('results/phase3_full_mesoscale/PUNCTURE_MESOFULLT01.csv')
cols = [c.strip().strip('"') for c in df.columns]
df.columns = cols

t = df['time'].to_numpy()
d_col = [c for c in cols if 'PUNCH_DISP' in c][0]
d = np.abs(df[d_col].to_numpy())
w = df['EXTERNAL WORK'].to_numpy()

# Smooth work
w_smooth = savgol_filter(w, 31, 3)
dw = np.diff(w_smooth, prepend=w_smooth[0])
dd = np.diff(d, prepend=d[0])

mask = dd > 1e-6
f_n = np.zeros_like(d)
f_n[mask] = dw[mask] / dd[mask]
f_kn = (f_n / 1000.0) * 4.0 # Full model force

# filter
f_kn_smooth = savgol_filter(f_kn, 21, 2)
f_kn_smooth = np.maximum(f_kn_smooth, 0.0)

print(f"Max Force from Work: {np.max(f_kn_smooth):.2f} kN at d = {d[np.argmax(f_kn_smooth)]:.2f} mm")

df_exp = pd.read_csv('experimental/force_displacement/experiment.csv')
d_exp = df_exp['displacement_mm'].to_numpy()
f_exp = df_exp['force_N'].to_numpy() / 1000.0

print(f"{'Disp (mm)':>10} | {'F_sim (kN)':>12} | {'F_exp (kN)':>12} | {'Diff (%)':>10}")
print("-" * 55)

for target_d in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.38, 5.7]:
    idx_s = np.argmin(np.abs(d - target_d))
    idx_e = np.argmin(np.abs(d_exp - target_d))
    diff = (f_kn_smooth[idx_s] - f_exp[idx_e]) / f_exp[idx_e] * 100.0 if f_exp[idx_e] > 0 else 0
    print(f"{target_d:>10.2f} | {f_kn_smooth[idx_s]:>12.2f} | {f_exp[idx_e]:>12.2f} | {diff:>9.1f}%")
