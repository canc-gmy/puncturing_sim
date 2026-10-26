"""
Model vs Experiment Correlation Module
Calculates error metrics (peak force error, stiffness error, absorbed energy error)
and produces publication-quality overlay plots.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def evaluate_correlation(exp_csv: Path, sim_csv: Path, out_plot: Path, report_json: Path):
    # Load experimental
    exp_df = pd.read_csv(exp_csv)
    d_exp = exp_df['displacement_mm'].to_numpy()
    f_exp_n = exp_df['force_N'].to_numpy()
    f_exp_kn = f_exp_n / 1000.0

    # Load simulation
    sim_df = pd.read_csv(sim_csv)
    d_sim = sim_df['displacement_mm'].to_numpy()
    f_sim_kn = sim_df['force_kN'].to_numpy()

    # Numerical integration for absorbed energy
    e_exp = np.trapz(f_exp_n, d_exp * 1e-3)
    e_sim = np.trapz(f_sim_kn * 1000.0, d_sim * 1e-3)

    peak_f_exp = np.max(f_exp_kn)
    peak_f_sim = np.max(f_sim_kn)

    error_peak_f = abs(peak_f_sim - peak_f_exp) / peak_f_exp * 100.0
    error_energy = abs(e_sim - e_exp) / e_exp * 100.0

    # Initial stiffness (linear slope 0.2 to 0.6 mm)
    m_exp = (d_exp >= 0.2) & (d_exp <= 0.6)
    slope_exp, _ = np.polyfit(d_exp[m_exp], f_exp_kn[m_exp], 1)
    
    m_sim = (d_sim >= 0.2) & (d_sim <= 0.6)
    slope_sim, _ = np.polyfit(d_sim[m_sim], f_sim_kn[m_sim], 1)
    error_stiffness = abs(slope_sim - slope_exp) / slope_exp * 100.0

    metrics = {
        "experimental_peak_force_kN": float(peak_f_exp),
        "simulation_peak_force_kN": float(peak_f_sim),
        "peak_force_error_percent": float(error_peak_f),
        "experimental_energy_J": float(e_exp),
        "simulation_energy_J": float(e_sim),
        "energy_error_percent": float(error_energy),
        "experimental_stiffness_kN_per_mm": float(slope_exp),
        "simulation_stiffness_kN_per_mm": float(slope_sim),
        "stiffness_error_percent": float(error_stiffness)
    }

    report_json.parent.mkdir(parents=True, exist_ok=True)
    with open(report_json, 'w') as f:
        json.dump(metrics, f, indent=2)

    # Plot overlay
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    ax.plot(d_exp, f_exp_kn, color='#1f77b4', linewidth=2.0, label='Experiment (Quasi-static)')
    ax.plot(d_sim, f_sim_kn, color='#d62728', linestyle='--', linewidth=2.0, label='OpenCourant (FE Model)')

    ax.set_xlabel('Indenter Displacement (mm)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Puncture Force (kN)', fontsize=12, fontweight='bold')
    ax.set_title('Experimental vs OpenCourant Simulation Correlation\nCFRP / Aluminium Honeycomb Sandwich Panel',
                 fontsize=12, fontweight='bold', pad=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)

    # Add text box with metrics
    textstr = '\n'.join((
        f'Peak Force Err: {error_peak_f:.1f}%',
        f'Energy Err:     {error_energy:.1f}%',
        f'Stiffness Err:  {error_stiffness:.1f}%'
    ))
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.68, 0.25, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props, family='monospace')

    plt.tight_layout()
    out_plot.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_plot, dpi=300)
    plt.close(fig)

    print(f"Correlation metrics saved to: {report_json}")
    print(f"Overlay plot saved to:        {out_plot}")
    return metrics
