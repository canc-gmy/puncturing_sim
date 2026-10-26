"""
Model vs Experiment Correlation Module
Calculates error metrics (peak force error, stiffness error, absorbed energy error)
and produces publication-quality overlay plots comparing Experiment, Phase 1, and Phase 2.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.integrate import trapezoid

def evaluate_all(exp_csv: Path, p1_csv: Path = None, p2_csv: Path = None, out_plot: Path = None, out_json: Path = None):
    exp_df = pd.read_csv(exp_csv)
    d_exp = exp_df['displacement_mm'].to_numpy()
    f_exp_n = exp_df['force_N'].to_numpy()
    f_exp_kn = f_exp_n / 1000.0
    e_exp = trapezoid(f_exp_n, d_exp * 1e-3)
    peak_exp = np.max(f_exp_kn)

    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=300)
    ax.plot(d_exp, f_exp_kn, color='#1f77b4', linewidth=2.2, label='Experiment (Quasi-Static)')

    metrics = {
        "experimental": {
            "peak_force_kN": float(peak_exp),
            "absorbed_energy_J": float(e_exp)
        }
    }

    if p1_csv and p1_csv.exists():
        df1 = pd.read_csv(p1_csv)
        d1 = df1['displacement_mm'].to_numpy()
        f1_kn = df1['force_kN'].to_numpy()
        e1 = trapezoid(f1_kn * 1000.0, d1 * 1e-3)
        peak1 = np.max(f1_kn)
        err_peak1 = abs(peak1 - peak_exp) / peak_exp * 100.0
        err_e1 = abs(e1 - e_exp) / e_exp * 100.0
        ax.plot(d1, f1_kn, color='#d62728', linestyle='--', linewidth=2.0, label='OpenCourant: Phase 1 (Homogenized)')
        metrics["phase1_homogenized"] = {
            "peak_force_kN": float(peak1),
            "peak_force_error_pct": float(err_peak1),
            "absorbed_energy_J": float(e1),
            "energy_error_pct": float(err_e1)
        }

    if p2_csv and p2_csv.exists():
        df2 = pd.read_csv(p2_csv)
        d2 = df2['displacement_mm'].to_numpy()
        f2_kn = df2['force_kN'].to_numpy()
        e2 = trapezoid(f2_kn * 1000.0, d2 * 1e-3)
        peak2 = np.max(f2_kn)
        err_peak2 = abs(peak2 - peak_exp) / peak_exp * 100.0
        err_e2 = abs(e2 - e_exp) / e_exp * 100.0
        ax.plot(d2, f2_kn, color='#2ca02c', linestyle='-.', linewidth=2.0, label='OpenCourant: Phase 2 (Meso-Scale Hybrid)')
        metrics["phase2_mesoscale"] = {
            "peak_force_kN": float(peak2),
            "peak_force_error_pct": float(err_peak2),
            "absorbed_energy_J": float(e2),
            "energy_error_pct": float(err_e2)
        }

    ax.set_xlabel('Indenter Displacement (mm)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Puncture Force (kN)', fontsize=12, fontweight='bold')
    ax.set_title('Quasi-Static Puncture: Experimental vs OpenCourant Finite Element Models\nCFRP / Aluminium Honeycomb Sandwich Panel (⌀25 mm Punch, ⌀30 mm Aperture)',
                 fontsize=11, fontweight='bold', pad=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)

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
    plot_out = base_dir / "docs" / "reports" / "correlation_overlay.png"
    json_out = base_dir / "docs" / "reports" / "correlation_metrics.json"

    evaluate_all(exp, p1, p2, plot_out, json_out)
