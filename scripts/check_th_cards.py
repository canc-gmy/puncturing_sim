with open('models/phase3_full_mesoscale/starter/PUNCTURE_MESOFULL_0000.rad') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if l.startswith('/TH/'):
        print(''.join(lines[i:i+6]))
