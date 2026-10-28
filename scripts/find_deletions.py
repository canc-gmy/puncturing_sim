with open('results/phase3_full_mesoscale/PUNCTURE_MESOFULL_0001.out') as f:
    lines = f.readlines()

del_lines = []
for i, l in enumerate(lines):
    if 'DELETE SOLID' in l or 'FAILURE (TENS)' in l:
        # find the preceding time stamp line
        time_str = "Unknown"
        for k in range(i-1, max(0, i-50), -1):
            if 'ANIMATION' in lines[k] or ('E-' in lines[k] and len(lines[k].split()) >= 4):
                time_str = lines[k].strip()
                break
        del_lines.append((i, l.strip(), time_str))

print(f"Total element deletion events: {len(del_lines)}")
for i, l, t in del_lines:
    print(f"Line {i}: {l} | context: {t[:60]}")
