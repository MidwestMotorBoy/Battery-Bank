"""Export the parametric Monolith parts (built by monolith_fusion.py) from the active Fusion design as STEP and STL,
one file of each per part, in the pack frame (mm), sorted by material like hardware/mechanical/stl/.
True arcs: STEP carries real cylinders and fillets; the STLs are tessellated by Fusion at high refinement.
Fusion Personal allows STEP, STL, 3MF and F3D export (IGES is blocked).
Set OUT to hardware/mechanical/fusion/export (absolute path) before running."""
import adsk.core, adsk.fusion, os

OUT = os.path.join(os.path.expanduser('~'), 'Documents', 'BatteryBank', 'hardware', 'mechanical', 'fusion', 'export')
PARTS = {   # component -> (material folder, file stem)
    'Cup (parametric)': ('MJF_PA12', 'monolith_cup'),
    'Cap (parametric)': ('MJF_PA12', 'monolith_cap'),
    'Carrier (parametric)': ('MJF_PA12', 'monolith_carrier'),
    'Rails (parametric)': ('MJF_PA12', 'monolith_rails'),
    'Sleeves (parametric)': ('TPU_95A', 'monolith_sleeves'),
    'Bumper top (parametric)': ('TPU_95A', 'monolith_bumper_top'),
    'Bumper bottom (parametric)': ('TPU_95A', 'monolith_bumper_bottom'),
}
STL_DEVIATION_MM = 0.01            # chord deviation for the STL tessellation
STL_NORMAL_DEG = 5.0


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    em = des.exportManager
    occ = {o.component.name: o for o in des.rootComponent.occurrences}
    for name, (mat, stem) in PARTS.items():
        if name not in occ:
            print('missing', name)
            continue
        comp = occ[name].component
        d = os.path.join(OUT, mat)
        os.makedirs(d, exist_ok=True)
        step = os.path.join(d, stem + '.step')
        em.execute(em.createSTEPExportOptions(step, comp))
        stl = os.path.join(d, stem + '.stl')
        o = em.createSTLExportOptions(comp, stl)
        o.isBinaryFormat = True
        o.isOneFilePerBody = False
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementCustom
        o.surfaceDeviation = STL_DEVIATION_MM / 10.0
        o.normalDeviation = STL_NORMAL_DEG * 3.141592653589793 / 180.0
        o.maximumEdgeLength = 1.0                                          # cm
        o.aspectRatio = 21.5
        em.execute(o)
        vol = sum(b.volume for b in comp.bRepBodies) * 1000.0
        print('%-28s %d bodies %10.1f mm3  step %7d B  stl %8d B' % (name, comp.bRepBodies.count, vol,
              os.path.getsize(step), os.path.getsize(stl)))
