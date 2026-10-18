"""Low-profile bulk study (2026-10-18): replace the 6.3x7.7 mm cans (C421/C521 polymer, C208 hybrid) with parts no
taller than the inductors (APS0730M2R2F, 3.1 mm max).

USB side (AC_SNS_N, per port): unpowered in sleep, so leakage does not matter; 35 V polymer tantalum KEMET
T521D336M035ATE065 (33 uF, 65 mOhm, 2.2 A rms at 85 C, 3.1 mm max, 7343-31) next to more GMK325 22u 35V 1210.
PACK_P (shared bus): always live, so only MLCCs. Polymer aluminium chips (SP-Cap, CDE MPD) and polymer tantalum
are rated 0.1-0.3 CV of leakage (hundreds of uA), against a ~150 uA sleep budget. TMK325ABJ476MM 47u 25V 1210
(2.5 mm) gives the most capacitance per mm^2 at 16.8 V of the stocked MLCCs.

Reuses DevBoard/tools/cap_sims.py (USB side: ripple, RMS, cable damping) and pack_bus_sims.py (shared bus).
Run: "C:/Program Files/KiCad/10.0/bin/python.exe" -I Production/tools/low_profile_sims.py
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("pack_bus_sims", os.path.join(HERE, "pack_bus_sims.py"))
pb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pb)
cs = pb.cs

TA = "T521D336 33u 35V polymer Ta"
cs.PARTS[TA] = dict(c0=33e-6, esr=0.065, esl=2.0e-9, irms=2.2, area=42.3, kind="poly")
G, T, POLY = "GMK325 22u 35V 1210", "TMK325 47u 25V 1210", "HV1V107 100u 35V polymer"
S, I10, HYB = pb.S, pb.I10, pb.HYB
cs.PARTS[POLY]["area"] = 66.7  # production CP_Elec_6.3x7.7 courtyard

cs.BANKS["usb"] = {
    "U0 now: 4x 22u 1210 + 100u can (7.7 mm)": [(G, 4), (POLY, 1)],
    "L1: 4x 22u 1210 + 2x 33u T521D": [(G, 4), (TA, 2)],
    "L2: 5x 22u 1210 + 2x 33u T521D": [(G, 5), (TA, 2)],
    "L3: 4x 22u 1210 + 3x 33u T521D": [(G, 4), (TA, 3)],
    "L4: 6x 22u 1210 + 2x 33u T521D": [(G, 6), (TA, 2)],
}
cs.BANKS["bat"] = {}

pb.OPTIONS.clear()
pb.OPTIONS.update({
    "A2 now: 2x22u+1x10u per port, hybrid can at H": ([(S, 2), (I10, 1)], [(HYB, 1)]),
    "M1: 2x22u+1x10u per port, 7x 47u 1210 at H": ([(S, 2), (I10, 1)], [(T, 7)]),
    "M2: 2x47u+1x10u per port, 5x 47u 1210 at H": ([(T, 2), (I10, 1)], [(T, 5)]),
    "M3: 3x47u per port, 5x 47u 1210 at H": ([(T, 3)], [(T, 5)]),
    "M4: 2x47u+1x10u per port, 6x 47u 1210 at H": ([(T, 2), (I10, 1)], [(T, 6)]),
})


def main():
    print("== USB side, per port (BQ25756 C_IN >= 80 uF after derating, at 20 V)")
    cs.main()
    print("\n== Shared PACK_P bus (>= 80 uF at 16.8 V)")
    pb.main()


if __name__ == "__main__":
    main()
