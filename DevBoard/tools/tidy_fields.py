"""Cosmetic tidy for the dev board sheets (graphics only, no connectivity change).

- Places Reference/Value text of two-pin parts so it reads horizontally and clears the body:
  beside vertical parts (right side, or left if the right is crowded, or vertical text if both are),
  above/below horizontal parts.
- Hides the references of power symbols and PWR_FLAGs.
- Converts literal "\\n" in text items to real line breaks.
- Writes a title block on every sheet.

Run from DevBoard/: python tools/tidy_fields.py
"""
import re
import sys

BS = chr(92)
TWO_PIN = ("Device:R", "Device:C", "Device:L", "Device:D_Schottky", "Device:Fuse", "Device:Thermistor_NTC",
           "Device:LED", "Device:D_TVS", "Device:Battery_Cell", "Jumper:Jumper_2_Open")
DATE = "2026-10-11"
TITLES = {
    "MonolithDev.kicad_sch": ("Monolith dev board - top level", "Sheet index, PD address straps"),
    "gauge.kicad_sch": ("Cells and gauge", "4S input, BQ40Z50-R2 gauge/protector, protection FETs"),
    "power.kicad_sch": ("Sleep-current measurement and 3.3 V rail", "R_MEAS + INA190 x2, TPS70950, TPS62177"),
    "mcu.kicad_sch": ("MCU and board NTCs", "STM32WB1MMC, debug headers, NTC TH1-TH4"),
    "usb_port.kicad_sch": ("USB-C PD port (used twice)", "TPS25751D + BQ25756 + TPS62933; port 1 = 4xx, port 2 = 5xx"),
}


def skip_string(s, k):
    k += 1
    while s[k] != '"':
        if s[k] == BS:
            k += 1
        k += 1
    return k


def block_end(s, start):
    d, m = 0, start
    while True:
        ch = s[m]
        if ch == '"':
            m = skip_string(s, m)
        elif ch == '(':
            d += 1
        elif ch == ')':
            d -= 1
            if d == 0:
                return m
        m += 1


def top_blocks(s, head):
    root = s.index('(kicad_sch')
    end = block_end(s, root)
    k = root + 1
    while k < end:
        if s[k] == '"':
            k = skip_string(s, k)
        elif s[k] == '(':
            m = block_end(s, k)
            if re.match(r'\((\w+)', s[k:k + 40]).group(1) == head:
                yield k, m
            k = m
        k += 1


def set_field(block, name, x, y, ang, justify=None, hide=None, size=None):
    m = re.search(r'\(property "' + name + r'" "[^"]*"', block)
    if not m:
        return block
    start = m.start()
    end = block_end(block, start)
    prop = block[start:end + 1]
    prop = re.sub(r'\(at [-\d.]+ [-\d.]+ [-\d.]+\)', f'(at {x:.2f} {y:.2f} {ang})', prop, count=1)
    if hide is not None:
        prop = re.sub(r'\n\s*\(hide yes\)', '', prop)
        if hide:
            prop = prop.replace(f'(at {x:.2f} {y:.2f} {ang})', f'(at {x:.2f} {y:.2f} {ang})\n\t\t\t(hide yes)', 1)
    eff = re.search(r'\(effects', prop)
    if eff:
        es = eff.start()
        ee = block_end(prop, es)
        font = f'(size {size} {size})' if size else '(size 1.27 1.27)'
        just = f' (justify {justify})' if justify else ''
        prop = prop[:es] + f'(effects (font {font}){just})' + prop[ee + 1:]
    return block[:start] + prop + block[end + 1:]


def tidy(path):
    s = open(path, encoding='utf-8').read()
    syms = []
    for a, b in top_blocks(s, 'symbol'):
        blk = s[a:b + 1]
        lib = re.search(r'\(lib_id "([^"]+)"\)', blk).group(1)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', blk)
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
        syms.append((a, b, lib, float(at.group(1)), float(at.group(2)), int(float(at.group(3))), ref))
    pts = [(x, y) for _, _, lib, x, y, _, _ in syms if not lib.startswith('power:')]

    def crowded(x, y, x0, x1):
        return any(x0 < px - x <= x1 and abs(py - y) < 5.5 for px, py in pts)

    out, last = [], 0
    for a, b, lib, x, y, rot, ref in syms:
        blk = s[a:b + 1]
        if lib.startswith('power:'):
            blk = set_field(blk, 'Reference', x, y, 0, hide=True)
        elif lib in TWO_PIN:
            if rot in (90, 270):
                blk = set_field(blk, 'Reference', x, y - 2.54, 90)
                blk = set_field(blk, 'Value', x, y + 2.54, 90)
            else:
                right = crowded(x, y, 0.5, 14)
                left = any(0.5 < x - px <= 14 and abs(py - y) < 5.5 for px, py in pts)
                if not right:
                    blk = set_field(blk, 'Reference', x + 2.54, y - 1.27, 0, 'left')
                    blk = set_field(blk, 'Value', x + 2.54, y + 1.27, 0, 'left')
                elif not left:
                    blk = set_field(blk, 'Reference', x - 2.54, y - 1.27, 0, 'right')
                    blk = set_field(blk, 'Value', x - 2.54, y + 1.27, 0, 'right')
                else:
                    blk = set_field(blk, 'Reference', x - 2.03, y, 90, size=1.0)
                    blk = set_field(blk, 'Value', x + 2.03, y, 90, size=1.0)
        out.append(s[last:a])
        out.append(blk)
        last = b + 1
    out.append(s[last:])
    s = ''.join(out)

    # literal backslash-n typed into text items -> KiCad line break escape
    s = s.replace(BS + BS + 'n', BS + 'n')

    # title block
    name = path.replace(BS, '/').split('/')[-1]
    title, comment = TITLES.get(name, (name, ''))
    tb = (f'\t(title_block\n\t\t(title "{title}")\n\t\t(date "{DATE}")\n\t\t(rev "A (draft)")\n'
          f'\t\t(company "Monolith 100 W battery bank - dev board")\n'
          f'\t\t(comment 1 "{comment}")\n'
          f'\t\t(comment 2 "Spec: docs/devboard/circuit-description.md; changes and open items: DevBoard/README.md")\n'
          f'\t\t(comment 3 "Not reviewed, laid out, built or tested")\n\t)\n')
    s = re.sub(r'\t\(title_block\n.*?\n\t\)\n', '', s, flags=re.S)
    s = re.sub(r'(\t\(paper "[^"]+"\)\n)', r'\1' + tb.replace(BS, BS + BS), s, count=1)
    open(path, 'w', encoding='utf-8', newline='\n').write(s)
    print(path, len(syms), 'symbols')


for p in sys.argv[1:] or list(TITLES):
    tidy(p)
