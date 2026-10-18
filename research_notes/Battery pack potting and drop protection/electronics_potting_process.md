# Potting (or Coating) the Power-Bank Electronics Board: Stress, Heat, RF, Process, Repair

Scope: potting or coating a 0.8 mm six-layer FR4 board (0201–1210 MLCCs, QFN/WSON ICs, 7×7 mm inductors at about 1.6 W each, MOSFETs, two IP68 USB-C receptacles, CC2340R5 BLE module) that sits against an aluminium cover through a gap pad in a 3D-printed shell. Built in batches of tens to low hundreds.

Research limits: I made 18 tool calls. Several primary documents could not be read in full. The DfR/SMTA potting-stress PDF came back as binary, the TI CC2340R5MODA integration guide was not reached, and Electrolube's potting guide was not found. Where a claim comes from a single vendor blog, it is flagged. Statements in **Inferences** are my own engineering reasoning, not sourced facts.

## 1. Thermomechanical stress: modulus, CTE, Tg and cure shrinkage vs MLCCs, QFN/WSON joints and 0201s

### Takeaway
Stress on parts scales roughly with modulus × CTE mismatch × ΔT, and modulus dominates. A soft silicone or gel with a high CTE stresses parts less than a stiff epoxy with a lower CTE. The main risks to MLCCs are cure shrinkage and CTE mismatch: Murata recommends low-shrinkage resin and a silicone under-coat as a stress buffer. For QFN/WSON, the danger is tensile (lifting) stress when encapsulant under or around the package expands. A hard epoxy whose Tg falls inside the use or cycling range is the worst case.

### Cited Findings
- **Murata, coating or molding MLCCs:**
  - Cure contraction of resin can crack the capacitor, so "select a resin with low curing contraction."
  - A CTE mismatch between resin and capacitor can cause cracks or peeling, then lower insulation resistance or dielectric breakdown. A silicone resin under-coat can buffer the stress.
  - Hygroscopic resins degrade insulation resistance under high humidity.
  - Coatings containing halogen compounds or organic acids can corrode the chip; avoid strong-acid types.
  - Electrical characteristics can change once the part is coated, so verify reliability on the actual board.
  - [Murata FAQ: coating/molding precautions](https://www.murata.com/en-global/support/faqs/capacitor/ceramiccapacitor/mnt/0024); also in [Murata datasheet ENFA0005](https://www.murata.com/products/productdata/8796738977822/ENFA0005.pdf).
- **DfR Solutions paper (Serebreni, Blattau, Sharon, Hillman), "Effect of Encapsulation Materials on Tensile Stress during Thermo-Mechanical Cycling of Pb-Free Solder Joints":** Encapsulant expansion puts solder joints, at geometries relevant to QFN/BGA, into tension, which sharply shortens fatigue life. Joint stress depends on both the encapsulant's CTE and its modulus — [SMTnet PDF](https://smtnet.com/library/files/upload/tensile-stress.pdf). I saw only the search-result summary because the full text was unreadable, so specific numbers are not reproduced here.
- **DfR "Reliability of QFN Devices":** Discusses QFN joint sensitivity to tensile stress and how the Tg, modulus and CTE of conformal coatings matter in thermal cycling. It cites an acrylic coating with Tg of about 15 °C, which falls inside typical cycling ranges — [SMTnet PDF](https://dev.smtnet.com/library/files/upload/Reliability-of-QFN-Devices.pdf).
- **Incure (vendor blog; illustrative, not measured):**
  - Stress grows with modulus, CTE mismatch and ΔT, and a soft silicone with higher CTE produces less stress than a stiff epoxy.
  - Near or above Tg the material becomes viscoelastic and builds up residual strain over cycles.
  - Tg depends on the cure schedule, and DSC and TMA readings can differ by 10–20 °C.
  - It claims low-modulus encapsulants extend solder fatigue life 2–5×, and that 60 ppm/°C potting on copper delaminated within 200–400 cycles, with 35–45 ppm/°C recommended.
  - [Incure: potting reliability in heat](https://incurelab.com/wp/how-potting-compounds-extend-electronic-reliability-in-high-heat-environments); [Incure: 150 °C+ compounds](https://incurelab.com/wp/what-to-look-for-in-potting-compounds-for-150c-applications). These figures come from vendor marketing without cited data.
- **Cure shrinkage:** One potting resource says compounds shrink 5–10 % on cure, which creates residual stress (vendor source, indicative only) — [Incure: thermal stress cracks](https://incurelab.com/wp/?p=16576). For epoxies, heat of reaction and shrinkage can be a problem for sensitive components, so reactivity and exotherm should be matched to the job — [Gluespec: potting and encapsulation overview](https://gluespec.com/blog/potting-and-encapsulation-in-the-electronics-industry).

### Inferences
- **Hard epoxy is the wrong default for this board.** A 0.8 mm board is thin and flexible. Stiff epoxy cast on one side, shrinking as it cures, will bow the board and load the MLCCs in flex. The 1206/1210 MLCCs are the most crack-prone because of their long ceramic span. Parts near the board edge and next to the USB-C receptacles are worst placed.
- **Ranking for this board, safest first:**
  1. Silicone gel (Shore 00 or very low Shore A, modulus in the kPa–low MPa range, Tg about −120 °C, so no crossing in use).
  2. Soft silicone elastomer (Shore A 20–40).
  3. Soft or low-modulus PU, typically Shore A, with a Tg often in the −40 to +20 °C region. Check that the Tg sits outside the −20 to +60 °C use range.
  4. Flexibilised epoxy.
  5. Rigid epoxy.
- **If a harder compound is ever needed** (for example structural fixing of the USB-C receptacles), first buffer-coat the MLCCs and QFNs with silicone, following Murata's under-coat advice.
- **QFN/WSON underfill risk:** A low-viscosity compound that wicks under a QFN/WSON (standoff about 50–75 µm) and then expands on heating is the tensile-stress scenario DfR describes. A gel, or a high-viscosity compound that bridges rather than fills, reduces that risk.
- **0201 parts:** Their solder joints are tiny but the parts are low-mass. The main risk is likely a lifted joint from shrinkage or delamination of a stiff compound, not ceramic cracking.

### Gaps
- No peer-reviewed MLCC-crack-rate-under-potting dataset was found. The DfR paper's quantitative results (stress in MPa, cycle counts) were not readable.
- No IPC-HDBK-830 or IPC-CC-830 text was accessed. IPC-CC-830 covers conformal coatings, not potting.
- No SMTA or IEEE data was found specifically for WSON or 0201 parts under silicone gel versus PU.

## 2. Heat: does potting help or hurt the inductors and FETs?

### Takeaway
Any potting conducts heat about 10–25× better than still air. Standard compounds are only about 0.2–0.65 W/m·K, filled ones about 1–3 W/m·K. Potting helps only if it connects the hot parts to a real heat sink, here the aluminium cover. If it just fills an enclosed volume, it adds thermal mass and spreads heat toward the cells; it does not remove it.

### Cited Findings
- **Typical conductivities:**
  - Standard epoxy about 0.25–0.5 W/m·K. Filled epoxies about 1.0–1.5 W/m·K, at the cost of brittleness and price — [Incure: silicone vs epoxy vs PU](https://incurelab.com/wp/?p=16581).
  - Listed products: a silicone potting at 0.37 W/m·K, unfilled PU about 0.5 W/m·K, thermally conductive PU 0.65 W/m·K — [RS potting compounds listing](https://hkcn.rs-online.com/web/c/adhesives-sealants-tapes/sealants-resins/potting-compounds/?pn=2); [McMaster potting compounds](https://www.mcmaster.com/products/potting-compounds/for-use-on~iron-1).
- **Rule of thumb (single, non-authoritative source):** For boards dissipating more than 1 W, use 1–3 W/m·K thermally conductive potting. Without thermal simulation, junction temperatures can end up 10–30 °C higher than un-potted — [Zbotic: PCB potting](https://zbotic.in/pcb-potting-encapsulate-electronics-for-harsh-environments/).
- **Thermally conductive silicone potting exists**, for example CHT SILSO COOL 21018 — [CHT TDS](https://cht-silicones.com/product-tds/SILSO-COOL-21018). Its exact k value was not retrieved.

### Inferences
- **Still air for comparison:** about 0.026 W/m·K (general physics value, not from the sources above).
- **What this board already has:** The inductors (about 1.6 W each, worst case) and FETs presumably reach the aluminium cover through the gap pad (typically 1–6 W/m·K).
- **Where potting does help:** A conductive gel or silicone of about 1–2 W/m·K, sandwiched between the tall inductors and the cover, can stand in for or add to the gap pad. It also wets irregular part heights better.
- **Where potting does not help:** Bulk-filling the whole cavity with 0.3 W/m·K compound mainly adds thermal mass. That buffers short peaks, which is helpful in a power bank with intermittent high-power charging. It also couples inductor heat toward the cells, which is unwanted because Li-ion ageing rises with temperature.
- **Hidden cost:** A thermally conductive filler (alumina, boron nitride) raises viscosity, density, Dk and often modulus, which works against the stress, mass and RF goals.
- **Recommended pattern:** Use a gap pad or dispensable gap filler only where heat must flow to the cover. Leave the rest coated, not potted.

### Gaps
- No measured data was found on potted versus unpotted temperature rise for 7×7 mm power inductors or for QFN converters.
- No guidance was found on whether encapsulating a ferrite inductor changes core loss through magnetostriction or stress. This is known qualitatively for ferrites under stress but was not sourced here.

## 3. RF: detuning of the 2.4 GHz chip/PCB antenna and the CC2340R5MODA keep-out

### Takeaway
Dielectric right against a 2.4 GHz chip or PCB antenna detunes it downward in frequency and adds loss, and the effect is largest for compact antennas (IFA, meander, chip). Even an ABS enclosure wall gave a reported shift of about 100 MHz. A full encapsulation at Dk 2.7–4 shifts it far more, larger than the 2400–2483.5 MHz band. Practical options are to keep the antenna region free of potting (dam it off), or to pot it and retune the matching network in the final potted state. I could not confirm a published CC2340R5MODA potting keep-out.

### Cited Findings
- **Size of the shift:**
  - An ABS enclosure dropped a 2.4 GHz antenna by about 0.1 GHz. The respondent attributed it to dielectric (radome) loading and suggested retuning — [RF Cafe forum: covering an antenna with plastic](https://rfcafe.com/forums/antennas/Questions-about-covering-an-antenna-with-plastic.htm). This is a forum post, not authoritative.
  - The same thread adds that dielectric loss (tan δ) near the radiator matters, and that low-loss materials such as PTFE are preferred.
- **Clearance:** A few millimetres of plastic in the near field shifts resonance. About 5–8 mm of clearance is suggested at 2.4 GHz, and compact IFA and meander antennas are the most sensitive — [AISLER community: PCB antennas and 3D-printed enclosures](https://community.aisler.net/t/co-design-of-pcb-antennas-and-3d-printed-enclosures-practical-rf-insights/5518). This is a rule of thumb.
- **First-order model:** For a thin superstrate, ε_eff is roughly (1 + εr)/2 and resonance scales with 1/√ε_eff — [RF Essentials knowledge base](https://rfessentials.com/rf-knowledge-base/what-is-the-effect-of-plastic-mold-compound-on-antenna-performance-in-a-millimet/). The article is about mmWave mold compound, so this is only a rough guide.
- **Enclosure detuning in general:** Antenova lists enclosures as a detuning cause and notes that plastic, metal and glass each affect RF differently — [Antenova: designing around detuning](https://www.antenova.com/designing-around-detuning-how-to-avoid-nearby-component-interference-in-crowded-pcbs).
- **Module guidance (Microchip):** Keep the antenna away from plastic casings and never enclose it in metal — [Microchip external antenna placement](https://onlinedocs.microchip.com/oxy/GUID-3DDF7D25-768C-4E66-8343-E56E3AE4B4BB-en-US-2/GUID-ACD2A690-3258-4AD6-9A97-C670DF276EA6.html).
- **Potting with an antenna is a known engineering problem:**
  - US9368872 covers precision tuning of a miniature antenna to overcome the dielectric detuning introduced by encapsulation — [Google Patents US9368872](https://patents.google.com/patent/US9368872).
  - An Endress+Hauser patent family describes antennas matched for the potted state, with an impedance ratio set by √εr of the potting — [Justia 12136769](https://patents.justia.com/patent/12136769).
- **Johanson LTCC chip antennas:** Marketed for detuning resilience. Their datasheets show matching networks tuned on the evaluation board — [Johanson 2450AT18D0100001E datasheet](https://johansontechnology.com/docs/3791/Antenna-2450AT18D0100001E-Rev5.0.pdf). I found no Johanson encapsulated test data.
- **TI integration guide:** TI publishes an OEM integration guide for the CC2340R5MODA (Chinese ZHDA212, Dec 2025; English counterpart reportedly SDAA237) — [TI ZHDA212](https://www.ti.com.cn/cn/lit/pdf/zhda212). Its antenna or potting keep-out content was not retrieved.

### Inferences
- **Rough size of the shift:** With εr of about 3 fully surrounding a compact antenna, the resonance could drop by roughly 15–40 %, which is hundreds of MHz. The thin-coating case with ε_eff ≈ 2 gives about 29 %. Either way the antenna would miss the band. Parylene (about 25 µm, εr ≈ 2.6–3.1) or a thin acrylic coat shifts a chip antenna far less, typically a few MHz to some tens of MHz, and is usually tolerated by the module's margin.
- **Regulatory consequence:** A certified module (FCC, ISED, CE modular approval) is approved with its antenna in a defined condition. Potting over the module antenna changes the radiated performance, so retesting or a permissive-change assessment would likely be needed. Check the TI OEM integration guide (SDAA237) for TI's exact conditions.
- **Recommended approach:**
  1. Dam off the module's antenna end and its PCB ground keep-out with a printed wall or silicone bead, and leave it as air.
  2. If it has to be encapsulated, conformal-coat or parylene-coat that area only.
  3. Measure RSSI or a VNA S11 on a potted sample before committing.
- **3D-printed shell wall:** The shell already loads the antenna somewhat (PLA, PETG, ASA εr about 2.5–3), which is another reason to keep the potting compound away from it.

### Gaps
- No TI, Nordic, Ignion or Johanson app note with a quantified potting detuning figure (MHz per mm at a given εr) was found. Searches returned forum posts and patents.
- The exact keep-out stated in the CC2340R5MODA datasheet and SDAA237 was not verified.

## 4. Potting around IP68 USB-C receptacles without wicking

### Takeaway
IP68 USB-C receptacles are sealed by their own gasket or overmold, but low-viscosity compound can still wick along the shell, the PCB tails, or into the mating face if the dam fails. The recommended order is:
1. Mount and test the receptacle.
2. Seal its PCB interface with a high-viscosity (thixotropic) bead or dam.
3. Pot in a first shallow lift.
4. Fill.

Never let compound reach the front mating cavity.

### Cited Findings
- **Sealed receptacle design:** One USB Type-C patent describes a metal shell that forms a potting space behind the terminals, filled through an opening in the shell. It notes that conventional edge glue fails because thermal expansion opens gaps between the plastic housing and the terminals — [Justia 20240039205](https://patents.justia.com/patent/20240039205).
- **Potting the coupling in:** A USB-C coupling potted into its receptacle is described as watertight or splash-proof and tightly fixed — [Patsnap EP4765508A1](https://eureka.patsnap.com/patent-EP4765508A1).
- **Dams and gaskets:** A conventional gasket used to keep potting compound out can disable compressible contacts by squashing them — [Google Patents US6592018B2](https://patents.google.com/patent/US6592018). A soft, pliable, removable dam is used around wire bundles — [Google Patents EP0774815A2](https://patents.google.com/patent/EP0774815A2).
- **Workshop practice (anecdotal):** Putty or a thick two-part epoxy gel from a dispensing gun can serve as a dam around connectors — [Garage Journal forum](https://www.garagejournal.com/forum/posts/11702047/).

### Inferences
- **The receptacles are already IP68.** The enclosure seal is the receptacle's front gasket or O-ring against the shell wall. Potting is not needed for water ingress at the connector. It is needed only if the connector must be mechanically fixed for drops.
- **Practical recipe:**
  - Use a thixotropic, non-slumping silicone or PU (for example a dam-and-fill "dam" grade, or an RTV paste) as a 1–2 mm bead around each receptacle footprint and along the shell-to-PCB seam. Cure it before the fill pour.
  - Then pour a gel or low-viscosity fill to below the receptacle's rear face only.
- **Mating-face protection during potting:** Cap the mating cavity with a dummy plug or a silicone mating-face cap.
- **Before potting:** Verify the receptacle's IP68 gasket and shell rating, then plug in a cable to confirm mating force and contact after potting.

### Gaps
- No connector-vendor app note (Amphenol, GCT, JAE, Molex) on potting behind IP68 USB-C receptacles was found. Check the specific part's application spec for any "do not pot" or "max compound contact" note.

## 5. Small-batch process: mixing, degassing, cartridges, exotherm, PU moisture, Pt inhibition, priming, masking, programming

### Takeaway
For tens to hundreds of units:
- Use 50 ml or 400 ml dual cartridges with static mixers, which give a fixed ratio and fewer bubbles than hand mixing.
- Vacuum-degas the poured parts (or use a pre-degassed cartridge), and do it within the pot life.
- Pour in thin lifts to limit exotherm.
- Keep PU out of humidity.
- Keep platinum silicones away from flux residue, amines, sulfur and tin.

All programming, gauge learning and test access must happen before potting, unless test pads are deliberately left uncovered.

### Cited Findings
- **PU moisture:**
  - Moisture reacts with isocyanate to release CO₂ bubbles. Polyurethanes are hygroscopic. Badly contaminated PU foams, and those bubbles are "next to impossible to remove."
  - Avoid mixing on humid days, use a nitrogen blanket on opened containers, and use molecular-sieve moisture scavengers.
  - [Incure: why potting bubbles](https://incurelab.com/wp/?p=16592); [Chase/HumiSeal: 5 steps to eliminate bubbles](https://blog.chasecorp.com/humiseal/5-simple-steps-to-eliminate-bubbles-in-potting-encapsulants).
- **Degassing:**
  - Apply vacuum within the working window (about 15 minutes for fast systems up to about 4 hours for slow ones). After gel, bubbles cannot rise.
  - Use a vessel 5–6× the material volume, at 25–29 inHg.
  - Planetary centrifugal (non-contact) mixing introduces less air than hand mixing. Fillers act as bubble nucleation sites.
  - [Intertronics white paper: avoiding voids](https://smtnet.com/library/files/upload/wp21-1-Potting-and-encapsulating-avoiding-voids.pdf); [Crosslink degassing tips](https://www.crosslinktech.com/support/tips-and-tricks/degassing-materials.html).
- **Exotherm:** Heat builds in the core of deep pours in confined enclosures and accelerates the reaction — [Incure: exotherm damage](https://incurelab.com/wp/how-exotherm-in-potting-compounds-damages-electronics-and-how-to-prevent-it).
- **Pt-silicone cure inhibition:**
  - Platinum-cured silicones are "particularly susceptible" to cure inhibition — [USPTO 6509959](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6509959).
  - Inhibitors listed by CHT: compounds of N, S, P and As; organotin catalysts and PVC stabilisers; epoxy catalysts; sulfur-vulcanised rubber; condensation-cure silicones. Purge dispensing equipment that has held hydride-containing rubber — [CHT SILSO PROTECT 21001 TDS](https://cht-silicones.com/product-tds/SILSO-PROTECT-21001).
  - NuSil: amine-catalysed epoxies and solder flux are known inhibitors — [NuSil datasheet](https://nusil.avantorsciences.com/assetsvc/asset/en_US/id/46394520/contents).
  - Gluespec: sulfur, amines and plasticisers inhibit Pt catalysts — [Gluespec overview](https://gluespec.com/blog/potting-and-encapsulation-in-the-electronics-industry).

### Inferences
- **Flux is the big Pt-silicone risk.** No-clean flux residue under QFNs or around USB-C pins can leave tacky, uncured silicone right where it matters. Clean the board (IPA, or a saponifier wash) and run a cure test on a scrap board. Alternatively, choose a condensation-cure (alkoxy) silicone or a PU, which are inhibition-tolerant but slower or moisture-sensitive.
- **Avoid tin and condensation-cure contamination.** Do not use tin-catalysed condensation silicones or amine-cured epoxy dams near a Pt-cure gel.
- **Use a primer only if the datasheet calls for it.** Gels self-adhere poorly by design, which helps rework.
- **Exotherm on this board:** Pour depths are probably 3–10 mm, so exotherm is minor for silicone. It is more of a concern for fast PU or epoxy in the deeper inductor wells. Use two lifts.
- **Cartridges:**
  - A 50 ml 1:1 or 10:1 cartridge with a manual or pneumatic gun suits tens of units.
  - 400 ml cartridges with a pneumatic gun suit hundreds.
  - Discard the first mixer-length of output (unmixed lead).
  - Size the static mixer to the compound's pot life.
  - Pre-degassed cartridge grades exist and reduce the need for vacuum.
- **Test access (SMBus pogo pads, Tag-Connect SWD, BQ40Z50 golden-file and learning cycle):**
  - Complete everything before potting: CC2340 flash, BQ40Z50 data-flash and golden image, BQ25756 and TPS25751 configuration, and full functional test.
  - Or mask the pogo pads and Tag-Connect footprint with removable silicone plugs or caps, or peelable mask, so they are left as open wells. Tag-Connect legs and pogo pins need a clear, flat area around the pads.
  - The BQ40Z50 learning cycle needs the cells connected and a full charge/discharge. It can run with the board potted, provided SMBus is reachable through a connector or an unmasked pad well.
- **Masking:** Use peelable latex or synthetic mask, or silicone boots, for the pads, the antenna region, the USB-C mating faces and any thermal-pad contact faces.

### Gaps
- Electrolube's and Dow's own potting guides were not retrieved. Quantitative cartridge or static-mixer guidance (for example the minimum number of mixing elements) was not sourced.

## 6. Reworkability, repair and EU Battery Regulation 2023/1542

### Takeaway
Silicone gel is the only potting that is practically reworkable: it can be cut or peeled away and topped up. PU is hard to remove, and rigid epoxy effectively makes the board scrap. On the regulation, Article 11 removability applies from 18 February 2027. A law-firm analysis of the Commission's updated (July 2026) guidance says power banks fall outside Article 11 altogether, because they are themselves a portable battery. Potting the electronics is therefore probably not a regulatory blocker, but recyclers still benefit from separable cells.

### Cited Findings
- **Application date:** Article 11 applies from 18 February 2027 — [Dudkowiak](https://www.dudkowiak.com/blog/battery-replacement-and-removability-starting-in-2027-new-guidelines-from-the-european-commission/); [EUR-Lex C/2025/214 guidance](https://eur-lex.europa.eu/eli/C/2025/214/oj/eng).
- **What the Commission guidance says** ([EUR-Lex C/2025/214](https://eur-lex.europa.eu/eli/C/2025/214/oj/eng)):
  - A readily removable battery is one that can be removed with commercially available tools, without specialised tools (unless supplied free), proprietary tools, thermal energy or solvents.
  - The obligation applies to entire batteries, not cells.
  - The guidance is non-binding; the CJEU holds the binding interpretation.
- **Power banks excluded:** HLC (25 Aug 2026) reports that the updated Article 11 guidance, adopted alongside the 14 July 2026 delegated act, clarifies that "charging cases and power banks... fall outside Article 11 altogether," because they are a portable battery in themselves — [HLC](https://www.hlc.com/en/publications/avoiding-the-redesign-the-eus-latest-position-on-battery-removability). This is a secondary source; I did not read the updated guidance text.
- **Industry position:** The EPBA's January 2026 position paper argued that Article 11 should not apply to power banks — [EPBA](https://www.epbaeurope.net/assets/EPBA-Position-Paper-Powerbanks-.pdf).
- **More changes coming:** The Commission is considering further derogations (April 2026) — [ERP Recycling](https://erp-recycling.org/news-and-events/2026/04/batteries-eu-proposes-simpler-removability-and-replacement-rules/). A delegated act of 14 July 2026 added categories, reportedly not yet in force — [REACH24H](https://en.reach24h.com/news/industry-news/sustainability/eu-portable-battery-removability-exemptions-2026).

### Inferences
- **Other parts of the regulation still apply.** These include labelling, CE, carbon-footprint and other obligations, and end-of-life collection. A potted cell pack hampers safe discharge and dismantling at recyclers.
- **Keep the cells out of hard potting.** If the cell area is potted at all, a gel or foam that peels off keeps the pack separable, which is good for design-for-recycling and for the user's own failure analysis.
- **Rework of a gel-potted board:**
  - Cut the gel away locally, replace the part, clean, and re-dispense the gel. Gel adheres to itself.
  - Hot air on silicone residue produces some smoke and odour but works.
  - PU and epoxy require mechanical or chemical stripping, which damages 0201 and QFN parts.

### Gaps
- The text of the updated (July 2026) Commission guidance with the power-bank carve-out was not read directly.
- The six new derogation categories were not confirmed from the Official Journal.

## 7. Alternatives: conformal coating, parylene, nano-coatings, what IP68 needs, mass comparison

### Takeaway
IP68 is an enclosure property. Water is kept out by the shell, gaskets and the sealed connectors, and the board does not need potting to meet it. Conformal coating (25–200 µm) or parylene (13–51 µm) protects against condensation and incidental ingress at a few grams per board, against tens of grams for potting. Plasma nano-coatings (P2i, HZO) are thinner still and rated for splash-level protection (IPX2), with newer barrier grades aimed at IPX7. They protect the board, but they are not the enclosure seal.

### Cited Findings
- **Coating thicknesses** (SCS, a parylene vendor that may favour parylene):
  - Acrylic, urethane and epoxy coatings: 25–127 µm.
  - Silicone: 51–203 µm.
  - Parylene: 13–51 µm.
  - Acrylic is easy to rework but has low abrasion and solvent resistance. Silicone has poor abrasion resistance. Urethane has strong chemical resistance but cures more slowly and adheres less well.
  - [SCS: coating thickness comparison](https://scscoatings.com/newsroom/blog/conformal-coatings-thickness-comparing-parylene-with-liquid-coatings/); [Parylene blog: coating types](https://blog.paryleneconformalcoating.com/?p=2731).
- **P2i plasma nano-coating:**
  - The splash-proof hydrophobic layer is about 1000× thinner than a human hair. Its "Dunkable" barrier targets IPX7 — [The Engineer](https://theengineer.co.uk/uk-coating-innovation-makes-a-splash-for-smartphones).
  - A consumer article says the P2i coating gave phones IPX2 (splash), not submersion — [iCulture](https://www.iculture.nl/nieuws/smartphones-2018-waterproof/).
- **HZO:** Markets thin-film coatings for consumer electronics — [HZO consumer electronics](https://hzo.com/markets/consumer-electronics). No thickness or IP data was retrieved.
- **Murata's coating caution** applies here too: avoid coatings containing halogen or organic acid — [Murata FAQ](https://www.murata.com/en-global/support/faqs/capacitor/ceramiccapacitor/mnt/0024).
- **Tg inside the cycling range:** DfR flags an acrylic with Tg about 15 °C — [DfR QFN reliability](https://dev.smtnet.com/library/files/upload/Reliability-of-QFN-Devices.pdf).

### Inferences
- **Mass estimate** (my own calculation; board area assumed 50 × 80 mm = 40 cm², densities typical: coating about 1.0–1.3 g/cm³, potting about 1.0–1.6 g/cm³ unfilled to filled, parylene about 1.29 g/cm³):

  | Option | Assumed thickness | Approx. mass |
  |---|---|---|
  | Acrylic or urethane coating | 50 µm | ~0.2–0.3 g |
  | Silicone coating | 150 µm | ~0.6 g |
  | Parylene C | 25 µm | ~0.1 g |
  | Full potting | 5 mm average | ~20–30 g |
  | Thermally filled potting | 5 mm average | ~30–40 g |

  Potting is about 100× the mass of coating and directly reduces Wh/kg.
- **Drop protection:** Potting immobilises heavy parts (inductors, USB-C receptacles) against shock, but on a thin board it also couples shell impacts into the solder joints.
  - For drop, mechanical fixing is more effective: screws or bosses near the USB-C receptacles, a soft gel or foam pad against the inductors, and corner staking of the inductors and module with a flexible adhesive.
  - Corner staking or "glob" fixing of inductors and the BLE module with a soft silicone or UV-acrylic staking adhesive is a mid-way option with little mass or RF penalty.
- **Recommended baseline for this board:**
  - A selective conformal coat (silicone or urethane-modified acrylic, about 25–75 µm).
  - Masks over the pogo pads, Tag-Connect, USB-C mating faces, gap-pad contact areas and, optionally, the antenna.
  - Plus staking of the tall parts.
  - Reserve gel potting for cases where testing shows condensation or salt-fog failures that coating does not cover.
- **Parylene:** Excellent and thin, and it can coat under QFNs. However, it needs a vacuum batch service, requires masking of every connector, and is effectively non-reworkable without micro-abrasion. Outsourced lots for tens of boards are feasible but relatively costly.

### Gaps
- No independent IP-test data compares coating versus potting for boards inside a non-sealed shell.
- No cost-per-board figures for parylene or plasma coating at 10–200 units were found.
- No HZO thickness or IP figures were retrieved.

## 8. Outgassing and corrosion: acetoxy RTV, oxime, amines

### Takeaway
Never use acetoxy-cure ("vinegar-smelling") RTV on or near the electronics. It releases acetic acid, which corrodes copper and other metals, even as trapped vapour inside a closed enclosure. Use alkoxy (neutral, methanol-releasing) RTV or addition-cure (platinum) silicone instead. Oxime-cure is "mildly corrosive" to copper per some sources, so avoid direct contact. Amine-cured epoxies also poison platinum silicones if used nearby.

### Cited Findings
- **Acetoxy:**
  - Releases acetic acid on cure, so it is unsuitable where corrosion matters, and electronics is the named example. Specify neutral-cure alkoxy instead — [Intertronics: are RTV silicones corrosive?](https://intertronics.co.uk/2018/08/adhere-academy-are-rtv-silicone-sealants-corrosive/).
  - Trapped fumes in a sealed enclosure can corrode copper (anecdotal) — [EEVblog thread](https://eevblog.com/forum/beginners/silicone-sealant-(electronics-grade)).
- **Alkoxy:** Releases methanol or ethanol, is neutral and does not attack copper alloys. The drawback is slow cure, and it is easily hydrolysed in storage — [Intertronics TB008](https://www.intertronics.co.uk/articles/tb008.htm); [EPO EP0905195](https://data.epo.org/publication-server/rest/v1.2/publication-dates/20020327/patents/EP0905195NWB1/document.html).
- **Oxime:** Sources disagree.
  - Cameo (MFA Boston) lists it as mildly corrosive — [Cameo: silicone cure systems](https://cameo.mfa.org/wiki/Silicone_cure_systems).
  - An EPO patent says oxime compounds complex with copper — [EP0905195](https://data.epo.org/publication-server/rest/v1.2/publication-dates/20020327/patents/EP0905195NWB1/document.html).
  - Some vendors call it non-corrosive.
- **Murata:** Avoid coatings containing halogens, organic acids or hydrolysable chlorine on MLCCs — [Murata FAQ](https://www.murata.com/en-global/support/faqs/capacitor/ceramiccapacitor/mnt/0024).
- **Amine-cured epoxies** inhibit platinum silicones — [NuSil](https://nusil.avantorsciences.com/assetsvc/asset/en_US/id/46394520/contents).

### Inferences
- **Silver-bearing parts** such as MLCC terminations (Ni/Sn over Ag or Cu) and some chip antennas with Ag electrodes are also vulnerable to acid and sulfur attack. This is another reason to use alkoxy or addition-cure silicone only.
- **Hardware-store sealants are a hidden acetoxy risk.** The same rule applies to any sealant used to seal the shell or the USB-C bezel; most generic bathroom silicone is acetoxy.
- **Moisture-cure silicones need air.** In a closed potting cavity, alkoxy RTV cures from the surface inward, slowly. Thick sections may remain uncured for days. Use two-part addition-cure for anything thicker than about 6 mm. (This is general practice, not sourced here.)

### Gaps
- No quantitative outgassing data (TML/CVCM per ASTM E595) was gathered for candidate gels.
- No data was found on whether low-molecular-weight siloxane outgassing affects USB-C contact resistance. LMW siloxane contamination of relay and switch contacts is known in industry but was not sourced here.
