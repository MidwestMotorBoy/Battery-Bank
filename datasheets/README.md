# Datasheets

Datasheets and application notes for the parts chosen for Monolith (production board and dev board). The list, with source links, is in `sources.csv`.

To download them all, run from the repo root on a computer with normal internet access:

```
bash tools/fetch_datasheets.sh
```

The script saves each PDF here under the file name in `sources.csv`, skips files already present, and lists any it couldn't fetch (some sites serve a web page instead of the PDF) so you can grab those by hand.
