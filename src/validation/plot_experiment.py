"""
Experimental Data Analysis & Plotting
Parses experimental puncture force-displacement data and generates publication-grade plots.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def analyze_and_plot(csv_path: Path, output_dirs: list[Path]):
    df = pd.read_csv(csv_path)
    d = df['displacement_mm'].to_numpy()
    f_n = df['force_N'].to_numpy()
    f_kn = f_n / 1000.0

    # Calculate cumulative absorbed energy via trapezoidal rule: E = int(F dd) [Joules = N*m = mJ / 1000]
    energy_j = np.zeros_like(d)
    for i in range(1, len(d)):
        delta_d = (d[i] - d[i-1]) * 1e-3 # m
        avg_f = (f_n[i] + f_n[i-1]) / 2.0 # N
        energy_j[i] = energy_j[i-1] + avg_f * delta_d

    # Key metrics
    idx_max = np.argmax(f_kn)
    max_force_kn = f_kn[idx_max]
    disp_at_max = d[idx_max]
    total_energy_j = energy_j[-1]

    # Find initial skin puncture peak (around d ~ 0.5 - 1.5 mm)
    mask_early = (d >= 0.3) & (d <= 2.0)
    idx_early_max = np.where(mask_early)[0][np.argmax(f_kn[mask_early])]
    early_peak_f = f_kn[idx_early_max]
    early_peak_d = d[idx_early_max]

    print("=========================================")
    print("EXPERIMENTAL PUNCTURE TEST SUMMARY")
    print("=========================================")
    print(f"Top Skin Peak Force:       {early_peak_f:.2f} kN at {early_peak_d:.2f} mm")
    print(f"Ultimate Puncture Force:   {max_force_kn:.2f} kN at {disp_at_max:.2f} mm")
    print(f"Final Indenter Travel:     {d[-1]:.2f} mm")
    print(f"Total Energy Absorbed:     {total_energy_j:.2f} J")
    print("=========================================")

    # Plot
    fig, ax1 = plt.subplots(figsize=(8, 5.5), dpi=300)

    color_f = '#1f77b4'
    ax1.set_xlabel('Indenter Displacement (mm)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Contact Force (kN)', color=color_f, fontsize=12, fontweight='bold')
    line1 = ax1.plot(d, f_kn, color=color_f, linewidth=2.0, label='Force (kN)')
    ax1.tick_params(axis='y', labelcolor=color_f)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Annotate peaks
    ax1.scatter([early_peak_d], [early_peak_f], color='#d62728', zorder=5)
    ax1.annotate(f'Top Skin Failure\n{early_peak_f:.1f} kN',
                 xy=(early_peak_d, early_peak_f),
                 xytext=(early_peak_d + 1.2, early_peak_f + 2.0),
                 arrowprops=dict(facecolor='#d62728', shrink=0.08, width=1.2, headwidth=6),
                 fontsize=10, fontweight='bold', color='#d62728')

    ax1.scatter([disp_at_max], [max_force_kn], color='#2ca02c', zorder=5)
    ax1.annotate(f'Ultimate Peak (Core+Skin)\n{max_force_kn:.1f} kN',
                 xy=(disp_at_max, max_force_kn),
                 xytext=(disp_at_max - 5.5, max_force_kn + 1.5),
                 arrowprops=dict(facecolor='#2ca02c', shrink=0.08, width=1.2, headwidth=6),
                 fontsize=10, fontweight='bold', color='#2ca02c')

    # Energy secondary axis
    ax2 = ax1.twinx()
    color_e = '#ff7f0e'
    ax2.set_ylabel('Absorbed Energy (J)', color=color_e, fontsize=12, fontweight='bold')
    line2 = ax2.plot(d, energy_j, color=color_e, linestyle='--', linewidth=2.0, label='Absorbed Energy (J)')
    ax2.tick_params(axis='y', labelcolor=color_e)

    # Title & Legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', frameon=True, facecolor='white', framealpha=0.9)
    plt.title('Experimental Puncture Test: CFRP / Al Honeycomb Sandwich Panel\n(Flat Indenter ⌀25 mm, Support Aperture ⌀30 mm)',
              fontsize=12, fontweight='bold', pad=12)

    plt.tight_layout()

    for out_dir in output_dirs:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_fig = out_dir / 'experimental_curve.png'
        fig.savefig(out_fig, dpi=300)
        print(f"Saved plot to: {out_fig}")

    plt.close(fig)

    # Save summary metrics to json
    metrics = {
        "top_skin_peak_force_kN": float(early_peak_f),
        "top_skin_peak_disp_mm": float(early_peak_d),
        "ultimate_force_kN": float(max_force_kn),
        "ultimate_disp_mm": float(disp_at_max),
        "total_energy_J": float(total_energy_j),
        "final_displacement_mm": float(d[-1])
    }
    metrics_path = output_dirs[0] / 'experimental_metrics.json'
    import json
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics to: {metrics_path}")

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parents[2]
    csv_file = base_dir / 'experimental' / 'force_displacement' / 'experiment.csv'
    out_dirs = [
        base_dir / 'experimental' / 'force_displacement',
        base_dir / 'docs' / 'reports'
    ]
    analyze_and_plot(csv_file, out_dirs)
