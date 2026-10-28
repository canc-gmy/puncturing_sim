with open('results/phase3_full_mesoscale/PUNCTURE_MESOFULL_0001.out') as f:
    lines = f.readlines()

print(f"Total lines in out: {len(lines)}")
damage_lines = []
for i, l in enumerate(lines):
    if 'START DAMAGE' in l or 'FAILURE' in l or 'DELETE SOLID' in l or 'TOTAL RUPTURE' in l:
        # find the preceding time stamp line
        time_str = "Unknown"
        for k in range(i-1, max(0, i-25), -1):
            if 'ANIMATION' in lines[k] or ('E-' in lines[k] and len(lines[k].split()) >= 4):
                time_str = lines[k].strip()
                break
        damage_lines.append((i, l.strip(), time_str))

print(f"Found {len(damage_lines)} damage/failure events:")
for i, l, t in damage_lines[:30]:
    print(f"Line {i}: {l} | context: {t[:60]}")
