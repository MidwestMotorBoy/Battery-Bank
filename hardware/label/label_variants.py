"""Whole-label look variations of the --bl (Borderlands) label, to compare side by side: palettes, time of day, ink
weight, halftone skies, kraft panels. Each is a palette override (monolith_label.C) plus look flags (monolith_label.V).
Run: python label_variants.py   -> out/variants/label_variant_NN.png (each, with bleed) + out/label_variants.png (sheet)"""
import os, sys, io, copy
if __name__ == '__main__': sys.argv = [sys.argv[0], '--bl']
import monolith_label as M

NIGHT = dict(sky0='#121d36', sky1='#1d2c4d', sky2='#32456b', cloud='#7f8ca8', cloud_sh='#56627e', far='#4a5a75', far_sh='#33415a',
             far_hi='#61708e', snow='#d6dde8', snow_sh='#9aa6b8', hill='#3e6a3c', hill_sh='#2a4b2a', hill_hi='#4f7d47',
             pine='#2c5a35', pine_sh='#183a22', pine_hi='#3d6e45', pine_hi_dk='#244a2e', mesa='#a95a32', mesa_sh='#6e2c1c',
             mesa_top='#c47a4a', mesa_hi='#bd6c3c', sand='#a48459', sand_sh='#86683f', sun='#ebe5cc', sun_sh='#c7bf9f',
             sun_ray='#d8d0b2', ray_sh='#c7bf9f')
VARIANTS = [
    ('Current', {}, {}),
    ('Golden hour', dict(sky0='#d9714a', sky1='#f0a35c', sky2='#f8d48a', far='#8a7f9a', far_sh='#675c7a', far_hi='#a596b0',
                         snow_sh='#d6b9a8', hill='#86a24a', hill_hi='#b0c062', cloud='#fbe2c4', cloud_sh='#e2b394'), {}),
    ('Night, moon over the vent', NIGHT, dict(moon=True, stars=70)),
    ('Dusty wasteland', dict(sky0='#a9a27a', sky1='#cbbf8e', sky2='#e6d4a0', far='#8a8576', far_sh='#686457', far_hi='#a19c8b',
                             hill='#8e9a4e', hill_sh='#6a763a', hill_hi='#a8b266', pine='#4a7046', pine_sh='#2b4a2e',
                             mesa='#cf7a44', mesa_sh='#8c4026'), dict(grit=1.8)),
    ('Heavy ink', {}, dict(ink=1.35, grit=1.6)),
    ('Clean ink', {}, dict(ink=0.75, grit=0.35)),
    ('Comic halftone sky', {}, dict(halftone=True)),
    ('Kraft-paper panels', dict(cream='#e6cf9c', banner='#dcc28a'), dict(scuff=True)),
    ('Vivid', dict(sky0='#2b8cc4', sky1='#68c2d8', sky2='#ffd47a', hill='#6bb03a', hill_sh='#478a2a', hill_hi='#94cc54',
                   pine='#2f8443', pine_sh='#1b5a2b', pine_hi='#47a057', mesa='#ec6a2c', mesa_sh='#a8381c', mesa_hi='#f59050',
                   far='#7d94b0', far_sh='#5c7290'), {}),
    ('Alien dusk', dict(sky0='#2f2350', sky1='#5d3f78', sky2='#d4806a', far='#5b567a', far_sh='#403c5c', far_hi='#77709a',
                        cloud='#e9b8b0', cloud_sh='#b98a96', snow_sh='#b6a6c6', sun='#ffcf6a', star='#f8e6ff'), dict(stars=40, star_y=12)),
    ('Overcast alpine', dict(sky0='#7d96a3', sky1='#a6bac0', sky2='#d5dbd4', far='#6d7e8e', far_sh='#526272', far_hi='#8798a6',
                             hill='#6f9a52', hill_sh='#507a3a', cloud='#eef0ec', cloud_sh='#bcc6c8', sun='#f1dc8c'), {}),
]

def render(colours, flags, dpmm=12):
    import cairosvg
    base_c, base_v = copy.deepcopy(M.C), copy.deepcopy(M.V)
    try:
        M.C.update(colours); M.V.update(flags)
        M.out.clear(); M._clip[0] = 0; M.scene(); M.panels()
        pw, ph = M.W + 2 * M.BLEED, M.H + 2 * M.BLEED
        hole = [f'<circle cx="{M.VX:.3f}" cy="{M.VY:.3f}" r="{M.VENT_HOLE_D / 2:.3f}" fill="#ffffff"/>']
        svg = M.svg(list(M.out) + hole + M.cut_lines(sw=0.25), pw, ph, -M.BLEED, -M.BLEED)
        return cairosvg.svg2png(bytestring=svg.encode(), output_width=round(pw * dpmm), output_height=round(ph * dpmm),
                                background_color='white')
    finally:
        M.C.clear(); M.C.update(base_c); M.V.clear(); M.V.update(base_v)

def main():
    from PIL import Image, ImageDraw, ImageFont
    vd = os.path.join(M.OUT, 'variants'); os.makedirs(vd, exist_ok=True)
    tiles = []
    for i, (name, colours, flags) in enumerate(VARIANTS):
        png = render(colours, flags)
        with open(os.path.join(vd, f'label_variant_{i:02d}.png'), 'wb') as f: f.write(png)
        im = Image.open(io.BytesIO(png)).convert('RGB'); tiles.append((i, name, im.resize((im.width // 2, im.height // 2))))
    tw, th = tiles[0][2].size; cols, pad, head = 2, 16, 44
    rows = (len(tiles) + cols - 1) // cols
    img = Image.new('RGB', (cols * (tw + pad) + pad, rows * (th + head + pad) + pad), '#f4efe4')
    fp = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    font = ImageFont.truetype(fp, 28) if os.path.exists(fp) else ImageFont.load_default()
    dr = ImageDraw.Draw(img)
    for k, (n, name, t) in enumerate(tiles):
        cx, cy = pad + (k % cols) * (tw + pad), pad + (k // cols) * (th + head + pad)
        dr.text((cx, cy + 6), f'{n}. {name}' if n else f'0. {name} (for reference)', fill='#17120f', font=font)
        img.paste(t, (cx, cy + head))
    img.save(os.path.join(M.OUT, 'label_variants.png'))

if __name__ == '__main__':
    main()
