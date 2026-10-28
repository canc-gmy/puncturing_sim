"""
OpenRadioss / OpenCourant File Writer Utility (v3.1)
Writes conforming .rad starter and engine input decks with 20-column numerical precision.
Supports 3D Bricks (/BRICK), Cohesive Bricks (/PROP/TYPE43, /MAT/LAW59), 2D Shells (/SHELL),
Properties (/PROP), Materials (/MAT), Functions (/FUNCT), Surfaces (/SURF), Interfaces (/INTER),
Boundary Conditions (/BCS, /IMPVEL, /RBODY), and Time History outputs (/TH).
"""

from pathlib import Path
from dataclasses import dataclass, field
import numpy as np

@dataclass
class Node:
    id: int
    x: float
    y: float
    z: float

@dataclass
class BrickElem:
    id: int
    part_id: int
    n: list[int] # 8 nodes

@dataclass
class ShellElem:
    id: int
    part_id: int
    n: list[int] # 4 nodes

class RadiossDeck:
    def __init__(self, title: str = "PUNCTURE_SIM"):
        self.title = title
        self.nodes: dict[int, Node] = {}
        self.parts: dict[int, tuple[str, int, int]] = {} # part_id -> (name, prop_id, mat_id)
        self.bricks_by_part: dict[int, list[BrickElem]] = {}
        self.shells_by_part: dict[int, list[ShellElem]] = {}
        self.properties: list[str] = []
        self.functions: list[str] = []
        self.materials: list[str] = []
        self.node_groups: list[str] = []
        self.surfaces: list[str] = []
        self.contacts: list[str] = []
        self.bcs: list[str] = []
        self.time_histories: list[str] = []

    def add_node(self, nid: int, x: float, y: float, z: float):
        self.nodes[nid] = Node(nid, x, y, z)

    def add_brick(self, eid: int, part_id: int, nids: list[int]):
        if part_id not in self.bricks_by_part:
            self.bricks_by_part[part_id] = []
        self.bricks_by_part[part_id].append(BrickElem(eid, part_id, nids))

    def add_shell(self, eid: int, part_id: int, nids: list[int]):
        if part_id not in self.shells_by_part:
            self.shells_by_part[part_id] = []
        self.shells_by_part[part_id].append(ShellElem(eid, part_id, nids))

    def write_starter(self, filepath: Path):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write("#RADIOSS STARTER\n")
            f.write("/BEGIN\n")
            f.write(f"{self.title[:80]}\n")
            f.write("2026\n")
            f.write(f"{'Mg':<20}{'mm':<20}{'s':<20}\n")
            f.write(f"{'Mg':<20}{'mm':<20}{'s':<20}\n")
            
            # Nodes
            f.write("/NODE\n")
            for nid in sorted(self.nodes.keys()):
                node = self.nodes[nid]
                f.write(f"{node.id:10d}{node.x:20.6f}{node.y:20.6f}{node.z:20.6f}\n")

            # Parts
            for part_id, (name, prop_id, mat_id) in self.parts.items():
                f.write(f"/PART/{part_id}\n")
                f.write(f"{name}\n")
                f.write(f"{prop_id:10d}{mat_id:10d}         0\n")

            # Properties
            for prop in self.properties:
                f.write(prop + "\n")

            # Functions (before materials)
            for fn in self.functions:
                f.write(fn + "\n")

            # Materials
            for mat in self.materials:
                f.write(mat + "\n")

            # Solid Elements grouped by part
            for part_id, bricks in self.bricks_by_part.items():
                f.write(f"/BRICK/{part_id}\n")
                for b in bricks:
                    f.write(f"{b.id:10d}" + "".join(f"{n:10d}" for n in b.n) + "\n")

            # Shell Elements grouped by part
            for part_id, shells in self.shells_by_part.items():
                f.write(f"/SHELL/{part_id}\n")
                for s in shells:
                    f.write(f"{s.id:10d}" + "".join(f"{n:10d}" for n in s.n) + "\n")

            # Node Groups
            for grp in self.node_groups:
                f.write(grp + "\n")

            # Surfaces
            for surf in self.surfaces:
                f.write(surf + "\n")

            # Contacts / Interfaces
            for contact in self.contacts:
                f.write(contact + "\n")

            # Boundary Conditions
            for bc in self.bcs:
                f.write(bc + "\n")

            # Time Histories
            for th in self.time_histories:
                f.write(th + "\n")

            f.write("/END\n")

    def write_engine(
        self,
        filepath: Path,
        t_stop: float = 0.0865,
        anim_dt: float = 0.0005,
        th_dt: float = 0.00002,
        dt_noda: float = 4.5e-8,
        dt_inter_del: float = 2.0e-8,
        dt_brick_del: float = 1.0e-9,
        dt_shell_del: float = 1.0e-9,
        rfile_cycle: int = 20000
    ):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write("#RADIOSS ENGINE\n")
            f.write("/VERS/2026\n")
            f.write(f"/RUN/{self.title[:20]}/1\n")
            f.write(f"{t_stop:16.6f}\n")
            f.write(f"/ANIM/DT\n")
            f.write(f"0.0 {anim_dt:16.6f}\n")
            f.write("/PRINT/-500\n")
            if rfile_cycle > 0:
                f.write("/RFILE\n")
                f.write(f"{rfile_cycle:10d}\n")
            f.write("/ANIM/VECT/DISP\n")
            f.write("/ANIM/VECT/CONT\n")
            f.write("/ANIM/BRICK/TENS/STRESS/ALL\n")
            f.write("/ANIM/SHELL/TENS/STRESS/ALL\n")
            f.write("/ANIM/ELEM/EPSP\n")
            f.write("/ANIM/ELEM/ENERGY\n")
            f.write(f"/TFILE\n")
            f.write(f"{th_dt:16.6f}\n")
            f.write("/STOP\n")
            f.write("1.000000E+30    0.150000        10.00000         1         1\n")
            f.write("/DT/NODA/CST\n")
            f.write(f"0.900000        {dt_noda:16.6E}\n")
            if dt_inter_del > 0:
                f.write("/DT/INTER/DEL\n")
                f.write(f"0.900000        {dt_inter_del:16.6E}\n")
            f.write("/DT/BRICK/DEL\n")
            f.write(f"0.900000        {dt_brick_del:16.6E}\n")
            f.write("/DT/SHELL/DEL\n")
            f.write(f"0.900000        {dt_shell_del:16.6E}\n")
            f.write("/END\n")
