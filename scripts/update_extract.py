with open('src/postprocessing/extract_fd_curve.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace for phase3
old_p3 = """    elif target.lower() == "phase3":
        t01_csv = base_dir / "results" / "phase3_full_mesoscale" / "PUNCTURE_MESOFULLT01.csv"
        fd_out = base_dir / "results" / "phase3_full_mesoscale" / "simulation_fd.csv"
        use_work = False
        scale = 1.0"""

new_p3 = """    elif target.lower() == "phase3":
        t01_csv = base_dir / "results" / "phase3_full_mesoscale" / "PUNCTURE_MESOFULLT01.csv"
        fd_out = base_dir / "results" / "phase3_full_mesoscale" / "simulation_fd.csv"
        use_work = True
        scale = 4.0"""

if old_p3 in content:
    content = content.replace(old_p3, new_p3)
    with open('src/postprocessing/extract_fd_curve.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully replaced.")
else:
    print("Could not find old_p3 directly, checking line by line.")
    lines = content.splitlines()
    for i, l in enumerate(lines):
        if 'phase3' in l:
            for k in range(i, i+6):
                print(f"{k}: {repr(lines[k])}")
