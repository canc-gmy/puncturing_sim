"""
OpenCourant Post-Processing & Result Extraction Pipeline
Converts binary animation files (A-files) to VTK for ParaView,
and converts time history (.h3d / T01) to CSV for automated plotting.
"""

from pathlib import Path
import subprocess
import os
import sys

BASE_DIR = Path(__file__).resolve().parents[2]
OC_DIR = BASE_DIR / "tools" / "OpenCourant"

def find_opencourant_root() -> Path:
    if (OC_DIR / "exec").exists():
        return OC_DIR
    nested = list(OC_DIR.glob("**/exec"))
    if nested:
        return nested[0].parent
    raise FileNotFoundError(f"OpenCourant 'exec' directory not found inside {OC_DIR}")

def convert_results(results_dir: Path, model_prefix: str = "PUNCTURE_HOMOG"):
    oc_root = find_opencourant_root()
    exec_dir = oc_root / "exec"
    
    env = os.environ.copy()
    env["OPENCOURANT_PATH"] = str(oc_root)
    env["PATH"] = ";".join([
        str(oc_root / "exec"),
        str(oc_root / "extlib" / "hm_reader" / "win64"),
        str(oc_root / "extlib" / "h3d" / "lib" / "win64"),
        str(oc_root / "extlib" / "intelOneAPI_runtime" / "win64"),
    ]) + ";" + env.get("PATH", "")

    # 1. Convert Animation files to VTK
    anim_converter = exec_dir / "anim_to_vtk_win64.exe"
    a_files = sorted(list(results_dir.glob(f"{model_prefix}A*")))
    if anim_converter.exists() and a_files:
        vtk_dir = results_dir / "vtk"
        vtk_dir.mkdir(parents=True, exist_ok=True)
        print(f"Found {len(a_files)} animation files. Converting to VTK format...")
        for af in a_files:
            out_vtk = vtk_dir / f"{af.name}.vtk"
            with open(out_vtk, "w") as f_out:
                subprocess.run([str(anim_converter), af.name], cwd=results_dir, env=env, stdout=f_out)
        print(f"VTK animation files saved to: {vtk_dir}")

    # 2. Convert Time History to CSV
    th_converter = exec_dir / "th_to_csv_win64.exe"
    t_files = list(results_dir.glob(f"{model_prefix}T*"))
    t_files = [tf for tf in t_files if not tf.name.endswith(".csv")]
    if th_converter.exists() and t_files:
        print(f"Found time history file: {t_files[0].name}. Converting to CSV...")
        cmd = [str(th_converter), t_files[0].name]
        subprocess.run(cmd, cwd=results_dir, env=env)
        print("Time history CSV generated.")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "phase1"
    if target.lower() == "phase2":
        convert_results(BASE_DIR / "results" / "phase2_mesoscale", model_prefix="PUNCTURE_MESO")
    else:
        convert_results(BASE_DIR / "results" / "phase1_homogenized", model_prefix="PUNCTURE_HOMOG")
