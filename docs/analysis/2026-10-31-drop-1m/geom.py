"""Assembly meshes for the drop study, from hardware/mechanical/monolith_cup.py (cached in cache/assembly.npz).
A = [(key, triangles (n, 3, 3) mm, colour)] in the pack frame: x toward the board face, y across, z along the cells
(port end up). Run once after a mechanical change: python geom.py"""
import os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
MECH = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'hardware', 'mechanical'))
CACHE = os.path.join(HERE, 'cache', 'assembly.npz')

def load():
    if not os.path.exists(CACHE): build()
    z = np.load(CACHE, allow_pickle=True)
    A = [(k, z[f'v{i}'], tuple(c)) for i, (k, c) in enumerate(zip(z['keys'], z['cols']))]
    return A, z['mass'].item(), z['params'].item()

def build():
    sys.path.insert(0, MECH); cwd = os.getcwd(); os.chdir(MECH)
    try:
        import monolith_cup as K
        A = K.assembly(); m = K.masses(A)
        prm = dict(Z_TOP1=K.Z_TOP1, Z_TOP0=K.Z_TOP0, Z_MOUTH=K.Z_MOUTH, CAP_T=K.CAP_T, BUMP_T_TOP=K.BUMP_T_TOP,
                   BUMP_T_BOT=K.BUMP_T_BOT, BUMP_BAND=K.BUMP_BAND, BUMP_WALL=K.BUMP_WALL, BUMP_WALL_BOT=K.BUMP_WALL_BOT,
                   SLAB_FILL=K.SLAB_FILL, PAD_FILL=K.PAD_FILL, WALL=K.WALL, WALL_BF=K.WALL_BF, X_IN=K.X_IN, YI=K.YI,
                   POST_GAP=K.POST_GAP, TOP_T=K.TOP_T, MOUTH_T=K.MOUTH_T, size=K.size(A).tolist(), CELLS=K.CELLS,
                   sb_xb0=K.S.sb_xb0, sb_xb1=K.S.sb_xb1, PCB_T=K.S.SB_PCB_T)
    finally: os.chdir(cwd)
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    np.savez_compressed(CACHE, keys=np.array([k for k, _, _ in A]), cols=np.array([c for _, _, c in A]),
                        mass=np.array(m, dtype=object), params=np.array(prm, dtype=object),
                        **{f'v{i}': V.astype(np.float32) for i, (_, V, _) in enumerate(A)})
    print('wrote', CACHE, len(A), 'meshes', round(sum(m.values()), 1), 'g')

if __name__ == '__main__': build()
