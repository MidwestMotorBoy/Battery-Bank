# Research notes

Dated working notes and the sources behind decisions. Each folder is a snapshot of what was known on its date, so cell figures and part numbers can be out of date; the decisions they led to are in [`docs/spec.md`](../docs/spec.md), and the finished write-ups are in [`reports/`](../reports/).

| Folder | Date | Status |
| --- | --- | --- |
| [`Pack thermal BAK 65E/`](Pack%20thermal%20BAK%2065E/README.md) | 2026-10-23 to 29 | **Current.** 3-D thermal model of the BAK 65E pack in the cup, gap-filler choice (10-24), front-cell NTC placement. The board-mounted TH101 / TH104 NTCs ([`smd-ntc.md`](Pack%20thermal%20BAK%2065E/smd-ntc.md), 10-28) supersede the wired beads of [`ntc-placement.md`](Pack%20thermal%20BAK%2065E/ntc-placement.md) (10-24); `smd.py` gained the `SMD_LAYOUT=p0f` placed-board layout on 10-29 |
| [`protection-fets/`](protection-fets/options.md) | 2026-10-23 | **Current.** Q101/Q102 options for the 65E short circuit; BSC007N04LS6 chosen |
| [`Loss reduction/`](Loss%20reduction/summary.md) | 2026-10-21 | A–E and `summary.md`: the four loss cuts, all adopted; modelled with the EVE 58E, and the spec carries the current figures. **Superseded:** `F_tenpower_60xg.md` (Tenpower 60XG), `G_feb_21700g.md` and `H_feb_limits_plan.md` (FEB 21700G era) are cell studies replaced by the BAK 65E; the old cells' datasheet notes are in [`docs/archive/`](../docs/archive/) |
| [`Ground-up mechanical concepts/`](Ground-up%20mechanical%20concepts/brief.md) | 2026-10-21 | The five-concept study that produced the cup ([report](../reports/Ground-up%20mechanical%20design.md)). **Superseded:** the concept models and their STLs / PNGs in `model/` are the study's snapshot (the adopted cup is `hardware/mechanical/monolith_cup.py`), and its lumped thermal models used the FEB 21700G cells and are replaced by the 3-D model above |
| [`Battery pack potting and drop protection/`](Battery%20pack%20potting%20and%20drop%20protection/) | 2026-10-18 | Sources for the no-potting decision ([report](../reports/Battery%20pack%20potting%20and%20drop%20protection.md)), which still stands for the cup. Written for the 82 Wh EVE pack and the side tray |
