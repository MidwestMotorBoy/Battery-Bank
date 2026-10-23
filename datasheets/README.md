# Datasheets

Datasheets and application notes for the parts chosen for Monolith (production board and dev board), downloaded 2026-10-11. The list, with source links, is in `sources.csv`. These documents are the manufacturers' copyrighted material, included here for reference.

To re-download or refresh them, run from the repo root on a computer with normal internet access:

```
bash tools/fetch_datasheets.sh
```

The script saves each PDF here under the file name in `sources.csv`, skips files already present, and lists any it couldn't fetch (some sites serve a web page instead of the PDF) so you can grab those by hand.

Added 2026-10-14 (schematic review 3): the second-level protection and liquid-detection parts (BQ2947, WSFB1514, TPD2S300), the BQ40Z50-R2 technical reference manual and SLUA660, the BQ25756 and TPS25751 EVM guides (reference schematics), and the discretes (FETs, diodes, NTC, switch, test loop, C406). Not fetched, download by hand: ST AN5290 and AN5165 (st.com refuses scripted downloads) and the Everlight 19-217 LED datasheet (no LCSC PDF).

Added 2026-10-23: the BAK N21700CX-65E product specification (A/00, 2025-04-10), the pack cell adopted on 10-23. It came from Convoy's store, which the fetch script can't reach, so it was added by hand.
