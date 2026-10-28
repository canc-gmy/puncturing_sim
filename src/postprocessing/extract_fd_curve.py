"""
Force-Displacement Extraction Module (v2.2)
Extracts indenter displacement and force history from OpenCourant T01 output,
computing both contact reaction force and energy-gradient work force.
Supports quarter-symmetry 4x scaling and quasi-static velocity kinematics.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import sys
from scipy.signal import savgol_filter

def extract_fd(
    csv_path: Path,
    out_csv: Path,
    v_punch: float = 1000.0,
    scale_factor: float = 4.0,
    use_work_force: bool = False
) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().strip('"') for c in df.columns]
    if 'EXTERNAL WORK' in df.columns:
        df = df[df['EXTERNAL WORK'] < 1e8].copy()
    if 'time' in df.columns and len(df) > 10:
        if df['time'].iloc[-1] <= df['time'].iloc[-2] or (df['time'].iloc[-1] - df['time'].iloc[-2]) < 0.5 * (df['time'].iloc[-2] - df['time'].iloc[-3]):
            df = df.iloc[:-1].copy()

    time_s = df['time'].to_numpy()

    # 1. Displacement extraction
    disp_cols = [c for c in df.columns if 'PUNCH_DISP' in c or 'DZ' in c]
    if disp_cols:
        disp_mm = np.abs(df[disp_cols[0]].to_numpy())
        # If in seconds due to constant velocity scaling:
        if np.max(disp_mm) <= 0.05:
            disp_mm = time_s * v_punch
    else:
        disp_mm = time_s * v_punch

    # 2. Force extraction
    force_cols = [c for c in df.columns if 'PUNCH_FORCE' in c or 'FZ' in c or 'REACZ' in c]
    direct_force_found = False

    if not use_work_force and force_cols:
        raw_force = np.abs(df[force_cols[0]].to_numpy())
        if np.max(raw_force) > 0.1:
            direct_force_found = True
            # OpenRadioss /TH/RBODY output convention check:
            # If max > 500, units are N; if max <= 500, units are already kN.
            if np.max(raw_force) > 500.0:
                force_kn = raw_force / 1000.0
            else:
                force_kn = raw_force.copy()

    if not direct_force_found or use_work_force:
        # Calculate from external work or internal energy rate: F = dW / d(disp)
        if 'EXTERNAL WORK' in df.columns and np.max(df['EXTERNAL WORK']) > 1.0:
            w_mj = df['EXTERNAL WORK'].to_numpy() # N*mm = mJ
        else:
            w_mj = df['INTERNAL ENERGY'].to_numpy()
        
        # Smooth work curve to avoid discretization noise in derivative
        if len(w_mj) > 31:
            w_smooth = savgol_filter(w_mj, window_length=31, polyorder=3)
        else:
            w_smooth = w_mj

        dw = np.diff(w_smooth, prepend=w_smooth[0])
        dd = np.diff(disp_mm, prepend=disp_mm[0])
        force_n = np.zeros_like(disp_mm)
        mask = dd > 1e-6
        force_n[mask] = dw[mask] / dd[mask]
        force_kn = force_n / 1000.0

    # Scale reaction force and energy for quarter symmetry
    force_kn = force_kn * scale_factor

    # 3. Detect complete puncture perforation from external work plateau (if not direct force)
    if not direct_force_found and not use_work_force and 'EXTERNAL WORK' in df.columns:
        w = df['EXTERNAL WORK'].to_numpy()
        dw = np.diff(w, prepend=w[0])
        dd = np.diff(disp_mm, prepend=disp_mm[0])
        work_rate = np.zeros_like(disp_mm)
        mask = dd > 1e-6
        work_rate[mask] = dw[mask] / dd[mask]
        
        rupture_idx = None
        for i in range(len(disp_mm) - 1, 15, -1):
            if work_rate[i] > 100.0: # active work > 0.1 kN
                rupture_idx = i
                break
                
        if rupture_idx is not None and rupture_idx < len(disp_mm) - 5:
            # Sandwich completely punctured: force drops to zero as punch moves freely
            for k in range(1, 5):
                force_kn[rupture_idx + k] *= (1.0 - k / 5.0)
            force_kn[rupture_idx + 5:] = 0.0

    # 4. Filter high-frequency vibrations while preserving rupture
    if len(force_kn) > 15:
        w_len = min(21, len(force_kn) if len(force_kn) % 2 != 0 else len(force_kn) - 1)
        force_kn_smooth = savgol_filter(force_kn, window_length=w_len, polyorder=2)
        force_kn_smooth = np.maximum(force_kn_smooth, 0.0)
    else:
        force_kn_smooth = force_kn

    force_n_smooth = force_kn_smooth * 1000.0
    internal_energy_j = (df['INTERNAL ENERGY'].to_numpy() / 1000.0 * scale_factor) if 'INTERNAL ENERGY' in df.columns else np.zeros_like(disp_mm)

    result_df = pd.DataFrame({
        'displacement_mm': np.round(disp_mm, 4),
        'force_kN': np.round(force_kn_smooth, 4),
        'force_N': np.round(force_n_smooth, 2),
        'internal_energy_J': np.round(internal_energy_j, 4),
    })

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(out_csv, index=False)
    print(f"Extracted Force-Displacement curve saved to: {out_csv}")
    print(f"Peak Force: {np.max(force_kn_smooth):.2f} kN at {disp_mm[np.argmax(force_kn_smooth)]:.2f} mm")
    absorbed_energy = np.trapezoid(force_n_smooth, disp_mm * 1e-3)
    print(f"Absorbed Energy: {absorbed_energy:.2f} J")
    return result_df

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parents[2]
    target = sys.argv[1] if len(sys.argv) > 1 else "phase1"
    use_work = False
    if target.lower() == "phase2":
        t01_csv = base_dir / "results" / "phase2_mesoscale" / "PUNCTURE_MESOT01.csv"
        fd_out = base_dir / "results" / "phase2_mesoscale" / "simulation_fd.csv"
    elif target.lower() == "phase3":
        t01_csv = base_dir / "results" / "phase3_full_mesoscale" / "PUNCTURE_MESOFULLT01.csv"
        fd_out = base_dir / "results" / "phase3_full_mesoscale" / "simulation_fd.csv"
        use_work = True
    else:
        t01_csv = base_dir / "results" / "phase1_homogenized" / "PUNCTURE_HOMOGT01.csv"
        fd_out = base_dir / "results" / "phase1_homogenized" / "simulation_fd.csv"

    if t01_csv.exists():
        extract_fd(t01_csv, fd_out, use_work_force=use_work)
    else:
        print(f"File not found: {t01_csv}")
