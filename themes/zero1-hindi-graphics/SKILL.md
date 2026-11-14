---
name: "zero1-hindi-graphics"
description: "Turn a Zero1 Hindi IP script (faceless, 100% graphics, Hinglish VO, wooden-toy Arjun) into a beat-by-beat storyboard, image-generation prompts for every diorama, and 1920x1080 PNG + HTML graphics in the house style."
---

# Zero1 Hindi IP: script → storyboard → prompts → PNG + HTML

This IP is **faceless**: every second of VO sits on a designed frame, so the storyboard *is* the film. The house look is a handcrafted toy world:
- wooden-block **Arjun** (oval eyes, cut-paper hair, regional costume)
- crumpled-paper + sky backdrops
- twine-hung tags, boards and tables
- Impact + Bricolage Grotesque type, with one red (#B23636)

Built from 3 shipped episodes (V1 *State Culture × Money Mindset*, V2 *Noida Real Estate*, V3 *Kerala's Gold Obsession*).

**What you deliver:**
1. the storyboard (in chat + `storyboard.md`)
2. `image_prompts.md` for every plate the kit can't paint
3. one zip containing two flat folders, `PNG/` and `HTML/` (same names, self-contained HTML), plus `storyboard.md` and `image_prompts.md`

## Read budget
- **Storyboarding (always, before writing a single beat):**
  - `references/storyboarding_method.md`, in full. This is how the team thinks: one toy world, one camera, every line literalised.
  - **One full gold corpus**, the one closest to this script's shape:
    - `references/gold/v1_corpus.md`: Comparison (several Arjuns or states)
    - `references/gold/v2_corpus.md`: Investigation (one decision)
    - `references/gold/v3_corpus.md`: Life-story (one person + one object over time)
  - The "Top 10 storyboarding moves" section of the other two corpora.
  - `references/storyboard_rules.md` for the spine, density, Arjun and language rules.

  The corpora are the team's real VO → cue → final-frame records; imitate their thinking and their cue-writing voice.
- **Building:** `references/spec_format.md`. `references/plates_index.md`: 138 textless scenes from past episodes, reuse them as backgrounds when a set matches. `references/style_at_a_glance.jpg` (one look).
- **On demand:**
  - `references/frame_types.md` + `references/frames/_atlas_*.jpg` for layout references
  - `references/character_and_prompts.md` before writing `gen` prompts
  - `references/qa_checklist.md` before delivering
- **Theme guard:** use only this kit. Do not borrow from varsity-*, zo-* or other channel skills.

## Step 1: Setup
```bash
mkdir -p job && cd job
[ -d zero1-hindi-graphics ] || unzip -q /path/to/zero1-hindi-graphics.zip     # skip if installed as a skill
python3 -c "import playwright" 2>/dev/null || pip install playwright --break-system-packages -q; python3 -m playwright install chromium 2>/dev/null || true
pip install pyspellchecker --break-system-packages -q 2>/dev/null || true       # optional spell warnings
```
`$K` = the kit folder. If Chromium can't install, set `CHROMIUM_PATH`.

## Step 2: Storyboard (the most important step; stop here if that's all the user wants)
Follow `storyboarding_method.md` pass by pass. Don't skip passes and don't jump to frame types.
0. **Inventory:** episode question, shape, Arjun + his arc, every number, source, list and pivot line.
1. **World bible:**
   - 4–8 regionally authentic **sets** (with research notes)
   - 2–3 **recurring devices**, house devices first (sticker tag, wooden map, timeline spine, newspaper, hung option boards, desk ledger, hung table, checklist, see-saw, "?" + polaroids)
   - the **hero object**
   - 1–2 **hero animations**

   Print it at the top of the storyboard.
2. **Beats:** one cue `#N` per VO sentence or tight group, about 6 per minute like the team (≤ 1.2× the script's sentences). Split numbers, list items and pivots into `_b`/`_c` states inside a cue. ≤ ~25 new gen plates.
3. **Draft every beat with the move ladder:**
   1. literalise
   2. morph/build from the previous frame
   3. camera move
   4. number on an object
   5. bubble / Arjun's reaction
   6. source inside the world
   7. only then a typo over the current shot

   Write cues in the team's voice (see the gold corpora).
4. **Continuity chain:**
   - every cut is in-world: CAM, MATCH, MORPH or BUILD
   - every new set has an entry move
   - each chapter has ≥ 1 MORPH
   - chapter reveals come out of the world
   - devices are paid off in the conclusion
5. **Self-critique:** score the 9-point rubric, rewrite the weakest ≥ 10% of beats, re-score. Average must be ≥ 4. Print the scores with evidence.
6. **Production plan:** camera moves → start/end keyframes; builds → `_b`, `_c` states. For each frame: plate reuse (`plates_index.md`) / kit asset / `gen` prompt + kit text.

**Storyboard format** (the team's own doc layout: the VO line, then the cue under it):
```
WORLD BIBLE  sets: … · devices: … · hero object: … · hero animation: … · Arjun arc: …

INTRO
#1  ~0:00  [set: Bengaluru flat]  ← open (sound only)
VO: Miliye Arjun se. Bengaluru mein rehta hai, IT company mein kaam karta hai.
Cue: Arjun apne chhote Bengaluru flat ki balcony pe laptop bag ke saath khada hai (Koramangala rooftops, metro line piche). Camera slowly pull back hota hai, building ke upar city skyline reveal.
Text: meet ARJUN   ·   Moves: CAM, REGION   ·   Frames: 0.00 (balcony) → 0.00_b (skyline)   ·   Make: gen: blr_balcony + kit text
#2  ~0:04  [set: Bengaluru flat]  ← CAM: push back into the balcony
VO: Har mahine ₹85,000 kamata hai…
Cue: Same frame; Arjun ke upar notebook sticker tag latakta hai: SALARY ₹85,000 (red).
Text: ₹85,000   ·   Moves: BUILD, DEVICE, NUMOBJ   ·   Frames: 0.04   ·   Make: same plate + kit idtag
```
After the beats:
- **Numbers & names → frames**
- **Sources → frames**
- **Plates reused / assets / gen list**
- **Screen captures**
- **Rubric scores**
- **Flags:** typos fixed, facts to verify, missing connectors written

**If the user gives a storyboard** (cues already written): use SB-given mode in `storyboarding_method.md`:
- keep every camera move, morph and callback
- fill empty or vague cues (`[added]`)
- upgrade weak ones (`[upgraded]`, original kept)
- flag cue vs VO mismatches
- then Passes 5–6

If the user is around and the script is long, show the storyboard and get a go-ahead before building. If they're away, continue and state your assumptions at the top.

## Step 3: Spec + first build (layout with placeholders)
Write **one** `spec.json` (and save the storyboard as `storyboard.md` **next to it**, since packaging picks it up from there) (format: `spec_format.md`; working example of every type: `examples/example_spec.json`). Every picture the kit can't render is a `gen:<key>` with a prompt in `spec["gen"]`. Then:
```bash
python3 $K/scripts/build.py spec.json --out out
```
The build writes:
- `out/png/*.png` and `out/html/*.html`
- `out/_sheet_N.jpg` (6 frames per sheet)
- `out/_text.txt` (all on-screen text per frame)
- `out/_image_prompts.md` (full Magnific prompts with the style + character bible appended)

It also prints `WARN` lines for:
- SOP count ≠ chapter count, or a section with no chapter reveal
- text off-frame or overflowing
- off-palette colours, Devanagari, western ₹ grouping
- known shipped typos and placeholder text (unknown words are listed separately on one `SPELL?` line: confirm them, or add to `spec["allow_words"]`)
- article highlight not found in its body
- duplicate ids, missing assets

Ungenerated plates render as labelled dashed placeholders, so the layout can be reviewed now. Fix the spec and rebuild single frames with `--only 1.05,2.33`. Look at every `_sheet_N.jpg` once.

## Step 4: Images (generated by script, never drawn by hand)
**Never fake a plate with SVG/canvas/vector drawing.** The house look is photographed paper/clay/wood miniatures (stop-motion); vector stand-ins were rejected in review. Every pending `gen:` plate is either a real past-episode plate or comes from an image model through the script below.

```bash
python3 $K/scripts/gen_images.py spec.json --dry-run      # check prompts + reference images, no key needed
python3 $K/scripts/gen_images.py spec.json                # generate every pending gen:<key> -> gen/<key>.png
python3 $K/scripts/gen_images.py spec.json --only kandivali_flat --force   # redo one
python3 $K/scripts/build.py spec.json --out out           # rebuild with the images
```
- Needs one key in the environment: `GEMINI_API_KEY` (Google Nano Banana, recommended) or `OPENAI_API_KEY` (gpt-image-1). Override the model with `IMG_MODEL`. Standard library + Pillow only; no Figma or any other app.
- Style lock is automatic: each request carries the kit prompt (world + figure + Arjun bible) plus reference images: 3 house plates and the Arjun cut-out whenever Arjun is in the shot. To steer one scene, add `"refs": ["asset:plates/<file>.jpg", ...]` to its `spec["gen"]` entry (e.g. the closest past plate for layout).
- **Regional sets are always generated, not substituted.** If the episode is set in a new city (Mumbai flat, local train, cab on the WEH…), write those as `gen:` keys with regional detail in the prompt. Don't stand in a past episode's city plate (e.g. Noida towers for Kandivali) except as a flagged temporary placeholder.
- Output: 16:9 keys are cover-cropped to 1920×1080; `cutout` keys come back with the white removed. A log goes to `gen/_gen_log.json`.
- After generating, **open every image** and check it against the character bible (block wooden head, oval eyes, cut-paper hair, regional costume, no text, paper-3D look). Regenerate misses with `--only <key> --force`. Then rebuild and review the sheets.
- If no key is set or the network blocks the API, say so in one line. Give the user `out/_image_prompts.md` (self-contained prompts, tuned for Magnific; works with any image model) and the exact command to run once a key is available. Ungenerated plates stay as labelled dashed placeholders, never as drawn substitutes.
- Use **plates and kit assets first**: 138 textless scenes from past episodes in `assets/plate_sheets/` (see `plates_index.md`; reference as `asset:plates/<file>`, cut out automatically by the build; `build.py --unpack-plates` to view them), `assets/characters/` has Arjun in several poses for city / Kerala / Andhra / Meghalaya, `assets/props/` has tags, boards, rope, clipboard, see-saw, necklace and more, plus maps and scenes. Only generate what's new.
- Images the user supplies go in `gen/<key>.png` next to `spec.json` (remove backgrounds for `cutout` ones), then rebuild. Each scene uses its own plate: one plate repeated across unrelated beats reads as "only one graphic everywhere". Reuse a set only for beats that really happen there.

## Step 5: QA + deliver
Run `references/qa_checklist.md`: no `WARN` left, sheets look right, and `_text.txt` proofread against the script (numbers, spellings, SOP = chapters). Then:
```bash
python3 $K/scripts/build.py spec.json --out out --package Ep<NN>_<Title>_graphics
```
→ `out/Ep<NN>_<Title>_graphics.zip`:
```
Ep05_Gold-Loans_graphics/
  PNG/01_0.00_meet-arjun.png  02_0.06_lekin.png …      ← for the edit
  HTML/01_0.00_meet-arjun.html …                       ← same frames, fully self-contained (fonts + images inlined), editable
  storyboard.md   image_prompts.md
```
Files are `<order>_<timestamp>_<what it shows>`; states keep their suffix (`_b`, `_c`). **Never send PNGs without the matching HTML or a loose folder of files; send the one zip.** Close with:
- the frame count per section
- the images still pending
- screen-capture beats
- anything to verify

## House rules (memorise)
- **One world, one camera.** Every beat is a shot in Arjun's toy world reached by a camera move, match cut, morph or build. Never a slide.
- **Faceless and fully physical:**
  - lists → placards, tags, polaroids, checklist, option boards
  - numbers → big red Impact next to the object they describe
  - sources → re-typeset article cards or headline walls (never raw screenshots)
  - history → timeline spine with cut-out scenes
  - processes → object chains with arrows
- **Arjun in or implied in most frames**; every number happens to him. Expressions only on emotional beats. All side characters use the same wooden-block model (no Lego minifigs, no smooth faces).
- **Mood levers:**
  - darkened scene + gold numbers = reveal
  - greyscale world + colour subject = focus
  - sepia / grey vignettes = past
  - red flood = crisis
- **Type & colour:** Impact role (rendered with bundled Anton) for titles, years, big numbers and board names + Bricolage Grotesque for everything else. One red #B23636, gold #E0A422 on dark, blue/teal only for neutral data.
- **On screen:** English, plus Romanised Hinglish phrases lifted from the VO ("Lekin!", "₹2 cr. ka 75% = ?"). Never Devanagari. Indian number grouping. Correct script typos.
- **Generated images contain no text**: all words are kit layers.