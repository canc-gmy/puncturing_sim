with open('models/phase3_full_mesoscale/starter/PUNCTURE_MESOFULL_0000.rad') as f:
    lines = f.readlines()

cur_part = None
for i, l in enumerate(lines):
    if l.startswith('/BRICK/'):
        cur_part = l.strip()
    if '12330' in l:
        print(f"Found in {cur_part}: {l.strip()[:60]}")
    if '11798' in l:
        print(f"Found 11798 in {cur_part}: {l.strip()[:60]}")
