#!/usr/bin/env python3
"""Regenerate the P0 board pictures in this folder from hardware/Production/Monolith.kicad_pcb.

Writes monolith-p0-render-{top,bottom,iso-top,iso-bottom}.png (raytraced, with every 3D model),
monolith-p0-board-{front,back}.png (copper, mask and silk plots) and monolith-p0-layers.pdf
(front, back, then each copper layer, one page each). The board file is only read: KiCad runs
on a copy in a temporary folder, because kicad-cli rewrites the project file next to the board.

    python3 docs/hardware/board_pictures.py --label "master dd34285" [--models DIR] [--fast]

Needs: Docker with the kicad/kicad:10.0 image (see the kicad-tools-and-mcp skill), and Python
with cairosvg, pypdf and Pillow. The Docker image has no standard KiCad 3D library, so the
models the board uses from ${KICAD10_3DMODEL_DIR} are downloaded once from the kicad-packages3D
repository on GitLab into --models (default: a cache folder in the system temp directory).
--fast renders at basic quality (seconds instead of minutes) for a quick look.
"""
import argparse, io, os, re, shutil, subprocess, sys, tempfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PROD = os.path.join(REPO, 'hardware', 'Production')
IMAGE = 'kicad/kicad:10.0'
LIB_URL = 'https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/master/'
# (output name, side, rotation, final width): the top views lie on their side with the ports on the right,
# the two iso views look at the port end.
RENDERS = [('render-top', 'top', '0,0,-90', 1600), ('render-bottom', 'bottom', '0,0,-90', 1600),
           ('render-iso-top', 'top', '-45,0,150', 1600), ('render-iso-bottom', 'bottom', '-45,0,150', 1600)]
PAGES = [('Front: F.Cu, F.Mask, F.Silkscreen', 'F.Cu,F.Mask,F.Silkscreen,Edge.Cuts', False),
         ('Back: B.Cu, B.Mask, B.Silkscreen (seen from the back)', 'B.Cu,B.Mask,B.Silkscreen,Edge.Cuts', True),
         ('F.Cu (top copper, 2 oz)', 'F.Cu,Edge.Cuts', False),
         ('In1.Cu (0.5 oz)', 'In1.Cu,Edge.Cuts', False),
         ('In2.Cu (0.5 oz)', 'In2.Cu,Edge.Cuts', False),
         ('In3.Cu (0.5 oz)', 'In3.Cu,Edge.Cuts', False),
         ('In4.Cu (0.5 oz)', 'In4.Cu,Edge.Cuts', False),
         ('B.Cu (bottom copper, 2 oz, seen from the back)', 'B.Cu,Edge.Cuts', True)]


def kicad(work, models, *args):
    cmd = ['docker', 'run', '--rm', '-u', '0', '-e', 'KICAD10_3DMODEL_DIR=/k3d', '-v', work + ':/p',
           '-v', models + ':/k3d:ro', '-w', '/p', IMAGE, 'kicad-cli'] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit('kicad-cli failed: %s\n%s' % (' '.join(args), r.stdout[-2000:] + r.stderr[-2000:]))


def fetch_models(board, models):
    want = sorted(set(re.findall(r'\(model "\$\{KICAD10_3DMODEL_DIR\}/([^"]+)"', open(board).read())))
    for rel in want:
        dst = os.path.join(models, rel)
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            urllib.request.urlretrieve(LIB_URL + rel, dst)
    return len(want)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--label', required=True, help='text for the PDF page headers, for example "master dd34285"')
    ap.add_argument('--models', default=os.path.join(tempfile.gettempdir(), 'kicad-packages3D-cache'))
    ap.add_argument('--fast', action='store_true')
    a = ap.parse_args()
    import base64
    import cairosvg
    from PIL import Image
    from pypdf import PdfReader, PdfWriter

    work = tempfile.mkdtemp(prefix='monolith-pictures-')
    for f in ('Monolith.kicad_pcb', 'Monolith.kicad_pro'):
        shutil.copy(os.path.join(PROD, f), work)
    shutil.copytree(os.path.join(PROD, '3dmodels'), os.path.join(work, '3dmodels'))
    os.makedirs(a.models, exist_ok=True)
    n = fetch_models(os.path.join(work, 'Monolith.kicad_pcb'), a.models)
    subprocess.run(['chmod', '-R', 'a+rwX', work, a.models])
    print('standard-library 3D models used by the board:', n)

    for name, side, rot, width in RENDERS:
        kicad(work, a.models, 'pcb', 'render', '-o', name + '.png', '--side', side, '--rotate', "'%s'" % rot,
              '--quality', 'basic' if a.fast else 'high', '--background', 'transparent',
              '-w', '3200', '-h', '3200', '--zoom', '0.9', 'Monolith.kicad_pcb')
        im = Image.open(os.path.join(work, name + '.png')).convert('RGBA')
        box = im.getchannel('A').getbbox()
        m = 40
        im = im.crop((max(box[0] - m, 0), max(box[1] - m, 0), min(box[2] + m, im.width), min(box[3] + m, im.height)))
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.save(os.path.join(HERE, 'monolith-p0-%s.png' % name), optimize=True)
        print('wrote', name, im.size)

    out = PdfWriter()
    for i, (title, layers, mirror) in enumerate(PAGES):
        svg = 'page%d.svg' % i
        args = ['pcb', 'export', 'svg', '-o', svg, '-l', layers, '--mode-single', '--page-size-mode', '2',
                '--exclude-drawing-sheet', '--drill-shape-opt', '2']
        kicad(work, a.models, *(args + (['--mirror'] if mirror else []) + ['Monolith.kicad_pcb']))
        src = open(os.path.join(work, svg)).read()
        if i < 2:   # the two plots, 21 px per mm on a white background
            mm = float(re.search(r'width="([0-9.]+)mm"', src).group(1))
            cairosvg.svg2png(bytestring=src.encode(), output_width=round(mm * 21), background_color='white',
                             write_to=os.path.join(HERE, 'monolith-p0-board-%s.png' % ('front', 'back')[i]))
        w, h = (float(re.search(r'%s="([0-9.]+)mm"' % k, src).group(1)) for k in ('width', 'height'))
        head = 6.5  # mm of header above the plot; the page is the board at twice size
        page = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                'width="%.3fmm" height="%.3fmm" viewBox="0 0 %.3f %.3f">'
                '<rect width="100%%" height="100%%" fill="white"/>'
                '<text x="1.5" y="2.6" font-family="DejaVu Sans, sans-serif" font-size="1.5">Monolith P0, %s</text>'
                '<text x="1.5" y="5.2" font-family="DejaVu Sans, sans-serif" font-size="1.5">%d/%d %s</text>'
                '<image x="0" y="%.3f" width="%.3f" height="%.3f" xlink:href="data:image/svg+xml;base64,%s"/></svg>')
        page = page % (2 * w, 2 * h + 2 * head, w, h + head, a.label, i + 1, len(PAGES), title, head, w, h,
                       base64.b64encode(src.encode()).decode())
        out.append(PdfReader(io.BytesIO(cairosvg.svg2pdf(bytestring=page.encode()))))
    with open(os.path.join(HERE, 'monolith-p0-layers.pdf'), 'wb') as f:
        out.write(f)
    print('wrote plots and monolith-p0-layers.pdf (%d pages)' % len(PAGES))
    shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    main()
