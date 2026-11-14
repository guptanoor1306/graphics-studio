# Plates index: textless frames from V1–V3, reusable as backgrounds

Finished frames from the three episodes with their on-screen text removed. They ship tiled four to a sheet in `assets/plate_sheets/` (the skill upload allows max 200 files and no nested archives). `build.py` cuts them out automatically the first time a spec uses `asset:plates/<file>`. To look at plates before writing the spec, run `python3 $K/scripts/build.py --unpack-plates`, which prints the folder. Use one as `bg` or as an image layer (`asset:plates/<file>`) whenever a new beat happens in the same kind of set: a Kerala house, a jeweller counter, the township plaza, a builder office, a Khasi village, the wooden map, a govt building with placards, and so on. Add new text and tags with kit layers. Plates are 1280×720 (they scale to the frame).

"Soft patches" = text was painted out over scenery. Place new text in the same spot to cover them.

| Plate | Section | What it shows (from the gold corpus) | Quality |
|---|---|---|---|
| `plates/v1_1-2.jpg` | Intro | three Arjuns side by side on the paper-sky set: Andhra (white shirt + veshti), Kerala (red shirt + mundu), Meghalaya (red-gold turban, black jacket, red dhoti, bead necklace) | clean |
| `plates/v1_10-11.jpg` | Ch-1 Andhra | the same kirana with shelves fully stocked (oil, masala packs, rice sacks, red chillies, scale); the imagined stock is shown at low opacity in the edit | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v1_12.jpg` | Ch-1 Andhra | over-the-shoulder shot of Arjun at his counter on an Andhra street (tiled houses, palms), holding a phone; the screen wrongly shows a reused "NOIDA SOCIETY / Maintenance Fee / Payment Successfully" UI | clean |
| `plates/v1_15.jpg` | Ch-1 Andhra | headline "Andhra Pradesh 2010: Global Implications of the Crisis in Indian Microfinance" + body text + a torn-paper photo of an Andhra women's group, on paper-sky | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v1_17-18.jpg` | Ch-1 Andhra | the building's blue sign reads "🏛 BANK ?" above the man at the cash window | clean |
| `plates/v1_19-20-21.jpg` | Ch-1 Andhra | the same building, sign now reads "SELF HELO GROUPS" (typo carried over from the cue), green-shirt man at the window | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v1_22.jpg` | Ch-1 Andhra | a central "SGHs" building (sic) ringed by four toy bank buildings labelled "Bank-1"…"Bank-4" on paper (the real 90s bank names exist only as layer names) | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v1_23.jpg` | Ch-1 Andhra | zoom-out to a dark diorama landscape; spotlit clusters, each an "SHGs" building with houses around it, joined by winding paths | clean |
| `plates/v1_24.jpg` | Ch-1 Andhra | an "MFI Microfinance Institution" building; a real hand presses a rubber stamp leaving a red "COLLATERAL FREE" seal; an "Instalment Payment" sheet sits behind on the left | soft patches where 2 text block(s) were removed (put new text there) |
| `plates/v1_25-26.jpg` | Ch-1 Andhra | the source article is framed on the office wall at top-left (the zoom-in is done in the edit) | clean |
| `plates/v1_28.jpg` | Ch-1 Andhra | "2010" on the spine; an SHGs building with a big crowd of Andhra toy people and a hanging tag "1.7 crore Members" (the MFI + "97 lakh Borrowers" state is in the layers) | soft patches where 3 text block(s) were removed (put new text there) |
| `plates/v1_29.jpg` | Ch-1 Andhra | the red timeline dot balloons into a huge red disc behind "2010"; the SHG and MFI/97-lakh scenes fade out behind it | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v1_3-4-5.jpg` | Intro | (same PSD `3,4,5.jpg`; the merge of 3 Arjuns + stickers into one is animated in the edit) | soft patches where 22 text block(s) were removed (put new text there) |
| `plates/v1_30.jpg` | Ch-1 Andhra | a tiled Andhra house on dry earth, six ropes with "LOAN" tags pulling in from every side | clean |
| `plates/v1_31.jpg` | Ch-1 Andhra | the same house, ropes gone, about 83% of it tinted red; "83% Borrowers" with a hand-drawn arrow | clean |
| `plates/v1_32-33.jpg` | Ch-1 Andhra | the 4 slices covered in pinned notices: "OVERDUE", "FINAL NOTICE", "LATE PAYMENT", "PAY NOW", "LOAN REPAYMENT DUE" | clean |
| `plates/v1_35-36.jpg` | Ch-1 Andhra | three wooden signposts in front: "Mandatory Registration", "Collections & Recovery Rules", "Weekly Repayment Model" | soft patches where 2 text block(s) were removed (put new text there) |
| `plates/v1_37.jpg` | Ch-1 Andhra | the same set, the building swapped for an "MFI" office; two signposts: "Low Repayments", "Low Fresh Lending"; cracked earth | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v1_39.jpg` | Ch-1 Andhra | the #31 red-tinted house with "Need Credit" (Credit in big red) and an arrow | clean |
| `plates/v1_40-41.jpg` | Ch-1 Andhra | close crop of the 3D map; yellow dots fill AP; legend "● Yellow Dot = Other sources." | clean |
| `plates/v1_42-43.jpg` | Ch-1 Andhra | Andhra Arjun walks in front of the BANK building, steps behind him | clean |
| `plates/v1_44.jpg` | Ch-1 Andhra | the same bank, now with a teller window; Arjun hands cash to a toy teller | clean |
| `plates/v1_46.jpg` | Ch-2 Kerala | the 3D map cropped to the south, Kerala Arjun standing on Kerala; "Chapter-2 / Kerala's Money Mindset" with drifting clouds (no house) | clean |
| `plates/v1_47.jpg` | Ch-2 Kerala | Arjun looks at his phone; a large wooden-frame phone shows a chat from "BOSS": "…a bonus of Rs. 2 Lakh will be credited to your bank account…" | soft patches where 3 text block(s) were removed (put new text there) |
| `plates/v1_48.jpg` | Ch-2 Kerala | five cardboard thought-clouds around Arjun: Gold (bars), Mutual Fund (coin plant), Stocks (bar chart), Real Estate (house), Fixed Deposit (certificate) | soft patches where 5 text block(s) were removed (put new text there) |
| `plates/v1_49.jpg` | Ch-2 Kerala | Arjun beside an open cardboard vault full of gold jewellery, plaque "First Choice" | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v1_50.jpg` | Ch-2 Kerala | the 3D India map (the three states tinted), red dot on Kerala with an arrow to "Gold" | clean |
| `plates/v1_51.2.jpg` | Ch-2 Kerala | a YouTube page mock-up: a Kerala house with Arjun in the player, channel "Zero1 Hindi by Zerodha", 1.5M likes, but the placeholder title "When it rains, why Gurugram fails?" was left in | soft patches where 7 text block(s) were removed (put new text there) |
| `plates/v1_51.jpg` | Ch-2 Kerala | a night-graded Kerala village, every lit house showing a family with gold boxes; "90% of kerala households have bullion ya gold ornaments…" (`51.jpg` = alt: a daytime Kerala crowd at a gold stall, temple, houseboat, "KERALA" sign) | clean |
| `plates/v1_51new.jpg` |  | 51new | soft patches where 2 text block(s) were removed (put new text there) |
| `plates/v1_52.jpg` | Ch-2 Kerala | Arjun, hand to chin, with a wooden-edged thought bubble of a 1970s Kerala street (red bus, tiled shops, small figures) | clean |
| `plates/v1_53.jpg` | Ch-2 Kerala | full-frame memory: a 1970s Kerala street (KSRTC bus, "1970" poster, canal boat); father, little Arjun and mother walk to "K. R. Namboodiri & Sons, Gold & Silver Ornaments, Since 1958" (the "20% … of India's total gold consumption" | clean |
| `plates/v1_54.jpg` | Ch-2 Kerala | a real hand in a suit holds a printed Stanford Business page: "Depression Babies: Do Macroeconomic Experiences Affect Risk Taking?" with the abstract | clean |
| `plates/v1_56.jpg` | Ch-2 Kerala | a warm Kerala home interior: the mother tries on a gold necklace from a jewellery box while the father and Arjun watch, with a brass lamp (layers "surroundings", "school" and "Parwarishh" = three states) | clean |
| `plates/v1_57.jpg` | Ch-3 Meghalaya | the 3D map cropped to the north-east, Meghalaya Arjun on green Meghalaya; "Chapter-3 / Meghalaya Money Mindset", clouds | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v1_58-59-60.jpg` | Ch-3 Meghalaya | (single final PSD; the house highlight and the family removal are done in the edit) | clean |
| `plates/v1_61.jpg` | Ch-3 Meghalaya | a flat textured India map in ochre on the paper-sky, NE states left pale with labels (Sikkam (sic), Assam, Nagaland, Manipur, Mizoram, Tripura, Meghalaya, Arunachal) | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v1_62.jpg` | Ch-3 Meghalaya | zoomed in, the rest of India greyed out, the NE pale with faded labels, a big red "?" over it | clean |
| `plates/v1_63.jpg` | Ch-3 Meghalaya | back to the Khasi village with the family in front; typo "Matrilinieal System of / Inheritance" (sic) with "Inheritance" in big red | clean |
| `plates/v1_64.jpg` | Ch-3 Meghalaya | an older stone-and-thatch version of the ancestral house; a mother hands a key to her daughter in Khasi shawls; the surroundings are desaturated to grey (no MATRILINEAL banner) | clean |
| `plates/v1_65.jpg` | Ch-3 Meghalaya | a family-tree chart of toy portraits: Father, Mother → Younger sister (red "NO Kids" icon), Arjun, Elder sister → Elder sister's Daughter; village/house strip along the bottom (no key icons visible) | soft patches where 6 text block(s) were removed (put new text there) |
| `plates/v1_66.jpg` | Ch-3 Meghalaya | "Literacy (Gender)": 6 blue dots (Men) "<" 20 red dots (Women), village strip footer | soft patches where 3 text block(s) were removed (put new text there) |
| `plates/v1_67.jpg` | Ch-3 Meghalaya | a ScienceDirect page "The financial literacy gender gap and the role of culture" (highlights + abstract) on a board hung by ropes, village footer | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v1_68.jpg` | Ch-3 Meghalaya | a pale flat India map; Meghalaya (red), Nagaland (teal), Mizoram (ochre) with leader-line labels (`INDIA MAP.jpg` = an alt version in ochre with the same three states coloured) | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v1_69-70.jpg` | Ch-3 Meghalaya | a Khasi home interior; the father, little sister and mother sit at a low table counting stacks of notes and coins | clean |
| `plates/v1_7-8.jpg` | SOP | the three Arjuns stand on Kerala, Andhra Pradesh and Meghalaya (states tinted olive green), with bold black labels | clean |
| `plates/v1_71.jpg` | Ch-3 Meghalaya | the #70 frame darkened, with "But" in gold + "ab ek aur question hai…" | soft patches where 2 text block(s) were removed (put new text there) |
| `plates/v1_72-73.jpg` | Ch-3 Meghalaya | (same PSD `72,73.jpg`; the zoom to the father's face is done in the edit) | clean |
| `plates/v1_74-75-76-77.jpg` | Ch-3 Meghalaya | a big red ball ringed by 18 small blue dots on the paper-sky (end state before the red ball shrinks) | clean |
| `plates/v1_9.jpg` | Ch-1 Andhra | a close crop of the 3D map with AP in green and Andhra Arjun standing on it; "Chapter-1 / Andhra Pradesh Money Mindset" on the left over clouds (`Andhra Pradesh Map.jpg` = the lead-in: full map, AP labelled) | clean |
| `plates/v1_AndhraPradeshMap.jpg` |  | AndhraPradeshMap | clean |
| `plates/v1_Con3.jpg` |  | Con3 | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v1_INDIAMAP.jpg` |  | INDIAMAP | clean |
| `plates/v2_1.jpg` | Intro | Wooden 3D India map on paper bg, UP highlighted green with a red pin, "Uttar Pradesh" heading | clean |
| `plates/v2_10.1.jpg` | Ch1 | Same graph-paper desk: black/red tower icon block with big red "23 Flats" (the "52 Families" state is a hidden layer) | clean |
| `plates/v2_10.jpg` | Ch1 | Two pie charts, "Demand" and "Supply", on graph paper on a drafting desk (scissors, blueprints, ruler); 6 price buckets with legend | soft patches where 16 text block(s) were removed (put new text there) |
| `plates/v2_12.jpg` | Ch1 | Pie charts graded almost black, big yellow "4x" + "more inventory than buyer interest" | soft patches where 2 text block(s) were removed (put new text there) |
| `plates/v2_13.jpg` | Ch1 | Toy construction site: JCB with driver in front, towers and villas going up, hanging tags "₹3 Crore", "₹2 Crore", "₹5 Crore" | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v2_14-15-16.jpg` | Ch1 | Open newspaper/magazine spread: "How Noida International Airport is Reshaping Real Estate" (runway photo) and "AIRPORT AND BEYOND: THE CONNECTIVITY NET" (yellow infra/industrial/manufacturing panels) | clean |
| `plates/v2_17.jpg` | Ch1 | Isometric toy map of Noida packed with towers; Yamuna river, expressways out to DND, Greater Noida, Kalindi Kunj, Yamuna Expressway; tags Sector 18, Noida Metro, Sector 62 IT Park, Sector 15 Park, Botanical Garden | soft patches where 5 text block(s) were removed (put new text there) |
| `plates/v2_18.1.jpg` | Ch1 | Huge red "₹1,180,000,0…" with zeros running off frame right, over the locked-gate under-construction set from #7 | soft patches where 3 text block(s) were removed (put new text there) |
| `plates/v2_18.jpg` | Ch1 | Business Standard clipping: "India's 35% stalled housing projects in Noida: White paper on homebuyers", body text, "26 November 2023" stamp, torn photo of a construction worker | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v2_19.jpg` | Ch1 | Red binocular-vignette view of premium low-rise flats and villas with hanging tags "₹5 Crore", "₹2 Crore" | clean |
| `plates/v2_2.jpg` | Intro | Photo-collage skyline in a sky circle: "Noida" title, Supernova, WTT, Mall of India, Buddha statue, Noida sign, metro train | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v2_20.1.jpg` | Connector + Ch2 reveal | "Chapter-2 / Can You AFFORD A House In Noida?" over the skyline collage (Supernova, WTT, Mall of India, metro) | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v2_21.jpg` | Ch2 | Symmetrical society avenue: residential towers on both sides, Mall of India, Supernova and WTT at the vanishing point, empty plaza in the centre | clean |
| `plates/v2_22.jpg` | Ch2 | Same avenue; Arjun centre, back to camera, big red "SALARY?" in the sky | clean |
| `plates/v2_23.jpg` | Ch2 | Same set in greyscale except one tower on the left kept in colour; yellow "₹2 Crore" sign on a post beside Arjun, who now faces camera | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v2_24.jpg` | Ch2 | Wide aerial of a full township: tower rows, central lawn, clubhouse, pool. No labels and no Arjun in the final state (amenity highlights in hidden layers) | clean |
| `plates/v2_27-31.jpg` | Ch2 | (27-31.jpg) Full EMI table incl. "Total cost of ownership ₹3,79,11,842" and "X times more than 2 Cr 1.90x"; Arjun scratching his head at bottom right | soft patches where 17 text block(s) were removed (put new text there) |
| `plates/v2_3-4.jpg` | Intro | Blurred tagged towers in the foreground, barren desert land behind, big red "125% Increased" in the sky (year line only in hidden layers) | clean |
| `plates/v2_32.jpg` | Ch2 | Greyscale society avenue from #23; "₹2 Crore" sign crossed out with a red X; "Actual Value ₹3 Crore" in the sky; Arjun beside the sign | soft patches where 3 text block(s) were removed (put new text there) |
| `plates/v2_33.jpg` | Ch2 | Same greyscale set with Arjun and ₹2 Crore sign; "How much should be / Arjun's salary?" in red | clean |
| `plates/v2_34.jpg` | Ch2 | White cloth banner draped over a single tower facade: "EMI = ₹1,25,466 / EMI to income ratio = 30% / In hand salary per month = ₹4,18,220" | clean |
| `plates/v2_35.jpg` | Ch2 | Red-header "SALARY NEEDED" rope-hung table: Monthly ₹4,18,220, Annual ₹50,18,640, Approx CTC ₹71,69,486; Arjun scratching his head | soft patches where 7 text block(s) were removed (put new text there) |
| `plates/v2_36-37.jpg` | Ch2 | (36,37.jpg) Arjun in colour amid a dense greyscale crowd of toy office workers; no 0.5% text on screen | soft patches where 2 text block(s) were removed (put new text there) |
| `plates/v2_38.jpg` | Connector + Ch3 reveal | "Chapter-3 / What does Arjun 'Really' Get?" plus a photo card "Swimming Pool" with ← → carousel arrows and Arjun beside it | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v2_40.jpg` | Ch3 | Decayed society sports court: faded basketball court, weeds, rusty fence, stained towers; "Condition / After 10 Years" in red | clean |
| `plates/v2_42.jpg` | Ch3 | Stack of deckle-edged papers "AUDIT POLICY"; a suited (photoreal) hand stamps a red "NOIDA AUTHORITY" seal | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v2_43-44.jpg` | Ch3 | (43,44.jpg) Same office; Arjun scratching his head while still handing over the cash (no "?" visible) | clean |
| `plates/v2_45.jpg` | Ch3 | Greyscale township aerial with only the facilities in colour and callout tags "Power Backup", "Garden", "Pool", "Garbage Disposal" | soft patches where 4 text block(s) were removed (put new text there) |
| `plates/v2_46-47.jpg` | Ch3 | (46,47.jpg) Small worried Arjun with phone, scratching his head, black "?" above him (no bubble) | clean |
| `plates/v2_48.jpg` | Ch3 | Toy diorama of ~8 under-construction towers with cranes, JCBs, trucks, materials | clean |
| `plates/v2_49.jpg` | Ch3 | Arjun in a toy bathroom reaching under a dry tap, scratching his head; reflection in the mirror | clean |
| `plates/v2_50.jpg` | Ch3 | Cut-away below the #48 tower site: pile foundations driven into layered soil and rock ("104.79% Ground Water Extracted" is a PSD layer, not in the flat JPG) | soft patches where 2 text block(s) were removed (put new text there) |
| `plates/v2_51-53.jpg` | Ch3 / Stress test | (51-53.jpg) Balanced beam labelled "Stress Test" in small white type (crack states hidden) | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v2_54.jpg` | Ch3 / Stress test | Architect's township model in a glass case on an MDF table; big red "Proposed Plan" above | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v2_55.jpg` | Ch3 / Stress test | Clipboard "CHECKLIST" with icons (Occupancy load, Safe with Lifts, Water supply ticked; Electricity Check, Power backups, Maintenance open) and a pinned polaroid of Arjun in a lobby | clean |
| `plates/v2_56.jpg` | Ch3 / Stress test | Society avenue (towers both sides, green hill behind); Arjun centre, facing camera, writing on a clipboard | clean |
| `plates/v2_57.1-ChapterReveal.jpg` | Ch4 reveal | Same gate frame as #57 with "Chapter-4 / Is The Flat Really Yours?" top right | soft patches where 2 text block(s) were removed (put new text there) |
| `plates/v2_57.jpg` | Connector | New gated-society entrance: boom barrier down, toy security guard with his palm up stopping Arjun (walking in, back to camera) | clean |
| `plates/v2_58.jpg` | Ch4 | Cracked barren toy land plot with dry shrubs and a wooden signboard "Alloted" | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v2_59.jpg` | Ch4 | Same plot now holding mid-rise beige apartment blocks with trees | clean |
| `plates/v2_60.jpg` | Ch4 | "Occupancy Certificate 72,697" paper rising from behind the same blocks | clean |
| `plates/v2_61.jpg` | Ch4 | Same certificate, 72,697 faded, "29,079" in red with a red "NOT REGISTERED" rubber stamp | clean |
| `plates/v2_62.jpg` | Ch4 | Phone close-up layout from #46: "NOIDA SOCIETY / Pay Now / Registered" button; worried Arjun with phone, scratching his head | clean |
| `plates/v2_63-64.jpg` | Ch4 | Arjun on a sofa in a cosy toy living room, back to camera, watching the UP RERA website ("रेरा है तो भरोसा है..") on a TV | clean |
| `plates/v2_65.jpg` | Conclusion | Gated-society entrance (wide); sad Arjun beside a waist-high pile of document files | clean |
| `plates/v2_66.jpg` | Conclusion | Low-angle up between the society towers; giant red "₹2 Crore" filling the sky | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v2_68.jpg` | Conclusion | Gate set; smiling Arjun at the entrance with a thumbs-up and a clipboard | clean |
| `plates/v2_7.jpg` | Intro | Toy crowd with placards in front of a locked, chained black gate; under-construction towers with cranes and green nets behind ("1.65 lakhs Families" typo only in a hidden layer) | clean |
| `plates/v2_8.jpg` | SOP | Giant "?" made of shards of the #7 crowd/under-construction frame; 4 numbered polaroids around it: "How it made investment market?", "What should the salary be?", "The Hidden cost buying a property in NOIDA!", "How Noida made" | soft patches where 9 text block(s) were removed (put new text there) |
| `plates/v2_9.jpg` | Ch1 reveal | "Chapter-1 / The Noida Real Estate Paradox" over the BUILDINGS collage (towers, golf-course lawn) | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v2_BUILDINGS.jpg` |  | BUILDINGS | clean |
| `plates/v2_skyline.jpg` |  | skyline | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v3_1.jpg` | Intro | Arjun alone in front of a tiled-roof Kerala house with nilavilakku lamp and hibiscus shrubs; typo "meet ARJUN"; a hidden layer group holds the Kerala map + "Kochi" label for the zoom-out | clean |
| `plates/v3_12.jpg` | Sec 1 | Timeline "1950"; six Keralites in kasavu saris and mundus (detailed human-faced cutouts) beside a red velvet jewellery tray; caption "Gold wasn't a major consumer item"; the Black & White layer exists but is switched off | clean |
| `plates/v3_13.jpg` | Sec 1 | Timeline "1970"; Kerala village (church, mosque, palms, tiled houses) at left, Gulf town (dome, minaret, cranes, oil derrick) at right; five migrants with suitcases walk a road between; labels "Kerala"/"Gulf"; return-money layer h | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v3_14.jpg` | Sec 1 | Timeline "1980"; Kerala/Gulf vignettes shrink to the bottom corners; a gold coin (the Roman-coin asset) arcs along a dashed path from Gulf to a red velvet tray of jewellery above Kerala | clean |
| `plates/v3_16.jpg` | Sec 1 | Timeline "1990"; aged paper stack headed "GOLD CONTROL ACT"; a real suited hand presses a wooden rubber stamp leaving a red "REPEALED" seal | clean |
| `plates/v3_17.jpg` | Sec 1 | Timeline (no year); sailing ship on torn-paper waves, two porters passing gold-bar crates along a jetty to a wooden cart full of gold; palm islet; caption "Easy to Import" | clean |
| `plates/v3_18.jpg` | Sec 1 | Timeline; four tiled-roof wooden jewellery/pawn stalls with customers in mundus at the counters; caption "Local moneylenders aur pawnbrokers" | clean |
| `plates/v3_18a.jpg` | Sec 1 | Timeline "2000"; "MANAPPURAM FINANCE LIMITED", a columned "BANK" and "MUTHOOT FINCORP LTD" buildings with hanging "GOLD LOAN AVAILABLE" signs; caption "Under NBFCs organization" | clean |
| `plates/v3_19.jpg` | Sec 1 | Timeline; three-step flow: empty open vault "Collateral" → vault filled with jewellery "Gold" → stacks of ₹500 notes "Loan Amount" | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v3_2.jpg` | Intro | Same house now hung with marigold-jasmine garlands, pookalam at the door; Arjun beside three women in kasavu saris around a carved wooden cradle with the baby | clean |
| `plates/v3_25.jpg` | Sec 2 | Medium close-up of Arjun at right, necklace in hand; red "But…" + "actually that's not what happened" at left | clean |
| `plates/v3_27.jpg` | Sec 2 | Arjun walks toward a cardboard glass-top jewellery counter where a moustached jeweller holds out a red velvet tray; Arjun drawn with a smiling mouth and side-part hair (off-model) | clean |
| `plates/v3_28.jpg` | Sec 2 | Camera tilts up to the sky: real World Gold Council "Chart 1: Gold regains ground" (LBMA/MCX price, Jun-24 to Aug-26) pasted on a cloud background, with a blue marker dot | clean |
| `plates/v3_29.jpg` | Sec 2 | Back at the counter: Arjun seated with his back to camera, jeweller offering a tray; typo "Gold jewellery / is the best option for Arjun's daughter!" | clean |
| `plates/v3_3.jpg` | Intro | Top-down cardboard jewellery display case with a red velvet centre tray; callout pins "Bangles", "Anklets", "Gold chain"; Arjun not in frame | clean |
| `plates/v3_30.jpg` | Sec 2 | Shop set from #27 shrinks left; at right: "Current value = ₹1.48 Lakhs / Deduct 4% / Value of Gold = ₹1.42 Lakhs" | clean |
| `plates/v3_32.jpg` | Sec 2 | Desk top: paper on a craft desk (ruler, red scissors, blueprints) with a red-header "SELLING SIDE" table: ₹14,500 → ₹1,48,061 → 96% buyback ₹1,42,139 → STCG ₹12,642 + cess ₹506 = ₹13,147 → locker ₹1770 → "🏆FINAL RESULT · NET MONEY | soft patches where 22 text block(s) were removed (put new text there) |
| `plates/v3_36.jpg` | Sec 3 · Opt 1 | Cloud-sky set under the hanging "Option-1 GOLD COIN OR BAR" board; left: red velvet jewellery tray "Making charges ✅ / Wastage charges ✅"; right: coin stack + two "GOLD BAR" ingots "Making charges ❌ / Wastage charges ❌"; no Arjun | clean |
| `plates/v3_39.jpg` | Sec 3 · Opt 1 | Jewellery counter returns: thinking Arjun (hand on chin, off-model face with nose and mouth) and jeweller presenting a tray of coins and bars; the "…of gold" typo peeks out from behind the jeweller; 98-99% not visible | soft patches where 2 text block(s) were removed (put new text there) |
| `plates/v3_4.jpg` | Intro | Last of 5 stage states: grown daughter in kasavu saree at a wooden dressing-table mirror, "Wedding stage / Age (22-30)"; open carved sandook beside her holding gold coins and bangles (hidden states: Baby 0-2, Toddler 3-5, School 6 | clean |
| `plates/v3_40-41.jpg` | Sec 3 · Opt 2 | Aged "Gold ETF" paper stack being stamped with a red SEBI logo by the real hand from #16; cardboard "NSE" office building at right; a hidden scene holds "95-100% / Invested in gold related instruments" | soft patches where 1 text block(s) were removed (put new text there) |
| `plates/v3_45.jpg` | Sec 3 · Opt 2 | Desk-top set again: "Taxation" table, Gold ETF "Sell after 1 Year · 12.5%" vs Physical Gold "Sell after 2 Year · 12.5%" | soft patches where 5 text block(s) were removed (put new text there) |
| `plates/v3_46-47.jpg` | Sec 3 · Opt 3 | Over-the-shoulder close-up of Arjun's wooden head and hands holding a phone: "Invest in Gold ETF / Invest / Start Now →"; typo "NO…. DEMAT Account required" | clean |
| `plates/v3_48.1.jpg` | Sec 3 · Compare | Aged, moustached Arjun at centre, hands folded, ringed by four instruments each tagged "₹1 Lakh": Gold ETF paper, Mutual Fund (note rolls + coin stacks), Gold Jewellery (necklace), Gold coins and Bars | soft patches where 7 text block(s) were removed (put new text there) |
| `plates/v3_48.jpg` | Sec 3 · Opt 3 | Same desk-top Taxation table with columns swapped: Gold Mutual Fund "Sell after 2 Year · 12.5%" vs Gold ETF "Sell after 1 Year · 12.5%" | soft patches where 4 text block(s) were removed (put new text there) |
| `plates/v3_49.2.jpg` | Sec 3 · Compare | Gold nugget "Gold Ore ₹5.25 Lakh" at left vs necklace "Gold Jewellery ₹3.64 Lakh" at right, red falling arrow "30.6%"; below, Arjun's sad-faced family of five (grandfather, two women in sarees, aged Arjun, daughter) | soft patches where 2 text block(s) were removed (put new text there) |
| `plates/v3_50.jpg` | Conclusion | Kerala wedding mandap: bride (kasavu saree, gold jewellery) and groom on a sofa under a jasmine-rose arch, grey-haired moustached Arjun standing beside them; four nadaswaram players on a red carpet; hanging jasmine-rose garlands | clean |
| `plates/v3_51.1.jpg` | Conclusion | Bride standing alone under the flower arch wearing the necklace; typo "Iss necklace ka / ROI kya hai?" | clean |
| `plates/v3_51.jpg` | Conclusion | Aged Arjun standing beside a kasavu-draped table with jasmine swags; an open red velvet box displays the Section-2 necklace; same hanging garlands | clean |
| `plates/v3_52.jpg` | Conclusion | Extreme close-up of the bride's block face (maang tikka, jasmine in her hair) with tears running from both square eyes | clean |
| `plates/v3_53.jpg` | Conclusion | Aged Arjun at centre (full figure, no tears or smile) flanked by three greyscale "Memories" photo cards: walking his school-uniform daughter to school, building blocks together, drawing at a low table | clean |
| `plates/v3_55.jpg` | Conclusion | Tilt up from the blurred top of Arjun's head into the cloud sky, where two rope-hung boards read "Advantage-1 Jewellery for Kid's Wedding" and "Advantage-2 Investment in Gold" | clean |
| `plates/v3_9-10-11.jpg` | Sec 1 | Same coast at "1 AD": a sack-laden ship sails right, pin "Black pepper", "towards west →"; two Roman gold coins (seated figure, laureate head) labelled "Roman coins" | soft patches where 2 text block(s) were removed (put new text there) |
