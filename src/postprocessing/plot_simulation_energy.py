"""
Simulation Energy Conservation & Quality Diagnostics
Parses OpenCourant time-history CSV and evaluates:
- Internal Energy vs Kinetic Energy (Quasi-static validity ratio)
- Hourglass Energy dissipation ratio (< 5% threshold)
- Total energy conservation
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def plot_energy(csv_path: Path, out_plot: Path):
    df = pd.read_csv(csv_path)
    
    # Strip whitespace from column names
    df.columns = [c.strip().strip('"') for c in df.columns]

    time = df['time'].to_numpy() * 1000.0 # convert s to ms
    # Energy in mJ (since units are Mg, mm, s -> Energy is mJ = 1e-3 J)
    # 1 mJ = 1e-3 J, so dividing by 1000 gives Joules
    e_int = df['INTERNAL ENERGY'].to_numpy() / 1000.0
    e_kin = df['KINETIC ENERGY'].to_numpy() / 1000.0
    e_hg = df['HOURGLASS ENERGY'].to_numpy() / 1000.0
    e_tot = e_int + e_kin + e_hg

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True, dpi=300)

    # Subplot 1: Absolute Energies
    ax1.plot(time, e_tot, label='Total Energy', color='black', linewidth=1.8)
    ax1.plot(time, e_int, label='Internal Energy', color='#1f77b4', linewidth=1.8)
    ax1.plot(time, e_kin, label='Kinetic Energy', color='#d62728', linewidth=1.5, linestyle='--')
    ax1.plot(time, e_hg, label='Hourglass Energy', color='#2ca02c', linewidth=1.5, linestyle=':')
    ax1.set_ylabel('Energy (J)', fontsize=11, fontweight='bold')
    ax1.set_title('OpenCourant Energy Balance & Quality Diagnostics', fontsize=12, fontweight='bold', pad=10)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)

    # Subplot 2: Energy Ratios
    # To avoid division by zero early on:
    mask = e_int > 1e-6
    ratio_kin = np.zeros_like(time)
    ratio_hg = np.zeros_like(time)
    ratio_kin[mask] = (e_kin[mask] / e_int[mask]) * 100.0
    ratio_hg[mask] = (e_hg[mask] / e_int[mask]) * 100.0

    ax2.plot(time, ratio_kin, label='Kinetic / Internal (%)', color='#d62728', linewidth=1.5)
    ax2.plot(time, ratio_hg, label='Hourglass / Internal (%)', color='#2ca02c', linewidth=1.5)
    ax2.axhline(5.0, color='gray', linestyle='--', linewidth=1.0, label='5% Target Threshold')
    ax2.set_xlabel('Time (ms)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Energy Ratio (%)', fontsize=11, fontweight='bold')
    ax2.set_ylim(-0.5, 15.0)
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)

    plt.tight_layout()
    out_plot.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_plot, dpi=300)
    plt.close(fig)
    print(f"Energy diagnostics plot saved to: {out_plot}")

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parents[2]
    csv_file = base_dir / "results" / "phase1_homogenized" / "PUNCTURE_HOMOGT01.csv"
    plot_file = base_dir / "docs" / "reports" / "energy_balance.png"
    if csv_file.exists():
        plot_energy(csv_file, plot_file)
    else:
        print(f"File not found: {csv_file}")
