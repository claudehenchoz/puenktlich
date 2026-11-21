# Sprite overrides

Hand-touched sprite sheets that replace rendered ones, e.g.

    overrides/re460/1x/re460_8bpp.png
    overrides/re460/1x/re460_32bpp.png

Workflow: run `pk render <id>`, copy the sheet from `build/sprites/<id>/<scale>x/` here, edit it
(GIMP/Aseprite; keep 8bpp files in the TTD palette), then rebuild. Overrides replace the whole
sheet, so redo them whenever the model changes. `pk render` lists applied overrides.
