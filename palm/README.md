# Graphite Handheld

A Palm OS–style handheld organiser that runs in the browser, with working
**Graffiti** unistroke handwriting input.

Open `index.html` directly — no build step, no dependencies. The only network
request is the Silkscreen webfont used for the case silkscreen printing; it
falls back to a monospace stack offline.

## Files

| File | What it holds |
| --- | --- |
| `index.html` | the device shell: case, screen well, silkscreen row, hardware keys |
| `styles.css` | case styling plus the 160×160 virtual screen, scaled by `--u` |
| `graffiti.js` | the stroke table and the recognizer |
| `apps.js` | Date Book, Address, To Do, Memo Pad, Calc, Graffiti, HotSync, Prefs |
| `palm.js` | storage, routing, the pad, the on-screen keyboard, Find, menus |
| `build-artifact.sh` | emits the variant used when the page is published as an Artifact |

## Graffiti

Each character is one stroke, written on the pad below the screen: letters to
the left of the divider, numbers to the right.

| Stroke | Meaning |
| --- | --- |
| horizontal, left → right | space |
| horizontal, right → left | backspace |
| diagonal, top-right → bottom-left | return |
| diagonal, bottom-left → top-right | next field |
| vertical, bottom → top | shift (twice = caps lock) |
| a tap | period |

Letter shapes are capitals; the device writes lowercase until you stroke shift.
The on-device **Graffiti** application draws the full chart, generated from the
same point table the recognizer matches against, so the chart cannot drift out
of sync with the recognizer.

### How recognition works

`graffiti.js` uses the $1 Unistroke Recognizer's pipeline — resample to 40
points, scale into a reference square, translate to the centroid, then take the
mean point-to-point distance against each template — **without** its
rotate-to-indicative-angle step. Graffiti is orientation sensitive (`n` vs `u`,
`m` vs `w`), so rotation invariance would discard exactly the information the
alphabet depends on. The 1-D fix from the algorithm's later revision is kept, so
straight strokes (`i`, `l`, space) scale uniformly instead of being blown up
into noise.

A best score below the threshold set in **Prefs → Strokes** is rejected and the
pad flashes `?` rather than guessing.

Shapes follow the classic Graffiti conventions. Letters whose original strokes
retraced the spine are drawn here as the single printed stroke the chart shows.

## Storage

Records live in `localStorage` under `graphite-pda-v1`, in this browser only —
nothing is sent anywhere. **Prefs → Reset** erases them and restores the sample
records. Every access is wrapped in `try`/`catch`, so the device still runs in a
private window with site data blocked; it just will not remember anything.

## Not affiliated with Palm, Inc. — this is a tribute, not a product of theirs.
