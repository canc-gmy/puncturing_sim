import pandas as pd
import numpy as np

df2 = pd.read_csv('results/phase2_mesoscale/PUNCTURE_MESOT01.csv')
c31_2 = [c for c in df2.columns if 'PUNCH_FORCE' in c][0]
d_col2 = [c for c in df2.columns if 'PUNCH_DISP' in c][0]

df3 = pd.read_csv('results/phase3_full_mesoscale/PUNCTURE_MESOFULLT01.csv')
c31_3 = [c for c in df3.columns if 'PUNCH_FORCE' in c][0]
d_col3 = [c for c in df3.columns if 'PUNCH_DISP' in c][0]

print("Phase 2:")
print(f"Max disp: {df2[d_col2].abs().max():.3f} mm")
print(f"Max raw PUNCH_FORCE: {df2[c31_2].abs().max():.3f}")
print(f"Max External Work: {df2['EXTERNAL WORK'].max():.2f}")

print("\nPhase 3:")
print(f"Max disp: {df3[d_col3].abs().max():.3f} mm")
print(f"Max raw PUNCH_FORCE: {df3[c31_3].abs().max():.3f}")
print(f"Max External Work: {df3['EXTERNAL WORK'].max():.2f}")
