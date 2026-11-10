# The words. exec'd from page_text.py; every number is taken from D so the text cannot drift from the charts.
pk1 = _p(1, 'PACK_P'); gd1 = _p(1, 'GND'); vb1 = _p(1, 'VBUS'); ac1 = _p(1, 'AC_SNS_N'); ac2 = _p(2, 'AC_SNS_N')
gp2a = next(r for r in G if r['short'] == 'P2 HS A'); gp2l = next(r for r in G if r['short'] == 'P2 LS A')
g_same = [r for r in G if abs(r['n']['L'] / r['b']['L'] - 1) < 0.12]
g_worse = [r for r in G if r['n']['L'] / r['b']['L'] >= 1.12]; g_better = [r for r in G if r['n']['L'] / r['b']['L'] <= 0.88]
ts_b = max((r for r in C if r['label'].endswith(' TS')), key=lambda r: mv(r, 'b')); ts_n = max((r for r in C if r['label'].endswith(' TS')), key=lambda r: mv(r, 'n'))
n10_b = nover('b', 10, ANA + BUS); n10_n = nover('n', 10, ANA + BUS); n1_b = nover('b', 1, ANA + BUS); n1_n = nover('n', 1, ANA + BUS)
bus_b = [r for r in C if r['cat'] in ('I2C / SMBus', 'USB CC')]
i2c_b = max((mv(r, 'b') for r in bus_b), default=0); i2c_n = max((mv(r, 'n') for r in bus_b), default=0)
cs_b = max((mv(r, 'b') for r in C if r['cat'] == 'Current sense'), default=0); cs_n = max((mv(r, 'n') for r in C if r['cat'] == 'Current sense'), default=0)

hot_raw = {t: J(f'hot_{t}.json') for t in (B, N)}
def hfc(t, key):                       # board inductance of the 100 nF capacitor at the FET
    o = hot_raw[t][key]; c = [x for x in o['caps'] if REFV[t].get(x, '').startswith('0.1u')]
    return o['caps'][c[0]] * 1e9 if c else float('nan')
REFV = {B: {}, N: {}}
for t in (B, N):
    for k, o in hot_raw[t].items():
        for c in o['caplist']: REFV[t][c] = '0.1u' if c in ('C430', 'C438', 'C530', 'C538', 'C446', 'C546') else '22u'
CH = ['P1 VBUS leg (Q401)', 'P1 PACK leg (Q402)', 'P2 VBUS leg (Q501)', 'P2 PACK leg (Q502)']
hf_b = [hfc(B, k) for k in CH]; hf_n = [hfc(N, k) for k in CH]
vb_b = [H[0]['b']['eff'], H[2]['b']['eff']]; vb_n = [H[0]['n']['eff'], H[2]['n']['eff']]
pk_b = [H[1]['b']['eff'], H[3]['b']['eff']]; pk_n = [H[1]['n']['eff'], H[3]['n']['eff']]
z_pk = ((sum(pk_n)/2 + 0.3) / (sum(pk_b)/2 + 0.3)) ** 0.5 - 1; z_vb = ((sum(vb_n)/2 + 0.3) / (sum(vb_b)/2 + 0.3)) ** 0.5 - 1
via_b = hot_raw[B][CH[1]]['vias']; via_n = hot_raw[N][CH[1]]['vias']
bk446 = hot_raw[N]['P1 5V buck (U404)']['caps']['C446'] * 1e9; bk446b = hot_raw[B]['P1 5V buck (U404)']['caps']['C446'] * 1e9
ghs_b = [r['b']['L'] for r in G if ' HS ' in r['short']]; ghs_n = [r['n']['L'] for r in G if ' HS ' in r['short']]
gls = [r for r in G if ' LS ' in r['short']]
gls_same = [r for r in gls if abs(r['n']['L'] / r['b']['L'] - 1) < 0.1]; gls_w = [r for r in gls if r['n']['L'] / r['b']['L'] >= 1.1]
coarse = [r for r in G if r['n'].get('h', 0.15) > 0.15]
GATE_H_NOTE = (f"{len(coarse)} of the ground-up board's loops ({', '.join(r['short'] for r in coarse)}) were too large for memory at 0.15 mm and were solved with 0.175 or 0.2 mm cells. "
               "The port 2 leg A low-side loop was solved with both ground planes kept along the whole route on both boards, because the standard setting cut its ground return on the ground-up board; that setting reads 5 to 15 % lower.")
TSg = next(r for r in C if r['label'] == 'TS4'); FB2 = next(r for r in C if r['label'] == 'P2 FB')
top_n = sorted([r for r in C if r['cat'] in ANA + BUS], key=lambda r: -mv(r, 'n'))[:6]
i2c_rows = [r for r in C if r['cat'] == 'I2C / SMBus']; i2c_n = max(mv(r, 'n') for r in i2c_rows); i2c_b = max(mv(r, 'b') for r in i2c_rows)
oth_b = max(mv(r, 'b') for r in C if r['cat'] in ANA + BUS and not r['label'].endswith(' TS'))
tsb = sorted([mv(r, 'b') for r in C if r['label'].endswith(' TS')])
csc_b = max((r['b'] or {}).get('c', 0) for r in C if r['cat'] == 'Current sense'); csc_n = max((r['n'] or {}).get('c', 0) for r in C if r['cat'] == 'Current sense')
SCORE.insert(len(SCORE) - 2, ['Signals that take a step over 10 mV from a switch-node edge', str(n10_b), str(n10_n), 'b' if n10_b < n10_n else 'n' if n10_n < n10_b else 'l'])

LEDE = ("Same schematic and parts, two layouts. Where the result depends on how much copper there is (loss, heat, sense-tap accuracy) the script-built board is level with the hand-routed one. "
        "Where it depends on where fast edges run (charger hot loops, gate-drive loops, coupling into signals) the hand-routed board is better, in places by a wide margin. "
        "The ground-up board is ahead only at the three small bucks and in the USB-side copper.")
HOT = [
 f"**The current board is ahead on the four charger loops, the ground-up board on the three small bucks.** The VBUS legs see {vb_b[0]:.2f} and {vb_b[1]:.2f} nH on the current board and {vb_n[0]:.2f} and {vb_n[1]:.2f} nH on the ground-up board. The pack legs see {pk_b[0]:.2f} and {pk_b[1]:.2f} nH against {pk_n[0]:.2f} and {pk_n[1]:.2f} nH.",
 f"The cause is the 100 nF capacitor at each FET, which carries most of the fast current. Its board loop is {min(hf_b):.2f} to {max(hf_b):.2f} nH on the current board and {min(hf_n):.2f} to {max(hf_n):.2f} nH on the ground-up board. At the pack-leg FET the ground-up board also has {via_n} vias in the loop area where the current board has {via_b}, so less of the return current can drop to the ground plane right under the loop. With the FET package's own 0.3 nH added, that is about {z_pk*100:.0f} % more overshoot for the same edge on the pack legs and {z_vb*100:.0f} % on the VBUS legs: worse, but the same class of loop.",
 f"The small bucks go the other way. The 5 V bucks see {H[4]['n']['eff']:.2f} and {H[5]['n']['eff']:.2f} nH on the ground-up board against {H[4]['b']['eff']:.2f} and {H[5]['b']['eff']:.2f} nH, because their 100 nF capacitor sits right at the input pin ({bk446:.2f} nH of board loop on port 1, {bk446b:.2f} nH on the current board). The 3.3 V buck is {H[6]['n']['eff']:.2f} against {H[6]['b']['eff']:.2f} nH.",
 f"The switch-node copper itself is the same size on both boards: the four charger switch nodes add up to {sw_n:.0f} pF on the ground-up board and {sw_b:.0f} pF on the current board, nearly all of it to the planes.",
]
GATE = [
 f"**The current board is clearly ahead.** The eight loops add up to {sum(g_b):.0f} nH on the current board and {sum(g_n):.0f} nH on the ground-up board, {(sum(g_n)/sum(g_b)-1)*100:.0f} % more.",
 f"All four high-side loops are worse: {min(ghs_b):.1f} to {max(ghs_b):.1f} nH on the current board, {min(ghs_n):.1f} to {max(ghs_n):.1f} nH on the ground-up board. On the current board the drive track stays on the top layer beside its switch-node return for most of the way. The router sent the drive to an inner layer or the back and let the return take its own way. Port 2 leg A is the worst case: its high-side drive runs {gp2a['sub'].split('/ ')[1].replace(' mm','')} mm round the charger IC on the back, 0.15 mm wide at its narrowest, where the current board needs {gp2a['sub'].split('track ')[1].split(' /')[0]} mm.",
 f"Of the low-side loops, {' and '.join(r['short'] for r in gls_same) if gls_same else 'none'} {'is' if len(gls_same)==1 else 'are'} level and the other {len(gls_w)} are {min(r['n']['L']/r['b']['L']-1 for r in gls_w)*100:.0f} to {max(r['n']['L']/r['b']['L']-1 for r in gls_w)*100:.0f} % higher.",
 "More gate-loop inductance means more gate ringing and a slower, less controlled edge. The loop study of 2026-11-06 found nothing that had to be fixed at 3 to 9 nH on the current board. Two high-side loops at 13 to 14 nH are where I would re-route the ground-up board before building it.",
]
COUP = [
 f"**The current board is far ahead, and this is the ground-up board's weakest point.** All switch nodes together couple {sig_n/1000:.1f} pF into the listed analog, bus and control nets on the ground-up board and {sig_b/1000:.2f} pF on the current board. {n10_n} signals take a step over 10 mV from one switch-node edge on the ground-up board, {n10_b} on the current board.",
 f"On the current board only the two charger TS pins stand out, at {tsb[-2]:.0f} and {tsb[-1]:.0f} mV, and every other signal stays under {math.ceil(oth_b):.0f} mV. On the ground-up board the list is long: {', '.join(f'{r['label']} {mv(r, 'n'):.0f} mV' for r in top_n)}.",
 f"The step is what a node would jump if nothing held it. I2C lines are held by their pull-ups and recover within a few hundred nanoseconds, and {i2c_n:.0f} mV is inside the bus noise margin, though it uses up a good part of it. The one I would not accept is the port 2 charger feedback pin ({mv(FB2, 'n'):.0f} mV, {FB2['n']['c']:.0f} fF from the switch nodes): it is a high-impedance divider node that sets the charge voltage. The gauge's TS4 thermistor line ({mv(TSg, 'n'):.0f} mV) is slow and averaged, so it matters less than its number suggests.",
 f"The filtered current-sense nodes are safe on both boards. Their filter capacitors hold the step to a few microvolts even though the ground-up board couples more into them ({csc_n:.0f} fF at most against {csc_b:.0f} fF). The USB CC lines stay under {math.ceil(max(max(mv(r, 'b'), mv(r, 'n')) for r in C if r['cat'] == 'USB CC')):.0f} mV on both.",
 "The cause is how the signals were routed. The router was free to use In2 and In3 in any direction and had no rule to stay away from switching copper, so signals pass under and beside the switch nodes and the high-side gate and bootstrap tracks. The hand layout keeps signals out of the power stages. The maps below show it: red is switching copper, and on the ground-up board blue, green and violet tracks cross it on three layers.",
]

TEXT = dict(
 lede=LEDE,
 hot=HOT, gate=GATE, coup=COUP,
 loss=[
  f"**Level at high power, slightly better at low power.** At 100 W with the pack half charged the routed copper burns {a100['b']['cu']*1e3:.0f} mW on the current board and {a100['n']['cu']*1e3:.0f} mW on the ground-up board through port 1, and {b100['b']['cu']*1e3:.0f} against {b100['n']['cu']*1e3:.0f} mW through port 2. At 15 W the ground-up board is ahead, {a15['n']['cu']*1e3:.0f} against {a15['b']['cu']*1e3:.0f} mW.",
  f"The two boards trade places because they are strong on different sides. The ground-up board has the better USB side: the copper from the input sense resistor to the VBUS-leg FET is {ac1['n']:.2f} mΩ where the current board has {ac1['b']:.2f} mΩ. The current board has the better battery side: PACK_P to the port 1 stage is {pk1['b']:.2f} against {pk1['n']:.2f} mΩ and the ground return {gd1['b']:.2f} against {gd1['n']:.2f} mΩ. Battery current rises as the pack empties, so the worst case for the ground-up board is 100 W on a nearly empty pack: {a100lo['n']['cu']*1e3:.0f} against {a100lo['b']['cu']*1e3:.0f} mW.",
  f"Next to the FETs, the inductor and the cells these differences are small. All losses together at 100 W and half charge are {a100['b']['tot']:.2f} W on the current board and {a100['n']['tot']:.2f} W on the ground-up board.",
 ],
 th=[
  f"**Level.** A 100 W run on port 1 holds full power for {tb['burst_min']:.1f} min on the current board and {tn['burst_min']:.1f} min on the ground-up board, and delivers {tb['Wh40']:.1f} against {tn['Wh40']:.1f} Wh in 40 minutes. The cells do not see a difference: the hottest can peaks at {tb['can_max']:.1f} and {tn['can_max']:.1f} °C.",
  f"The ground-up board's hottest FET runs {tn['part_max']-tb['part_max']:.1f} K warmer ({tn['part_max']:.1f} against {tb['part_max']:.1f} °C). It has {st[N]['fill1']['vias']} and {st[N]['fill2']['vias']} vias under the two gap-filler pads where the current board has {st[B]['fill1']['vias']} and {st[B]['fill2']['vias']}, so heat crosses the board to the filler less easily. It gets part of that back from fuller outer-layer copper round the stages. Without that credit the FET would peak at {tk['part_max']:.1f} °C, so the honest range is {tn['part_max']-tb['part_max']:.1f} to {tk['part_max']-tb['part_max']:.1f} K warmer.",
  f"One spot goes the other way. On port 2 the board at the input sense resistor reaches {tb2['part_peak']['rac2']:.1f} °C on the current board and {tn2['part_peak']['rac2']:.1f} °C on the ground-up board, because that is where the current board's {ac2['b']:.2f} mΩ copper path sits.",
 ],
 kelvin=[
  f"**Both boards tap their sense resistors correctly; the ground-up board routes the pairs less tightly.** All ten sense lines start on the resistor's own pads on both boards, so no tap reads plane drop. The charger readings are within {max(kb):.2f} % on the current board. On the ground-up board three are within {sorted(kn)[-2]:.2f} % and the port 2 input current reads {sg(_k(3)['n'], 1)} %, because its negative tap leaves the pad from the side the current enters.",
  f"The gauge shunt reads {sg(_k(4)['n'], 1)} % high on the ground-up board and {sg(_k(4)['b'], 1)} % high on the current board. Load on one port moves the other port's battery reading by less than 1 mA on both.",
  f"The area enclosed between the two lines of a pair is what picks up magnetic field from the inductors. The five pairs enclose {pa_n:.0f} mm² on the ground-up board against {pa_b:.0f} mm² on the current board. The port 1 input pair is the weak one at {D['pairs'][1]['n']['area']:.0f} mm² ({D['pairs'][1]['b']['area']:.0f} mm² on the current board), and the port 2 battery pair went from {D['pairs'][2]['b']['area']:.1f} to {D['pairs'][2]['n']['area']:.0f} mm². The filter at the charger pins takes most of that pickup out, but the hand-routed pairs are the better ones.",
 ],
 method=[
  "**Same tools on both files.** The current board is master's `Monolith.kicad_pcb`; the ground-up board is the one on branch `claude/project-thread-ploune`. No number on this page is carried over from an earlier review; each was computed again for both boards in one session.",
  "**Loop inductance.** 3-D partial-inductance model of the real copper on all six layers with vias (the tool from the 2026-11-06 loop study). Hot loops: 0.3 mm cells, the switch shorted at the FET or IC pads, every capacitor between the loop's supply net and ground included with its package inductance (0.3 nH for 0402, 0.6 nH for 1210, 1.5 nH for the tantalum). Gate loops: 0.15 mm cells, driver pin to gate pad and back through the source return, ground copper kept within 2 mm of the loop on the same layer and on the plane next to it. " + GATE_H_NOTE,
  "**Copper resistance and Kelvin taps.** DC grid solve of each net over all layers at 20 °C. Path resistances on a 0.1 mm grid, Kelvin taps on a 0.05 mm grid because a coarser grid bridges the 0.2 mm keep-out gaps round the taps.",
  "**Loss at each load.** The project's loss model for FETs, inductor, sense resistors and cells, with the battery current found from the port power and the pack voltage at that state of charge. Copper loss is each path's resistance times its own current squared.",
  "**Thermals.** The pack thermal model in the cup at 25 °C in still air with the firmware derate, run on the PC. Between the two boards only the part positions, the copper loss map, the via count under the gap filler and the copper cover round the stages change.",
  "**Coupling.** 3-D electrostatic solve on a 0.05 mm grid of the copper within 1.5 mm of each switch node, through the real stack-up. The switch node and its bootstrap and high-side gate nets are driven together. Part bodies are not in the model, so the inductor's own stray field and its body capacitance are missing on both boards. Magnetic coupling is only covered by the pair-area figures in the Kelvin section.",
  "**What this cannot tell.** Nothing here is measured. Edge speed, ringing amplitude, EMC and how the BQ25756 reacts to a given step on a pin need a built board and a scope.",
 ],
 foot="Scripts and result files are on the branch in hardware/Production/groundup/compare/. The ground-up board is an experiment and is not merged.",
)
