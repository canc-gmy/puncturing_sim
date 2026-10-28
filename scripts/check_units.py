with open('results/phase1_homogenized/PUNCTURE_HOMOG_0001.out') as f:
    for i in range(150):
        l = f.readline()
        if 'FORCE' in l or 'UNIT' in l or 'NEWTON' in l:
            print(l.strip())
