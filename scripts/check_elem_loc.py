import numpy as np

with open('models/phase3_full_mesoscale/starter/PUNCTURE_MESOFULL_0000.rad') as f:
    lines = f.readlines()

nodes = {}
in_node = False
for l in lines:
    if l.startswith('/NODE'):
        in_node = True
        continue
    if in_node:
        if l.startswith('/'):
            in_node = False
            continue
        try:
            nid = int(l[:10])
            x = float(l[10:30])
            y = float(l[30:50])
            z = float(l[50:70])
            nodes[nid] = (x, y, z)
        except ValueError:
            pass

print(f"Loaded {len(nodes)} nodes.")

in_brick = False
for l in lines:
    if l.startswith('/BRICK/'):
        in_brick = True
        continue
    if in_brick and l.startswith('/'):
        in_brick = False
        continue
    if in_brick:
        parts = l.split()
        if len(parts) >= 9:
            eid = int(parts[0])
            if eid in [12330, 12329, 12354, 11798, 11822, 11872]:
                e_nodes = [int(p) for p in parts[1:9]]
                xs = [nodes[n][0] for n in e_nodes]
                ys = [nodes[n][1] for n in e_nodes]
                zs = [nodes[n][2] for n in e_nodes]
                rs = [np.sqrt(x**2 + y**2) for x, y in zip(xs, ys)]
                print(f"Elem {eid}: r in [{min(rs):.2f}, {max(rs):.2f}] mm, z in [{min(zs):.3f}, {max(zs):.3f}] mm")
