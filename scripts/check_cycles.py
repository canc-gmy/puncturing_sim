with open('results/phase3_full_mesoscale/PUNCTURE_MESOFULL_0001.out') as f:
    for line in f:
        parts = line.split()
        if len(parts) >= 12 and parts[0].isdigit():
            cyc = int(parts[0])
            if cyc % 100000 == 0:
                t = float(parts[1])
                ie = float(parts[6])
                ke = float(parts[7])
                ew = float(parts[9])
                print(f"Cycle {cyc:8d}: t={t*1000:6.2f}ms | IE={ie:12.4e} | KE={ke:12.4e} | ExtWork={ew:12.4e}")
