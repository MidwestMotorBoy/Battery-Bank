"""Build the JLC BOM and CPL files for the board from its footprints (run by make_package.sh, inside kicad/kicad:10.0).

usage: python3 make_jlc_files.py BOARD.kicad_pcb KICAD_POS.csv OUT_DIR

Reads part fields (Value, LCSC, MPN, DNP / exclude flags) straight from the board, and positions from kicad-cli's
position file, so the BOM and CPL match the copper exactly. Then applies the hand-made fixes that live only in the order
files, never in the board (ORDER-NOTES.md):
  - LCSC / MPN overrides (R412/R512, whose LCSC code is not in the schematic yet),
  - rotation offsets and body shifts found in JLC's placement preview (per footprint, so they carry across layouts).
Writes the full BOM/CPL, the top-only BOM/CPL that JLC assembles, the four-column top BOM, and the bottom hand-solder list.
"""
import csv
import math
import os
import re
import sys

import pcbnew

# Parts JLC must not place (test pads, wire pads, holes are already excluded from the BOM on the board; DNP by flag).
SKIP_PREFIX = ('TP',)

# Hand-made BOM fixes (ref -> field overrides). Keep until the schematic carries them.
OVERRIDES = {
    # 49.9k 1 % 0201 for the 9 V gate-drive divider. JLC/LCSC stock it as C7343965, which is Stackpole RMCF0201FT49K9
    # (lcsc.com/product-detail/C7343965.html); the schematic's MPN field (UNI-ROYAL 0201WMF4992TEE) has no LCSC code.
    'R412': {'LCSC': 'C7343965', 'MPN': 'RMCF0201FT49K9 (Stackpole)'},
    'R512': {'LCSC': 'C7343965', 'MPN': 'RMCF0201FT49K9 (Stackpole)'},
}

# Rotation offsets from Logan's JLC preview of 2026-10-30 (hand-routed board), in degrees, CCW positive as the CPL is.
# They are a property of JLC's library footprint against KiCad's, so they carry to any layout with the same footprints.
ROT_FIX = {r: -90 for r in ('U402', 'U502', 'U403', 'U503', 'U405', 'U505', 'U406', 'U506', 'Q101', 'Q102', 'U204')}
ROT_FIX.update({r: 180 for r in ('Q103', 'Q104', 'U404', 'U504', 'Q409', 'Q509')})

# Body shifts in the footprint's own frame (mm, y up as the CPL is). F102: JLC drew the body 0.65 mm toward pads 1/2;
# on the hand-routed board (F102 at 180 deg) that was +0.65 mm in board X, which is -0.65 mm in the footprint's x.
SHIFT = {'F102': (-0.65, 0.0)}


def natural(ref):
    m = re.match(r'([A-Za-z]+)(\d+)', ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def main(board, pos_csv, out):
    b = pcbnew.LoadBoard(board)
    parts = {}
    for f in b.GetFootprints():
        ref = f.GetReference()
        if f.IsDNP() or f.IsExcludedFromBOM() or f.IsExcludedFromPosFiles() or ref.startswith(SKIP_PREFIX):
            continue
        fl = {x.GetName(): x.GetText() for x in f.GetFields()}
        p = dict(ref=ref, val=f.GetValue(), fp=str(f.GetFPID().GetLibItemName()),
                 lcsc=fl.get('LCSC', ''), mpn=fl.get('MPN', ''), side='bottom' if f.IsFlipped() else 'top')
        o = OVERRIDES.get(ref, {})
        p['lcsc'] = o.get('LCSC', p['lcsc'])
        p['mpn'] = o.get('MPN', p['mpn'])
        parts[ref] = p
    pos = {r['Ref']: r for r in csv.DictReader(open(pos_csv))}
    missing = sorted(set(parts) - set(pos))
    if missing:
        sys.exit(f'parts with no position: {missing}')
    for k in list(ROT_FIX) + list(SHIFT):
        if k not in parts:
            sys.exit(f'fix for {k}, which is not placed')

    cpl = []
    for ref in sorted(parts, key=natural):
        r = pos[ref]
        x, y, rot = float(r['PosX']), float(r['PosY']), float(r['Rot'])
        if ref in SHIFT:
            dx, dy = SHIFT[ref]
            a = math.radians(rot)
            x += dx * math.cos(a) - dy * math.sin(a)
            y += dx * math.sin(a) + dy * math.cos(a)
        rot = (rot + ROT_FIX.get(ref, 0)) % 360
        cpl.append(dict(ref=ref, x=x, y=y, layer=parts[ref]['side'].capitalize(), rot=rot))

    def groups(sel):
        g = {}
        for ref in sorted(sel, key=natural):
            p = parts[ref]
            g.setdefault((p['val'], p['fp'], p['lcsc'], p['mpn']), []).append(ref)
        return sorted(g.items(), key=lambda kv: natural(kv[1][0]))

    def write_bom(name, sel, simple=False):
        with open(os.path.join(out, name), 'w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['Comment', 'Designator', 'Footprint', 'JLCPCB Part #'] if simple else
                       ['Comment', 'Designator', 'Footprint', 'LCSC Part #', 'MPN', 'Qty'])
            for (val, fp, lcsc, mpn), refs in groups(sel):
                w.writerow([val, ','.join(refs), fp, lcsc] if simple else [val, ','.join(refs), fp, lcsc, mpn, len(refs)])

    def write_cpl(name, rows):
        with open(os.path.join(out, name), 'w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
            for c in rows:
                w.writerow([c['ref'], f"{c['x']:.4f}mm", f"{c['y']:.4f}mm", c['layer'], f"{c['rot']:g}"])

    top = [r for r in parts if parts[r]['side'] == 'top']
    bot = [r for r in parts if parts[r]['side'] == 'bottom']
    write_bom('Monolith_BOM_JLC.csv', parts)
    write_bom('Monolith_BOM_JLC_top.csv', top)
    write_bom('Monolith_BOM_JLC_top_simple.csv', top, simple=True)
    write_bom('Monolith_bottom_hand_solder.csv', bot)
    write_cpl('Monolith_CPL_JLC.csv', cpl)
    write_cpl('Monolith_CPL_JLC_top.csv', [c for c in cpl if c['layer'] == 'Top'])
    print(f'{len(parts)} placed parts: {len(top)} top, {len(bot)} bottom; {len(groups(parts))} BOM lines; '
          f'no LCSC code: {sorted(r for r in parts if not parts[r]["lcsc"])}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
