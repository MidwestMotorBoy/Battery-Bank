"""Flexible 50A honeycomb at 9 and 12 mm, TPU 95A honeycomb 15-16 %, and the 50A modulus x0.67 / x1.5 (port end; prints only)"""
import bumper_struct as S
for ts in (1.5, 2.0):
    for rho in (0.15, 0.2, 0.25, 0.3, 0.35):
        r1 = S.run('top', 'honeycomb', rho, 'Flexible 50A', 'Flexible 50A', 1.0, ts); r15 = S.run('top', 'honeycomb', rho, 'Flexible 50A', 'Flexible 50A', 1.5, ts)
        print(f'{6*ts:.0f} mm 50A honeycomb {rho}', r1['g'], r15['g'], r1['crush'], r15['crush'], 'slab', r1['slab_g'], flush=True)
for rho in (0.15, 0.16):
    print('TPU hc', rho, S.run('top', 'honeycomb', rho, 'TPU 95A', 'TPU 95A')['g'], S.run('top', 'honeycomb', rho, 'TPU 95A', 'TPU 95A', 1.5)['g'])
# sensitivity: 50A modulus x0.67 / x1.5 at its best 6 mm build
for e in (2.6, 5.85):
    S.E_IMP['Flexible 50A'] = e
    print('50A E', e, S.run('top', 'honeycomb', 0.35, 'Flexible 50A', 'Flexible 50A')['g'], S.run('top', 'honeycomb', 0.30, 'Flexible 50A', 'Flexible 50A')['g'], S.run('top', 'honeycomb', 0.25, 'Flexible 50A', 'Flexible 50A')['g'])
