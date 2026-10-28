with open('models/phase3_full_mesoscale/PUNCTURE_MESOFULL_0000.rad') as f:
    for line in f:
        if line.startswith('/PART/'):
            cur_part = line.strip()
            print(cur_part)
