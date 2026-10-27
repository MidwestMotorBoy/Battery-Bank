"""Preview of the wrap label on the cup with the TPU bumpers, from three sides (run monolith_label.py first).
The cup's outside is a prism, so each perimeter segment of the label is one flat quad: it is texture-mapped from
out/monolith_label_cut_art.png with a perspective transform and shaded by its normal. Bumpers are simplified to
prisms of their outlines in monolith_cup: the bottom band with its lip over the label, the top band and slab.
Run: python monolith_label_preview.py  -> out/monolith_label_on_cup.png"""
import os, math, numpy as np
from PIL import Image, ImageDraw, ImageFont
import monolith_label as LB
import monolith_cup as K

OUT = LB.OUT
BUMPER = (46, 46, 44)                     # black TPU
VENT = (236, 236, 230)
LIGHT = np.array([0.35, -0.55, 0.75]); LIGHT /= np.linalg.norm(LIGHT)

def ring(cs): return np.array(cs.to_polygons()[0], float)
P0 = LB.L['poly']
Z_VIS0 = LB.L['z_bot'] + LB.TUCK                       # bottom bumper top edge
Z_VIS1 = K.Z_TOP1 - K.BUMP_BAND                        # top bumper bottom edge
TOPB = ring(K.cs_out.offset(K.BUMP_WALL, K.ROUND)); TOP_Z = (Z_VIS1, K.Z_TOP1 + K.BUMP_T_TOP)
BOTA = ring(K.cs_col1.offset(K.BUMP_WALL_BOT, K.ROUND)); BOTA_Z = (K.Z_MOUTH - K.CAP_T - K.BUMP_T_BOT, K.Z_MOUTH + K.COLLAR_H)
BOTB = ring(K.cs_out.offset(K.LABEL_RELIEF + K.LIP_WALL, K.ROUND)); BOTB_Z = (K.Z_MOUTH + K.COLLAR_H, Z_VIS0)

class Cam:
    def __init__(self, az, el, dist=330.0, f=2500.0, size=(900, 1100), target=(4.0, 0.0, 39.0)):
        a, e = math.radians(az), math.radians(el)
        self.t = np.array(target); self.d = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
        self.pos = self.t + dist * self.d
        fwd = -self.d; right = np.cross(fwd, [0, 0, 1]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
        self.R = np.array([right, up, fwd]); self.f, self.size = f, size
    def proj(self, p):
        q = (np.asarray(p, float) - self.pos) @ self.R.T
        return np.stack([self.size[0] / 2 + self.f * q[..., 0] / q[..., 2], self.size[1] / 2 - self.f * q[..., 1] / q[..., 2]], -1), q[..., 2]
    def facing(self, ctr, n): return np.dot(self.pos - ctr, n) > 0

def shade(rgb, n, amb=0.55):
    k = amb + (1 - amb) * max(0.0, float(np.dot(n, LIGHT)))
    return tuple(int(min(255, c * k)) for c in rgb)

def homography(dst, src):
    """coefficients mapping output (dst) pixels to input (src) pixels, for Image.PERSPECTIVE"""
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]; b += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(b, float))

def side_faces(poly, z0, z1):
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        e = b - a; nrm = np.array([e[1], -e[0], 0.0]); L = np.linalg.norm(nrm)
        if L < 1e-9: continue
        yield i, a, b, nrm / L

def render(cam, tex, ss=2):
    W0, H0 = cam.size; cam = Cam.__new__(Cam).__dict__.update(cam.__dict__) or cam
    img = Image.new('RGB', (W0 * ss, H0 * ss), (250, 248, 243)); dr = ImageDraw.Draw(img)
    pj = lambda p: cam.proj(p)[0] * ss
    tw, th = tex.size; kx, ky = tw / LB.W, th / LB.H
    sarr = LB.L['s']; per, seam = LB.PER, LB.L['seam']
    zt = LB.L['z_top']
    def quad(a, b, u0, u1, n):
        q3 = [(a[0], a[1], Z_VIS1), (b[0], b[1], Z_VIS1), (b[0], b[1], Z_VIS0), (a[0], a[1], Z_VIS0)]
        q2 = pj(np.array(q3))
        src = [(u0 * kx, (zt - Z_VIS1) * ky), (u1 * kx, (zt - Z_VIS1) * ky), (u1 * kx, (zt - Z_VIS0) * ky), (u0 * kx, (zt - Z_VIS0) * ky)]
        x0, y0 = np.floor(q2.min(0)).astype(int) - 1; x1, y1 = np.ceil(q2.max(0)).astype(int) + 1
        if x1 - x0 < 1: return
        coeffs = homography([(x - x0, y - y0) for x, y in q2], src)
        patch = tex.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC)
        k = 0.62 + 0.38 * max(0.0, float(np.dot(n, LIGHT)))
        patch = Image.eval(patch, lambda c: int(c * k))
        mask = Image.new('L', patch.size, 0); ImageDraw.Draw(mask).polygon([(x - x0, y - y0) for x, y in q2], fill=255)
        img.paste(patch, (x0, y0), mask)

    def bumper(poly, z0, z1):
        for i, a, b, n in side_faces(poly, z0, z1):
            ctr = np.array([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (z0 + z1) / 2])
            if not cam.facing(ctr, n): continue
            q = pj(np.array([(a[0], a[1], z1), (b[0], b[1], z1), (b[0], b[1], z0), (a[0], a[1], z0)]))
            c = shade(BUMPER, n, 0.7); dr.polygon([tuple(p) for p in q], fill=c, outline=c)
        if cam.d[2] > 0:
            dr.polygon([tuple(p) for p in pj(np.c_[poly, np.full(len(poly), z1)])], fill=shade(BUMPER, np.array([0, 0, 1.0]), 0.7))
    # bottom bumper first (the label covers its inner top face), then the label, then the top bumper
    bumper(BOTA, *BOTA_Z); bumper(BOTB, *BOTB_Z)
    # label quads (only the band between the bumpers is visible)
    for i, a, b, n in side_faces(P0, Z_VIS0, Z_VIS1):
        ctr = np.array([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 40.0])
        if not cam.facing(ctr, n): continue
        u0 = (sarr[i] - seam) % per; u1 = u0 + np.linalg.norm(b - a)
        if u1 > per + 1e-6:                                  # the segment holding the seam: two faces
            m = a + (b - a) * (per - u0) / (u1 - u0)
            parts = [(a, m, u0, per), (m, b, 0.0, u1 - per)]
        else: parts = [(a, b, u0, u1)]
        for a, b, u0, u1 in parts: quad(a, b, u0, u1, n)
    bumper(TOPB, *TOP_Z)
    # port well and the two USB-C openings on the top
    zt1 = TOP_Z[1]
    well = [(K.PORT_X - 4.5, -14.0), (K.PORT_X + 4.5, -14.0), (K.PORT_X + 4.5, 14.0), (K.PORT_X - 4.5, 14.0)]
    dr.polygon([tuple(p) for p in pj(np.array([(x, y, zt1) for x, y in well]))], fill=(24, 24, 23))
    for py in K.PORT_YS:
        t = np.linspace(0, 2 * np.pi, 40); hx, hy = 2.0, 4.8
        st = [(K.PORT_X + hx * math.cos(a), py + (hy - hx) * np.sign(math.sin(a)) + hx * math.sin(a), zt1) for a in t]
        dr.polygon([tuple(p) for p in pj(np.array(st))], fill=(8, 8, 8), outline=(90, 90, 92))
    return img.resize((W0, H0), Image.LANCZOS)

def main():
    tex = Image.open(os.path.join(OUT, LB.NAME + '_cut_art.png')).convert('RGB')
    arr = np.array(tex); g = (arr[..., 1] > 200) & (arr[..., 0] < 60) & (arr[..., 2] < 60); arr[g] = VENT
    tex = Image.fromarray(arr)
    views = [(-40, 18, 'board face + side A'), (50, 18, 'board face + side B'), (180, 18, 'back + seam')]
    tiles = [render(Cam(az, el), tex) for az, el, _ in views]
    w, h = tiles[0].size
    sheet = Image.new('RGB', (w * len(tiles), h + 60), (250, 248, 243)); d = ImageDraw.Draw(sheet)
    try: font = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-SemiBold.otf', 26)
    except OSError: font = ImageFont.load_default()
    for k, (t, (_, _, name)) in enumerate(zip(tiles, views)):
        sheet.paste(t, (k * w, 0)); tw = d.textlength(name, font=font); d.text((k * w + (w - tw) / 2, h + 12), name, fill=(60, 56, 50), font=font)
    sheet.save(os.path.join(OUT, LB.NAME + '_on_cup.png'))

if __name__ == '__main__':
    main()
