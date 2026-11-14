# QA checklist (run before delivering)

Every issue below shipped in at least one of V1–V3. The build's `WARN` lines catch some of them; the rest need you to proofread `out/_text.txt` against the script.

**Structure**
- [ ] SOP lists exactly the chapters that follow, same order, same count (V2 showed 4 with a garbled 4th while the VO says 3). *Build warns.*
- [ ] Every chapter has a connector line + chapter reveal (V3 had none for Ch-2/3). *Build warns per section.*
- [ ] Paired frames are structurally identical (5-years vs 10-years versions carry the same lines).
- [ ] Callbacks reuse the earlier frame's composition.

**Text**
- [ ] Spelling: correct script typos (HELO, SGHs, Sikkam, Matrilinieal, Alloted, Wasteage, REality). *Build flags known typos + unknown words if `pyspellchecker` is installed.*
- [ ] No Devanagari. *Build warns.*
- [ ] Every number matches the VO; Indian grouping (₹3,79,11,842), never ₹1,180,000,0. *Build warns on western grouping.*
- [ ] Data fields aren't copy-pasted (V1 ID tag had INFO = ₹50 Lakh, a copy of salary).
- [ ] No placeholder / lorem ipsum. *Build warns.*
- [ ] Sources: publication + date on SRC frames; highlight matches the exact sentence the VO reads. *Build warns if the highlight isn't in the body.*
- [ ] Real names researched where the doc asks (V1 left "Bank-1…Bank-4" for 1990s banks).

**Look**
- [ ] Only Impact + Bricolage; only palette colours; one red. *Build warns on off-palette colours.*
- [ ] No text off-frame or overflowing. *Build warns.*
- [ ] All people are wooden-block figures with oval eyes, costume consistent per episode.
- [ ] Generated plates contain no stray text/logos; before/after plates share the camera angle.
- [ ] Pending `gen:` placeholders are listed in the final message (they are expected until images come back).
