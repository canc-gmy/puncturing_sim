"""
Force-Displacement Extraction Module
Extracts indenter displacement and force history from OpenCourant T01 output,
computing both contact reaction force and energy-gradient work force.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import sys
from scipy.signal import savgol_filter

def extract_fd(csv_path: Path, out_csv: Path, v_punch: float = 1000.0) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().strip('"') for c in df.columns]

    time_s = df['time'].to_numpy()

    # Check for direct displacement column
    disp_cols = [c for c in df.columns if 'PUNCH_DISP' in c or 'DZ' in c]
    if disp_cols:
        disp_mm = np.abs(df[disp_cols[0]].to_numpy())
        # If in seconds due to constant velocity scaling:
        if np.max(disp_mm) <= 0.05:
            disp_mm = time_s * v_punch
    else:
        disp_mm = time_s * v_punch

    # Check for direct force column (FZ or REACZ)
    force_cols = [c for c in df.columns if 'PUNCH_FORCE' in c or 'FZ' in c or 'REACZ' in c]
    direct_force_found = False
    if force_cols:
        raw_force = np.abs(df[force_cols[0]].to_numpy())
        if np.max(raw_force) > 1.0:
            force_n = raw_force
            direct_force_found = True

    if not direct_force_found:
        # Calculate from internal energy rate: F = dE / d(disp)
        e_int_mj = df['INTERNAL ENERGY'].to_numpy()
        force_n = np.zeros_like(disp_mm)
        for i in range(1, len(disp_mm)):
            dd = disp_mm[i] - disp_mm[i-1]
            de = e_int_mj[i] - e_int_mj[i-1]
            if dd > 1e-8:
                force_n[i] = de / dd
            else:
                force_n[i] = force_n[i-1]

    # Filter out numerical high-frequency vibrations
    if len(force_n) > 15:
        w_len = min(31, len(force_n) if len(force_n) % 2 != 0 else len(force_n) - 1)
        force_n_smooth = savgol_filter(force_n, window_length=w_len, polyorder=2)
        force_n_smooth = np.maximum(force_n_smooth, 0.0)
    else:
        force_n_smooth = force_n

    force_kn = force_n_smooth / 1000.0

    internal_energy_j = df['INTERNAL ENERGY'].to_numpy() / 1000.0 if 'INTERNAL ENERGY' in df.columns else np.zeros_like(disp_mm)

    result_df = pd.DataFrame({
        'displacement_mm': np.round(disp_mm, 4),
        'force_kN': np.round(force_kn, 4),
        'force_N': np.round(force_n_smooth, 2),
        'internal_energy_J': np.round(internal_energy_j, 4),
    })

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(out_csv, index=False)
    print(f"Extracted Force-Displacement curve saved to: {out_csv}")
    print(f"Peak Force: {np.max(force_kn):.2f} kN at {disp_mm[np.argmax(force_kn)]:.2f} mm")
    return result_df

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parents[2]
    target = sys.argv[1] if len(sys.argv) > 1 else "phase1"
    if target.lower() == "phase2":
        t01_csv = base_dir / "results" / "phase2_mesoscale" / "PUNCTURE_MESOT01.csv"
        fd_out = base_dir / "results" / "phase2_mesoscale" / "simulation_fd.csv"
    else:
        t01_csv = base_dir / "results" / "phase1_homogenized" / "PUNCTURE_HOMOGT01.csv"
        fd_out = base_dir / "results" / "phase1_homogenized" / "simulation_fd.csv"

    if t01_csv.exists():
        extract_fd(t01_csv, fd_out)
    else:
        print(f"File not found: {t01_csv}")
