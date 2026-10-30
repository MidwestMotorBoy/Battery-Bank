# Wrap label

The printed vinyl label that wraps round the cup. Its top and bottom edges sit under the TPU bumpers. It is one flat rectangle, 199.3 × 70.85 mm cut size with R2 corners, plus 2 mm of bleed. The length is the cup perimeter plus a 5 mm overlap, and the seam is in the middle of the back face. The size comes from the cup model (`hardware/mechanical/monolith_cup.py`: `LABEL_T`, `LABEL_TUCK`, `LABEL_Z`), so re-run the label after a cup change.

The adopted artwork is the Borderlands-style version (`--bl`): brush inking, the vivid palette with heavy ink (Logan's pick, variant 8-1, 2026-10-27), and the angular mother bear and cub (option 9i-7). The vent hole was removed on 2026-10-28; the sun stays where it was, solid.

## Scripts

| Script | Writes | What it is |
|---|---|---|
| `monolith_label.py --bl` | `out/monolith_label_bl_*` | The adopted label. Needs numpy, fonttools, manifold3d, cairosvg, pypdf, svgpathtools and scipy. |
| `monolith_label.py` | `out/monolith_label_*` | The same layout in the earlier flat style, without `--bl`. |
| `monolith_label_preview.py [--bl]` | `out/<name>_on_cup.png` | The label on the cup with the bumpers, from three sides. Run `monolith_label.py` first. |
| `bear_options.py` | `out/bear_options*.png` (git-ignored) | The bear options for the back, which is where 9i-7 came from. |
| `label_variants.py` | `out/label_variants*.png`, `out/variants*/` (git-ignored) | The whole-label look variations, which is where 8-1 came from. |

## Outputs (`out/`)

| File | Use |
|---|---|
| `monolith_label_bl_print.pdf` | The file to send. Artwork with 2 mm bleed and all text as outlines. TrimBox is the cut size, and the die line is a CutContour spot-colour stroke. |
| `monolith_label_bl_stickerapp.pdf` | The same for StickerApp: the outer cut line only, as the spot colour "die cut", 1 pt, on its own layer. |
| `monolith_label_bl_trim.pdf` | The artwork cut to size, with no bleed or die line, for shops that cut from the artwork outline. |
| `monolith_label_bl_print.svg`, `monolith_label_bl_cut.svg` | The artwork, and the die line on the same page. |
| `monolith_label_bl_proof.png`, `monolith_label_bl_on_cup.png` | Proofs: the art with the die line and face folds, and the label on the cup. |

The intermediates (`*_cut_art.*`, `*_proof.svg`, `*_trim.svg`, `_*`) and the option sheets are git-ignored (`out/.gitignore`).

## Fonts

`fonts/` holds Bangers and Barlow Condensed (SemiBold, Bold, ExtraBold), both under the SIL Open Font License 1.1 (`fonts/OFL-*.txt`). The label embeds the text as outlines, so the print files need no fonts.
