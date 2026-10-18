# Drop and shock protection for a small hand-held Li-ion power bank (4S1P 21700, ~333 g)

Research scope: drop and shock requirements, how cylindrical cells and electronics fail in drops, and which measures give the most drop resistance per gram. Research done 2026-10-18. Several key primary sources (ScienceDirect, TUM repository, Nature) blocked automated fetching, so some findings rely on search-result abstracts and snippets. These are flagged where it matters.

---

## 1. Applicable drop and shock tests and pass criteria

### Takeaway
The regulatory bar is low. IEC 62133-2 needs three 1.0 m drops onto concrete with no fire or explosion, and UN 38.3 T4 needs a 150 g / 6 ms half-sine (cells and small batteries) with no leak, vent, rupture or fire and OCV at least 90 %. Neither requires the product to keep working. Consumer expectations (1.5–2.4 m, "MIL-STD-810") are higher than the regulations and are a design choice, not a compliance requirement.

### Cited Findings
- IEC 62133-2 free fall: each fully charged cell or battery is dropped three times from 1.0 m onto a concrete floor in varied orientations, then inspected after about 1 hour. Pass criterion: no fire, no explosion. — [EverExceed overview](https://www.everexceed.com/overview-of-lithium-battery-safety-testing-iec-62133_n426); [Tritek IEC 62133-2 report template](https://tritekbattery.com/iec-62133-2-test-report/)
- For battery packs, the IEC 62133 drop has no cold-temperature preconditioning, whatever the battery's specified lower operating temperature. — [In Compliance Magazine, "Achieving Compliance to Small Format Battery Pack Standards"](https://incompliancemag.com/achieving-compliance-to-small-format-battery-pack-standards/)
- Cell makers specify the same test at cell level. The Samsung INR21700-40T datasheet requires fully charged cells dropped onto concrete from 1.0 m, random orientation, three times, with no fire and no explosion. — [Samsung INR21700-40T datasheet (DNK Power)](https://www.dnkpower.com/wp-content/uploads/2019/02/SAMSUNG-INR21700-40T-Datasheet.pdf)
- A battery-vendor opinion says the IEC 62133 drop is relatively easy to pass compared with UN 38.3. — [EverExceed](https://everexceed.com/blog/lithium-battery-safety-testing-standard-part-1_b297) (vendor opinion)
- UN 38.3 T.3 vibration: a logarithmic sinusoidal sweep from 7 Hz to 200 Hz and back in 15 min, repeated 12 times (3 h) on each of three perpendicular axes, one of them perpendicular to the terminal face. For cells and batteries of 12 kg or less: 1 g from 7 to 18 Hz, then 0.8 mm amplitude up to 8 g peak (about 50 Hz), then 8 g up to 200 Hz. Batteries over 12 kg use a 2 g plateau. — [Lenovo UN38.3 test summary](https://static.lenovo.com/ww/docs/regulatory/msds/SB10W51939_UN38.3.pdf); [RS Online UN38.3 report](https://docs.rs-online.com/aca2/A700000014241203.pdf)
- UN 38.3 T.4 shock: three shocks in each direction on three perpendicular axes (18 shocks). Small cells and batteries get a 150 g_n half-sine of 6 ms; large cells and batteries can use 50 g_n for 11 ms. Pass criteria: no leakage, venting, disassembly, rupture or fire, and OCV at least 90 % of the pre-test value. — [Lenovo UN38.3 summary](https://static.lenovo.com/ww/docs/regulatory/msds/SB10W51939_UN38.3.pdf); [Smoothroad UN38.3 report](https://www.smoothroad.com/wp-content/uploads/2022/03/W03153008921D_1-AA-UN.pdf)
- US power banks: Amazon and other channels accept either Option A (UL 2056 plus UN 38.3) or Option B (IEC/UL/CSA 62368-1 plus IEC/UL/CSA 62133-2 plus UN 38.3). — [ComplianceGate, US power bank regulations](https://www.compliancegate.com/power-banks-regulations-united-states)
- UL 2056 (first edition, power banks) was under CPSC comment in October 2023. The letter's excerpt did not show the drop-test parameters. — [CPSC letter on UL 2056 proposal](https://cpsc.gov/s3fs-public/UL-letter-UL-2056-proposal-October-2023-6b-final.pdf)
- MIL-STD-810 Method 516 Procedure IV (transit drop) uses real drops to represent accidental drops during loading, unloading, or carrying by people. — [DES Solutions](https://www.desolutions.com/resources/mil-std-810-method-516-shock-testing-procedure-iv-transit-drop)
- A MIL-STD-810E-based report lists a 122 cm drop height and 26 drops covering each face, edge and corner. — [TDK-Lambda Vega Mil-810E shock report](https://www.emea.lambda.tdk.com/ch/KB/Vega-Mil-810E-Shock-Summary-Report.pdf). Under 810H, the 26 drops can be split across up to five test units. — [Trenton Systems](https://www.trentonsystems.com/en-us/resource-hub/blog/mil-std-810-shock-testing-overview-method-516.8)
- Consumer reviews of ultralight power banks drop-test well above 1 m. CleverHiker says the Nitecore NB10000 Gen4 "handily passed our eight-foot drop test" (about 2.4 m) with full function. — [CleverHiker NB10000 Gen4 review](https://www.cleverhiker.com/backpacking/nitecore-nb-10000-gen4-power-bank-review/). Backpacking Light's editor's note cites unpublished drop research by Rex Sanders in which the NB10000 "performed poorly". — [Backpacking Light NB10000 review](https://backpackinglight.com/nitecore-nb10000-portable-battery-charger-review). These two sources conflict, and the Sanders method and model generation are unknown.

### Inferences
- UN 38.3 T4 converted to drop terms: a 150 g, 6 ms half-sine has a velocity change of Δv = (2/π)·150·9.81·0.006 ≈ 5.6 m/s. A free fall gives that impact speed from about 1.6 m. The stopping distance over the pulse is v₀·T/2 ≈ 17 mm. So every cell that passed T4 has already survived a velocity change like a 1.6 m drop, but spread over about 17 mm of travel. On bare concrete the stopping distance is much shorter and the peak g much higher. The 50 g / 11 ms option gives Δv ≈ 3.4 m/s, equivalent to about 0.6 m.
- IEC 62133-2's 1.0 m drop gives 4.43 m/s and, for this 333 g pack, 3.3 J. The user's 1.5 m target gives 5.42 m/s and 4.9 J.
- Passing IEC 62133-2 or UN 38.3 does not mean the product still works afterwards. Only safety matters (no fire, vent or leak, OCV at least 90 %). A pack can "pass" with a dead BMS or an open CID. A functional-survival target (for example 26 drops from 1.22–1.5 m) is a separate product requirement.

### Gaps
- UL 2056 drop height, number of drops and pass criteria were not found in an open source. Check the published UL 2056 text.
- IEC 62368-1 drop test (Annex T, hand-held equipment): no open source found. From general knowledge, the hand-held drop is 1 m onto a hardwood surface, three times. This is unverified and must be checked against the standard.
- I could not confirm the exact MIL-STD-810H 516.8 Procedure IV table (weight thresholds and default 122 cm height). The 26-drop / 122 cm figures come from an 810E-era report.

---

## 2. How 18650/21700 cells fail in drops and shocks

### Takeaway
Modern cylindrical cells tolerate shocks beyond automotive standards. The documented drop failure is an axial (end-on) impact that breaks electrical contact in the CID / top-cap region. That gives a high-resistance, open-circuit cell, usually without a thermal event. Internal shorts come from radial crush or deformation of the jelly roll. Aged and dynamically loaded cells short at smaller deformations. Protecting the cell ends against axial impact matters most.

### Cited Findings
- A 2021 Journal of Energy Storage study on 18650 cells under shock and drop (vol. 43, 103213) found that shock tests beyond automotive standards had little effect on modern cells, while older cell types showed damage and higher ohmic resistance. In axial drop tests, several cell types failed ohmically without a thermal event. CT and post-mortem analysis showed that the main failure mechanism was contact loss in the CID region. — [ScienceDirect S2352152X21009105](https://www.sciencedirect.com/science/article/pii/S2352152X21009105); [TUM mediaTUM full text](https://mediatum.ub.tum.de/doc/1639525/1639525.pdf); [ResearchGate](https://www.researchgate.net/publication/354845348_Experimental_investigation_of_the_failure_mechanism_of_18650_lithium-ion_batteries_due_to_shock_and_drop). Note: findings come from the abstract and snippets. Full text was blocked (403 or bot wall), so drop heights and g-levels were not extracted. The authors noted that further work on SOC effects and other formats such as 21700 was needed.
- Under dynamic (impact-rate) loading, 18650 cells short at a smaller displacement than under quasi-static loading, because of a loading-rate effect. — [Engineering Failure Analysis, "Mechanism of failure behaviour and analysis of 18650 lithium-ion battery under dynamic loadings"](https://www.sciencedirect.com/science/article/abs/pii/S1350630723005423)
- Mechanical behaviour depends on SOC. Higher SOC makes cells stiffer, and failure strain at short-circuit onset falls roughly linearly as SOC rises. So a fully charged cell is the stiffest and the most brittle against shorting. — [Scientific Reports 2016, "State of Charge Dependent Mechanical Integrity Behavior of 18650 Lithium-ion Batteries"](https://www.nature.com/articles/srep21829)
- Charged 21700 cells under dynamic out-of-plane loads: aging to 80 % capacity reduced the displacement, force and absorbed work needed to reach a major internal short. Cell orientation reduced internal-short risk by up to 51 % on average in the crash scenario studied. — [ResearchGate figure/paper on 21700 dynamic loading](https://www.researchgate.net/figure/Disassembled-cylindrical-21700-cell-Inner-parts-consist-of-anode-cathode-and_fig3_366607930) (snippet-level only)
- Models of jelly-roll deformation link separator failure to internal short. — [ResearchGate, "Failure of Li-Ion 18650 Cylindrical Cells Subjected to Mechanical Loading and Computational Model Development"](https://www.researchgate.net/publication/353598011_Failure_of_Li-Ion_18650_Cylindrical_Cells_Subjected_to_Mechanical_Loading_and_Computational_Model_Development)
- For a 4800 mAh 21700, nail-penetration work puts the internal-short resistance threshold for thermal runaway between 0.005 and 0.006 Ω. Only harder shorts than that triggered runaway. — [Applied Thermal Engineering 2022 (Warwick open copy)](https://wrap.warwick.ac.uk/id/eprint/163401/7/WRAP-characterizing-predicting-21700-NMC-lithium-ion-battery-thermal-runaway-induced-nail-penetration-Wen-2022.pdf)

### Inferences
- In this pack the cells lie with their axes along the 83 mm length (21700 = 70 mm long). An end-on drop onto either end bumper therefore loads all four cells axially, which is the mode that caused CID contact loss in the 2021 study. The end bumpers and any foam on the cell ends (positive cap and negative can bottom) are the most important protection.
- The weld between the nickel strip and the cap acts as a mass-on-a-spring load path. Each cell (about 70 g, an unsourced typical figure for 21700) pulls on its strip during a shock. Strip slack or a strain-relief loop, and not using the strip to restrain the cell, prevents peeled welds. This is an engineering inference. No drop study on strip/weld failure was found.
- Ageing and full SOC both lower the deformation needed to short. Design for an end-of-life cell at 100 % SOC.
- A likely field failure in a drop is "the pack goes dead" (CID open, cracked weld, or a cracked MLCC on the BMS), not fire. That passes IEC 62133-2 but is a product failure.

### Gaps
- I found no Sandia or NREL drop-specific cell data in this search budget. Sandia's mechanical-abuse work is mostly crush and penetration.
- No published g-level damage threshold for 21700 cells in free-fall drops was found. The only quantitative anchor is that cells survive UN 38.3's 150 g / 6 ms.
- No EVE INR21700-58E-specific drop or shock data was found. Check its datasheet for the cell-level drop and shock clause.
- No data on nickel-strip or spot-weld failure in drops.

---

## 3. Electronics failure in drops, and whether potting helps

### Takeaway
In drops, MLCCs crack mainly from board flex: stress passes through the solder fillets and is highest at the bottom of the termination. Potting the board stops flex and supports heavy parts, so it should help against drop and shock. The risk is thermal: rigid, high-Tg, unfilled epoxy builds CTE stress on solder joints and MLCCs. A low-modulus silicone or polyurethane avoids most of that. Most sources here are vendor blogs.

### Cited Findings
- Board bending passes stress through the solder fillets into the MLCC body, and the stress is highest at the bottom of the capacitor where the termination bands end. — [DigiKey TechForum, MLCC flex cracking](https://forum.digikey.com/t/ceramic-capacitor-failure-design-solutions-mitigating-board-flex-cracking/26195); [DigiKey, MLCC common failure (flex cracking)](https://forum.digikey.com/t/mlcc-common-failure-issue-flex-cracking/572)
- Countermeasures include soft or flexible terminations (silver-epoxy layer) and metal-frame parts such as TDK MEGACAP. TDK data show fewer solder cracks under flexure and thermal shock. — [TDK solder-crack countermeasures](https://www.mouser.com/pdfdocs/TDK-SolderCrack-Countermeasures.pdf); [TDK solution guide](https://product.tdk.com/en/products/solutionguide/mlcc_solder-crack.html); [WTS FlexCap article](https://www.wts-electronic.de/download/wts%20Automotive%20grade%20Technical-Article%20FlexCap.pdf?id=2069)
- Smaller pads and thinner solder reduce joint stiffness, which helps in flex applications. — [DigiKey TechForum](https://forum.digikey.com/t/ceramic-capacitor-failure-design-solutions-mitigating-board-flex-cracking/26195)
- Stress from potting depends on both CTE mismatch and modulus. Silicone has a higher CTE than filled epoxy, but its very low modulus makes it put less stress on joints. Unfilled epoxy is about 50–70 ppm/°C, FR4 about 15–25 ppm/°C and solder about 30 ppm/°C. Silica-filled epoxy can reach about 20–30 ppm/°C. — [Venture Mfg, epoxy vs silicone potting](https://www.venture-mfg.com/epoxy-vs-silicone-potting-for-power-electronics) (vendor); [patent US5708056, hot-melt epoxy encapsulation](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/5708056)
- Low-Tg compounds (polyurethane, silicone) are usually used on SMT boards, because high-Tg compounds can break solder bonds as they shrink. — [Wikipedia, Potting (electronics)](https://en.wikipedia.org/wiki/Potting_(electronics))
- Rigid epoxy gives structural retention and impact strength. Silicone gives a wider temperature range, absorbs vibration and can be reworked. PU sits between them. — [ITW Performance Polymers](https://itwperformancepolymers.com/blog/choosing-the-right-potting-material-for-electronics-epoxy-vs-silicone-in-modern-applications); [ALLPCB](https://www.allpcb.com/allelectrohub/epoxy-vs-silicone-selecting-the-optimal-potting-material-for-harsh-environment-electronics) (vendor content)

### Inferences
- For a small BMS/charger board, potting turns the board and its parts into one stiff block. That stops flex, which is the main MLCC drop-failure driver, and keeps the inductors and USB-C receptacle from loading their pads in shear. In a drop, potting is very likely a net positive.
- Potting adds mass, which has its own cost. The potted block hits the shell harder and its mounts must carry it. It should float on, or be held by, a compliant mount and not be bonded rigidly to the shell wall that takes the impact.
- The USB-C receptacle is the part of the potted block exposed to impact through the port opening, from cable levering and port-first drops. Through-hole shell tabs, plus a printed shell boss that takes the plug and receptacle loads, matter more than the potting.
- Choose a low-modulus PU or silicone potting, Shore A below about 60, with low Tg. Avoid unfilled rigid epoxy. Put flex-termination MLCCs on the largest case sizes (1206 and above) and orient MLCCs parallel to the likely bending axis. The orientation rule is standard industry guidance and was not separately sourced here.

### Gaps
- No peer-reviewed study was found that drop-tests potted vs unpotted boards and measures MLCC or solder-joint survival.
- No density data was gathered for candidate potting compounds. Typical silicones and PUs are about 1.0–1.5 g/cm³ (unsourced), so each cm³ of potting costs about 1–1.5 g.

---

## 4. Energy-absorbing materials and performance per gram

### Takeaway
Candidate pad materials are all light. PORON XRD has a specific gravity of 0.14–0.24, so a 30 cm³ pad weighs about 4–7 g. Sorbothane is dense (SG 1.27–1.32) and heavy per unit of energy absorbed. Printed TPU gyroid at 20–30 % density sits in between. The binding limit for this pack is internal volume (crush stroke), not mass. Vendor "absorbs 90 %" claims give no test conditions and are not comparable.

### Cited Findings
- PORON XRD comes in 9, 12 and 15 lb/ft³ grades (SG 0.14, 0.19, 0.24) and 4.0, 6.0, 9.5 and 12.7 mm thicknesses. The datasheet gives compression force at 25 % deflection at several strain rates (rate-stiffening), and says the impact claims are not a guarantee. — [PORON XRD datasheet (Algeos)](https://www.algeos.com.au/pdfs/PORONXRDDataSheet.pdf)
- Rogers claims PORON XRD absorbs over 90 % of impact energy and "up to 90 %" of peak force, against about 60 % for competing EVA blends. Ejendals claims it keeps 98 % of its performance after repeated hits. Neither gives a test method, impact energy or peak force. — [Rogers impact absorption](https://www.rogerscorp.com/applications/impact-absorption); [Design World](https://www.designworldonline.com/rogers-introduces-poron-xrd-extreme-impact-protection-material/); [Ejendals PORON XRD](https://www.ejendals.com/pl/jalas/materials/poron-xrd/) (all vendor marketing)
- Sorbothane is a polyether polyurethane viscoelastic solid. Specific gravity is 1.270–1.320, it is cast at 30–70 Shore 00, and its operating range is −29 to +72 °C. The vendor claims it absorbs up to 94.7 % of impact shock (vendor claim). — [Sorbothane SDS](https://www.sorbothane.com/wp-content/uploads/110-sorbothane-safety-data-sheet.pdf); [Sorbothane overview](https://www.sorbothane.com/technical-data/material-properties/); [Sorbothane article](https://www.sorbothane.com/technical-data/articles/why-sorbothane-outperforms-traditional-shock-absorbing-materials/)
- Sorbothane 30 Shore 00: tensile strength at break 26 psi, elongation 334 % (ASTM D412). — [Knowde listing](https://www.knowde.com/stores/elastomer-engineering/products/dlr-elastomer-engineering-ltd-sorbothane-durometer-30-shore-00)
- In 3D-printed TPU gyroid at 30 % relative density, all samples show a plateau between 10 and 30 % strain (early energy absorption). Stress and stiffness rise with density. — [PMC, gyroid relative density TPU and flexible nylon for footwear](https://pmc.ncbi.nlm.nih.gov/articles/PMC13186003/)
- FDM TPU honeycomb and gyroid lattices absorb a lot of energy and recover well (rebound). The tests were quasi-static. — [Scientific Reports 2026, "Energy absorption and rebound behavior of 3D-printed TPU lattice structures"](https://www.nature.com/articles/s41598-026-36271-1) (abstract only, full text blocked)
- Drop-weight simulation and testing of TPU 95A lattice cores: unit-cell design, strut diameter and the material's apparent stiffness govern energy absorption and collapse. — [PMC8622326](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8622326/)
- In gyroid lattices generally, higher relative density raises peak and mean crushing force. A reinforced gyroid gives a higher initial stress peak, which means higher deceleration and is undesirable for occupant protection. — [Springer, 3D printed metamaterials for motorsport](https://link.springer.com/article/10.1007/s12239-024-00136-1); [Springer Professional, graded gyroid impact](https://www.springerprofessional.de/en/impact-responses-of-heat-treated-functional-graded-3d-printed-gy/52388078)

### Inferences
- Mass per absorber, using a 30 cm³ pad as an example: PORON XRD at SG 0.19 is about 6 g. Printed TPU (solid about 1.2 g/cm³, an unsourced typical value) at 25 % relative density is about 9 g. Sorbothane at SG 1.29 is about 39 g. Sorbothane makes little sense for this pack. PORON or other microcellular PU, or graded TPU lattice, are the efficient choices.
- A graded TPU lattice (soft at the face, denser behind) can be printed into the end bumpers at no extra part count. It avoids the initial stress spike of a uniform dense lattice.
- Foams lose about 30–40 % of their thickness to densification, so usable stroke is about 60–70 % of pad thickness (general cushioning practice, unsourced).

### Gaps
- No independent drop-test data (peak g vs thickness and drop height, i.e. cushioning curves) was found for PORON, D3O, EVA, silicone foam or printed TPU at this energy scale (about 5 J, about 0.3 kg).
- No D3O density or impact data was retrieved.
- No EVA foam density or cushioning-curve data was retrieved. Typical EVA is about 0.03–0.2 g/cm³ (unsourced).

---

## 5. Design patterns from commercial rugged power banks and flashlights

### Takeaway
Little hard data. The best-known ultralight bank (Nitecore NB10000) uses a carbon-fibre-reinforced polymer frame with IPX5 (later IPX7) sealing and has conflicting drop reviews. I found no teardown or engineering source documenting floating cell carriers or over-moulded corners in power banks within this research budget.

### Cited Findings
- Nitecore NB10000: carbon-fibre-reinforced polymer frame, IPX5 on early versions. — [Backpacking Light](https://backpackinglight.com/nitecore-nb10000-portable-battery-charger-review); [The Gadgeteer review](https://the-gadgeteer.com/2020/10/29/nitecore-nb10000-ultralight-power-bank-review). The Gen4 is rated IPX7 and passed an 8 ft drop in CleverHiker's test. — [CleverHiker](https://www.cleverhiker.com/backpacking/nitecore-nb-10000-gen4-power-bank-review/). Backpacking Light reports a poor result in Rex Sanders's unpublished drop research. — [Backpacking Light](https://backpackinglight.com/nitecore-nb10000-portable-battery-charger-review) (conflicting)

### Inferences
- The NB10000 uses pouch/prismatic-style cells in a rigid shell. A 4×21700 pack carries more concentrated mass (about 280 g of cells, unsourced estimate) and has steel cans that resist crush well, but the CID is weak to axial impact. So the generic patterns apply: keep a gap between cells and the impacted wall, use compliant end stops, and make the corners crush first. A rigid can/shell alone does not.
- The user's existing architecture (end bumpers, foam on cells, aluminium cover) already follows the recommended pattern. The open question is stroke: how many mm of compliant material sit between the cell ends and the outer bumper face.

### Gaps
- No teardown data was found (iFixit or other) for Anker, Goal Zero, BioLite or rugged e-bike packs showing cell-carrier compliance.
- No manufacturer drop ratings were found for those brands.

---

## 6. 3D-printed shell impact behaviour (PETG / ASA / PA / PC)

### Takeaway
FDM impact strength depends heavily on orientation. Upright-printed parts, where impact loads the layer interfaces, give the lowest impact strength, and PC and PETG are the most sensitive to layer thickness. Quantitative cross-material XY-vs-Z data was not found.

### Cited Findings
- A study of PC, PETG, ABS and PLA FDM impact specimens found PC most affected by layer thickness, then PETG, ABS and PLA. The upright print orientation gave the lowest impact strength. — [Pamukkale Univ. record (Materials Today Communications 2021)](https://gcris.pau.edu.tr/handle/11499/46272)
- Stratasys FDM ASA: notched Izod 64 J/m and unnotched 321 J/m in XZ orientation (ASTM D256, 23 °C). — [Stratasys ASA spec](https://uploads-ssl.webflow.com/61adb9ea839c73aa18037eae/61b12089ca2938b62510d160_FDM_ASA_Material_Specifications.pdf)
- Fibre-filled nylon FDM parts are especially weak against forces parallel to the layers and in impact (preprint, not peer-reviewed). — [Preprints.org 202409.2382](https://www.preprints.org/manuscript/202409.2382)
- One FDM study reports that XZ orientation gives good impact and compressive strength. This may conflict with the usual expectation, possibly because of how the axes were defined. — [Springer, Iranian J. Sci. Tech. (s40997-022-00514-z)](https://link.springer.com/10.1007/s40997-022-00514-z)
- Izod impact strength of FDM PLA and PETG depends on specimen thickness. Only citation metadata was retrieved. — [OUCI record](https://ouci.dntb.gov.ua/works/7W5J5mLl)

### Inferences
- Print the shell so that drop loads on the corners and ends run along the extrusion paths, not across layer interfaces. For a tall 83 mm tray printed upright, end impacts land on the layer planes and are worst for delamination. Printing the tray on its long side, or adding perimeters, helps.
- Short-carbon-fibre PA is stiff but brittle in impact across layers. Unfilled PA (PA12 or PA6/66) or PC is tougher. The shell's job is to spread load and survive, while the bumpers and foam do the energy absorption. A tougher, slightly compliant shell (PETG, PA12) beats a stiff brittle one (PA-CF) for drops. This is inferred from general material behaviour and was not verified with direct comparative data here.

### Gaps
- No single source compared notched Izod or Charpy in XY and Z for PETG, ASA, PA12, PA-CF and PC.
- No data on wall thickness vs drop survival for printed enclosures.

---

## 7. Engineering estimate: stroke needed for a 333 g pack dropped 1.5 m

### Takeaway
Holding a 1.5 m drop to 100 g takes about 15 mm of stroke with a perfect constant-force absorber and about 30 mm with a linear spring. Holding it to 200 g takes about 7.5 to 15 mm. Allowing for foam densification (about 65 % usable strain), an ideal foam needs about 11.5 mm of thickness for 200 g and 23 mm for 100 g. That much stroke is unrealistic on every face of a 54 × 49 × 83 mm pack. Realistic targets are about 5–8 mm of compliant material at the ends, giving roughly 300–500 g ideal, more in practice. Rely on the cells' demonstrated tolerance (UN 38.3: 150 g / 6 ms) and protect the axial ends hardest.

### Cited Findings
- Cells qualified to UN 38.3 survive 150 g, 6 ms half-sine shocks (18 times) without leakage, venting, rupture, fire or more than a 10 % OCV drop. — [Lenovo UN38.3 summary](https://static.lenovo.com/ww/docs/regulatory/msds/SB10W51939_UN38.3.pdf)

### Inferences (first-principles calculations)
- Impact energy E = m·g·h = 0.333 × 9.81 × 1.5 = **4.90 J**. Impact speed v = √(2gh) = **5.42 m/s**. For 1.0 m: 3.27 J and 4.43 m/s. For 2.4 m (the 8 ft review test): 7.8 J and 6.9 m/s.
- Ideal constant-force (square-wave) absorber: stroke s = h / G.
  - 100 g → 15 mm; 150 g → 10 mm; 200 g → 7.5 mm; 500 g → 3 mm.
- Linear spring (elastomer bumper, no plateau): s = v² / (G·g), twice the ideal.
  - 100 g → 30 mm; 200 g → 15 mm; 500 g → 6 mm.
- Real foam, with about 65 % usable strain and a non-ideal plateau: about 1.5 × the ideal stroke divided by 0.65, so 200 g needs about 11.5–17 mm of pad thickness.
- Required plateau stress, the face-stress check: the peak force at 200 g is 0.333 × 9.81 × 200 = 653 N. Across the full end face (54 × 49 = 2646 mm²) that is 0.25 MPa. In a corner drop with about 300 mm² of contact it is about 2.2 MPa, which crushes a soft foam to densification at once. So corner and edge drops need a stiffer crushable corner element (dense TPU lattice or solid TPU nose) that grows its contact area as it crushes. Face-only foam does not cover them.
- Absorber volume at 200 g on the end face: V = E / (σ·ε) = 4.9 J / (0.25 MPa × 0.6) ≈ 33 cm³. That is about 6 g of PORON XRD at SG 0.19, or about 10 g of 25 %-density TPU. **Mass is not the constraint. Volume and envelope are.**
- Comparison with UN 38.3: a 150 g / 6 ms half-sine already gives Δv ≈ 5.6 m/s with about 17 mm of stopping distance. So a cell protected to UN 38.3-like severity in a 1.5 m drop would need 10–17 mm of stroke. With less stroke the peak g on the cells will exceed 150 g, and survival then depends on margin that is not documented.
- Practical split for this pack, the main design inference:
  1. **End bumpers (axial, the worst cell load case):** give the largest stroke the envelope allows, ideally 6–10 mm of graded TPU lattice or PORON between the cell ends and the outer face. Put a separate thin compliant layer of 1–2 mm PORON directly on each cell end so the CID cap never contacts a rigid shell boss.
  2. **Sides:** 1–3 mm of foam around the cells mainly keeps the cells off the shell walls. The aluminium cover and shell spread the load.
  3. **Corners:** dense TPU noses that crush progressively.
  4. **Electronics:** keep the soft-potted board block compliantly mounted, not hard-bonded to the impact face.
- Rebound: an elastic bumper (Sorbothane aside) returns much of the energy and the pack may bounce and hit again on a corner. Viscoelastic or microcellular PU absorbs more per hit than solid TPU. This is inferred from the vendor energy-absorption claims and is unquantified.

### Gaps
- No measured peak-g data for hand-held plastic electronics dropped bare onto concrete was found. Thousands of g at sub-millisecond pulses is commonly quoted but was not sourced here. An accelerometer drop test of a printed prototype with a dummy cell mass is the practical way to close this.
- Without cushioning curves (peak g vs static stress at a given thickness and drop height) for PORON or printed TPU, the stroke estimates above are idealised bounds, not predictions.
