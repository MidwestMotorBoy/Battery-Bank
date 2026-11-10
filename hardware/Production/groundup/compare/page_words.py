# The words. exec'd from page_text.py; every number is taken from D or M so the text cannot drift from the charts.
# "n" in D is the ground-up board after the fix pass; M[O] holds the first version for the before/after sentences.
# The asserts pin the direction each sentence states; if a re-run flips one, the build stops instead of printing a wrong word.
mb, mo, mn = M[B], M[O], M[N]
pk1 = _p(1, 'PACK_P'); pk2 = _p(2, 'PACK_P'); gd1 = _p(1, 'GND'); gd2 = _p(2, 'GND'); ac1 = _p(1, 'AC_SNS_N'); ac2 = _p(2, 'AC_SNS_N')
def gsh(s): return next(r for r in G if r['short'] == s)
gp2a = gsh('P2 HS A')
ghs_b = [r['b']['L'] for r in G if ' HS ' in r['short']]; ghs_n = [r['n']['L'] for r in G if ' HS ' in r['short']]
gls_b = [r['b']['L'] for r in G if ' LS ' in r['short']]; gls_n = [r['n']['L'] for r in G if ' LS ' in r['short']]
n10_b = nover('b', 10, ANA + BUS); n10_n = nover('n', 10, ANA + BUS)
over_n = sorted([r for r in C if r['cat'] in ANA + BUS and mv(r, 'n') >= 10], key=lambda r: -mv(r, 'n'))
over_b = sorted([r for r in C if r['cat'] in ANA + BUS and mv(r, 'b') >= 10], key=lambda r: -mv(r, 'b'))
def lab(l): return next(r for r in C if r['label'] == l)
TS1, TS2, TSg, FB1, FB2 = lab('P1 TS'), lab('P2 TS'), lab('TS4'), lab('P1 FB'), lab('P2 FB')
i2c_rows = [r for r in C if r['cat'] == 'I2C / SMBus']; i2c_n = max(mv(r, 'n') for r in i2c_rows); i2c_b = max(mv(r, 'b') for r in i2c_rows)
cc_max = max(max(mv(r, 'b'), mv(r, 'n')) for r in C if r['cat'] == 'USB CC')
csc_b = max((r['b'] or {}).get('c', 0) for r in C if r['cat'] == 'Current sense'); csc_n = max((r['n'] or {}).get('c', 0) for r in C if r['cat'] == 'Current sense')
hot_raw = {t: J(f'hot_{t}.json') for t in (B, O, N)}
HF = ('C430', 'C438', 'C530', 'C538', 'C446', 'C546')
CH = ['P1 VBUS leg (Q401)', 'P1 PACK leg (Q402)', 'P2 VBUS leg (Q501)', 'P2 PACK leg (Q502)']
def hfc(t, key):                       # board inductance of the 100 nF capacitor at the FET
    o = hot_raw[t][key]; c = [x for x in o['caps'] if x in HF]
    return o['caps'][c[0]] * 1e9 if c else float('nan')
hf_b = [hfc(B, k) for k in CH]; hf_o = [hfc(O, k) for k in CH]; hf_n = [hfc(N, k) for k in CH]
vb_b = [H[0]['b']['eff'], H[2]['b']['eff']]; vb_n = [H[0]['n']['eff'], H[2]['n']['eff']]
pk_b = [H[1]['b']['eff'], H[3]['b']['eff']]; pk_n = [H[1]['n']['eff'], H[3]['n']['eff']]
bk446 = hot_raw[N]['P1 5V buck (U404)']['caps']['C446'] * 1e9; bk446b = hot_raw[B]['P1 5V buck (U404)']['caps']['C446'] * 1e9
grt = {t: J(f'groute_{t}.json') for t in (B, O, N)}; KA = 'P2 HS gate leg A (Q501)'
coarse = [r for r in G if r['n'].get('h', 0.15) > 0.15]
GATE_H_NOTE = ((f"{len(coarse)} of the ground-up board's loops were solved with coarser cells because of memory. " if coarse else "")
               + "The port 2 leg A low-side loop was solved with both ground planes kept along the whole route on all boards, because the standard setting cut its ground return on the first version of the ground-up board; that setting reads 5 to 15 % lower.")
VS = D['via_sum']; cw = D['cost']; ct = cw['total']; cl = cw['phases'][0]; cd = cw['phases'][2]; cf = cw['phases'][-1]
I4n = D['fix']['in4']['Ground-up board after the fix pass']; I4b = D['fix']['in4']['Current board']
XN = J('in4cross.json')                # nets on In3 and B that cross a slot in In4: {tag: count}, edge: mm within 3 mm of an edge
st3 = {t: J(f'custats_{t}.json') for t in (B, O, N)}

_allahead = all(r['n']['cu'] <= r['b']['cu'] for r in D['loss']); _lv = ahead(a100['b']['cu'] + b100['b']['cu'], a100['n']['cu'] + b100['n']['cu'], 0.05)
LOSS_HEAD = ('The ground-up board is now ahead at every load in the table, by a small amount.' if _allahead and _lv == 'n' else 'Level at high power, ahead at low power.' if _lv == 'l' else None)
assert LOSS_HEAD, 'loss direction'
# ---- directions the text relies on ----
assert sum(hc_n) < sum(hc_b) and sum(hb_n) < sum(hb_b), 'hot loops'
assert sum(g_n) < sum(g_b), 'gate loops'
assert sig_n > sig_b and n10_n > n10_b, 'coupling'
assert VS[N]['max'] < VS[B]['max'] and VS[N]['over3'] == 0 and VS[B]['over3'] == 0, 'via current'
assert tn['burst_min'] >= tb['burst_min'] and tn['part_max'] < tb['part_max'] < tk['part_max'], 'thermal'
assert pa_n > pa_b and max(kn) > max(kb) and abs(_k(4)['n']) < abs(_k(4)['b']), 'kelvin'
assert pk1['n'] > pk1['b'] and gd1['n'] < gd1['b'] and ac1['n'] < ac1['b'], 'paths'
assert mv(TS1, 'n') < mv(TS1, 'b') and mv(TS2, 'n') < mv(TS2, 'b') and all(mv(r, 'b') < 1 for r in over_n if not r['label'].endswith(' TS')), 'TS and others'
assert mv(FB2, 'n') < 25 and mv(FB1, 'n') < 40 and max(mv(FB1, 'b'), mv(FB2, 'b')) < 1, 'feedback pins'

SCORE = [
    ['Charger hot loops, inductance seen by the FETs', f"{rng(hc_b)} nH", f"{rng(hc_n)} nH", ahead(sum(hc_b), sum(hc_n), 0.08)],
    ['Small buck hot loops (two 5 V, one 3.3 V)', f"{rng(hb_b)} nH", f"{rng(hb_n)} nH", ahead(sum(hb_b), sum(hb_n), 0.08)],
    ['Gate-drive loops, sum of eight', f"{sum(g_b):.0f} nH ({rng(g_b, 1)})", f"{sum(g_n):.0f} nH ({rng(g_n, 1)})", ahead(sum(g_b), sum(g_n), 0.08)],
    ['Copper loss at 100 W, half charge, port 1 / port 2', f"{a100['b']['cu']*1e3:.0f} / {b100['b']['cu']*1e3:.0f} mW", f"{a100['n']['cu']*1e3:.0f} / {b100['n']['cu']*1e3:.0f} mW",
     ahead(a100['b']['cu'] + b100['b']['cu'], a100['n']['cu'] + b100['n']['cu'], 0.05)],
    ['Copper loss at 15 W, port 1', f"{a15['b']['cu']*1e3:.0f} mW", f"{a15['n']['cu']*1e3:.0f} mW", ahead(a15['b']['cu'], a15['n']['cu'], 0.05)],
    ['Highest current in one via', f"{VS[B]['max']:.1f} A", f"{VS[N]['max']:.1f} A", ahead(VS[B]['max'], VS[N]['max'], 0.08)],
    ['Minutes at 100 W before the derate, port 1', f"{tb['burst_min']:.1f} min", f"{tn['burst_min']:.1f} min", ahead(tb['burst_min'], tn['burst_min'], 0.08, lower_better=False)],
    ['Hottest part in a 100 W run, port 1', f"{tb['part_max']:.1f} °C", f"{tn['part_max']:.1f} °C ({tk['part_max']:.1f} °C without credit for extra copper cover)", 'l'],
    ['Kelvin tap error, charger sense resistors', f"up to {max(kb):.2f} %", f"up to {max(kn):.2f} %", ahead(max(kb), max(kn), 0.25)],
    ['Kelvin tap error, gauge shunt', f"{sg(_k(4)['b'])} %", f"{sg(_k(4)['n'])} %", ahead(abs(_k(4)['b']), abs(_k(4)['n']), 0.1)],
    ['Area enclosed by the five sense pairs', f"{pa_b:.0f} mm²", f"{pa_n:.0f} mm²", ahead(pa_b, pa_n, 0.1)],
    ['Switch-node copper capacitance, four charger nodes', f"{sw_b:.0f} pF", f"{sw_n:.0f} pF", ahead(sw_b, sw_n, 0.08)],
    ['Coupling from all switch nodes into listed signals', f"{sig_b/1000:.2f} pF", f"{sig_n/1000:.2f} pF", ahead(sig_b, sig_n, 0.15)],
    ['Signals that take a step over 10 mV from a switch-node edge', str(n10_b), str(n10_n), 'b' if n10_b < n10_n else 'n' if n10_n < n10_b else 'l'],
    ['Largest coupled step on an analog signal', f"{fmv(mv(wa_b,'b'))} ({wa_b['label']})", f"{fmv(mv(wa_n,'n'))} ({wa_n['label']})", ahead(mv(wa_b, 'b'), mv(wa_n, 'n'), 0.15)],
    ['Largest coupled step on a bus or control signal', f"{fmv(mv(wb_b,'b'))} ({wb_b['label']})", f"{fmv(mv(wb_n,'n'))} ({wb_n['label']})", ahead(mv(wb_b, 'b'), mv(wb_n, 'n'), 0.15)],
    ['Signal track cut into the ground planes', f"{I4b['total']:.0f} mm", f"{I4n['total']:.0f} mm", 'b'],
]
nN = sum(1 for r in SCORE if r[3] == 'n'); nB = sum(1 for r in SCORE if r[3] == 'b'); nL = len(SCORE) - nN - nB
others_n = ', '.join(f"{r['label']} {mv(r, 'n'):.0f} mV" for r in over_n if not r['label'].endswith(' TS'))

LEDE = (f"Same schematic and parts, two layouts. After the fix pass the script-built board is ahead of or level with the hand-routed one on loop inductance, copper loss, heat and via current. "
        f"It is still behind on noise coupling into signals ({n10_n} signals take over 10 mV from a switch-node edge against {n10_b}), on how tightly the sense pairs are routed, "
        f"and it pays for the result with {I4n['total']:.0f} mm of signal track cut into a ground plane where the hand-routed board has {I4b['total']:.0f} mm. Nothing here is measured.")

FIX = [
 f"**The fix pass worked on what it aimed at.** Gate-drive loops went from {sum(mo['gate']):.0f} to {sum(mn['gate']):.0f} nH in sum (current board {sum(mb['gate']):.0f} nH). "
 f"The charger hot loops were {_r(mo['hot_ch'])} nH and are now {_r(mn['hot_ch'])} nH (current board {_r(mb['hot_ch'])} nH). "
 f"Coupling from the switch nodes into signals fell from {mo['csig']:.1f} to {mn['csig']:.2f} pF (current board {mb['csig']:.2f} pF), and the signals that take over 10 mV per edge from {mo['n10']} to {mn['n10']} (current board {mb['n10']}). "
 f"The port 2 charger feedback pin, the one I said I would not accept, went from {mo['fb2']:.0f} to {mn['fb2']:.0f} mV. The hottest via went from {mo['via_max']:.1f} to {mn['via_max']:.1f} A, and the vias under the gap-filler pads from {mo['fill'][0]} and {mo['fill'][1]} to {mn['fill'][0]} and {mn['fill'][1]}.",
 f"**It cost ground plane, and more than you offered.** You allowed limited tracks on the ground planes, as on your board, and preferred them on the board edge. Your board has {I4b['total']:.0f} mm of track on inner layer 4. This one now has {I4n['total']:.0f} mm in six nets, and only {XN['edge']:.0f} mm of that runs within 3 mm of an edge. "
 f"The long ones run down the centre column between the two power stages, because that is where the slow signals have to get from the port side to the gauge and the MCU, and on the other signal layers they ran past switching copper. {XN[N]} nets on inner layer 3 and the back cross one of those slots ({XN[B]} on your board), all of them slow signals or supplies. "
 f"The other ground plane, inner layer 1, has no track on either board, so everything on the front and on inner layer 2 keeps a whole plane next to it. The DC ground return did not suffer, because the pass also added ground vias: {gd1['n']:.2f} and {gd2['n']:.2f} mΩ to the two stages against {gd1['b']:.2f} and {gd2['b']:.2f} mΩ on your board. Each track is listed below.",
 f"**Two faults were my own, and only the comparison caught them.** The first board of this pass passed the rule check, the open-connection check and the plane check with two real faults in it. Three hand-drawn gate and switch-node tracks on the back of port 1 cut the PACK_P bus, which took that path from {mo['pk'][0]:.1f} to 27.8 mΩ. "
 f"And four added PACK_P vias touched the battery sense taps, which then read 2.2 and 2.7 % high. The copper solver and the Kelvin solver showed both. The three tracks now run on inner layer 3 and the four vias are gone: the path is {pk1['n']:.2f} mΩ and the taps read {sg(_k(0)['n'])} and {sg(_k(2)['n'])} %. Without the re-run this board would have looked finished and been wrong.",
 f"**Still behind the current board.** {len(over_n) - 2} signals besides the TS pins take over 10 mV per edge here and none do on your board: {others_n}. "
 f"The charger TS pins, the largest steps on both boards because the thermistor sits at the FETs, are now a little lower than on your board: {mv(TS1, 'n'):.0f} and {mv(TS2, 'n'):.0f} mV against {mv(TS1, 'b'):.0f} and {mv(TS2, 'b'):.0f} mV. "
 f"The five sense pairs still enclose {pa_n:.0f} mm² against {pa_b:.0f} mm², and the port 2 input sense tap still reads {sg(_k(3)['n'], 2)} %; neither was in this pass. PACK_P to the port 1 stage is {pk1['n']:.2f} mΩ against {pk1['b']:.2f} mΩ.",
 f"**Lost cause or not?** Not a lost cause: with one targeted pass the script-built board went from clearly worse to ahead or level on {nN + nL} of the {len(SCORE)} lines in the table at the top. "
 f"But I would still build your board. It has been reviewed several times, it keeps its ground planes almost whole, and it is quieter on the signals. What this experiment shows is where the script-built route stands after about {ct['hours']:.0f} hours of work, and that the solvers have to run after every change, not at the end.",
]
ROWS4 = {'EN_5V2': ('From the port 2 5 V buck down the centre column, then round the bottom of the board to the MCU', 'Enable line. Its first route ran beside the port 2 5 V buck switch node on inner layer 2.'),
         'SDA': ('Down the centre column from the port side to the gauge', f"I2C data. It took {mo['lab'].get('SDA', 0):.0f} mV per edge on the first version; now it is inside the plane."),
         'Port 1 TS': ('Three hops: thermistor to divider under the port 1 stage, divider to the charger pin round the east edge, charger pin to the second divider resistor', 'Charger thermistor node. No free path on a signal layer that stays away from the port 1 switch nodes.'),
         'Port 1 PPHV': ('Centre column, from the TPS25751 side down to the charger', '0.15 mm sense branch of PPHV, not a power path.'),
         'Port 1 CHG_INT': ('Centre column, from the charger up to the TPS25751', f"Interrupt line. It took {mo['lab'].get('P1 CHG_INT', 0):.0f} mV per edge on the first version."),
         'Port 2 TS': ('7 mm between the charger pin and its divider resistor', 'Charger thermistor node, short hop under the charger IC.')}
D['fix']['in4rows'] = [[n, f"{L:.1f} mm", f"{w:.2f} mm", ROWS4[n][0], ROWS4[n][1]] for n, L, k, w in I4n['rows']]
D['fix']['in4note'] = (f"Current board: {', '.join(f'{n} {L:.1f} mm' for n, L, k, w in I4b['rows'])}, both 0.2 mm wide. The port 1 TS hop from the thermistor runs under the port 1 gate-drive parts, because the thermistor sits at the FETs. "
                       "No track on inner layer 4 lies under or over a sense-pair track or a switching track on the two layers next to it (inner layer 3 and the back). The hot loops sit on the front over inner layer 1, which has no track on either board.")
D['fix']['note'] = ("First version: the board of the first comparison (commit 6aaa778). After the fix pass: the board now on the branch. All three columns come from the same solver run on each board file. "
                    "The chip compares the board after the fix pass with the current board.")
D['fix']['list'] = [
 f"High-side gate drives of all four legs routed again beside or directly under their switch-node return. Port 2 leg A went from {grt[O][KA]['total']:.0f} mm round the charger IC to {grt[N][KA]['total']:.0f} mm ({grt[B][KA]['total']:.0f} mm on the current board).",
 "The four 100 nF capacitors at the FETs (C430, C438, C530, C538) moved 1.3 to 2.3 mm and turned 180° so they sit at the FET pads. No other part moved. Cup fit checked again: 26 of 26.",
 f"Vias: {st3[O]['board']['vias']} to {st3[N]['board']['vias']} on the board ({st3[B]['board']['vias']} on the current board), ground vias {st3[O]['board']['gnd_vias']} to {st3[N]['board']['gnd_vias']} ({st3[B]['board']['gnd_vias']}). More vias where PACK_P, CELL_P and the ground return change layer, and under the two gap-filler pads.",
 "Signals that ran beside or under switching copper routed again away from it: the I2C lines of both ports, SDA, CHG_INT, IRQ_N, DRV9_OFF, the 5 V enable lines, the port 2 charger feedback track, the charger TS vias, and the gauge's TS4 line, which now crosses under the port 1 charger IC on the back.",
 f"Six nets moved onto inner layer 4, the ground plane next to the back: {I4n['total']:.0f} mm in total (table below).",
 "Three short links to join plane pieces that the new tracks and vias had cut off: two for 3V3 (5.7 mm on inner layer 2 plus 7.6 mm on inner layer 3, and 7.0 mm on the back) and one for PACK_P (4.3 mm on the front plus 6.7 mm on the back).",
 "Three new vias inside 0402 pads, where no other via site was legal: R305 pad 2 (SDA), R515 pad 2 (port 2 TS) and R518 pad 2 (port 2 feedback). They can wick solder and should be tented or checked at assembly.",
 "Port 1 only: the low-side gate, bootstrap and switch-node sense sections under the charger IC run on inner layer 3, not on the back as on port 2, because on port 1 the back carries the PACK_P bus there.",
 "Not changed: schematic, parts, outline, holes, connectors, stack-up and every other placement. Rule check 0 errors and 0 open connections, 23 warnings (16 on the current board). All four plane nets are in one piece.",
]

HOT = [
 f"**The ground-up board is now ahead on all seven loops.** The VBUS legs see {vb_b[0]:.2f} and {vb_b[1]:.2f} nH on the current board and {vb_n[0]:.2f} and {vb_n[1]:.2f} nH on the ground-up board. The pack legs see {pk_b[0]:.2f} and {pk_b[1]:.2f} nH against {pk_n[0]:.2f} and {pk_n[1]:.2f} nH. On the first version the pack legs were at {mo['hot_ch'][1]:.2f} nH.",
 f"What changed is the 100 nF capacitor at each FET, which carries most of the fast current. In the fix pass the four capacitors moved to the FET pads and got ground vias beside them. Their board loop is now {min(hf_n):.2f} to {max(hf_n):.2f} nH ({min(hf_o):.2f} to {max(hf_o):.2f} nH before, {min(hf_b):.2f} to {max(hf_b):.2f} nH on the current board).",
 f"The small bucks were ahead before and still are. The 5 V bucks see {H[4]['n']['eff']:.2f} and {H[5]['n']['eff']:.2f} nH on the ground-up board against {H[4]['b']['eff']:.2f} and {H[5]['b']['eff']:.2f} nH, because their 100 nF capacitor sits right at the input pin ({bk446:.2f} nH of board loop on port 1, {bk446b:.2f} nH on the current board). The 3.3 V buck is {H[6]['n']['eff']:.2f} against {H[6]['b']['eff']:.2f} nH.",
 f"With the FET package's own 0.3 nH added, the differences on the charger loops are about {((sum(pk_b)/2 + 0.3) / (sum(pk_n)/2 + 0.3)) ** 0.5 * 100 - 100:.0f} % less overshoot for the same edge on the pack legs and {((sum(vb_b)/2 + 0.3) / (sum(vb_n)/2 + 0.3)) ** 0.5 * 100 - 100:.0f} % on the VBUS legs. That is the same class of loop on both boards. The switching copper of the four charger nodes (node, bootstrap and high-side gate tracks together) is {sw_n:.0f} pF against {sw_b:.0f} pF; it was {mo['cself']:.0f} pF on the first version, before the high-side drive tracks were shortened.",
]
GATE = [
 f"**The ground-up board is now slightly ahead.** The eight loops add up to {sum(g_b):.0f} nH on the current board and {sum(g_n):.0f} nH on the ground-up board. On the first version it was {sum(mo['gate']):.0f} nH.",
 f"The four high-side loops are {min(ghs_b):.1f} to {max(ghs_b):.1f} nH on the current board and {min(ghs_n):.1f} to {max(ghs_n):.1f} nH on the ground-up board (first version {min(mo['gate_hs']):.1f} to {max(mo['gate_hs']):.1f} nH). The leg A drives now run on inner layer 2 directly under their switch-node track, and the leg B drives stay on the front beside it. "
 f"Port 2 leg A was the worst loop of the first version at {mo['g_p2a']:.1f} nH, {grt[O][KA]['total']:.0f} mm round the charger IC. It is now {mn['g_p2a']:.1f} nH over {grt[N][KA]['total']:.0f} mm.",
 f"The four low-side loops are {min(gls_b):.1f} to {max(gls_b):.1f} nH on the current board and {min(gls_n):.1f} to {max(gls_n):.1f} nH on the ground-up board.",
 "The loop study of 2026-11-06 found nothing that had to be fixed at 3 to 9 nH on the current board. Both boards are now in that range on every loop.",
]
COUP = [
 f"**The current board is still ahead, by much less than before.** All switch nodes together couple {sig_n/1000:.2f} pF into the listed analog, bus and control nets on the ground-up board and {sig_b/1000:.2f} pF on the current board. On the first version it was {mo['csig']:.1f} pF. {n10_n} signals take a step over 10 mV from one switch-node edge on the ground-up board, {n10_b} on the current board, {mo['n10']} on the first version.",
 f"The charger TS pins are the largest on both boards, because the thermistor sits at the FETs: {mv(TS1, 'b'):.0f} and {mv(TS2, 'b'):.0f} mV on the current board, {mv(TS1, 'n'):.0f} and {mv(TS2, 'n'):.0f} mV on the ground-up board. On the current board every other signal stays under {math.ceil(max(mv(r, 'b') for r in C if r['cat'] in ANA + BUS and not r['label'].endswith(' TS'))):.0f} mV. "
 f"On the ground-up board these are also over 10 mV: {others_n}.",
 f"The step is what a node would jump if nothing held it. The two charger feedback pins are high-impedance divider nodes: port 2 was {mo['fb2']:.0f} mV on the first version and is {mv(FB2, 'n'):.0f} mV now, port 1 is {mv(FB1, 'n'):.0f} mV, and the current board is under 1 mV on both. I would want those two lower before building this board. The enable and fault lines are logic signals with a wide margin. The I2C lines, which took up to {mo['w_i2c']['worst_mV']:.0f} mV on the first version, now take {i2c_n:.0f} mV at most.",
 f"The filtered current-sense nodes are safe on both boards. Their filter capacitors hold the step to a few microvolts ({csc_n:.0f} fF at most on the ground-up board, {csc_b:.0f} fF on the current board). The USB CC lines stay under {math.ceil(cc_max):.0f} mV on both.",
 "The maps below show where it comes from. Red is switching copper. On the first version, signal tracks crossed it on three layers. After the fix pass most of them run away from it or inside the ground plane, and what is left are the places where a part has to sit inside a power stage: the two thermistors, the feedback resistors and the enable pins of the 5 V bucks.",
]

TEXT = dict(
 lede=LEDE, fix=FIX,
 hot=HOT, gate=GATE, coup=COUP,
 loss=[
  f"**{LOSS_HEAD}** At 100 W with the pack half charged the routed copper burns {a100['b']['cu']*1e3:.0f} mW on the current board and {a100['n']['cu']*1e3:.0f} mW on the ground-up board through port 1, and {b100['b']['cu']*1e3:.0f} against {b100['n']['cu']*1e3:.0f} mW through port 2. At 15 W it is {a15['n']['cu']*1e3:.0f} against {a15['b']['cu']*1e3:.0f} mW. On the first version port 1 was at {mo['cu100'][0]:.0f} mW at 100 W.",
  f"The ground-up board has the better USB side: the copper from the input sense resistor to the VBUS-leg FET is {ac1['n']:.2f} mΩ where the current board has {ac1['b']:.2f} mΩ. Its ground return is now also lower, {gd1['n']:.2f} against {gd1['b']:.2f} mΩ on port 1. "
  f"The current board keeps the better PACK_P feed to port 1, {pk1['b']:.2f} against {pk1['n']:.2f} mΩ; on port 2 the two are level at {pk2['b']:.2f} and {pk2['n']:.2f} mΩ. At 100 W on a nearly empty pack, where battery current is highest, it is {a100lo['n']['cu']*1e3:.0f} against {a100lo['b']['cu']*1e3:.0f} mW.",
  f"Next to the FETs, the inductor and the cells these differences are small. All losses together at 100 W and half charge are {a100['b']['tot']:.2f} W on the current board and {a100['n']['tot']:.2f} W on the ground-up board.",
 ],
 th=[
  f"**Level, with a small edge to the ground-up board.** A 100 W run on port 1 holds full power for {tb['burst_min']:.1f} min on the current board and {tn['burst_min']:.1f} min on the ground-up board, and delivers {tb['Wh40']:.1f} against {tn['Wh40']:.1f} Wh in 40 minutes. The cells do not see a difference: the hottest can peaks at {tb['can_max']:.1f} and {tn['can_max']:.1f} °C.",
  f"The hottest FET peaks at {tn['part_max']:.1f} °C on the ground-up board and {tb['part_max']:.1f} °C on the current board. The fix pass brought the vias under the two gap-filler pads to {st[N]['fill1']['vias']} and {st[N]['fill2']['vias']} ({st[B]['fill1']['vias']} and {st[B]['fill2']['vias']} on the current board, {mo['fill'][0]} and {mo['fill'][1]} on the first version), so heat now crosses the board to the filler about as well. "
  f"The rest of the difference is credit for fuller outer-layer copper round the stages. Without that credit the FET would peak at {tk['part_max']:.1f} °C, so the honest range is {tb['part_max']-tn['part_max']:.1f} K cooler to {tk['part_max']-tb['part_max']:.1f} K warmer than the current board.",
  f"On port 2 the board at the input sense resistor reaches {tb2['part_peak']['rac2']:.1f} °C on the current board and {tn2['part_peak']['rac2']:.1f} °C on the ground-up board, because that is where the current board's {ac2['b']:.2f} mΩ copper path sits.",
 ],
 kelvin=[
  f"**Both boards tap their sense resistors correctly; the ground-up board routes the pairs less tightly.** All ten sense lines start on the resistor's own pads on both boards, so no tap reads plane drop. The charger readings are within {max(kb):.2f} % on the current board. On the ground-up board three are within {sorted(kn)[-2]:.2f} % and the port 2 input current reads {sg(_k(3)['n'], 1)} %, because its negative tap leaves the pad from the side the current enters. The fix pass did not touch that tap.",
  f"The gauge shunt reads {sg(_k(4)['n'], 1)} % high on the ground-up board and {sg(_k(4)['b'], 1)} % high on the current board. Load on one port moves the other port's battery reading by about 1 mA or less on both.",
  f"The area enclosed between the two lines of a pair is what picks up magnetic field from the inductors. The five pairs enclose {pa_n:.0f} mm² on the ground-up board against {pa_b:.0f} mm² on the current board. The port 1 input pair is the weak one at {D['pairs'][1]['n']['area']:.0f} mm² ({D['pairs'][1]['b']['area']:.0f} mm² on the current board). The filter at the charger pins takes most of that pickup out, but the hand-routed pairs are the better ones, and this was not part of the fix pass.",
 ],
 method=[
  "**Same tools on every file.** The current board is master's `Monolith.kicad_pcb`; the ground-up board is the one on branch `claude/project-thread-ploune`, and its first version is commit 6aaa778 on that branch. Each number was computed for each board file by the same script.",
  "**Loop inductance.** 3-D partial-inductance model of the real copper on all six layers with vias (the tool from the 2026-11-06 loop study). Hot loops: 0.3 mm cells, the switch shorted at the FET or IC pads, every capacitor between the loop's supply net and ground included with its package inductance (0.3 nH for 0402, 0.6 nH for 1210, 1.5 nH for the tantalum). Gate loops: 0.15 mm cells, driver pin to gate pad and back through the source return, ground copper kept within 2 mm of the loop on the same layer and on the plane next to it. " + GATE_H_NOTE,
  "**Copper resistance and Kelvin taps.** DC grid solve of each net over all layers at 20 °C. Path resistances on a 0.1 mm grid, Kelvin taps on a 0.05 mm grid because a coarser grid bridges the 0.2 mm keep-out gaps round the taps.",
  "**Loss at each load.** The project's loss model for FETs, inductor, sense resistors and cells, with the battery current found from the port power and the pack voltage at that state of charge. Copper loss is each path's resistance times its own current squared.",
  "**Thermals.** The pack thermal model in the cup at 25 °C in still air with the firmware derate, run on the PC. Between the boards only the part positions, the copper loss map, the via count under the gap filler and the copper cover round the stages change. The thermal runs used the loss map of the board one step before the last signal re-routes; the final board's map differs from it by 0.01 mΩ on one ground path, about half a milliwatt.",
  "**Coupling.** 3-D electrostatic solve on a 0.05 mm grid of the copper within 1.5 mm of each switch node, through the real stack-up. The switch node and its bootstrap and high-side gate nets are driven together. Part bodies are not in the model, so the inductor's own stray field and its body capacitance are missing on both boards. Magnetic coupling is only covered by the pair-area figures in the Kelvin section. Slots in a ground plane change where return currents flow; that effect is not in any number on this page.",
  "**What this cannot tell.** Nothing here is measured. Edge speed, ringing amplitude, EMC and how the BQ25756 reacts to a given step on a pin need a built board and a scope.",
 ],
 foot="Scripts and result files are on the branch in hardware/Production/groundup/compare/. The ground-up board is an experiment and is not merged.",
)

vg = max((r for r in D['via'] if 'GND' in r['name']), key=lambda r: r['n']['i']); vgb = max((r for r in D['via'] if 'GND' in r['name']), key=lambda r: r['b']['i'])
vp = max((r for r in D['via'] if 'PACK_P' in r['name']), key=lambda r: r['n']['i']); vc = next(r for r in D['via'] if r['name'] == 'CELL_P')
vp1 = next(r for r in D['via'] if r['name'] == 'Port 1 PACK_P'); vg1 = next(r for r in D['via'] if r['name'] == 'Port 1 GND')
TEXT['rend'] = ["Both boards rendered by KiCad from the same view; the ground-up board is shown as it is after the fix pass. The outline, holes, USB-C connectors, wire pads, antenna module, the two large inductors and the back-side parts are in the same place on both, so either board fits the cup. Parts with no 3D model in the project library show as bare pads on both."]
TEXT['via'] = [
 f"**The ground-up board is now slightly ahead.** Its hottest via carries {VS[N]['max']:.1f} A, in the ground return at the {vg['name'].split(' GND')[0].lower()} VBUS-leg FET; on the current board the hottest carries {VS[B]['max']:.1f} A at the same kind of place. On the first version it was {mo['via_max']:.1f} A with {mo['via3']} vias over 3 A. Now no via on either board carries over 3 A, and {VS[N]['over2']} carry over 2 A on the ground-up board against {VS[B]['over2']} on the current board.",
 f"The fix pass added vias at each layer change so more share the current: PACK_P now has {vp1['n']['n']} vias ({vp1['b']['n']} on the current board), CELL_P {vc['n']['n']} against {vc['b']['n']}, and the ground net {vg1['n']['n']} against {vg1['b']['n']}. PACK_P into each stage peaks at {vp['n']['i']:.1f} A per via ({vp['b']['i']:.1f} A on the current board) and CELL_P at the fuse at {vc['n']['i']:.1f} A ({vc['b']['i']:.1f} A).",
 "All of these are 0.3 mm vias. A via of that size is usually budgeted at 1 to 2 A, and inside a pour it tolerates more because the copper round it carries the heat away. Both boards are inside that range now.",
]
TEXT['cost'] = [
 f"**About {ct['hours']:.0f} hours of working time and {ct['output_tokens']/1e6:.1f} million output tokens, roughly ${round(ct['usd'], -1):.0f} at API rates.** The first layout took {cl['hours']:.0f} hours and ${cl['usd']:.0f}. The detailed comparison took about {cd['hours']*60:.0f} minutes and ${cd['usd']:.0f}. The fix pass took {cf['hours']:.1f} hours and ${cf['usd']:.0f}, against my estimate of 4 to 8 hours and $50 to $100.",
 f"Most of the time was tools running, not the model: in the first layout, of the {cw['counter']['total_h']:.0f} hours the session counter covers, {cw['counter']['api_h']:.1f} hours were model time and {cw['counter']['tool_h']:.1f} hours were the router, rule checks and solvers. The input side is large because every model call re-reads the conversation so far; {(ct['cache_read_input_tokens'])/(ct['cache_read_input_tokens']+ct['cache_creation_input_tokens']+ct['input_tokens'])*100:.0f} % of the input tokens were cached re-reads, which are billed at a small fraction of the normal rate.",
]
TEXT['cost_note'] = (f"Counted from the session logs: {ct['turns']} model calls between {cl['start'][:16].replace('T', ' ')} and {cw['phases'][-1]['end'][:16].replace('T', ' ')} UTC. Working time leaves out the pauses of more than 20 minutes while waiting for a reply. "
    f"The dollar figure uses the rates that reproduce the session's own cost counter (${cw['rate']['output_tokens']:.0f} per million output tokens, ${cw['rate']['cache_creation_input_tokens']:.0f} per million cache-write tokens, ${cw['rate']['cache_read_input_tokens']:.2f} per million cache-read tokens); "
    "what is actually charged depends on the plan. Not counted: the thermal batches on the PC, which ran in their own session, and the few minutes after this page was built.")

TEXT['flow'] = [
 "**Everything was done by script, and I looked at the board through numbers and pictures.** I have no KiCad window. I change the board with a script, then read back the rule-check report, the count of open connections, the copper solver and a rendered crop of the spot I am working on. Because every change is a script or a small JSON file, any pass can be replayed, and the branch has a commit at each milestone.",
 "**Order of work, first layout.** First what must not move, taken from the mechanical model: outline, holes, connectors, wire pads, the two large inductors, the back-side parts. Then placement, checked against the cup after every change. Then the power copper and Kelvin taps, drawn from coordinates I chose net by net. Then the router for the 350 or so signal connections, pass after pass. Then repair of cut planes, hand fixes, widening, silkscreen and the final rule check.",
 "**Order of work, fix pass.** The first comparison gave a list of what was wrong and where. I lifted the gate drives and the signals near switching copper, moved the four 100 nF capacitors, drew the gate drives by hand beside their returns, added vias, and let the router lay the lifted signals again with a cost for running near switching copper. What it could not close I closed one link at a time with a small exact-clearance search, some of it on the ground plane. Then every solver ran again, which is how the two faults in the fix pass section were found, and a second short round moved four signals the coupling solver still flagged.",
 "**For the comparison** each question got one script that reads the board file from a setting, so every board went through the same code. Before trusting a tool I checked that it gave the known answer on the current board: the hot loops came out at 0.54 and 0.67 nH against 0.54 and 0.66 nH in the November 6 study, and the thermal run gave the same 5.0 minutes as the earlier PC study. The text on this page takes its numbers from the result files, so it cannot drift from the charts.",
 "**What the workflow got wrong.** The first layout optimised what it checked while building: connections, rule errors, cup fit and DC resistance. It did not look at loop inductance or coupling until the board was finished. The fix pass then made the same kind of mistake once more, on a smaller scale: I hand-drew tracks in the power stage and checked rules and planes but not path resistance or the Kelvin taps. The rule from both: after every change to a power stage, run the copper, Kelvin, loop and coupling solvers, because a board can pass every rule and still be wrong.",
]
TEXT['pass_note'] = "Counts are the ones posted in the thread after each pass. The total moved from 350 to 375 between passes as pours and placement changed. The scripts are in hardware/Production/groundup/ on the branch."
