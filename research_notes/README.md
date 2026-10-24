# Research notes

Dated working notes and the sources behind decisions. Each folder is a snapshot of what was known on its date, so cell figures and part numbers can be out of date; the decisions they led to are in [`docs/spec.md`](../docs/spec.md), and the finished write-ups are in [`reports/`](../reports/).

| Folder | Date | Status |
| --- | --- | --- |
| [`Pack thermal BAK 65E/`](Pack%20thermal%20BAK%2065E/README.md) | 2026-10-23 / 24 | **Current.** 3-D thermal model of the BAK 65E pack in the cup, gap-filler choice, front-cell NTC placement |
| [`protection-fets/`](protection-fets/options.md) | 2026-10-23 | **Current.** Q101/Q102 options for the 65E short circuit; BSC007N04LS6 chosen |
| [`Loss reduction/`](Loss%20reduction/summary.md) | 2026-10-21 | The four loss cuts, all adopted. Modelled with the EVE 58E; the spec carries the current figures. `F_tenpower_60xg.md`, `G_feb_21700g.md` and `H_feb_limits_plan.md` are cell studies superseded by the BAK 65E |
| [`Ground-up mechanical concepts/`](Ground-up%20mechanical%20concepts/brief.md) | 2026-10-21 | The five-concept study that produced the cup ([report](../reports/Ground-up%20mechanical%20design.md)). Its lumped thermal models (`model/`) used the FEB cells and are superseded by the 3-D model above |
| [`Battery pack potting and drop protection/`](Battery%20pack%20potting%20and%20drop%20protection/) | 2026-10-18 | Sources for the no-potting decision ([report](../reports/Battery%20pack%20potting%20and%20drop%20protection.md)). Written for the 82 Wh EVE pack |
