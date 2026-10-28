import pandas as pd
import numpy as np

df = pd.read_csv('results/phase3_full_mesoscale/PUNCTURE_MESOFULLT01.csv')
cols = [c.strip().strip('"') for c in df.columns]
df.columns = cols

t = df['time'].to_numpy()
d = np.abs(df[[c for c in cols if 'PUNCH_DISP' in c][0]].to_numpy())

print("Time, Disp, Var 24, Var 25, Var 26, Var 31, ExtWork, IntEnergy")
for i in range(0, len(df), len(df)//20):
    v24 = df[cols[24]].iloc[i]
    v25 = df[cols[25]].iloc[i]
    v26 = df[cols[26]].iloc[i]
    v31 = df[cols[31]].iloc[i]
    w = df['EXTERNAL WORK'].iloc[i]
    ie = df['INTERNAL ENERGY'].iloc[i]
    print(f"t={t[i]*1000:5.2f}ms | d={d[i]:5.2f}mm | v24={v24:10.2f} | v25={v25:10.2f} | v26={v26:10.2f} | v31={v31:10.2f} | W={w:10.2f} | IE={ie:10.2f}")
