import pandas as pd
import numpy as np

df_sim = pd.read_csv('results/phase3_full_mesoscale/PUNCTURE_MESOFULLT01.csv')
cols = [c.strip().strip('"') for c in df_sim.columns]
df_sim.columns = cols

d_col = [c for c in cols if 'PUNCH_DISP' in c][0]
f_col = [c for c in cols if 'PUNCH_FORCE' in c][0]

d_sim = np.abs(df_sim[d_col].to_numpy())
f_sim_quarter = np.abs(df_sim[f_col].to_numpy())
f_sim_full = f_sim_quarter * 4.0 # Full model force in kN

df_exp = pd.read_csv('experimental/force_displacement/experiment.csv')
d_exp = df_exp['displacement_mm'].to_numpy()
f_exp = df_exp['force_N'].to_numpy() / 1000.0

print(f"{'Disp (mm)':>10} | {'F_sim (kN)':>12} | {'F_exp (kN)':>12} | {'Diff (%)':>10}")
print("-" * 55)

for target_d in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.38, 5.7]:
    idx_s = np.argmin(np.abs(d_sim - target_d))
    idx_e = np.argmin(np.abs(d_exp - target_d))
    diff = (f_sim_full[idx_s] - f_exp[idx_e]) / f_exp[idx_e] * 100.0 if f_exp[idx_e] > 0 else 0
    print(f"{target_d:>10.2f} | {f_sim_full[idx_s]:>12.2f} | {f_exp[idx_e]:>12.2f} | {diff:>9.1f}%")

print(f"Max Exp Force: {np.max(f_exp):.2f} kN at {d_exp[np.argmax(f_exp)]:.2f} mm")
print(f"Max Sim Force: {np.max(f_sim_full):.2f} kN at {d_sim[np.argmax(f_sim_full)]:.2f} mm")
