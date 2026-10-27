"""
Model vs Experiment Correlation Module
Calculates error metrics:
- Peak force error (%)
- Absorbed energy error (%)
- Sprague-Geers validation metrics: Magnitude error M, Phase error P, Comprehensive error C (ISO / ASME V&V standard)
and produces publication-quality overlay plots comparing Experiment, Phase 1, Phase 2, and Phase 3.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import trapezoid

def compute_sprague_geers(d_exp: np.ndarray, f_exp: np.ndarray, d_sim: np.ndarray, f_sim: np.ndarray) -> dict:
    """
    Computes Sprague-Geers metrics (M, P, C) over the common displacement range.
    """
    d_max = min(float(np.max(d_exp)), float(np.max(d_sim)))
    d_common = np.linspace(0.0, d_max, 500)
    
    m = np.interp(d_common, d_exp, f_exp)
    c = np.interp(d_common, d_sim, f_sim)
    
    I_mm = trapezoid(m**2, d_common)
    I_cc = trapezoid(c**2, d_common)
    I_mc = trapezoid(m * c, d_common)
    
    if I_mm <= 1e-12 or I_cc <= 1e-12:
        return {
            "sprague_geers_M_pct": 0.0,
            "sprague_geers_P_pct": 0.0,
            "sprague_geers_C_pct": 0.0,
            "M": 0.0, "P": 0.0, "C": 0.0
        }
    
    M = np.sqrt(I_cc / I_mm) - 1.0
    denom = np.sqrt(I_mm * I_cc)
    cos_val = np.clip(I_mc / denom, -1.0, 1.0)
    P = (1.0 / np.pi) * np.arccos(cos_val)
    C = np.sqrt(M**2 + P**2)
    
    return {
        "sprague_geers_M_pct": round(float(M * 100.0), 2),
        "sprague_geers_P_pct": round(float(P * 100.0), 2),
        "sprague_geers_C_pct": round(float(C * 100.0), 2),
        "M": round(float(M), 4),
        "P": round(float(P), 4),
        "C": round(float(C), 4)
    }

def evaluate_all(exp_csv: Path, p1_csv: Path = None, p2_csv: Path = None, p3_csv: Path = None, out_plot: Path = None, out_json: Path = None):
    exp_df = pd.read_csv(exp_csv)
    d_exp = exp_df['displacement_mm'].to_numpy()
    f_exp_n = exp_df['force_N'].to_numpy()
    f_exp_kn = f_exp_n / 1000.0
    e_exp = trapezoid(f_exp_n, d_exp * 1e-3)
    peak_exp = np.max(f_exp_kn)
    d_at_peak_exp = d_exp[np.argmax(f_exp_kn)]

    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.plot(d_exp, f_exp_kn, color='#1f77b4', linewidth=2.5, label=f'Experiment (Peak: {peak_exp:.1f} kN @ {d_at_peak_exp:.1f} mm, E={e_exp:.1f} J)')

    metrics = {
        "experimental": {
            "peak_force_kN": round(float(peak_exp), 2),
            "displacement_at_peak_mm": round(float(d_at_peak_exp), 2),
            "absorbed_energy_J": round(float(e_exp), 2)
        }
    }

    if p1_csv and p1_csv.exists():
        df1 = pd.read_csv(p1_csv)
        d1 = df1['displacement_mm'].to_numpy()
        f1_kn = df1['force_kN'].to_numpy()
        e1 = trapezoid(f1_kn * 1000.0, d1 * 1e-3)
        peak1 = np.max(f1_kn)
        d_peak1 = d1[np.argmax(f1_kn)]
        err_peak1 = abs(peak1 - peak_exp) / peak_exp * 100.0
        err_e1 = abs(e1 - e_exp) / e_exp * 100.0
        
        sg1 = compute_sprague_geers(d_exp, f_exp_kn, d1, f1_kn)
        
        ax.plot(d1, f1_kn, color='#d62728', linestyle='--', linewidth=1.8, 
                label=f'Phase 1 Homogenized (Peak: {peak1:.1f} kN @ {d_peak1:.1f} mm, C={sg1["sprague_geers_C_pct"]}%)')
        metrics["phase1_homogenized"] = {
            "peak_force_kN": round(float(peak1), 2),
            "displacement_at_peak_mm": round(float(d_peak1), 2),
            "peak_force_error_pct": round(float(err_peak1), 2),
            "absorbed_energy_J": round(float(e1), 2),
            "energy_error_pct": round(float(err_e1), 2),
            "sprague_geers": sg1
        }

    if p2_csv and p2_csv.exists():
        df2 = pd.read_csv(p2_csv)
        d2 = df2['displacement_mm'].to_numpy()
        f2_kn = df2['force_kN'].to_numpy()
        e2 = trapezoid(f2_kn * 1000.0, d2 * 1e-3)
        peak2 = np.max(f2_kn)
        d_peak2 = d2[np.argmax(f2_kn)]
        err_peak2 = abs(peak2 - peak_exp) / peak_exp * 100.0
        err_e2 = abs(e2 - e_exp) / e_exp * 100.0
        
        sg2 = compute_sprague_geers(d_exp, f_exp_kn, d2, f2_kn)
        
        ax.plot(d2, f2_kn, color='#2ca02c', linestyle='-.', linewidth=1.8, 
                label=f'Phase 2 Meso-Scale Hybrid (Peak: {peak2:.1f} kN @ {d_peak2:.1f} mm, C={sg2["sprague_geers_C_pct"]}%)')
        metrics["phase2_mesoscale"] = {
            "peak_force_kN": round(float(peak2), 2),
            "displacement_at_peak_mm": round(float(d_peak2), 2),
            "peak_force_error_pct": round(float(err_peak2), 2),
            "absorbed_energy_J": round(float(e2), 2),
            "energy_error_pct": round(float(err_e2), 2),
            "sprague_geers": sg2
        }

    if p3_csv and p3_csv.exists():
        df3 = pd.read_csv(p3_csv)
        d3 = df3['displacement_mm'].to_numpy()
        f3_kn = df3['force_kN'].to_numpy()
        e3 = trapezoid(f3_kn * 1000.0, d3 * 1e-3)
        peak3 = np.max(f3_kn)
        d_peak3 = d3[np.argmax(f3_kn)]
        err_peak3 = abs(peak3 - peak_exp) / peak_exp * 100.0
        err_e3 = abs(e3 - e_exp) / e_exp * 100.0
        
        sg3 = compute_sprague_geers(d_exp, f_exp_kn, d3, f3_kn)
        
        ax.plot(d3, f3_kn, color='#ff7f0e', linestyle='-', linewidth=2.2, 
                label=f'Phase 3 Full Discrete Meso-Scale (Peak: {peak3:.1f} kN @ {d_peak3:.1f} mm, C={sg3["sprague_geers_C_pct"]}%)')
        metrics["phase3_full_mesoscale"] = {
            "peak_force_kN": round(float(peak3), 2),
            "displacement_at_peak_mm": round(float(d_peak3), 2),
            "peak_force_error_pct": round(float(err_peak3), 2),
            "absorbed_energy_J": round(float(e3), 2),
            "energy_error_pct": round(float(err_e3), 2),
            "sprague_geers": sg3
        }

    ax.set_xlabel('Indenter Displacement (mm)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Puncture Reaction Force (kN)', fontsize=12, fontweight='bold')
    ax.set_title('Quasi-Static Sandwich Puncture: Experimental vs OpenCourant FEA\nCFRP / Aluminium Honeycomb Panel (⌀25 mm Punch, ⌀30 mm Support Aperture)',
                 fontsize=11, fontweight='bold', pad=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)

    plt.tight_layout()
    if out_plot:
        out_plot.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_plot, dpi=300)
        print(f"Comparison plot saved to: {out_plot}")
    plt.close(fig)

    if out_json:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        with open(out_json, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"Metrics saved to: {out_json}")

    return metrics

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parents[2]
    exp = base_dir / "experimental" / "force_displacement" / "experiment.csv"
    p1 = base_dir / "results" / "phase1_homogenized" / "simulation_fd.csv"
    p2 = base_dir / "results" / "phase2_mesoscale" / "simulation_fd.csv"
    p3 = base_dir / "results" / "phase3_full_mesoscale" / "simulation_fd.csv"
    plot_out = base_dir / "docs" / "reports" / "correlation_overlay.png"
    json_out = base_dir / "docs" / "reports" / "correlation_metrics.json"

    evaluate_all(exp, p1, p2, p3, plot_out, json_out)
