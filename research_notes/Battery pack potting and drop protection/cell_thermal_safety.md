# Potting 21700 cells: temperature, venting and thermal-runaway safety (4S1P EVE 58E sealed power bank)

Context: 4 x EVE INR21700-58E, 4S1P, ~82 Wh, up to 100 W discharge (~7 A/cell, ~1.2-1.4C), up to ~5.5 A charge (~1C), 3D-printed sealed shell with one ePTFE vent, potted electronics board dissipating several watts beside the cells.

Research-budget note: about 15 tool calls. Several primary sources (58E datasheet on NKON, MDPI papers, NASA NTRS PDF) returned 403 or unreadable binary, so some key numbers are missing and are listed under Gaps. Numbers marked "calc" are my own back-of-envelope estimates from stated assumptions, not published data.

## Q1. Heat generation of the EVE 58E (and similar 5 Ah 21700s) at ~1.4C discharge / ~1.1C charge

### Takeaway
I found no published DCIR or still-air heating test for the 58E. Using DCIR between the Molicel P45B's 15 mOhm (a power cell) and a plausible 25-40 mOhm for an energy cell, each cell makes about 0.7-2 W at 7 A. That is 3-8 W for the pack, before the board's own watts are added. In a sealed shell that is enough for a 30-60 K rise over a 45-60 min discharge if the heat has no conductive path out.

### Cited Findings
- EVE 58E retailer specs: 5700 mAh nominal, 16.8 A max discharge, flat top, unprotected, ~21.5 x 70.8 mm, ~71 g. Standard charge 1.12 A CC-CV. Discharge temperature range -20 to 60 C. These come from vendor listings, not an EVE document I could open. — [NKON 58E listing](https://www.nkon.nl/en/eve-inr21700-58e-5700mah-16-8a.html); [18650battery.com 58E](https://18650battery.com/products/eve-58e-21700-5700mah-18a-battery)
- A BudgetLightForum user reported finding almost no independent test data on the 58E, only EVE's release announcement. — [BLF thread](https://budgetlightforum.com/t/eve-21700-40pl-70-amp-cell/225506)
- A reseller's EVE 50E summary gives a 60 C ambient discharge limit and a 70 C surface discharge limit (third-party, not the manufacturer's document). — [18650batterystore EVE 50E](https://www.18650batterystore.com/products/eve-50e-21700-5000mah-15a-battery)
- EVE datasheets (40P, 50PL) specify "initial internal impedance" as AC 1 kHz, which is not DCIR. Test conditions are 25 +/- 2 C and <65% RH. — [EVE 50PL datasheet](https://eurolamp.ua/shop/wp-content/uploads/eve-inr21700-50pl-datasheet.pdf)
- Molicel P45B (4.5 Ah power cell) datasheet v1.2: typical DC impedance 15 mOhm at 50% SOC, AC impedance 7 mOhm at 30% SOC, continuous discharge 45 A with an 80 C cut-off. — [Molicel P45B datasheet](https://www.imrbatteries.com/content/molicel_p45b.pdf)
- An Endless-Sphere bench test says the P45B's DCIR is about 22% lower than the P42A's, with no absolute value given. — [Endless-Sphere P45B thread](https://endless-sphere.com/sphere/threads/bench-test-results-molicel-p45b-50a-4500mah-21700-an-extraordinary-cell.116190/latest)
- A Zenodo dataset (FreeTwinEV) holds internal-resistance measurements on 600 P45B cells, useful for spread. I did not extract its values. — [Zenodo 17242656](https://zenodo.org/records/17242656)
- In a LiFePO4 cylindrical-cell study, reversible (entropic) heat could reach the same magnitude as irreversible heat at low rates. — [IIETA cylindrical cell thermal behaviour](https://www.iieta.org/journals/ti-ijes/paper/10.18280/ti-ijes.652-412)
- A 2024 thesis measured entropic coefficients and heat-transfer coefficients for a commercial 21700 NCA cell at 0.5C, 1C and 2C. This is the best open source to pull numbers from; I did not extract them. — [PoliMi thesis](https://www.politesi.polimi.it/retrieve/ac66fb49-59f7-4d00-bfc8-83952c035094/Thesis.pdf)
- A Waterloo thesis covers electro-thermal modelling of the Samsung INR21700-50E. It is a likely source for 50E heat-generation parameters, but I did not extract them. — [UWaterloo 50E thesis](https://uwspace.uwaterloo.ca/items/d1e28be0-72d5-41fa-8625-d032a6e73a32)

### Inferences
- calc, cell current: 100 W / (4 x 3.6 V) = 6.9 A nominal. Near the end of discharge (4 x 3.2 V) it is about 7.8 A. At 5.5 A charge the heat per cell is about 60% of the discharge figure (I² scaling), plus the entropic term.
- calc, Joule heat per cell, P = I²·R_DC: 7 A, 15 mOhm gives 0.74 W; 25 mOhm gives 1.2 W; 40 mOhm gives 2.0 W. High-energy 5.7 Ah cells (58E, 50E) are built for energy rather than power, so a DCIR above the P45B's 15 mOhm is likely. Plan on about 1-1.5 W per cell (4-6 W for the pack) and treat 2 W per cell as a stress case. DCIR roughly doubles at low SOC and below about 10 C, so the end of a cold discharge is the worst case.
- Entropic term (unsourced magnitude): Q_rev = I·T·dU/dT. For NMC/NCA, dU/dT is of order ±0.1-0.3 mV/K and depends on SOC, which gives roughly ±0.2-0.6 W per cell at 7 A. It is not negligible against Joule heat at 1.4C, and its sign changes with SOC and with charge vs discharge. Verify against the PoliMi thesis data.
- calc, still air, single cell: surface area of one 21700 is about 5.3e-3 m². At h = 7 W/m²K, conductance to air is about 0.037 W/K, so the steady-state rise at 1.2 W is about 32 K. Cell heat capacity (71 g x ~1 J/gK, assumed) is about 70 J/K, giving a time constant of about 1900 s. A 50 min discharge would therefore reach about 25-30 K above the *internal air*. The internal air is itself heated by the board and the other cells, and in a sealed shell it rises well above ambient. Four touching cells expose only about 60% of their area to air, which makes this worse.
- calc, adiabatic bound: 4-6 W into 4 cells (~280 J/K) for 3000 s gives a 43-64 K rise if no heat leaves. Starting from 25 C ambient this approaches or exceeds the 60 C discharge and 70 C surface limits. A sealed 100 W pack therefore needs a deliberate conductive path from the cells to the shell. Relying on internal air is not enough.

### Gaps
- No EVE 58E DCIR (DC, at 10 s/30 s pulses vs SOC) found. The NKON datasheet download returned 403. Pull the EVE spec PDF directly or measure (HPPC pulse at 7 A).
- No independent (Mooch / lygte-info) test of the 58E found. lygte-info may not have tested it. Mooch tests of the Samsung 50E exist on forums but were not retrieved.
- No published 58E/50E still-air temperature-rise curve at 1-1.5C was found.

## Q2. Still-air natural convection in a closed enclosure vs conduction through potting: when potting helps vs hurts

### Takeaway
Narrow internal air gaps are poor conductors. Air's k is about 0.026 W/mK, and convection barely develops in gaps of a few mm. Almost any solid potting that bridges cell to shell conducts better: unfilled silicone or PU is about 0.15-0.3 W/mK and filled grades about 0.6-2 W/mK. Potting only matches air when it is a low-density foam (k about 0.03-0.06 W/mK) or when it surrounds cells without touching a heat-rejecting wall. Once the cells are coupled, the bottleneck moves to the printed shell wall and the outside convection.

### Cited Findings
- SAE 2024-28-0224 simulated an LFP pack of 32700 cells encapsulated with PU foam, silicone or silicone-modified epoxy. The silicone-potted pack ran 2.57 C cooler at 1C and 3.84 C cooler at 2C than the air-filled pack. (Format: 32700 LFP, simulation.) — [SAE 2024-28-0224](https://saemobilus.sae.org/papers/thermal-performance-encapsulated-lfp-battery-packs-encapsulants-2024-28-0224)
- MathWorks Simscape Battery docs: cylindrical cells are often joined with potting compound for rigidity *and thermal isolation*. The space between cells may hold adhesive, potting, a holder, air or a mix, and inter-cell resistance must be computed from the actual fill. — [MathWorks inter-cell thermal path](https://www.mathworks.com/help/simscape-battery/ug/inter-cell-thermal-path-workflow.html)
- Behi et al. (Designs 2022), cylindrical Li-ion module: maximum temperature was 64.38 C under natural convection, 40.4 C with PCM and 39 C with PCM-graphite. That is a 38% and 40% reduction, and temperature uniformity improved 60% and 96%. — [Behi et al., Designs 2022 (DOAJ)](https://doaj.org/article/fc51d87754d749988f6f17755f4aa228)
- A 2024 J. Energy Storage numerical study (reported in search summary) found pure PCM and PCM composites (Al2O3, carbon black, EG) cut module maximum temperature by only 2-4 C vs natural convection. At modest rates, then, the benefit is small. — search summary; primary URL not confirmed (see Gaps)
- A 21700 pack study (Applied Thermal Engineering 2024, KFUPM) reported internal cell temperature >50 C at 2C and >94 C at 5C, at pack level with its own cooling arrangement. — [KFUPM 21700 pack study](https://pure.kfupm.edu.sa/en/publications/thermal-management-of-21700-li-ion-battery-packs-experimental-and/)
- A 2025 Batteries paper analyses the convective and radiative shares of passive heat loss from 21700 cells. I did not extract its numbers. — [MDPI Batteries 11/7/246](https://www.mdpi.com/2313-0105/11/7/246)

### Inferences
- Equations (calc framework):
  - Cell to wall through a layer of thickness t and conductivity k: R'' = t/k, equivalent h_eq = k/t. Still air across a 3 mm gap: 0.026/0.003 ≈ 9 W/m²K, about the same as weak natural convection. Unfilled silicone (k ≈ 0.2) across 3 mm: about 67 W/m²K. Filled potting (k ≈ 1) across 3 mm: about 330 W/m²K. Silicone foam (k ≈ 0.05) across 3 mm: about 17 W/m²K.
  - Shell wall: PLA/PETG k ≈ 0.15-0.2 W/mK, so a 2 mm wall gives h_eq ≈ 75-100 W/m²K. That is not the bottleneck.
  - Outside of the shell: natural convection plus radiation in room air gives about 8-12 W/m²K combined. For a shell of about 0.04 m² external area, that is roughly 0.3-0.5 W/K. At 8-10 W total (cells plus board), the steady shell-to-ambient rise is about 20-30 K. That is the floor no internal potting can beat, because only a bigger or metal shell, or airflow, lowers it.
  - So: with air inside, the cells sit 30-60 K above the internal air, which sits above the shell. With coupled potting, the cells sit only a few K above the shell. **Potting helps whenever it physically bridges cells to the shell walls and has k > ~0.1 W/mK.**
- Potting hurts when: (a) foam or aerated potting (k ≈ air) wraps the cells but the heat path to the shell is otherwise unchanged, which gives no gain and blocks any convection or radiation that existed; (b) potting couples the hot board to the cells, so its several watts flow into the cells. Keep a thermal break, or a low-k layer, between the board's hot parts and the cells, or give the board its own path to the shell; (c) it covers the positive-end vent (Q4); (d) it is high-k and rigid between cells, which raises propagation coupling unless the heat spreads to a sink (Q6).
- Thin conformal-gap potting (1-3 mm around each cell into the shell) gives most of the benefit at low mass. Volume-filling the whole cavity adds thermal mass (Q3) but also weight.

### Gaps
- No peer-reviewed study found that potted 21700 cells inside a *sealed plastic* enclosure and compared them with an air-filled one. The SAE study (32700, simulation) is the closest.
- Primary URLs for the J. Energy Storage CPCM study and the Zhang et al. 2020 JPS paraffin/EG 18650 study (reported 44.7% peak reduction vs air at 3C) were not confirmed.

## Q3. Thermal mass as a buffer during a 45-60 min 100 W discharge

### Takeaway
The cells are already about 280 J/K. Adding 100-200 g of silicone or PU potting adds about 50-100% more heat capacity, which cuts the adiabatic-limited rise by roughly a third to a half over a 50 min discharge. Phase-change material absorbs much more per gram near its melt point, which is why PCM studies show 30-40% peak reductions vs natural convection.

### Cited Findings
- PCM and PCM-graphite cut module peak temperature from 64.38 C to 40.4 C and 39 C under natural-convection conditions (cylindrical cells). — [Behi et al., Designs 2022](https://doaj.org/article/fc51d87754d749988f6f17755f4aa228)
- COMSOL application model: thermal management of a battery pack with phase-change material (method reference). — [COMSOL PCM battery model](https://comsol.com/model/thermal-management-of-a-battery-pack-using-a-phase-change-material-115571)

### Inferences
- calc: ΔT_adiabatic = Q·t / (m_cells·c_cells + m_pot·c_pot). With 5 W for 3000 s (15 kJ), cells only (≈280 J/K, assuming c ≈ 1 J/gK): 54 K. With 150 g silicone (c ≈ 1.3 J/gK assumed, +195 J/K): 32 K. With 150 g paraffin PCM (latent heat ≈ 150-200 J/g assumed, melting at about 40-45 C): 22-30 kJ of latent capacity, which would absorb the whole discharge near the melt point.
- With a conductive path to the shell (Q2), the potting mass mainly flattens the transient while the shell carries the steady load. Both effects stack.
- PCM caveats for a sealed product: paraffin is flammable (it is fuel in a runaway), leaks when molten unless shape-stabilised (EG matrix), and is saturated after one discharge with slow recovery in still air. For a consumer power bank, a filled silicone or PU (flame-retardant, UL94 V-0) is the safer mass buffer.

### Gaps
- No measured 21700 heat capacity for the 58E. About 1 J/gK is a common assumption for NMC/NCA cylindrical cells, not verified here (the Chalmers calorimeter thesis measures cp for 21700: [Chalmers](https://odr.chalmers.se/server/api/core/bitstreams/dc314830-f51f-471f-8c7d-2dc754ab142c/content)).
- Potting-compound cp and density figures above are typical assumed values. Use the chosen compound's TDS.

## Q4. Cell venting: vent/CID location, why it must not be blocked, cell-maker guidance on potting/adhesives/pressure

### Takeaway
The 21700 vent and CID sit in the positive-cap assembly. Scored vents rupture to relieve pressure in a controlled way, and some cans also have bottom vents. The only cell-maker-derived guidance I found (A123, second-hand) says cells must be mounted so they do not interfere with the vent function. Leave the positive end free of potting with an open gas path. I could not retrieve EVE, Samsung SDI, Murata or Molicel handling-manual text on potting.

### Cited Findings
- Cylindrical cell containers usually have two parts, a can and a positive terminal cap, with vents provided on both. The scored region ruptures to release excess pressure in a controlled manner. — [US20070122692A1 battery venting system](https://www.google.com.au/patents/US20070122692)
- A123 guidance, quoted second-hand in a forum: "Cells shall be mounted in the application, in a way that will not interfere with the vent function on the cell." A poorly designed pack can prevent vented gas from dispersing, or stop the cell from venting. — [All About Circuits forum](https://forum.allaboutcircuits.com/threads/considerations-for-lithium-battery-venting-in-product-design.193758/post-1821826)
- A European patent application on potted cylindrical modules describes potting covering cell tops, with some embodiments leaving middle cells uncovered. Industry potting does sometimes cover ends, by design. — [EP4583278](https://data.epo.org/publication-server/rest/v1.2/patents/EP4583278NWA1/document.html)
- Standard cell vents do not prevent fire spreading from cell to cell. Vent-directing designs steer heat away from adjacent surfaces. — [Purdue PRF safety vent design](https://licensing.prf.org/product/safety-vent-design-for-li-ion-batteries)
- Hobby pack practice: insulation rings on the positive end protect the negative shoulder around the positive cap. — [electric-skateboard.builders](https://electric-skateboard.builders/t/fishpaper-and-cell-level-fusing-use-it/35026)

### Inferences
- A potted-over positive cap can (a) raise the burst pressure, so the can fails at the sidewall instead (the most violent propagation mode, see Q6), and (b) block the CID's venting path. Keep the positive end free of potting with a dam, cap or foam plug, leaving an open plenum that leads to the enclosure's relief path.
- A single ePTFE membrane vent is sized for breathing and pressure equalisation, not for runaway gas. A 21700 in runaway releases litres of gas within seconds (magnitude not sourced here). A sealed printed shell needs a designed burst or weak point (thin wall section, pop-out panel) aimed away from the user, or it will rupture somewhere unplanned.
- Pressure on the can: radial potting stress is low (see Q5). Avoid hard potting or adhesive bridging the positive-cap crimp and gasket region, and do not compress the cap.

### Gaps
- Could not retrieve EVE, Samsung SDI, LG, Murata or Molicel application or handling manuals. No direct cell-maker quote on potting, adhesive or clearance above the vent was found. Request the EVE 58E product spec "precautions" section from the supplier.
- No Tesla source on leaving cell tops unpotted was found in this pass.

## Q5. Cell swelling and expansion over aging; is hard potting a problem?

### Takeaway
A steel-can 21700 barely changes diameter. A thick-walled-cylinder estimate gives sub-micron to a few-micron radial growth from internal pressure. Measured aging growth is small, but it rises with capacity loss. Hard potting will not crush a healthy cylindrical cell. The concerns are CTE mismatch and thermal-cycle stress at the cap and crimp, and locking cells in rigid contact, which aids propagation.

### Cited Findings
- IEST calculation (thick-walled cylinder, steel E = 210 GPa, 1.0-1.2 MPa assumed internal pressure): radial expansion Δr ≈ 0.43 µm for 21700 and 0.25 µm for 18650. These are calculated, not measured. Real deformation is likely smaller. Irreversible growth with cycling fixes a peak-valley shell pattern (qualitative). — [IEST cylindrical expansion force analysis](https://iestbattery.com/case/cylindrical-cells-expansion-force-analysis)
- The jelly roll sits in a small gap inside the can. The gap shrinks over the first cycles, and diameter growth tracks capacity loss and internal pressure in aging studies (18650-dominated). — [MDPI Batteries 9/1/6](https://www.mdpi.com/2313-0105/9/1/6); [TUM thesis](https://mediatum.ub.tum.de/doc/1774579/1774579.pdf)
- In-situ cylindrical swelling instruments resolve 0.1 µm, which shows how small the changes are. — [IEST CCS system](https://iestbattery.com/wp-content/uploads/2024/11/IEST-Cylindrical-Battery-In-Situ-Volume-Swelling-Testing-System-CCS.pdf)

### Inferences
- The rigidity concern for potted cylindrical cells is thermal expansion of the potting itself, not cell swelling. Epoxy CTE is about 50-80 ppm/K and silicone about 200-300 ppm/K, against roughly 12 ppm/K for steel (typical values, unsourced). A soft, low-modulus silicone or PU is preferred over hard epoxy because it tolerates thermal cycling and allows rework or inspection.
- Gas build-up in an aged cell shows up as pressure (CID trip) rather than diameter, so potting does not mask or worsen it, provided the cap stays free.

### Gaps
- No measured 21700 diameter-vs-cycle data with numbers retrieved. The MDPI paper returned 403.

## Q6. Thermal-runaway propagation: do potting, intumescent or ceramifying compounds, or air gaps reduce propagation?

### Takeaway
NASA's rule is that cells in direct contact with no alternate heat path will almost always propagate, and the spacing needed is inversely proportional to how well heat is spread away. Air gaps alone are weak: 4 mm air spacing still let neighbours get damaged. Aluminium interstitial heat sinks, or the right insulating foams that also contain sidewall rupture, stop propagation in 18650/21700 tests. Low-temperature silicone or PU foams are contested: Aspen claims they fail, while Warwick found some foams successful.

### Cited Findings
- NASA (Darcy et al.): "direct contact between cells without alternate heat dissipation paths nearly assures propagation"; "spacing required is inversely proportional to effectiveness of heat dissipation path." — [NASA NTRS 20160010200](https://ntrs.nasa.gov/api/citations/20160010200/downloads/20160010200.pdf); [NASA NTRS 20170001655](https://ntrs.nasa.gov/api/citations/20170001655/downloads/20170001655.pdf)
- NASA: adjacent cells were damaged (shorted) even at 4 mm spacing when the only other heat path was the parallel electrical connections (2014 result cited in a 2017 talk). — [NASA NTRS 20170001655](https://ntrs.nasa.gov/api/citations/20170001655/downloads/20170001655.pdf)
- A NASA propagation-resistant brick of 65 LG MJ1 18650s (13P5S) used 0.5 mm cell spacing in Al 6061-T6 interstitial heat sinks with no cell-to-cell contact, at about 191 Wh/kg brick level. The baseline 80-cell pack with no heat path propagated, with external surfaces reaching 350 C. — [NASA NTRS 20150020936](https://ntrs.nasa.gov/api/citations/20150020936/downloads/20150020936.pdf); [NASA NTRS 20160013684](https://ntrs.nasa.gov/api/citations/20160013684/downloads/20160013684.pdf)
- NASA: modern 18650s at >275 Wh/kg present high risk of sidewall breach during runaway. Interstitial support materials are used to prevent side-can failures. — [NASA NTRS 20180004170](https://ntrs.nasa.gov/api/citations/20180004170/downloads/20180004170.pdf)
- Warwick (J. Power Sources 2025): interstitial foams tested under sidewall rupture, described as the most violent mode. Some materials contained sidewall rupture and prevented propagation, and neighbours kept their open-circuit voltage. Lower-density foams outperformed higher-density ones when lid-plates were removed. Full numbers are in the open-access PDF, which I did not parse. — [Warwick WRAP 190638](https://wrap.warwick.ac.uk/id/eprint/190638)
- Warwick (2024): six propagation tests on seven-cell hexagonal 21700 modules at 3 mm spacing, with sidewall rupture in about half the runs. — [Warwick WRAP 188615](https://wrap.warwick.ac.uk/id/eprint/188615)
- Fraunhofer FEM of a seven-cell 21700 module with one cell in runaway studied insulation and heat buffering (gases not modelled). — [Fraunhofer publica 445200](https://publica.fraunhofer.de/handle/publica/445200)
- Ceramifiable silicone foam composite: the authors report it intercepted gas jets and confined runaway to a single cell in module tests (authors' own claim). — [NML ceramifiable foam paper](https://nmlett.org/index.php/nml/article/download/2529/4797/9291)
- Aspen Aerogels (vendor view): PU and silicone foams make good compression pads but, being low-temperature materials, "cannot withstand thermal runaway situations." — [Charged EVs / Aspen](https://chargedevs.com/features/thermal-runaway-in-ev-battery-packs-designing-a-mitigation-strategy/)
- SAE 2024-01-2901 compared propagation across module configurations, varying spacing and applying PCM and silica aerogel (results not extracted). — [SAE 2024-01-2901](https://saemobilus.sae.org/papers/a-comparative-analysis-thermal-runaway-propagation-different-modular-lithium-ion-battery-configuration-2024-01-2901)

### Inferences
- For a 4S1P pack, propagation would turn one cell's event into four. It is the dominant hazard beyond simple overheating. The NASA principle suggests two ways out: (a) separate the cells by a few mm of an insulating, intumescent or ceramifying layer (low k at runaway temperatures) that also stiffens the sidewall, or (b) put them in a conductive spreader to a large sink. In a small plastic power bank the sink is too small, so (a) is the realistic route.
- This creates a design tension with Q2, because normal-operation cooling wants high-k coupling to the shell. A reconciling layout: each cell sits in its own pocket. A thin, filled, flame-retardant silicone or PU (k ≈ 0.5-1) couples the outer face of each cell to the shell. Between cells sits a ceramifying or intumescent silicone or mica/aerogel sheet (k ≈ 0.02-0.2), which stays insulating and structural during runaway. Positive caps face a common open vent channel.
- Paraffin PCM is a poor choice here because it adds fuel. Unfilled, non-flame-retardant PU foam can burn.

### Gaps
- No UL 9540A-style or e-bike pack result was retrieved giving the propagation outcome of fully potted (solid silicone) 21700 packs vs air gaps.
- The numerical details of the Warwick 2025 foam paper and NASA spacing tables were not extracted (PDF not parsed).

## Q7. Effect on the gauge: BQ40Z50 NTC coupling and lag

### Takeaway
Potting the NTC against the can improves cell-to-sensor coupling and cuts lag. In still air, an NTC that is not bonded reads closer to air or board temperature than to the cell. The main risk is the board's own heat reaching the NTC through the potting, which biases the reading upward.

### Cited Findings
- No source retrieved on NTC placement or lag in potted cylindrical packs or BQ40Z50 thermistor coupling.

### Inferences
- Bond each cell NTC (or the TMP1075 I2C sensors planned for the CC2340 variant) directly to the can wall with thermal epoxy at mid-height before potting. Keep it at least a few mm from the board's hot parts, with low-k material between.
- The cell's own core-to-surface gradient at about 1.4C is likely a few K. The gauge sees the surface, so set the charge-inhibit and overtemperature thresholds with margin, for example 5 K under the 60 C discharge and 45 C charge limits.
- The cell's thermal time constant (calc, about 30 min in air, shorter when potted to the shell) is much longer than the NTC's, so lag is dominated by the cell. Sensor lag matters little once the sensor is bonded.

### Gaps
- No measured data on surface-vs-core offset for the 58E at 7 A. No TI application note on potted-thermistor placement was retrieved (TI SLUA-series gauge app notes would be the next source).
