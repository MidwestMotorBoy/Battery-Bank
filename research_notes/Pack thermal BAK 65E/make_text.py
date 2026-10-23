"""Page text for the HTML report, with every number pulled from the result files. Run: python make_text.py -> page_text.json"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__)); RD = os.path.join(HERE, 'renders')
S = json.load(open(os.path.join(RD, 'summary.json')))
FL = {r['variant']: r for r in json.load(open(os.path.join(RD, 'fill.json')))}
SE = json.load(open(os.path.join(RD, 'sensitivity.json')))
def sv(prefix): return next(r for r in SE if r['label'].startswith(prefix))
d100, d60, d30, x2, c1, c2, ps = (S[k] for k in ('dis100', 'dis60', 'dis30', 'dis100x2', 'chg1', 'chg2', 'pass'))
pol, ntcb, a35, h4 = sv('Derate moved'), sv('Front-cell NTCs'), sv('35 °C'), sv('In a pack')
r12, r16 = sv('Cell DC resistance 12'), sv('Cell DC resistance 16')
q100 = d100['q_cells_0'] + d100['q_board_0']
f = lambda v, n=1: f'{v:.{n}f}'

T = {}
T['lede'] = (f"A 3-D model of the cup pack with the BAK 65E cells and the P0 board. At 100 W the pack now makes about {f(q100)} W of heat, "
             f"half the ~12 W of the FEB design, and only {f(d100['q_cells_0'])} W of that is in the cells. The power stage on the board is now the main heat "
             f"source. It sets how long a 100 W burst lasts and where the hot spots sit. The cells stay well inside BAK's limits in every case. "
             f"Model values at 25 °C in still air, not measurements.")
T['tiles'] = [
    dict(v=f"{f(q100)}<small> W</small>", k=f"heat at 100 W out ({f(d100['q_cells_0'])} W in the cells). Was about 12 W with the FEB cells"),
    dict(v=f"{f(d100['min_full'], 0)}<small> min</small>", k="of full 100 W from a full pack at 25 °C, then 40 W to empty. The board and the cell derate end it at about the same time"),
    dict(v=f"{f(max(d100['surf_max'], c1['surf_max'], ps['surf_max']), 0)}<small> °C</small>", k="hottest point on any can, worst case (pass-through). BAK allows 60 °C cell in discharge, 45 °C cell in charge"),
    dict(v=f"{f(c1['t_full'], 0)}<small> min</small>", k="to charge from 5 % to 95 % from one 100 W charger. The 40 °C ramp starts trimming current after about half an hour"),
]
T['findings'] = [
    f"<b>The heat moved from the cells to the board.</b> At 100 W out the cells make {f(d100['q_cells_0'], 2)} W and the board {f(d100['q_board_0'], 2)} W. "
    f"With the FEB cells it was about 6.5 W and 5.5 W. Cell resistance barely matters now: 12 or 16 mΩ instead of 14 changes the 40-minute energy by under 1 Wh.",
    f"<b>The 100 W burst lasts about {f(d100['min_full'], 0)} minutes, and the board would end it anyway.</b> It ends when the hottest cell NTC reaches 33 °C, "
    f"heated mostly by the USB1 stage through the gap filler. The stage's own copper is only a kelvin short of the 55 °C board ramp by then. "
    f"Moving the cell ramp to 40 → 44 °C hands the limit to the board ramp, so the burst only grows to {f(pol['min_full'])} min. It does let the pack deliver "
    f"{f(pol['wh_40'])} Wh in the first 40 minutes instead of {f(sv('Baseline')['wh_40'])} Wh, with the hottest can at {f(pol['surf'])} °C. "
    f"Splitting 100 W over both ports (65 + 35 W) spreads the board heat and gives {f(x2['min_full'])} min.",
    f"<b>The cells are far from their limits.</b> The hottest can point is {f(d100['surf_max'])} °C at 100 W, {f(ps['surf_max'])} °C in pass-through and "
    f"{f(c1['surf_max'])} °C while charging, against BAK's 60 °C discharge and 45 °C charge cell limits. The 33 °C derate start is a comfort and cycle-life choice "
    f"made for the FEB cells. It is now the tighter limit, not the cells.",
    f"<b>Within a cell, the gradient comes from the board.</b> The front cell under the busy stage (C4 for USB1) carries a hot stripe on its board-facing side, "
    f"over the gap filler. That stripe runs up to {f(d100['within_max'])} K above the cell's coolest point at 100 W and {f(ps['within_max'])} K in pass-through. "
    f"The cells make so little heat themselves that their core runs within a kelvin of their can. At 30 W the whole spread is under {f(d30['within_max'] + 0.1, 0)} K.",
    f"<b>Between cells:</b> the front pair (C1, C4) runs {f(d100['front_back'])} K above the back pair at 100 W and {f(ps['front_back'])} K in pass-through. "
    f"The largest cell-to-cell difference in mean temperature is {f(d100['spread_max'])} K at 100 W, {f(ps['spread_max'])} K in pass-through and {f(d30['spread_max'])} K at 30 W.",
    f"<b>The NTCs read low.</b> An NTC at mid-length, facing the pack centre, reads up to {f(d100['ntc_lag'])} K below the hottest can point at 100 W and "
    f"{f(c1['ntc_lag'])} K while charging. That is why charging stops at a {f(c1['surf_max'])} °C can stripe while the NTC still shows {f(c1['ntc_max'])} °C. "
    f"With the front-cell NTCs on the board-facing side, the firmware sees the real hot spot. The burst then ends sooner ({f(ntcb['min_full'])} min) "
    f"unless the thresholds move up with it.",
    f"<b>Everyday loads are easy.</b> 30 W never derates: {f(d30['t_end'] / 60)} h to empty with cans at or below {f(d30['surf_max'], 0)} °C. "
    f"60 W runs at full power for {f(d60['min_full'], 0)} minutes, then settles at 40 W.",
    f"<b>Charging:</b> {f(c1['t_full'], 0)} min from 5 % to 95 % on one port, {f(c2['t_full'], 0)} min on two 45 W chargers. On two ports the heat is shared, "
    f"so the hottest part runs {f(c2['part_max'], 0)} °C instead of {f(c1['part_max'], 0)} °C. The 40 → 45 °C ramp starts trimming current at "
    f"{f(c1['t_derate'], 0)} and {f(c2['t_derate'], 0)} min. The spec's ~2 h estimate was too long.",
    f"<b>Pass-through is the hottest case for the board.</b> With a 100 W charger on USB1 and 30 W out of USB2, the board makes {f(ps['q_board_0'])} W. "
    f"The hottest part reaches {f(ps['part_max'], 0)} °C, the outer face over the board {f(ps['skin_max'], 0)} °C, and charging is trimmed after "
    f"{f(ps['t_derate'], 0)} minutes. At 100 W the outer face peaks at {f(d100['skin_max'], 0)} °C, so the pack is warm to hold over the board side.",
]
B = FL['base']
T['filler'] = [
    f"<b>Use about {f(B['grams'], 1)} g of a soft, dispensable 3–3.6 W/m·K silicone gap filler, only where it is now.</b> It goes between the board's B.Cu via zone "
    f"and the two front cells, over each power stage (|y| 7–16 mm, z 27–53 mm), about {f(B['cc'])} cc in all. The bond line is 2.75 mm at the cell tangent "
    f"and opens to about 3.8 mm at the zone edges, so it has to be a gel or a cure-in-place filler, not a pad. A pad cannot follow the curved can.",
    f"<b>Product for P0: Parker Chomerics THERM-A-GAP GEL 30</b> (3.5 W/m·K, specific gravity 3.1, one part, supplied fully cured). It needs no mixing or "
    f"curing, a 10 cc syringe (65-00-GEL30-0010) covers about six packs, and it peels off cleanly if the module has to come apart during bring-up. "
    f"For gift packs a two-part cure-in-place filler holds its shape better through drops: <b>Bergquist TGF 3600</b> (3.6 W/m·K, 3.0 g/cc, 1:1, "
    f"15 h at room temperature, Shore 00 35) or <b>Laird Tflex CR350S</b> (3.6 W/m·K). Cure them at room temperature only, never 100 °C, with cells fitted. "
    f"Both come in 50 cc cartridges at the smallest, which is far more than a few packs need.",
    f"<b>What it does:</b> it is a board-protection part. It keeps the hottest power part {f(FL['none']['part'] - B['part'])} K cooler at 100 W and "
    f"{f(FL['none']['chg_part'] - B['chg_part'])} K cooler while charging. Without it, the board ramp ends the 100 W burst after {f(FL['none']['min_full'], 0)} min. "
    f"The catch is that its heat goes into C1 and C4, where the cell NTCs see it. Under today's 33 °C cell ramp that costs about "
    f"{f(FL['none']['wh_40'] - B['wh_40'])} Wh over the first 40 minutes. That is one more reason to move the cell ramp up.",
    f"<b>What doesn't pay off:</b> a 6 W/m·K filler takes {f(B['part'] - FL['k6']['part'])} K off the parts and nothing else. Filling the whole rail gap "
    f"(+{f(FL['wide']['grams'] - B['grams'])} g) takes {f(B['part'] - FL['wide']['part'])} K off. Beads between the front and back cells "
    f"(+{f(FL['beads']['grams'] - B['grams'])} g) narrow the front-to-back spread by about 1 K. A pad from the parts side of the stages to the cup wall "
    f"(+{f(FL['lid']['grams'] - B['grams'])} g) takes {f(B['part'] - FL['lid']['part'])} K off. None of them is worth the mass against the 400 g target. "
    f"Filler between the cells and the cup wall would do nothing: the cans already sit 0.15 mm from the wall. The 1.2 mm of PA12 and the still air outside are what hold the heat in. "
    f"A 1.5 W/m·K filler (or a cheaper gel) costs only {f(FL['k15']['part'] - B['part'])} K on the parts, so it is an acceptable fallback.",
]
T['fillnote'] = ("The 100 W columns cover the first 40 minutes from a full pack. Charging is one port from 5 %. The baseline row is the design as specified. "
                 f"Mass assumes {3.1} g/cc. The filler is assumed to wet both faces fully. Voids in the bead would cost more than any change of material.")
T['sens'] = ("The 100 W case was re-run for its first 40 minutes with one assumption changed at a time. Cell resistance hardly matters. "
             "What matters is the ambient temperature (at 35 °C the cells start inside the derate ramp, so there is no burst), where the NTCs sit, "
             "and the derate thresholds themselves.")
T['assumptions'] = [
    ['Surroundings', '25 °C, still air, pack standing alone. Every outer face loses heat at 10 W/m²K (natural convection about 4.5, radiation about 5.5 with emissivity 0.9). '
                     'The pack-pocket run uses 4 W/m²K.'],
    ['Cell DC resistance', '14 mΩ per cell at 25 °C from 30 % to 100 % charge, rising to 1.8× at empty and falling about 27 % by 45 °C. BAK only gives ≤ 8 mΩ at 1 kHz. '
                           'A single-cell check reproduces BatteryRealData\'s 25 A test peaking at 80 °C with 14–16 mΩ, and the 12 and 16 mΩ runs bracket it.'],
    ['Reversible heat', 'Not modelled. At these currents it can be a real fraction of the cell heat, but the cells make only about a third of the pack\'s heat. '
                        'It moves cell temperatures by about a kelvin.'],
    ['Cell build', '68 J/K per cell (72 g at 0.95 J/g·K). The wound roll conducts 0.6 W/m·K across its layers and 20 along them (round and along the can). '
                   '0.25 mm steel can, PVC wrap, 3 mm mandrel hole, 2.5 mm header under the + cap.'],
    ['Board', '6 layers, 1.6 mm: 38 W/m·K in-plane and 0.45 through. The via zone under the stages conducts 8 W/m·K through. Parts are smeared into a board heat capacity of about 20 J/K. '
              'The P0 layout isn\'t final, so each port\'s stage is assumed to sit over its own front cell (USB1 over C4, USB2 over C1). '
              'The protection FETs are assumed at the bottom edge and the USB-C ports at the top.'],
    ['Losses (P0 parts)', 'BSC007N04LS6 2 × 0.85 mΩ, F102 2.5 mΩ, shunt 1 mΩ, nickel and copper 4.1 mΩ. SiZ240DT 13 mΩ at the 5 V gate drive (9 V drive off, as shipped). '
                          'XGL7030-332 12 mΩ plus 0.15 W core at 500 kHz. 5 + 5 mΩ sense resistors, TPS25751 18 mΩ, USB-C 10 mΩ, 0.2 W per running converter.'],
    ['Enclosure', 'MJF PA12 0.22 W/m·K (cup, cap, carrier), solid TPU bands 0.20, lattice bumpers 0.08. Air inside 0.038 W/m·K, which includes radiation across mm gaps.'],
    ['Firmware', 'The 10-21 policy in the spec, acting on the hottest of four NTCs. Each NTC is assumed at mid-length on the side of its can facing the pack centre. '
                 'Board ramp 55 → 70 °C on each charger\'s TS NTC. 5 W re-advertising steps with 2 K hysteresis. USB1 priority with a 20 W USB2 minimum.'],
    ['Cell voltage', 'A generic silicon-graphite / NMC open-circuit curve, 3.5 V average, 6.5 Ah. Discharge stops at 2.8 V per cell under load. Charging stops at 95 %.'],
]
T['checks'] = [
    'Measure the 65E DC resistance with a 10 s pulse at 50 % and 10 % charge, and replace the 14 mΩ in <code>pack3d.py</code>.',
    'Run 100 W from full with thermocouples on C4 at its board-facing stripe (z ≈ 40 mm), C4 at the NTC spot, C3, the USB1 FET case, the inductor and the outer face over the board. '
    'Compare the curves with this page. The stripe-to-NTC difference is the number that matters most.',
    'Decide where the front-cell NTCs go. On the board-facing side, just above the filler (z ≈ 56 mm), they see the real hot spot. Then raise the derate start so the burst doesn\'t shrink.',
    f"Retune the discharge derate for the 65E. In the model a 40 → 44 °C cell ramp kept the cans under {f(pol['surf'] + 0.5, 0)} °C and delivered "
    f"{f((pol['wh_40'] / sv('Baseline')['wh_40'] - 1) * 100, 0)} % more energy in the first 40 minutes. "
    'The 100 W burst itself sits right at the board ramp, so it only gets longer with a cooler stage or by splitting the load over both ports.',
    'Cut a dummy module after dispensing to check the filler bead wets both the board and the cans across the whole zone.',
]
T['method'] = [
    'The pack is a 100 × 87 × 64 voxel model (0.6 × 0.6 × 1.5 mm, about 480,000 cells inside the outline) built from the cup geometry in '
    '<code>hardware/mechanical/monolith_shell.py</code> and <code>monolith_cup.py</code>. Conductances between voxels come from a four-times-finer material grid. '
    'Thin layers like the cell wrap, the can and the 1.5 mm gaps between cells keep their real resistance. The wound cell roll is anisotropic, '
    'and the board is anisotropic with its via zone.',
    'Time steps are implicit (10 s for discharge, 20 s for charging), solved with algebraic-multigrid CG. Each step runs the electrical model '
    '(loss per part, cell resistance by temperature and charge) and the firmware policy, then puts each loss into its part: the cell rolls, the nickel, '
    'the protection FETs, each stage\'s FETs, inductor, IC and sense resistors, each TPS25751 and each USB-C contact set.',
    'Files: <code>research_notes/Pack thermal BAK 65E/</code> in the repo. <code>pack3d.py</code> is the model and cases, <code>fill.py</code> the gap-filler options, '
    '<code>sens.py</code> the sensitivity runs, <code>render.py</code> the maps, <code>summary.py</code> the table. <code>python jobs.py</code> re-runs everything in about 1.5 h on 4 cores.',
]
T['cases'] = {
    'idle': dict(facts=f"Sleep with BLE advertising, about 6 mW. Steady state: nothing rises more than {f(S['idle']['rise'], 1)} K above ambient.",
                 cap_pack='Idle is flat: the maps show ambient everywhere.', cap_cells='The board and cans sit at ambient.'),
}
def facts(s, extra=''):
    parts = []
    if 'asked' in s and s['name'] != 'pass':
        parts.append(f"full power <b>{f(s['min_full'])} min</b>")
        parts.append(f"empty at <b>{f(s['t_end'], 0)} min</b>")
        parts.append(f"<b>{f(s['wh_out'], 0)} Wh</b> delivered")
    if 't_full' in s and s['name'] != 'pass':
        parts.append(f"95 % at <b>{f(s['t_full'], 0)} min</b>"); parts.append(f"current trimmed from <b>{f(s['t_derate'], 0)} min</b>")
    if s['name'] == 'pass':
        parts.append(f"charging trimmed from <b>{f(s['t_derate'], 0)} min</b>"); parts.append(f"<b>{f(s['soc_end']*100, 0)} %</b> after 2 h")
    parts += [f"hottest can <b>{f(s['surf_max'])} °C</b> ({s['surf_cell']})", f"hottest board part <b>{f(s['part_max'])} °C</b>",
              f"within one cell <b>{f(s['within_max'])} K</b>", f"outer skin <b>{f(s['skin_max'])} °C</b>"]
    return ' · '.join(parts) + extra
CAP = ("Left: the four cans and the board, pulled 34 mm out so both show. Middle: a slice across the pack through both power stages. "
       "Right: a lengthwise slice through C3, C4 and the USB1 stage. Contours every 2 °C.")
CAPC = ("The board on its own scale, then each can's surface unrolled: across is the angle round the can (0° faces the board), up is the length. "
        "The cell panels share one scale so the gradients show.")
for n in ('dis30', 'dis60', 'dis100', 'dis100x2', 'chg1', 'chg2', 'pass'):
    T['cases'][n] = dict(facts=facts(S[n]), cap_pack=CAP, cap_cells=CAPC)
for n in ('dis60', 'dis100', 'dis100x2'):
    T['cases'][n]['refs'] = [dict(v=33, label='derate starts (NTC 33 °C)'), dict(v=55, label='board ramp starts (55 °C)')]
for n in ('chg1', 'chg2', 'pass'):
    T['cases'][n]['refs'] = [dict(v=40, label='charge ramp starts (NTC 40 °C)'), dict(v=55, label='board ramp starts (55 °C)')]
json.dump(T, open(os.path.join(HERE, 'page_text.json'), 'w'), indent=1, ensure_ascii=False)
print('ok')
