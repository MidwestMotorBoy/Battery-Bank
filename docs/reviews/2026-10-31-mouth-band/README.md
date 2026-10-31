# Cup mouth: collar vs thick mouth band (2026-10-31)

Logan doubted that the cap's 1.5 mm outer collar was helping the seal (it doesn't retain the O-ring; the skirt groove does). Its job was to stop the cup's 1.2 mm mouth flats bowing outward off the O-ring. `mouth_plate.py` is a plate model of one side flat that tests whether it does.

The table gives the squeeze left at the worst spot on a flat. Nominal squeeze is 25 %, and the low-tolerance column assumes 0.35 mm of compression instead of 0.5.

| Mouth | nominal | low tol | +25 kPa inside | +50 kPa |
|---|---|---|---|---|
| No collar | 10.7 % | 7.9 % | 0 (lifts) | 0 |
| Cap collar 1.5 mm, 3 crush ribs a flat | 15.5 % | 11.2 % | 12.0 % | 8.5 % |
| Cup mouth 2.0 mm, no collar | 16.7 % | 12.1 % | 10.6 % | 4.0 % |
| **Cup mouth 2.4 mm, no collar (adopted)** | **18.8 %** | **13.5 %** | **14.0 %** | **9.1 %** |

The collar helps, but only about half as much as a rigid collar would, because it bends as a cantilever off the cap plate. Logan chose the 2.4 mm mouth band. It is 7.5 mm tall and tapers back to 1.2 mm over its top 0.8 mm. Compared with the collar:

- The pack is 1.3 g lighter: the cup gains 1.4 g, the cap loses 2.5 g, and the bottom bumper gets smaller.
- The bottom is 1.2 mm narrower in x and 0.9 mm narrower in y.
- The screws' ligament shear at +50 kPa halves, from 19 to 9.5 MPa.

**Limits of the model:**
- It is linear and uses short-term moduli. PA12 creeps under the O-ring's constant push, so every case gets worse with time.
- The O-ring force of about 1.1 N/mm at 25 % is an estimate for 70A NBR and could be off by ±50 %.
- The ends of the flat are taken as simply supported.

Coupon B (`hardware/mechanical/monolith_coupons.py`) is the real test: measure the squeeze in the middle of each flat, then dunk at 1 m.
