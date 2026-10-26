"""
OpenCourant Simulation Runner
Sets up the runtime environment (Intel oneAPI, OpenCourant libraries, RAD_CFG_PATH)
and executes the Starter and Engine solvers for Phase 1 or Phase 2 models.
"""

from pathlib import Path
import subprocess
import shutil
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

def setup_environment(oc_root: Path) -> dict:
    env = os.environ.copy()
    env["OPENCOURANT_PATH"] = str(oc_root)
    env["RAD_CFG_PATH"] = str(oc_root / "hm_cfg_files")
    env["KMP_STACKSIZE"] = "400m"

    paths_to_add = [
        str(oc_root / "exec"),
        str(oc_root / "extlib" / "hm_reader" / "win64"),
        str(oc_root / "extlib" / "h3d" / "lib" / "win64"),
        str(oc_root / "extlib" / "intelOneAPI_runtime" / "win64"),
    ]
    env["PATH"] = ";".join(paths_to_add) + ";" + env.get("PATH", "")
    return env

def run_simulation(model_prefix: str = "PUNCTURE_HOMOG", run_dir: Path = None, model_dir: Path = None, num_threads: int = 4):
    oc_root = find_opencourant_root()
    env = setup_environment(oc_root)
    exec_dir = oc_root / "exec"

    starter_exe = exec_dir / "starter_win64.exe"
    engine_exe = exec_dir / "engine_win64_sp.exe"
    if not engine_exe.exists():
        engine_exe = exec_dir / "engine_win64.exe"

    if model_dir is None:
        if "MESO" in model_prefix.upper():
            model_dir = BASE_DIR / "models" / "phase2_mesoscale"
        else:
            model_dir = BASE_DIR / "models" / "phase1_homogenized"

    if run_dir is None:
        if "MESO" in model_prefix.upper():
            run_dir = BASE_DIR / "results" / "phase2_mesoscale"
        else:
            run_dir = BASE_DIR / "results" / "phase1_homogenized"
    run_dir.mkdir(parents=True, exist_ok=True)

    starter_src = model_dir / "starter" / f"{model_prefix}_0000.rad"
    engine_src = model_dir / "engine" / f"{model_prefix}_0001.rad"

    starter_dst = run_dir / f"{model_prefix}_0000.rad"
    engine_dst = run_dir / f"{model_prefix}_0001.rad"

    print(f"Copying model decks from {model_dir} to run directory: {run_dir}")
    shutil.copy2(starter_src, starter_dst)
    shutil.copy2(engine_src, engine_dst)

    print(f"=== OpenCourant Solver Runner ===")
    print(f"OpenCourant Root: {oc_root}")
    print(f"Starter Exe:      {starter_exe}")
    print(f"Engine Exe:       {engine_exe}")
    print(f"Work Directory:   {run_dir}")
    print(f"Model Prefix:     {model_prefix}")
    print(f"Threads:          {num_threads}")
    print("=================================")

    # 1. Run Starter
    print("\n[Step 1/2] Running Starter...")
    cmd_starter = [str(starter_exe), "-i", f"{model_prefix}_0000.rad", "-nspmd", "1", "-np", str(num_threads)]
    ret_starter = subprocess.run(cmd_starter, cwd=run_dir, env=env)
    if ret_starter.returncode != 0:
        print(f"ERROR: Starter exited with code {ret_starter.returncode}")
        out_file = run_dir / f"{model_prefix}_0000.out"
        if out_file.exists():
            print("\n--- Starter .out file excerpt ---")
            lines = out_file.read_text(errors='ignore').splitlines()
            for line in lines[-30:]:
                print(line)
        return False

    print("Starter completed successfully.")

    # 2. Run Engine
    print(f"\n[Step 2/2] Running Engine for {model_prefix}_0001.rad...")
    cmd_engine = [str(engine_exe), "-i", f"{model_prefix}_0001.rad", "-nt", str(num_threads)]
    ret_engine = subprocess.run(cmd_engine, cwd=run_dir, env=env)
    if ret_engine.returncode != 0:
        print(f"ERROR: Engine exited with code {ret_engine.returncode}")
        out_file = run_dir / f"{model_prefix}_0001.out"
        if out_file.exists():
            print("\n--- Engine .out file excerpt ---")
            lines = out_file.read_text(errors='ignore').splitlines()
            for line in lines[-30:]:
                print(line)
        return False

    print("\nSimulation execution completed successfully!")
    return True

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "phase1"
    if target.lower() == "phase2":
        run_simulation(model_prefix="PUNCTURE_MESO")
    else:
        run_simulation(model_prefix="PUNCTURE_HOMOG")
