---
name: "zo-graphic-maker"
description: "Make Zerodha Online explainer graphics (1920x1080, white grid + doodle look, or text over the presenter) from a short brief or a storyboard PDF, in batches, delivered in the layered Bulletin format."
---

# ZO graphic maker: storyboard or brief → layered 1920×1080 graphics (Family Portfolio / Life cycle fund look)

Use this for **a few graphics from a short brief** ("make a table of exit load slabs", "a pie for 60/30/10", "a title over the presenter: No lock in period") **and for a whole storyboard PDF** ("make 5 graphics first", then "make remaining").

Output: a zipped `<Video>_layers/` folder in the team's layered Bulletin format (Step 5). Never deliver loose class-based HTML.

## Workflow at a glance
1. **Read the storyboard.** Read the PDF with the `pages` parameter, 4 pages at a time. Each beat is VO text plus an optional reference image. List the beats that need a graphic.
2. **Plan the batch.** If the user says "first N", build N frames and stop. When they say "make remaining", build the rest and **re-zip the full set** (all frames from every batch).
3. **Set up the kit once** (Step 1). Write all frames from one Python generator, `gen/make.py` (Step 2).
4. **Render, then check the contact sheets** (Step 4). Fix only what's broken, then re-render.
5. **Export and diff** (Step 5). Write spec/README, zip, and send each PNG plus the zip with `SendUserFile`.
6. **Reply briefly.** Say what each frame shows, what you added or changed in the copy, what you skipped and why, and which plates are stand-ins. End with what comes next.

### Reading a storyboard
- **Numbering.** If the SB has frame numbers, keep them as file numbers (`02_`, `04_`…). If it has none, number the frames in script order (01, 02…). A skipped beat keeps its number as a gap (e.g. no `12_`), and that number is logged in `spec.json` → `skipped`.
- **Reference images.** Rebuild each one in the house style with the script's exact numbers and generic names (XYZ Ltd). Never copy a screenshot.
- **Screen captures.** Skip them: website pages, calculators, "show the charges page" beats. Log each in `skipped` with a reason.
- **Text-on-screen beats without a ref.** Make an over-presenter frame. A row of reference frames sharing a pattern (e.g. "1. Do I understand…", "2. How long…") gets **one template** reused for all of them.
- **Build-up beats** (a list that highlights one item at a time). Make one frame in its final state: the active item at full size with a blue pointer, the others at `opacity:.35`. Tell the user they can animate it by toggling those layers.
- **Arithmetic.** Check every number in the script (totals, percentages, interest maths) before drawing. Write the numbers exactly as given, with Indian grouping (₹1,00,000; ₹1.6 lakh).
- **Copy discipline.** Headings stay ≤6 words. You may add a short clarifying subline (e.g. "Buy and sell ₹1 lakh worth of shares"), but **name every added or reworded line in your reply** so the user can delete it.

## The look (learned from 37 shipped frames, refined over 41 more)
**Full-screen (FSS):** white background with a light 52px grid. Decor sits around the edges and never touches text:
- a black hand-drawn loop doodle (often just left of the heading/hero)
- two solid rounded triangles (purple / green / orange / yellow)
- a grey 4-point star
- an orange dash on the left and a short green dash on the right

Optional: a soft grey blob behind a hero object, or a pale yellow glow circle (#fff6d6) behind title text.

**Type:** Inter, **weights 400/500/600/700 only**. 800 isn't embedded, so the export falls back and fails the diff.
- Heading: 72px semibold, dark ink #1d2228, ≤6 words, **one** coloured keyword or number (blue or orange).
- Optional short thick underline bar (yellow, or purple) under centred headings. Only use it under short centred headings; under a long heading it lands mid-word.
- Labels ≥34px, nothing under 26px.

**Colours:** blue #387fd1 · orange #f07339 · yellow #fec02d · green #4dab4d · purple #a77bf3 · table highlight #ffd064 · loss rows #fde6e6 with #d23c3c text · interest/cost notes #fde3d6 with #c4521f text.
- Pick 2–3 colours per frame.
- Same thing = same colour across a video (e.g. "you pay" = blue/orange, "Zerodha funds" = yellow, interest = blue, brokerage = yellow).

**Over the presenter (anchor):**
- No panels and no lower-third bars. White text with a soft shadow, key words **yellow**, placed in the plate's text zone (never over the face).
- Formats: big title + thin underline (blue segment at left); white lead line + yellow fact; yellow box with dark bold text; pills; speech bubble; pill rail; one-line caption across the bottom.
- Decor: only one orange triangle, one purple triangle and a white doodle (`zoDecor({dark:true,…})`).

## Pattern → recipe
| Beat | Recipe |
|---|---|
| Title / acronym card | small grey kicker ("MTF stands for") + yellow box (4px ink border, `box-shadow:0 12px 0 #1d2228`) with initials bold 700 and the rest 400 |
| Question title ("1. Do I understand…") | 240px number + ".", two 84px lines with the key phrase blue, pale yellow glow circle behind the right half, short green dash below (`qtitle()` helper) |
| Numbered 2–4 steps | `.step.blue/.orange/.yellow` (straight; no rotation on boxes holding text) |
| Slab / schedule table | `.card` + `.dots` + `table.zt`, highlighted row `tr.hl`; left-aligned heading with coloured keyword + `.sub` line; ≤5 cols × 6 rows; cells 44px with 30px padding |
| Chart + table example | left `.card` with an SVG line chart (gradient area fill, end-point circles), HTML axis labels, ₹ price tags with ink border, a "falls 10%" pill; right: stacked table rows (alternating #f6f7f9), loss rows red. Put the chart title above the top axis label so they don't collide |
| Split / funding bar | stock row (XYZ Ltd + outlined MTF tag) → two-colour bar with 4px ink border → icons + labels under each part → bracket SVG + "Total … ₹1,00,000"; optional interest tag sitting on the funded part |
| Cost comparison over time | one row per option: name + "Lower" tag, sub-label with the pricing, stacked horizontal bar (interest blue + brokerage yellow) scaled to the max, total at the bar end, legend at the bottom |
| Up vs down outcome | two panels split by a light divider; green bars rising from a baseline (left), orange bars hanging below one (right); value + caption above/below each bar, axis labels 34px and nowrap |
| One % stat | SVG donut (stroke-dasharray) with the % in an HTML div on top + 2-line caption at right |
| Allocation % | `zoPie(el,{size,pad,slices})` + centred heading + `.bar`; must sum to 100 |
| One number to remember | `.fbox.hero` (blue card, 220px ₹0) beside an illustration on a `.blob`; "before" values as faded `.fbox` with an orange strike bar |
| People / holders | two cards with a line-face icon in a coloured circle, label, big coloured value, grey note |
| Category / list of items | white cards with coloured bottom shadow (`box-shadow:0 10px 0 -2px <colour>`) + icon circle + 52px label, 2×2 grid |
| Checklist of charges | `.card` with rows of blue tick-circle SVG + 46px label, illustration on the left |
| Decision options | source card (orange border) → arrow → "Decide before you enter" + 2×2 numbered option boxes (badge `flex-shrink:0`, label 34px nowrap, box ≥450px) |
| Build list ("Will you…") | items stacked, the active one 84px with a blue chevron circle, the others 64px at .35 opacity |
| Recap ("five things") | heading + numbered list, badges in the 5 house colours, key phrase blue |
| Options / categories | stacked `.pill` (active colour, next yellow, rest `.faded`) |
| Things over time | `.axis` line, `.folder`s on it, captions below |
| Important note | `.note-tab` + `.note-body` (orange) |
| Big phrase | huge blue word + doodle + illustration + ink phrase |
| Over presenter | see Over-presenter recipes below |

Draw icons as simple inline SVG line art (2–6px ink strokes, flat blue/orange/yellow fills): wallet, money bag with ₹, calendar, coin stack, parcel, price tag, gift, balance scale, growth bars, warning triangle, down arrow, chevron, tick. No emoji, no real logos (Zerodha/Kite/Coin names in text are fine).

### Over-presenter recipes
Plates live in `zo-product-graphics/assets/plates/` (`plates.json` gives each plate's `face` box and text `zone`). Pick the plate by where the text goes:

| Text position | Plate | Shade div |
|---|---|---|
| Left half | `m2_right.jpg` (face on the right) | `left:0;width:1100px;linear-gradient(90deg,rgba(0,0,0,.45),transparent)` |
| Right half | `m2_left.jpg` | `left:900px;width:1020px;linear-gradient(90deg,transparent,rgba(0,0,0,.55))` |
| Bottom caption / bubble | `m2_centre.jpg` (zone y 760–1060) | `top:560px;height:520px;linear-gradient(180deg,transparent,rgba(0,0,0,.75))` |

The shade is a real named div (`Plate shade`), never `::after`.

- **Speech bubble:** a white rounded rect (radius 40, shadow), an SVG tail and a white `?` beside it. Small grey line ("How do I use it?") over a 92px blue bold line ("Should I use it?").
- **Big word:** 64px lead ("So"), a 240px yellow 700 word ("MTF"), then a 72px two-line ending, with green up-arrows above.
- **Caption line:** a yellow arrow-circle icon + 72px yellow sentence, with a 52px white follow-up line below, centred in the bottom zone.
- **Pill rail:** a white lead line, a thin white vertical rail with a blue active segment, and pills in a flex column (gap 34). The active pill is filled blue; the others have a #6fa3e0 outline on rgba(0,0,0,.25).
- **Title + relation:** a 96px title with a yellow keyword, a thin underline, then a pill → arrow → orange pill ("Longer hold → More interest"), with a 48px note below.

Plates are always **stand-ins** unless the user gives a still. Say so, and note it in `spec.json` notes.

## Layout rules that caught real bugs
- Give every label that sits in a fixed-width box `white-space:nowrap`, and make sure the box fits it. Badge/icon children get `flex-shrink:0`.
- Side-by-side labels under bars collide. Space the bars ≥250px apart and drop labels to 34px.
- Never use `line-height:0` or `<br>` to stack inline-block pills. Use a flex column with `gap`.
- A chart's top axis label collides with the chart title. Put the title ≥40px above the plot.
- Table row labels wrap ("Borrowed amount owed"). Use nowrap at 36px and widen the table.
- Decor: always pass explicit `doodleAt/tri1/tri2/starAt/dash1/dash2` per frame, and recheck that the doodle and dashes don't touch the heading, cards or table.
- Big numbers inside donuts/cards: size them to fit (e.g. 116px inside a 400px donut hole).

## Step 1: set up the kit (once per session)
- **Font:** check `fc-list | grep -qi "Inter"`. If it's missing, run `npm i @fontsource/inter` and add `@import "node_modules/@fontsource/inter/index.css";` atop zo.css.
- **Playwright + Chromium** are usually preinstalled (`python3 -c "import playwright"`).
- **Write the kit files.** Put zo.css, decor.js and extra.css in `src/`, and walker.js and flatten.py in the job folder. The fastest way is a small Python script that extracts each fenced block from this SKILL.md by its heading.
- **Reuse for the next video:** copy `src/{zo.css,decor.js,extra.css}`, `walker.js` and `flatten.py` into the new job folder.
- Use one job folder per video (`zo_<video>/src`, `gen/`, `out/`).

### zo.css
```css
/* ZO graphics kit — v2 white-grid look. 1920x1080. */
:root{--blue:#387fd1;--orange:#f07339;--yellow:#fec02d;--green:#4dab4d;--purple:#a77bf3;
--ink:#1d2228;--grey:#8a8f96;--line:#ececec;--blob:#f2f2f2;--hl:#ffd064;--tint:#fff3d6;}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1920px;height:1080px;overflow:hidden}
body{font-family:Inter,'Inter Display',sans-serif;color:var(--ink);position:relative;background:#fff}
.grid{position:absolute;inset:0;background:
 radial-gradient(ellipse 46% 52% at 50% 50%,#fff 55%,rgba(255,255,255,0) 100%),
 repeating-linear-gradient(0deg,var(--line) 0 2px,transparent 2px 52px),
 repeating-linear-gradient(90deg,var(--line) 0 2px,transparent 2px 52px),#fff}
.plate{position:absolute;inset:0;background-size:cover;background-position:center}
.plate::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.35),rgba(0,0,0,0) 55%)}
.abs{position:absolute}
.center{position:absolute;left:50%;transform:translateX(-50%)}
/* headings */
.h{font-size:72px;font-weight:600;letter-spacing:-1px;line-height:1.1;white-space:nowrap}
.h .b,.b{color:var(--blue)} .h .o,.o{color:var(--orange)} .h .y,.y{color:var(--yellow)} .g{color:var(--green)}
.sub{font-size:40px;font-weight:400;margin-top:6px}
.bar{height:9px;width:110px;border-radius:9px;background:var(--yellow);margin:14px auto 0}
.bar.purple{background:var(--purple)} .bar.orange{background:var(--orange)} .bar.green{background:var(--green)}
/* text sizes */
.t36{font-size:36px}.t44{font-size:44px}.t56{font-size:56px}.big{font-size:220px;font-weight:700;line-height:1}
.w5{font-weight:500}.w6{font-weight:600}.w7{font-weight:700}
/* pills */
.pill{display:inline-block;border-radius:999px;padding:18px 54px;font-size:56px;font-weight:500;color:#fff;white-space:nowrap}
.pill.blue{background:var(--blue)}.pill.orange{background:var(--orange)}.pill.yellow{background:var(--yellow);color:var(--ink)}
.pill.green{background:var(--green)}.pill.purple{background:var(--purple)}.pill.faded{opacity:.45}
/* grey blob behind hero */
.blob{position:absolute;background:var(--blob);border-radius:46% 54% 60% 40%/50% 42% 58% 50%;z-index:0}
/* steps (tilted stickers) */
.step{position:relative;width:740px;min-height:150px;border-radius:30px;display:flex;align-items:center;gap:34px;
 padding:20px 60px 20px 36px;font-size:34px;line-height:1.3;border:3px solid var(--ink);box-shadow:0 8px 0 var(--ink)}
.step .n{font-size:96px;font-weight:500;min-width:60px}
.step::after{content:"";position:absolute;right:22px;top:50%;width:18px;height:18px;border-radius:50%;background:#fff;border:2px solid var(--ink)}
.step.blue{background:var(--blue);color:#fff}.step.orange{background:var(--orange);color:#fff}.step.yellow{background:var(--yellow)}
/* card / window */
.card{background:#fff;border:2px solid #cfd2d6;border-radius:18px;box-shadow:0 10px 0 -2px var(--yellow)}
.card.plain{box-shadow:none}
.dots{position:absolute;top:16px;left:22px;display:flex;gap:7px}
.dots i{width:11px;height:11px;border-radius:50%;background:var(--orange)} .dots i:nth-child(n+2){background:var(--yellow)}
/* table */
table.zt{border-collapse:collapse;width:100%;font-size:30px}
.zt th{font-size:38px;font-weight:600;padding:26px 20px 10px;text-align:center}
.zt th small{display:block;font-size:20px;font-weight:400;color:#444;margin-top:8px}
.zt td{padding:16px 20px;text-align:center}
.zt td+td,.zt th+th{border-left:2px solid #e3e3e3}
.zt tr.hl td{background:var(--hl);font-weight:600;font-size:34px}
.zt.left td:first-child,.zt.left th:first-child{text-align:left}
/* note */
.note-tab{background:#fff;border:2px solid var(--ink);border-radius:14px 14px 0 0;padding:14px 40px;font-size:40px;font-weight:600}
.note-body{background:var(--orange);color:#fff;clip-path:polygon(0 0,100% 0,103% 100%,-3% 100%);padding:70px 80px;font-size:48px;line-height:1.35;border-radius:0 0 18px 18px}
/* check list */
.check{display:flex;align-items:center;gap:26px;font-size:56px;margin:18px 0}
.check::before{content:"";width:46px;height:30px;border-left:9px solid var(--green);border-bottom:9px solid var(--green);transform:rotate(-45deg) translateY(-8px)}
.check.dim{opacity:.35}
/* circles */
.circle{border-radius:50%;display:flex;align-items:center;justify-content:center;text-align:center;color:#fff;font-weight:500;border:2px solid rgba(0,0,0,.25)}
/* folder */
.folder{position:relative;width:200px;height:120px;border-radius:6px 10px 10px 10px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:34px;font-weight:500}
.folder::before{content:"";position:absolute;top:-16px;left:0;width:80px;height:24px;border-radius:6px 14px 0 0;background:inherit;filter:brightness(.92)}
.folder.orange{background:var(--orange)}.folder.blue{background:var(--blue)}.folder.yellow{background:var(--yellow);color:var(--ink)}
/* timeline axis */
.axis{position:absolute;height:4px;background:var(--ink);border-radius:4px}
.axis::before,.axis::after{content:"";position:absolute;top:-6px;width:16px;height:16px;border-radius:50%;background:var(--blue)}
.axis::before{left:-6px}.axis::after{right:-6px}
/* circled text (hand-drawn ring) */
.ring{position:relative;display:inline-block;padding:10px 30px;font-size:52px;font-weight:500}
.ring::before{content:"";position:absolute;inset:0;border:3px solid var(--orange);border-radius:50%;transform:rotate(-3deg)}
.ring::after{content:"";position:absolute;inset:-6px 4px 6px -4px;border-top:3px solid var(--orange);border-radius:50%;transform:rotate(2deg)}
/* presenter overlay text */
.ov{color:#fff;text-shadow:0 4px 18px rgba(0,0,0,.45);font-weight:600}
.ov .y{color:var(--yellow)}
.ov-title{font-size:150px;letter-spacing:-2px;line-height:1}
.ov-line{height:4px;background:linear-gradient(90deg,var(--blue) 0 18%,rgba(255,255,255,.8) 18%);border-radius:4px;margin-top:14px;position:relative}
.ybox{text-shadow:none;background:var(--yellow);color:var(--ink);border-radius:18px;padding:18px 44px;font-size:76px;font-weight:700;line-height:1.1;text-align:center}
/* coin-style fund card */
.fund{width:600px;background:#fff;border-radius:28px;padding:36px;font-size:24px;color:var(--ink);box-shadow:0 10px 40px rgba(0,0,0,.25)}
.fund .tag{position:absolute;top:-56px;left:0;background:var(--yellow);border-radius:10px 10px 0 0;padding:8px 18px;font-size:30px;font-weight:600}
.fund .stats{background:#f4f5f7;border-radius:16px;padding:22px 24px;display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:22px 0}
.fund .stats span{display:block;color:#777;font-size:19px}.fund .stats b{font-size:28px}
.fund .btn{background:#15181c;color:#fff;border-radius:12px;text-align:center;padding:20px;font-weight:600;font-size:24px}
.chip{display:inline-block;background:#e4f6ea;color:#1f8a4c;border-radius:20px;padding:4px 14px;font-size:18px}
/* layered-export overrides: plain grid like the Bulletin files */
.grid{background-color:#fff;background-image:linear-gradient(rgb(242,242,242) 1.5px,transparent 1.5px),linear-gradient(90deg,rgb(242,242,242) 1.5px,transparent 1.5px);background-size:52px 52px;background-position:-6px -6px}
#decor,#content{position:absolute;inset:0}
.dots{position:absolute;top:16px;left:22px;display:flex;gap:7px}
.dots>div{width:11px;height:11px;border-radius:50%;background:var(--yellow)} .dots>div:first-child{background:var(--orange)}
```

### decor.js
```js
// Static-ready decor: appends named layers into #decor (or body).
function zoDecor(o={}){
 const host=document.getElementById('decor')||document.body;
 const dark=!!o.dark, s=o.seed||1, r=(i)=>{const x=Math.sin(s*97+i*13.7)*1e4;return x-Math.floor(x)};
 const add=(name,html,css)=>{const d=document.createElement('div');d.setAttribute('data-name',name);d.style.position='absolute';d.innerHTML=html;Object.assign(d.style,css);host.appendChild(d)};
 const doodle=c=>`<svg width="150" height="90" viewBox="0 0 150 90"><path d="M6 40c18-26 26-36 18-34-8 2-12 34 6 34s20-24 12-22-6 26 12 26 18-22 12-20-4 26 14 26 18-18 12-16-2 22 18 30" fill="none" stroke="${c}" stroke-width="4" stroke-linecap="round"/></svg>`;
 const tri=(c,rot,sz)=>`<svg width="${sz}" height="${sz}" viewBox="0 0 40 40"><path d="M8 6 L36 20 L8 34 Z" fill="${c}" stroke="${c}" stroke-width="5" stroke-linejoin="round" transform="rotate(${rot} 20 20)"/></svg>`;
 const star=`<svg width="70" height="70" viewBox="0 0 40 40"><path d="M20 2 L24 16 L38 20 L24 24 L20 38 L16 24 L2 20 L16 16Z" fill="#c9cbcf" transform="rotate(20 20 20)"/></svg>`;
 const cols=['#a77bf3','#4dab4d','#f07339','#fec02d'];
 if(o.doodle!==false) add('Squiggle',doodle(dark?'#fff':'#1d2228'),o.doodleAt||{left:'210px',top:'110px'});
 const c1=cols[Math.floor(r(1)*4)], c2=cols[(Math.floor(r(1)*4)+1+Math.floor(r(2)*3))%4];
 add('Triangle',tri(dark?'#f07339':c1,Math.floor(r(3)*360),dark?60:56),o.tri1||{right:'250px',top:'150px'});
 add('Triangle',tri(dark?'#a77bf3':c2,Math.floor(r(4)*360),dark?64:80),o.tri2||{left:'230px',bottom:'170px'});
 if(!dark){
  if(o.star!==false) add('Sparkle',star,o.starAt||{right:'230px',bottom:'130px'});
  add('Dash','<div style="width:64px;height:10px;border-radius:10px;background:#f07339"></div>',o.dash1||{left:'180px',top:'46%'});
  add('Dash','<div style="width:58px;height:6px;border-radius:6px;background:#4dab4d"></div>',o.dash2||{right:'170px',top:'20%'});
 }
}
// Pie: zoPie(el,{size,pad,slices:[{v,color,label,stroke,text}]}) — SVG slices + HTML % and labels (exporter-safe).
function zoPie(el,o){const R=o.size/2,cx=R+o.pad,cy=R+o.pad,W=o.size+2*o.pad;let a=-90,svg='',lab='';
 const P=(ang,rr)=>[cx+rr*Math.cos(ang*Math.PI/180),cy+rr*Math.sin(ang*Math.PI/180)];
 const T=(x,y,txt,fs,col,anchor,name)=>{const tx=anchor==='start'?'0':anchor==='end'?'-100%':'-50%';
  return `<div data-name="${name}" style="position:absolute;left:${x}px;top:${y}px;transform:translate(${tx},-50%);white-space:nowrap"><div style="font-size:${fs}px;font-weight:500;color:${col}">${txt}</div></div>`};
 o.slices.forEach((s,i)=>{const sw=s.v*3.6,[x1,y1]=P(a,R),[x2,y2]=P(a+sw,R),m=a+sw/2;
  svg+=`<path d="M${cx} ${cy}L${x1} ${y1}A${R} ${R} 0 ${sw>180?1:0} 1 ${x2} ${y2}Z" fill="${s.color}" stroke="${s.stroke||'#fff'}" stroke-width="2"/>`;
  const big=s.v>=30,sm=s.v<8,[tx,ty]=P(m,R*(big?.55:sm?.8:.66));
  lab+=T(tx,ty,s.v+'%',big?110:sm?40:56,s.text||'#fff','middle','Value / '+(s.label||i+1));
  if(s.label){const[lx,ly]=P(m,R+50),c=Math.cos(m*Math.PI/180);lab+=T(lx,ly,s.label,44,'#1d2228',c>0.2?'start':c<-0.2?'end':'middle','Label / '+s.label)}
  a+=sw});
 el.style.width=W+'px';el.style.height=W+'px';
 el.innerHTML=`<svg data-name="Slices" style="position:absolute;left:0;top:0" width="${W}" height="${W}" viewBox="0 0 ${W} ${W}">${svg}</svg>`+lab}
```

### extra.css
```css
.pos{background:#fff;border:3px solid var(--blue);border-radius:22px;padding:30px 40px;box-shadow:0 10px 0 -2px var(--blue)}
.row{display:flex;align-items:center;justify-content:space-between;gap:30px}
.tk{display:flex;align-items:center;gap:18px;font-weight:700;font-size:44px;letter-spacing:.5px}
.ic{width:56px;height:56px;border-radius:50%;background:var(--blue);display:flex;align-items:center;justify-content:center}
.lbl{font-size:36px;color:#5b6168}
.up{color:var(--green);font-weight:600}
.tagc{display:inline-block;border-radius:12px;padding:8px 22px;font-size:34px;font-weight:600}
.watch{background:#fff;border:2px solid #cfd2d6;border-radius:18px;padding:30px 40px}
.cursor{position:absolute;width:60px}
.fbox{border-radius:24px;padding:30px 40px;text-align:center;background:#fff;border:3px solid #cfd2d6;min-width:300px}
.fbox b{display:block;font-size:72px;font-weight:700;letter-spacing:-1px}
.fbox span{font-size:36px;color:#5b6168}
.fbox.hero{background:var(--blue);border-color:var(--blue);color:#fff}.fbox.hero span{color:#e3edf9}
.op{font-size:76px;font-weight:500;color:var(--ink)}
.barrow{margin:40px 0}
.barrow .row{font-size:44px;font-weight:600;margin-bottom:18px}
.track{height:64px;border-radius:40px;background:#eef0f2;position:relative;overflow:hidden}
.fill{position:absolute;left:0;top:0;bottom:0;border-radius:40px}
```

## Step 2: write all frames from one generator
Don't hand-write each HTML file. Keep one `gen/make.py` that writes every source file into `src/`, re-run it after every fix, and make fixes as exact string replacements in the generator (assert each old string exists). When you start a new video, copy only the helper section (everything above the first frame); slicing by line count once cut a string in half.

```python
OUT='/home/claude/zo_<video>/src/'
HEAD='''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="zo.css"><link rel="stylesheet" href="extra.css"><script src="decor.js"></script></head><body>
<div class="grid" data-name="Background grid" style="position:absolute;inset:0"></div>
<div id="decor" data-name="Decor"></div>
<div id="content" data-name="Content">
'''
def fss(name,body,decor):   # decor = JS object literal string for zoDecor
    open(OUT+name+'.html','w').write(HEAD+body+'\n<script>zoDecor('+decor+');</script>\n</div></body></html>\n')
def ov(name,plate,shade,body,decor):   # over-presenter; shade = inline css of the shade div
    open(OUT+name+'.html','w').write(f'''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="zo.css"><link rel="stylesheet" href="extra.css"><script src="decor.js"></script></head><body>
<img data-name="Presenter plate" src="{plate}" style="position:absolute;left:0;top:0;width:1920px;height:1080px;object-fit:cover">
<div data-name="Plate shade" style="position:absolute;{shade}"></div>
<div id="content" data-name="Content">{body}</div><div id="decor" data-name="Decor"></div>
<script>zoDecor({decor});</script></body></html>
''')
def heading(parts,top=120,center=True,bar=True):   # parts=[('text ',''),('keyword','b')]
    spans=''.join(f'<span class="{c}">{t}</span>' if c else f'<span>{t}</span>' for t,c in parts)
    b='<div class="bar" data-name="Yellow underline"></div>' if bar else ''
    if center: return f'<div class="center" data-name="Heading" style="top:{top}px;text-align:center"><div class="h" data-name="Heading text">{spans}</div>{b}</div>'
    return f'<div class="abs" data-name="Heading" style="left:300px;top:{top}px"><div class="h" data-name="Heading text">{spans}</div></div>'
DOTS='<div class="dots" data-name="Window dots"><div data-name="Dot"></div><div data-name="Dot"></div><div data-name="Dot"></div></div>'
def tick(s=56,c='#387fd1'):
    return f'<svg data-name="Tick" width="{s}" height="{s}" viewBox="0 0 60 60"><circle cx="30" cy="30" r="30" fill="{c}"/><path d="M17 31 L26 40 L44 21" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
```
Decor call example: `"{seed:4,doodleAt:{left:'200px',top:'280px'},tri1:{right:'130px',top:'170px'},tri2:{left:'170px',bottom:'110px'},starAt:{right:'130px',bottom:'90px'},dash1:{left:'120px',top:'60%'},dash2:{right:'130px',top:'45%'}}"`. Over the presenter: `"{seed:1,dark:true,doodleAt:{...},tri1:{...},tri2:{...}}"`.

Source rules (the exporter depends on them):
- Body = grid + `#decor` + `#content` + the `zoDecor(...)` script, or the plate + shade + `#content` + `#decor` over the presenter.
- Put `data-name` on every meaningful block: Heading, Heading text, Yellow underline, `Card / <x>`, `Row / <x>`, `Pill / <text>`, `Tag / <text>`, `Icon / <x>`, `Bar / <x>`, `Option / <x>`. Unnamed wrappers are flattened away.
- A coloured keyword is its own `<span>`, so it becomes its own text layer. Text inside a pill/tag/box goes in a child `<div>`.
- These break the export:
  - `::before/::after`
  - `<text>` inside SVG (overlay an HTML div instead)
  - transforms other than translate
  - `scale`/`zoom`
- Never tilt anything that holds text; tilt only inside an SVG. SVG `<defs>` gradients are fine.
- Use curly ’ “ ”, single spaces, and the true minus − for negative %.
- Dashed borders export as pictures; use them only for decoration (dashed SVG strokes are fine).
- `.step`, `.check`, `.folder`, `.axis`, `.ring` and `.plate` draw parts with pseudo-elements. When you use them, add those parts as real named child divs.
- Window dots: `DOTS`.

## Step 3: plates and stills
For over-presenter frames, copy plates from `zo-product-graphics/assets/plates/` into `src/` (e.g. `plate.jpg`, `plate_centre.jpg`, `plate_left.jpg`), and read `plates.json` for `face` and `zone` before placing text. If the user gives a still, use it instead. Otherwise label the frame as a stand-in in the reply and in the spec notes.

## Step 4: check the design
1. Run `python3 flatten.py src out/<Video>_layers`. It renders `out/src_<name>.png` for each source and exports the layered set.
2. Build 2×3 contact sheets at 960×540 per tile (PIL) into the scratchpad, covering only the new batch, and view each one once.
3. Check that:
   - decor doesn't touch text
   - nothing is cut off, overflowing its box or wrapping unexpectedly
   - each heading has one coloured keyword
   - text sizes are right
   - numbers match the script exactly
4. Fix in the generator, re-run, and view a 2×2 sheet of only the fixed frames. For tight spots (option boxes, table labels), crop the area at full size and read it.

## Step 5: export in the layered Bulletin format (always)
```
<Video>_layers/
  html/<NN>_<Section>_<What-it-shows>.html   self-contained, 1920x1080, Inter embedded, no scripts/classes
  png/<same name>.png                         rendered from that html
  layers/<same name>.json                     layer tree (group/box/text/svg/img, absolute x,y,w,h, styles)
  LAYERS.txt  README.txt  spec.json
```
Name files `NN_Section_What-it-shows` (Section = Intro, Q1…Q5, Delivery, DP, AMC, MTF, Closing…; over-presenter frames carry `TOS` in the name).

**Diff check.** For each frame, compare `png/` with `out/src_<name>.png` (ImageChops, threshold 60, count changed pixels). A few hundred to ~2,500 pixels is sub-pixel text placement. Confirm by cropping the bbox once. Shapes that move or vanish mean a style the exporter missed (pseudo-element, 800 weight, rotation); fix the source.

**Fonts.** `flatten.py` embeds Inter 400/500/600/700 TTFs, which it finds in `zo-product-graphics/fonts`, `./fonts` or `$INTER_DIR`.

**spec.json:**
- `video`
- `frames:[{id,name,section,mode:"FSS"|"Over presenter",vo,html,png,layers,text:[…]}]`. Fill `text` by walking the layers JSON for text nodes, and `vo` from the storyboard.
- `skipped:[{id,beat,reason}]`
- `notes:[…]` for stand-in plates, build-state frames and example numbers.

**README.txt:** the folder layout, the frame range, which frames are over the presenter (stand-in plates), shared templates, and skipped beats.

Then delete the `src_*.png` check renders, zip the folder (re-zip the full set after every batch), and send each new PNG plus the zip with `SendUserFile`.

### walker.js
```js
(() => {
const R = v => Math.round(v*100)/100;
const visBox = cs => {
  const bg = cs.backgroundColor, hasBg = bg && !/rgba\(.*, 0\)$/.test(bg) && bg!=='transparent';
  const hasImg = cs.backgroundImage && cs.backgroundImage!=='none';
  const bw = ['Top','Right','Bottom','Left'].some(s=>parseFloat(cs['border'+s+'Width'])>0 && cs['border'+s+'Style']!=='none');
  const sh = cs.boxShadow && cs.boxShadow!=='none';
  return hasBg||hasImg||bw||sh;
};
const opa = el => { let o=1; for(let e=el;e&&e!==document.documentElement;e=e.parentElement){o*=parseFloat(getComputedStyle(e).opacity)} return R(o); };
const boxLeaf = (el,name) => {
  const cs=getComputedStyle(el), r=el.getBoundingClientRect();
  const sides=['Top','Right','Bottom','Left'];
  const bw=sides.some(s=>parseFloat(cs['border'+s+'Width'])>0&&cs['border'+s+'Style']!=='none');
  return {type:'box',name,x:R(r.left),y:R(r.top),w:R(r.width),h:R(r.height),bg:cs.backgroundColor,
    bgimg:cs.backgroundImage,bgsize:cs.backgroundImage!=='none'?cs.backgroundSize:'',bgpos:cs.backgroundPosition,bgrepeat:cs.backgroundRepeat,
    radius:(()=>{const c=[cs.borderTopLeftRadius,cs.borderTopRightRadius,cs.borderBottomRightRadius,cs.borderBottomLeftRadius].map(v=>v.split(' '));
      const h=c.map(v=>v[0]),v=c.map(v=>v[1]||v[0]); return h.join(' ')===v.join(' ')?h.join(' '):h.join(' ')+' / '+v.join(' ');})(),
    border:bw?sides.map(s=>`${cs['border'+s+'Width']} ${cs['border'+s+'Style']} ${cs['border'+s+'Color']}`):null,
    shadow:cs.boxShadow==='none'?'':cs.boxShadow,opacity:opa(el)};
};
const textLeaves = (node) => {
  const el=node.parentElement, cs=getComputedStyle(el), out=[];
  const s=node.textContent; const re=/\S+/g; let m; const words=[];
  while((m=re.exec(s))){const rg=document.createRange();rg.setStart(node,m.index);rg.setEnd(node,m.index+m[0].length);
    const rs=[...rg.getClientRects()].filter(q=>q.width>0); if(!rs.length) continue;
    const q=rs[0]; words.push({t:m[0],l:q.left,t0:q.top,r:Math.max(...rs.map(z=>z.right)),b:q.bottom});}
  const lines=[]; for(const w of words){const L=lines.find(l=>Math.abs(l.t0-w.t0)<3); if(L){L.ws.push(w)} else lines.push({t0:w.t0,ws:[w]})}
  for(const L of lines){ let txt=L.ws.map(w=>w.t).join(' '); if(cs.textTransform==='uppercase') txt=txt.toUpperCase();
    const l=Math.min(...L.ws.map(w=>w.l)), r=Math.max(...L.ws.map(w=>w.r)), t=Math.min(...L.ws.map(w=>w.t0)), b=Math.max(...L.ws.map(w=>w.b));
    out.push({type:'text',name:txt,text:txt,x:R(l),y:R(t),w:R(r-l+2),h:R(b-t),mono:false,size:R(parseFloat(cs.fontSize)),weight:cs.fontWeight,
      style:'normal',color:cs.color,ls:cs.letterSpacing==='normal'?0:R(parseFloat(cs.letterSpacing)),tt:'none',deco:'',
      shadow:cs.textShadow==='none'?'':cs.textShadow,stroke:'',opacity:opa(el)});}
  return out;
};
const warn=[];
const walk = (el, defName) => {
  // returns list of nodes (a group if named, else flattened children)
  const cs=getComputedStyle(el); if(cs.display==='none'||cs.visibility==='hidden') return [];
  const name=el.getAttribute('data-name');
  if(el.tagName.toLowerCase()==='svg'){
    if(el.querySelector('text')) warn.push('svg text in '+(name||'svg'));
    const r=el.getBoundingClientRect(); const c=el.cloneNode(true);
    if(!c.getAttribute('viewBox')) c.setAttribute('viewBox',`0 0 ${r.width} ${r.height}`);
    ['class','style','data-name','width','height'].forEach(a=>c.removeAttribute(a));
    c.setAttribute('width','100%');c.setAttribute('height','100%');c.setAttribute('preserveAspectRatio','none');
    return [{type:'svg',name:name||'Shapes',x:R(r.left),y:R(r.top),w:R(r.width),h:R(r.height),opacity:opa(el),svg:c.outerHTML}];
  }
  if(el.tagName==='IMG'){const r=el.getBoundingClientRect();
    return [{type:'img',name:name||'Image',x:R(r.left),y:R(r.top),w:R(r.width),h:R(r.height),src:el.getAttribute('src'),fit:cs.objectFit||'fill',opacity:opa(el)}];}
  const kids=[];
  if(visBox(cs)) kids.push(boxLeaf(el, name && !hasContent(el) ? name : 'Background'));
  for(const ch of el.childNodes){
    if(ch.nodeType===3){ if(ch.textContent.trim()) kids.push(...textLeaves(ch)); }
    else if(ch.nodeType===1 && !['SCRIPT','STYLE','DEFS'].includes(ch.tagName)) kids.push(...walk(ch));
  }
  if(name && !(kids.length===1 && kids[0].type==='box' && kids[0].name===name)) {
    if(!kids.length) return [];
    if(kids.length===1 && kids[0].type!=='group' && !name.includes('/')) { if(kids[0].type!=='text') kids[0].name=name; return [kids[0]]; }
    return [{type:'group',name,children:kids}];
  }
  return kids;
};
function hasContent(el){return el.textContent.trim().length>0 || el.querySelector('svg,div,span,img')}
const top=[];
for(const ch of document.body.children){ if(ch.tagName!=='SCRIPT') top.push(...walk(ch)); }
return {tree:top,warn};
})()
```

### flatten.py
```python
import sys, os, json, re, base64, glob
from playwright.sync_api import sync_playwright
_cands=([os.environ['INTER_DIR']] if os.environ.get('INTER_DIR') else [])+glob.glob('/mnt/skills/plugins/zo-product-graphics/fonts')+glob.glob('/mnt/skills/*/zo-product-graphics/fonts')+glob.glob('/root/.claude/skills/synced/*/zo-product-graphics/fonts')+['./fonts']
FONTDIR=next(d for d in _cands if os.path.exists(f'{d}/Inter-Regular.ttf'))
FONTS=''.join(f"@font-face{{font-family:Inter;font-weight:{w};src:url(data:font/ttf;base64,{base64.b64encode(open(f'{FONTDIR}/Inter-{n}.ttf','rb').read()).decode()}) format('truetype')}}" for w,n in [(400,'Regular'),(500,'Medium'),(600,'SemiBold'),(700,'Bold')])
WALK=open('walker.js').read()
def slug(s):
    s=re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-'); return s or 'layer'
def bbox(n):
    if n['type']=='group':
        bs=[bbox(c) for c in n['children']]
        return (min(b[0] for b in bs),min(b[1] for b in bs),max(b[2] for b in bs),max(b[3] for b in bs))
    return (n['x'],n['y'],n['x']+n['w'],n['y']+n['h'])
def dedupe(children):
    seen={}
    for c in children:
        k=c['name']; seen[k]=seen.get(k,0)+1
        if seen[k]>1: c['name']=f"{k} {seen[k]}"
        if c['type']=='group': dedupe(c['children'])
R=lambda v: round(v,2)
def emit(n,px,py,ids,ind):
    sp='  '*ind
    def uid(name):
        b=slug(name); i=b; k=2
        while i in ids: i=f'{b}-{k}'; k+=1
        ids.add(i); return i
    if n['type']=='group':
        x0,y0,x1,y1=bbox(n)
        s=f'{sp}<div data-name="{esc(n["name"])}" id="{uid(n["name"])}" data-type="group" style="position:absolute;left:{R(x0-px)}px;top:{R(y0-py)}px;width:{R(x1-x0)}px;height:{R(y1-y0)}px">\n'
        for c in n['children']: s+=emit(c,x0,y0,ids,ind+1)
        return s+f'{sp}</div>\n'
    pos=f'position:absolute;left:{R(n["x"]-px)}px;top:{R(n["y"]-py)}px;width:{n["w"]}px;height:{n["h"]}px;'
    op=f'opacity:{n["opacity"]};' if n['opacity']<1 else ''
    if n['type']=='text':
        st=pos+f'line-height:{n["h"]}px;font-family:Inter,sans-serif;font-size:{n["size"]}px;font-weight:{n["weight"]};font-style:normal;color:{n["color"]};white-space:pre;'
        if n['ls']: st+=f'letter-spacing:{n["ls"]}px;'
        if n['shadow']: st+=f'text-shadow:{n["shadow"]};'
        return f'{sp}<div data-name="Text / {esc(n["name"])}" id="{uid(n["name"])}" data-type="text" style="{st}{op}">{esc(n["text"])}</div>\n'
    if n['type']=='box':
        st=pos+f'background-color:{n["bg"]};border-radius:{n["radius"]};'
        if n['bgimg']!='none': st+=f'background-image:{n["bgimg"]};background-size:{n["bgsize"]};background-position:{n["bgpos"]};background-repeat:{n["bgrepeat"]};'
        if n['border']:
            for side,b in zip(['top','right','bottom','left'],n['border']): st+=f'border-{side}:{b};'
        if n['shadow']: st+=f'box-shadow:{n["shadow"]};'
        return f'{sp}<div data-name="{esc(n["name"])}" id="{uid(n["name"])}" data-type="shape" style="{st}{op}"></div>\n'
    if n['type']=='img':
        import mimetypes
        p=os.path.join(SRC,n['src']); mt=mimetypes.guess_type(p)[0] or 'image/jpeg'
        data=base64.b64encode(open(p,'rb').read()).decode()
        return f'{sp}<img data-name="{esc(n["name"])}" id="{uid(n["name"])}" data-type="image" src="data:{mt};base64,{data}" style="{pos}object-fit:{n["fit"]};{op}">\n'
    if n['type']=='svg':
        return f'{sp}<div data-name="{esc(n["name"])}" id="{uid(n["name"])}" data-type="vector" style="{pos}{op}">{n["svg"]}</div>\n'
def esc(s): return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')
def jsonify(n):
    if n['type']=='group': return {'type':'group','name':n['name'],'children':[jsonify(c) for c in n['children']]}
    d={k:v for k,v in n.items() if k!='svg'}; return d
def outline(n,ind,lines):
    sp='  '*ind
    if n['type']=='group':
        lines.append(f'{sp}▸ {n["name"]}'); [outline(c,ind+1,lines) for c in n['children']]
    else: lines.append(f'{sp}· {n["name"]}  [{ {"box":"box","text":"text","svg":"svg","img":"img"}[n["type"]] }]')
def main(src_dir,out_dir):
    global SRC; SRC=src_dir
    for d in ['html','png','layers']: os.makedirs(f'{out_dir}/{d}',exist_ok=True)
    outl=[]; frames=[]
    with sync_playwright() as p:
        b=p.chromium.launch(); pg=b.new_page(viewport={'width':1920,'height':1080})
        for f in sorted(glob.glob(f'{src_dir}/[0-9]*.html')):
            name=os.path.basename(f)[:-5]
            pg.goto('file://'+os.path.abspath(f)); pg.wait_for_timeout(300)
            pg.screenshot(path=f'{out_dir}/../src_{name}.png')
            res=pg.evaluate(WALK)
            for w in res['warn']: print('WARN',name,w)
            tree=res['tree']; dedupe(tree)
            ids=set()
            body=''.join(emit(n,0,0,ids,1) for n in tree)
            html=f'<!doctype html>\n<html><head><meta charset="utf-8"><title>{name}</title>\n<style>{FONTS}\n*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:1920px;height:1080px;overflow:hidden;background:#fff}}body{{position:relative;-webkit-font-smoothing:antialiased}}</style></head>\n<body data-name="Frame {name}">\n{body}</body></html>\n'
            open(f'{out_dir}/html/{name}.html','w').write(html)
            root={'type':'group','name':f'Frame {name}','children':[jsonify(n) for n in tree]}
            json.dump(root,open(f'{out_dir}/layers/{name}.json','w'),indent=1,ensure_ascii=False)
            outl.append(f'▸ Frame {name}'); [outline(n,1,outl) for n in tree]; outl.append('')
            frames.append(name)
        for name in frames:
            pg.goto('file://'+os.path.abspath(f'{out_dir}/html/{name}.html')); pg.wait_for_timeout(300)
            pg.screenshot(path=f'{out_dir}/png/{name}.png')
        b.close()
    open(f'{out_dir}/LAYERS.txt','w').write('\n'.join(outl))
    return frames
if __name__=='__main__':
    print(main(sys.argv[1],sys.argv[2]))
```

## Reply format after each batch
Give the user:
- what each frame shows, by number
- any copy you added or reworded
- beats you skipped (screen captures) and why
- which frames use stand-in plates
- one line on what comes next, e.g. "Next numbered graphics are 10, 12, 13… should I go ahead?"

Don't recap the build steps.