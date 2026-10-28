with open('results/phase2_mesoscale/PUNCTURE_MESOT01.csv') as f:
    header = f.readline().split(',')
    line2 = f.readline().split(',')

for i, (h, v) in enumerate(zip(header, line2)):
    print(f"Col {i:2d}: {h.strip()} = {v.strip()}")
