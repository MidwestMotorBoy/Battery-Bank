"""Capacitor-bank simulations for the board-shrink study (rev2-changes.md item 1d, 2026-10-17).

Steady-state switching ripple, per-capacitor RMS current, input-filter damping (Middlebrook) and the TPS62933
load-step estimate, for the current capacitor banks and for smaller alternatives. Pure numpy; writes
cap_sims.json next to this file for the report.

Method:
- Ripple / RMS: the converter's switched current (ideal CCM waveform from L, fsw, D) is split into harmonics of
  fsw; each harmonic divides between the capacitors (ESR + ESL + DC-bias-derated C) and the external path
  (cable, or pack wiring + cells) by admittance. Gives each part's RMS current and the rail's p-p ripple.
- Damping: |Zout| of source + bank against the converter's negative input resistance V^2/P. Middlebrook wants
  |Zout| well below |Zin| at every frequency; the peak sits at the source-inductance / bank resonance.
- TPS62933 load step: TI's eq. 21 (datasheet sec. 10.2.2.8), which assumes about 8 cycles to respond.
Run: python -I tools/cap_sims.py
"""
import json, os
import numpy as np

# ---- parts. C0 nominal; DC bias C(V) = C0 / (1 + (V/Vk)^p) fitted to the figures in DevBoard/README.md and
# the review notes (GMK325 22u35V: 8.5 uF at 20 V; CL31A226 22u25V: ~4.7 uF at 16.8 V; TMK325 47u25V: 10.3 uF
# at 16.8 V; CL31A106 10u50V: ~4 uF at 16.8 V). Worst case adds -20 % tolerance and -10 % at 85 C for MLCCs,
# -20 % for polymers. irms: allowed ripple current; MLCC values are assumptions (about 20 C rise), polymers
# from their datasheets. area: courtyard area measured on MonolithDev.kicad_pcb (mm^2).
PARTS = {
    "GMK325 22u 35V 1210": dict(c0=22e-6, vk=15.0, p=1.6, esr=0.004, esl=1.0e-9, irms=3.0, area=14.6, kind="mlcc"),
    "CL31A226 22u 25V 1206": dict(c0=22e-6, vk=7.4, p=1.6, esr=0.005, esl=0.9e-9, irms=2.5, area=10.5, kind="mlcc"),
    "TMK325 47u 25V 1210": dict(c0=47e-6, vk=6.5, p=1.6, esr=0.003, esl=1.0e-9, irms=3.5, area=14.6, kind="mlcc"),
    "CL31A106 10u 50V 1206": dict(c0=10e-6, vk=13.0, p=1.6, esr=0.006, esl=0.9e-9, irms=2.5, area=10.5, kind="mlcc"),
    "CL10A106 10u 25V 0603": dict(c0=10e-6, vk=4.0, p=1.6, esr=0.008, esl=0.6e-9, irms=1.5, area=4.0, kind="mlcc"),
    "HV1V107 100u 35V polymer": dict(c0=100e-6, esr=0.048, esl=3e-9, irms=1.5, area=53.8, kind="poly"),
    "EEH-ZA1E101 100u 25V hybrid": dict(c0=100e-6, esr=0.030, esl=3e-9, irms=2.0, area=53.8, kind="poly"),
}

def c_eff(part, v, worst=True):
    p = PARTS[part]
    if p["kind"] == "poly":
        return p["c0"] * (0.8 if worst else 1.0)
    c = p["c0"] / (1 + (v / p["vk"]) ** p["p"])
    return c * (0.8 * 0.9 if worst else 1.0)

def bank_c(bank, v, worst=True):
    return sum(n * c_eff(part, v, worst) for part, n in bank)

def bank_area(bank):
    return sum(n * PARTS[part]["area"] for part, n in bank)

# ---- banks per port (port 2 is identical). Current design first in each list.
G, S, T, I10, P0603 = "GMK325 22u 35V 1210", "CL31A226 22u 25V 1206", "TMK325 47u 25V 1210", "CL31A106 10u 50V 1206", "CL10A106 10u 25V 0603"
POLY, HYB = "HV1V107 100u 35V polymer", "EEH-ZA1E101 100u 25V hybrid"
BANKS = {
    "usb": {  # AC_SNS_N: charger input (forward) / output (reverse); BQ25756 >= 80 uF after derating
        "U0 now: 4x 22u 1210 + 100u polymer": [(G, 4), (POLY, 1)],
        "U1: 4x 22u 1210, no polymer": [(G, 4)],
        "U2: 2x 22u 1210 + 100u polymer": [(G, 2), (POLY, 1)],
        "U3: 6x 22u 1210, no polymer": [(G, 6)],
        "U4: 3x 22u 1210 + 100u polymer": [(G, 3), (POLY, 1)],
    },
    "bat": {  # BAT_SNS_P: charger output (forward) / input (reverse); BQ25756 >= 80 uF after derating
        "B0 now: 3x 22u 1206 + 100u hybrid": [(S, 3), (HYB, 1)],
        "B1: 3x 22u 1206, no hybrid": [(S, 3)],
        "B2: 2x 22u 1206 + 100u hybrid": [(S, 2), (HYB, 1)],
        "B3: 3x 47u 1210, no hybrid": [(T, 3)],
    },
    "pp5v": {  # TPS62933 output: TI typical 20 uF, minimum 10 uF effective (table 10-2, 5 V at 1.2 MHz)
        "P0 now: C407 + 2x 22u 1206 + 100u polymer": [(P0603, 1), (S, 2), (POLY, 1)],
        "P1: C407 + 2x 22u 1206, no polymer": [(P0603, 1), (S, 2)],
        "P2: C407 + 1x 22u 1206": [(P0603, 1), (S, 1)],
        "P3: C407 + 3x 22u 1206, no polymer": [(P0603, 1), (S, 3)],
    },
    "5vin": {  # TPS62933 input (5V_IN from PACK_P): TI typical 10 uF + 0.1 uF
        "I0 now: 2x 10u 50V 1206": [(I10, 2)],
        "I1: 1x 10u 50V 1206": [(I10, 1)],
    },
}

FSW, L1 = 600e3, 2.2e-6           # BQ25756: R412 sets ~600 kHz; L401 2.2 uH
FSW5, L5, V5 = 1.2e6, 3.3e-6, 5.16  # TPS62933: 1.2 MHz, L402 3.3 uH, PP5V 5.16 V
ICHG, ETA = 5.5, 0.95
KMAX = 10                            # highest harmonic kept (x fsw)
HF = dict(c=0.05e-6, esr=0.02, esl=0.4e-9)  # 0.1 uF 50 V 0402 X7R, about half left at 16-20 V
N = 4096

def ext_cable(L=1.0e-6, R=0.15):   # USB-C cable round trip + contacts + TPS25751 switch
    return lambda w: R + 1j * w * L

def ext_pack(L=0.3e-6, R=0.085):   # 4 cells (~18 mOhm each) + RBAT/bus/leads
    return lambda w: R + 1j * w * L

def waveform(mode, vin, vout, p_out, L, fsw):
    """Switched currents on the input and output sides of an ideal CCM converter, one period."""
    t = np.arange(N) / N
    if mode == "buck":
        d = vout / vin; il = p_out / vout; di = (vin - vout) * d / (L * fsw)
        ramp = np.where(t < d, il - di / 2 + di * t / d, il + di / 2 - di * (t - d) / (1 - d))
        i_in = np.where(t < d, ramp, 0.0); i_out = ramp
    else:
        d = 1 - vin / vout; il = p_out / ETA / vin; di = vin * d / (L * fsw)
        ramp = np.where(t < d, il - di / 2 + di * t / d, il + di / 2 - di * (t - d) / (1 - d))
        i_in = ramp; i_out = np.where(t < d, 0.0, ramp)
    return i_in, i_out, d, il, di

def split(i_sw, bank, v, fsw, zext):
    """Harmonic current division between the bank and the external path. Returns rail p-p ripple and per-part
    RMS (per single capacitor)."""
    X = np.fft.rfft(i_sw - i_sw.mean()) / N * 2  # peak amplitude per harmonic
    k = np.arange(len(X)); k[0] = 1
    X[k > KMAX] = 0  # up to 10 x fsw: the capacitive + ESR ripple the bank sets; edge/ESL spikes are a layout matter
    w = 2 * np.pi * fsw * k
    zs = {}
    zhf = HF["esr"] + 1j * w * HF["esl"] + 1 / (1j * w * HF["c"])  # the 0.1 uF 0402 at the FETs (C430/C438)
    for part, n in bank:
        pp = PARTS[part]
        zs[part] = (pp["esr"] + 1j * w * pp["esl"] + 1 / (1j * w * c_eff(part, v)), n)
    ytot = sum(n / z for z, n in zs.values()) + 1 / zext(w) + 1 / zhf
    V = X / ytot; V[0] = 0
    vt = np.fft.irfft(V / 2 * N, n=N)
    rms = {part: float(np.sqrt(np.sum(np.abs(V / z) ** 2) / 2)) for part, (z, n) in zs.items()}
    return float(vt.max() - vt.min()), rms

def ripple_study():
    out = []
    fwd = [(5, 3), (9, 3), (15, 3), (20, 5)]
    for side_usb, usb_v, usb_i in [(s, v, i) for s in ("fwd", "rev") for v, i in fwd]:
        for vbat in ((12.0, 14.8, 16.8) if side_usb == "fwd" else (10.0, 12.0, 14.8, 16.8)):
            if side_usb == "fwd":
                p_out = min(usb_v * usb_i * ETA, vbat * ICHG); vin, vout = usb_v, vbat
            else:
                p_out = usb_v * usb_i; vin, vout = vbat, usb_v
            mode = "buck" if vin >= vout else "boost"
            i_in, i_out, d, il, di = waveform(mode, vin, vout, p_out, L1, FSW)
            usb_sw, bat_sw = (i_in, i_out) if side_usb == "fwd" else (i_out, i_in)
            row = dict(dir=side_usb, usb_v=usb_v, usb_i=usb_i, vbat=vbat, mode=mode, p_out=round(p_out, 1),
                       il=round(il, 2), il_pk=round(il + di / 2, 2), banks={})
            for name, bank in BANKS["usb"].items():
                vpp, rms = split(usb_sw, bank, usb_v, FSW, ext_cable())
                row["banks"][name] = dict(vpp=vpp, rms=rms)
            for name, bank in BANKS["bat"].items():
                vpp, rms = split(bat_sw, bank, vbat, FSW, ext_pack())
                row["banks"][name] = dict(vpp=vpp, rms=rms)
            out.append(row)
    return out

def worst(rows, bankname):
    """Worst-case ripple and the worst RMS/limit ratio of any single part in this bank, over all points."""
    w = dict(vpp=0, vpp_at="", ratio=0, ratio_part="", ratio_at="")
    for r in rows:
        b = r["banks"].get(bankname)
        if not b: continue
        at = f'{r["dir"]} USB {r["usb_v"]} V {r["usb_i"]} A, pack {r["vbat"]} V ({r["mode"]})'
        if b["vpp"] > w["vpp"]: w.update(vpp=b["vpp"], vpp_at=at)
        for part, i in b["rms"].items():
            ratio = i / PARTS[part]["irms"]
            if ratio > w["ratio"]: w.update(ratio=ratio, ratio_part=part, ratio_irms=i, ratio_at=at)
    return w

def damping_study():
    """Peak |Zout| of the source + bank vs |Zin| = V^2/P of the charger, forward mode (USB side) and reverse
    mode (battery side)."""
    f = np.logspace(3, 6.3, 600); w = 2 * np.pi * f
    res = {"usb": [], "bat": [], "f": f.tolist()}
    for name, bank in BANKS["usb"].items():
        for v, i in [(5, 3), (9, 3), (15, 3), (20, 5)]:
            for Lc, Rc in ((0.5e-6, 0.06), (1.0e-6, 0.06), (1.5e-6, 0.06), (1.0e-6, 0.15), (1.5e-6, 0.15)):
                zb = 1 / sum(n / (PARTS[p]["esr"] + 1j * w * PARTS[p]["esl"] + 1 / (1j * w * c_eff(p, v))) for p, n in bank)
                zo = 1 / (1 / zb + 1 / ext_cable(Lc, Rc)(w))
                zin = v * v / (v * i)
                k = int(np.argmax(abs(zo)))
                res["usb"].append(dict(bank=name, v=v, i=i, Lc_uH=Lc * 1e6, R=Rc, zpk=float(abs(zo[k])), fpk=float(f[k]),
                                       zin=zin, margin_db=float(20 * np.log10(zin / abs(zo[k]))),
                                       curve=[float(x) for x in abs(zo)] if (Lc, Rc) == (1.0e-6, 0.06) and (v, i) == (5, 3) else None))
    for name, bank in BANKS["bat"].items():
        for vbat in (10.0, 12.0, 16.8):
            for Lp, Rp in ((0.2e-6, 0.05), (0.5e-6, 0.05), (0.5e-6, 0.085)):
                zb = 1 / sum(n / (PARTS[p]["esr"] + 1j * w * PARTS[p]["esl"] + 1 / (1j * w * c_eff(p, vbat))) for p, n in bank)
                zo = 1 / (1 / zb + 1 / ext_pack(Lp, Rp)(w))
                zin = vbat * vbat / (100 / ETA)
                k = int(np.argmax(abs(zo)))
                res["bat"].append(dict(bank=name, v=vbat, Lp_uH=Lp * 1e6, R=Rp, zpk=float(abs(zo[k])), fpk=float(f[k]), zin=zin,
                                       margin_db=float(20 * np.log10(zin / abs(zo[k]))),
                                       curve=[float(x) for x in abs(zo)] if (Lp, Rp) == (0.5e-6, 0.05) and vbat == 10.0 else None))
    return res

def pp5v_study():
    out = []
    for name, bank in BANKS["pp5v"].items():
        c = bank_c(bank, V5)
        row = dict(bank=name, c_eff=c * 1e6, c_eff_typ=bank_c(bank, V5, worst=False) * 1e6, area=bank_area(bank))
        worst_vpp, worst_rms = 0, {}
        for vin in (10.0, 12.0, 16.8):
            _, i_out, d, il, di = waveform("buck", vin, V5, V5 * 3, L5, FSW5)
            vpp, rms = split(i_out, bank, V5, FSW5, lambda w: 0.05 + 1j * w * 1e-6)  # VBUS path + cable to the sink
            if vpp > worst_vpp: worst_vpp, worst_rms = vpp, rms
        row["vpp"] = worst_vpp; row["rms"] = worst_rms
        # TI eq. 21: Cout > dI / (fsw * dV * K) * ((1 - D)(1 + K) + K^2/12 (2 - D)); 0.5 -> 3 A step, 250 mV
        dI, dV, vin = 2.5, 0.25, 16.8
        D = V5 / vin; K = (vin - V5) * D / (L5 * FSW5) / 3.0
        row["cout_min_step_uF"] = dI / (FSW5 * dV * K) * ((1 - D) * (1 + K) + K * K / 12 * (2 - D)) * 1e6
        row["undershoot_est_mV"] = row["cout_min_step_uF"] / (c * 1e6) * 250
        out.append(row)
    for name, bank in BANKS["5vin"].items():
        worst_vpp, worst_rms = 0, {}
        for vin in (10.0, 12.0, 16.8):
            i_in, _, d, il, di = waveform("buck", vin, V5, V5 * 3, L5, FSW5)
            vpp, rms = split(i_in, bank, vin, FSW5, ext_pack(0.2e-6, 0.09))
            if vpp > worst_vpp: worst_vpp, worst_rms = vpp, rms
        out.append(dict(bank=name, c_eff=bank_c(bank, 16.8) * 1e6, area=bank_area(bank), vpp=worst_vpp, rms=worst_rms))
    return out

def main():
    rows = ripple_study()
    summary = {}
    for side, v in (("usb", 20.0), ("bat", 16.8)):
        for name, bank in BANKS[side].items():
            w = worst(rows, name)
            summary[name] = dict(side=side, c_eff_worst=bank_c(bank, v) * 1e6, c_eff_typ=bank_c(bank, v, worst=False) * 1e6,
                                 meets_80=bank_c(bank, v) >= 80e-6, area=bank_area(bank), **w)
    damp = damping_study()
    pp5 = pp5v_study()
    out = dict(summary=summary, rows=rows, damping=damp, pp5v=pp5, parts=PARTS)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cap_sims.json")
    json.dump(out, open(path, "w"), indent=1)
    for name, s in summary.items():
        print(f'{name:42s} Ceff {s["c_eff_worst"]:6.1f} uF (typ {s["c_eff_typ"]:5.1f}) {"OK " if s["meets_80"] else "LOW"} '
              f'area {s["area"]:5.1f} mm2  ripple {s["vpp"]*1e3:6.0f} mV  worst part {s["ratio"]*100:4.0f}% of rating '
              f'({s["ratio_part"]}, {s.get("ratio_irms", 0):.2f} A)  at {s["ratio_at"]}')
    print()
    for side in ("usb", "bat"):
        names = BANKS[side]
        for name in names:
            rs = [r for r in damp[side] if r["bank"] == name]
            m = min(rs, key=lambda r: r["margin_db"])
            print(f'damping {name:42s} worst margin {m["margin_db"]:5.1f} dB  (|Zout| {m["zpk"]*1e3:5.0f} mOhm at {m["fpk"]/1e3:5.1f} kHz vs |Zin| {m["zin"]:.2f} Ohm; {m["v"]} V, L {m.get("Lc_uH", m.get("Lp_uH"))} uH, R {m["R"]*1e3:.0f} mOhm)')
    print()
    for r in pp5:
        print(f'{r["bank"]:44s} Ceff {r["c_eff"]:6.1f} uF  area {r["area"]:5.1f}  ripple {r["vpp"]*1e3:5.1f} mV  '
              + (f'step Cmin {r["cout_min_step_uF"]:.0f} uF, undershoot ~{r["undershoot_est_mV"]:.0f} mV  ' if "cout_min_step_uF" in r else "")
              + ", ".join(f'{p.split()[0]} {i:.2f} A' for p, i in r["rms"].items()))

if __name__ == "__main__":
    main()
