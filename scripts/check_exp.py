import pandas as pd
import numpy as np

df_exp = pd.read_csv('experimental/force_displacement/experiment.csv')
print(f"Total rows: {len(df_exp)}")
print(f"Max disp: {df_exp['displacement_mm'].max():.2f} mm")
print(f"Max force: {df_exp['force_N'].max():.2f} N at {df_exp.loc[df_exp['force_N'].idxmax()]['displacement_mm']:.2f} mm")

# print every 20 rows
for i in range(0, len(df_exp), 20):
    row = df_exp.iloc[i]
    print(f"d = {row['displacement_mm']:5.2f} mm | F = {row['force_N']/1000.0:6.2f} kN")
print(f"Final: d = {df_exp.iloc[-1]['displacement_mm']:5.2f} mm | F = {df_exp.iloc[-1]['force_N']/1000.0:6.2f} kN")
