# Patterns from M4 · Episode 2 "Futures Terminology" (31 graphics the team approved)

Look at `m4_futures_ep2_sheet_1.jpg` and `m4_futures_ep2_sheet_2.jpg` once. This is the look for Futures (and any OSA-heavy
episode): every heading is the **window heading**, every OSA block a frosted light card with dark words, so it reads on the
dark studio footage. Use these patterns instead of plain text cards; give most beats a second state (`_b`).

| beat in the script | frame | spec |
|---|---|---|
| episode opens with the terms it will cover | OSA list with a prop icon per term | `osa` `kind:list`, items with `icon: prop:…` |
| a term is defined ("Spot price is…") | OSA quote, heading = the term | `osa` `kind:quote` |
| a question to the viewer, then the answer | OSA text, `_b` adds the answer with `==No==:` / `==The exchange==:` | `osa` `kind:text`, two states |
| "which of these is right?" | quiz, `_b` reveals | `quiz` (timer 5 → answer) |
| two definitions to pair up | match the following, `_b` reveals | `match` (timer 5 → pairs) |
| near / next / far month, roll-over | month cards, states for expiry and the new month | `monthcards` (`active`, `expired`, `new`) |
| a ticker / abbreviation decoded ("FUT") | magnified word, `_b` without the lens | `magnify` |
| lot size, multiples | OSA tags: `1 lot · 750 qty`, `2 lots · 1,500 qty` | `osa` `kind:tags` |
| contract value / margin worked out | OSA calc: lot size × price = value; `_b` adds "Required ₹1,28,000" | `osa` `kind:calc` |
| an everyday analogy (quick-delivery app minimum quantity) | phone UI beside the presenter + an OSA tag card | `phone` / `img` + `osa` `kind:tags` |
| Kite order window (qty, price) | screen capture, or `window` element for a mock | storyboard decides |
| recap of the terms | OSA list with `checks: true` | `osa` `kind:list` |
| "questions that remain" | numbered OSA list, `active` highlights the one being read | `osa` `kind:list`, no icons, `active` |
| series / next episode | episode cards on the arc | `episodes` |

Copy: short English, the term as the heading, numbers exactly from the script (750, ₹975.15, ₹7,31,362.50).
