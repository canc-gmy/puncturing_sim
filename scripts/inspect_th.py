import pandas as pd
import numpy as np

df = pd.read_csv('results/phase3_full_mesoscale/PUNCTURE_MESOFULLT01.csv')
cols = [c.strip().strip('"') for c in df.columns]
df.columns = cols

t = df['time'].to_numpy()
w = df['EXTERNAL WORK'].to_numpy()
ie = df['INTERNAL ENERGY'].to_numpy()
ke = df['KINETIC ENERGY'].to_numpy()
ce = df['CONTACT ENERGY'].to_numpy()
disp_col = [c for c in cols if 'PUNCH_DISP' in c][0]
d = np.abs(df[disp_col].to_numpy())

# F_work
from scipy.signal import savgol_filter
if len(w) > 31:
    w_smooth = savgol_filter(w, 31, 3)
else:
    w_smooth = w

dw = np.diff(w_smooth, prepend=w_smooth[0])
dd = np.diff(d, prepend=d[0])
mask = dd > 1e-6
f_work = np.zeros_like(d)
f_work[mask] = dw[mask] / dd[mask] * 4.0 / 1000.0 # Full model force in kN

die = np.diff(ie, prepend=ie[0])
f_ie = np.zeros_like(d)
f_ie[mask] = die[mask] / dd[mask] * 4.0 / 1000.0

print(f"{'Time (ms)':>10} | {'Disp (mm)':>10} | {'F_work (kN)':>12} | {'F_ie (kN)':>12} | {'IE (J)':>10} | {'KE (J)':>10} | {'CE (J)':>10}")
print("-" * 85)

for target_d in np.arange(0.5, 6.1, 0.5):
    idx = np.argmin(np.abs(d - target_d))
    print(f"{t[idx]*1000:>10.2f} | {d[idx]:>10.3f} | {f_work[idx]:>12.2f} | {f_ie[idx]:>12.2f} | {ie[idx]*4/1000:>10.2f} | {ke[idx]*4/1000:>10.2f} | {ce[idx]*4/1000:>10.2f}")

print(f"{t[-1]*1000:>10.2f} | {d[-1]:>10.3f} | {f_work[-1]:>12.2f} | {f_ie[-1]:>12.2f} | {ie[-1]*4/1000:>10.2f} | {ke[-1]*4/1000:>10.2f} | {ce[-1]*4/1000:>10.2f}")
