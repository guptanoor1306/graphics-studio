"""All Claude calls live here. Two jobs:
  1. storyboard(script, look)   -> {"storyboard": str, "spec": {...}}   (one call per video)
  2. edit_frame(frame, ask)     -> new frame JSON                         (one small call per edit)

Cost controls:
  - The theme's rules (SKILL.md + spec_format.md + example spec) go in a cached system block,
    so every call after the first in ~5 minutes pays a fraction for them.
  - Frame edits send only that frame's JSON, never the whole video.
  - Output is forced through a tool schema, so there's no prose to pay for or parse.
API key: ANTHROPIC_API_KEY in .env (loaded by app.py) or the environment.
"""
import json, os, pathlib, re

from spec_enrich import enrich_spec

_ROOT = pathlib.Path(__file__).parent
# Cursor-style slugs → Anthropic API model IDs (Opus 5.5 default effort is already "medium")
_MODEL_ALIASES = {
    "claude-opus-5-5-medium": "claude-opus-5-5",
    "claude-sonnet-5-5-high": "claude-sonnet-5-5",
    "claude-haiku-5-5-medium": "claude-haiku-5-5",
}
# Models that reject tool_choice type "tool" / "any" (must use "auto")
_ADAPTIVE_TOOL_MODELS = (
    "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", "claude-sonnet-5",
    "claude-haiku-5-5", "claude-fable-5-1",
)


def resolve_model(name: str | None = None) -> str:
    raw = (name or os.environ.get("STUDIO_MODEL", "claude-opus-5-5")).strip()
    return _MODEL_ALIASES.get(raw, raw)


MODEL = resolve_model()


def is_mf_theme(theme_dir: pathlib.Path) -> bool:
    return (theme_dir / "templates" / "render.js").is_file()


def theme_rules(theme_dir: pathlib.Path) -> str:
    """Skill rules + asset index + style guide so specs use kit buildings, people, etc."""
    parts = []
    if is_mf_theme(theme_dir):
        rels = (
            "SKILL.md",
            "references/spec_format.md",
            "references/studio_brief.md",
            "references/style_guide.md",
            "references/gift_city_breakdown.md",
            "scenes/gift_city_spec.json",
            "assets/INDEX.md",
        )
    else:
        rels = (
            "SKILL.md",
            "references/spec_format.md",
            "references/studio_brief.md",
            "references/app_storyboard_overrides.md",
            "scenes/example_spec.json",
            "assets/INDEX.md",
            "references/deep/style_guide.md",
        )
    for rel in rels:
        p = theme_dir / rel
        if p.exists():
            parts.append(f"===== {rel} =====\n{p.read_text()}")
    return "\n\n".join(parts)


_ITEM_TYPES = [
    "title", "pill", "htab", "points", "num", "label", "text", "glass_table", "calc_table",
    "popup", "bars", "nlist", "cards", "person", "asset", "html", "callout", "hpill", "result_pill",
]
_FRAME_ITEM = {
    "type": "object",
    "properties": {"t": {"type": "string", "enum": _ITEM_TYPES}},
    "required": ["t"],
    "additionalProperties": True,
}
_FRAME = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "mode": {"type": "string", "enum": ["anchor", "fss"]},
        "items": {"type": "array", "items": _FRAME_ITEM, "minItems": 1},
        "person_left": {"type": "boolean"},
        "prop": {"type": "boolean"},
    },
    "required": ["id", "mode", "items"],
    "additionalProperties": True,
}
SB_TOOL = {
    "name": "submit_storyboard",
    "description": "Return the storyboard text and the full build spec for every graphic beat.",
    "input_schema": {
        "type": "object",
        "properties": {
            "storyboard": {"type": "string", "description": "SB Doc text, one line per beat, in the skill's format"},
            "spec": {
                "type": "object",
                "description": "spec.json with look and frames[]; each frame must have mode anchor|fss",
                "properties": {
                    "look": {"type": "object"},
                    "frames": {"type": "array", "items": _FRAME, "minItems": 1},
                },
                "required": ["look", "frames"],
            },
        },
        "required": ["storyboard", "spec"],
    },
}
MF_SB_TOOL = {
    "name": "submit_storyboard",
    "description": "Return the MF storyboard (SB Doc) and full spec.json (title, look string, frames with type).",
    "input_schema": {
        "type": "object",
        "properties": {
            "storyboard": {"type": "string"},
            "spec": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "look": {"type": "string", "description": "One-line visual brief for the video"},
                    "frames": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["id", "type"],
                            "additionalProperties": True,
                        },
                    },
                },
                "required": ["title", "look", "frames"],
            },
        },
        "required": ["storyboard", "spec"],
    },
}
FRAME_TOOL = {
    "name": "submit_frame",
    "description": "Return the edited frame object (same id unless asked to rename).",
    "input_schema": {"type": "object", "properties": {"frame": {"type": "object"}}, "required": ["frame"]},
}

_ROLE = (
    "You are the graphics designer described in the skill below. You are running inside a web app, "
    "not a chat: ignore the skill's setup, build, QA and delivery steps (the app renders frames). "
    "Only decide beats and write the spec. Follow the design rules strictly. "
    "Follow references/app_storyboard_overrides.md for beat tagging (OST/OSA/FSS) and frame count — it overrides the skill density shortcut. "
    "Topic prop: at most one corner prop per video (first entry in look.props); corner props are not scene illustrations. "
    "Every OSA/FSS storyboard line must appear in spec with matching assets from INDEX (grep by beat meaning). "
    "Hero title frames are title-only (no asset/person). htab+points/text beats need explicit `asset`/`person`/`glass_table`/`calc_table` as in example_spec.json."
)


_SETTINGS = _ROOT / "data" / "settings.json"
_DOTENV = _ROOT / ".env"


def _dotenv_api_key() -> str | None:
    if not _DOTENV.exists():
        return None
    for line in _DOTENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == "ANTHROPIC_API_KEY":
            v = v.strip().strip('"').strip("'")
            return v or None
    return None


def api_key() -> str | None:
    k = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if k:
        return k
    if _SETTINGS.exists():
        try:
            k = json.loads(_SETTINGS.read_text()).get("anthropic_api_key", "").strip()
            if k:
                return k
        except (json.JSONDecodeError, OSError):
            pass
    return None


def set_api_key(key: str) -> None:
    _SETTINGS.parent.mkdir(exist_ok=True)
    _SETTINGS.write_text(json.dumps({"anthropic_api_key": key.strip()}))


def clear_saved_api_key() -> None:
    if _SETTINGS.exists():
        _SETTINGS.unlink()


def key_status() -> dict:
    k = api_key()
    if not k:
        return {"configured": False, "source": None, "hint": None}
    dot = _dotenv_api_key()
    if dot and k == dot:
        return {"configured": True, "source": "dotenv", "hint": _hint(k)}
    if os.environ.get("ANTHROPIC_API_KEY", "").strip() == k:
        return {"configured": True, "source": "env", "hint": _hint(k)}
    return {"configured": True, "source": "saved", "hint": _hint(k)}


def _hint(k: str) -> str:
    if len(k) <= 12:
        return "••••"
    return k[:7] + "…" + k[-4:]


def _client():
    k = api_key()
    if not k:
        raise RuntimeError(
            "No Anthropic API key. Set ANTHROPIC_API_KEY in .env or save one in the sidebar."
        )
    import anthropic
    return anthropic.Anthropic(api_key=k)


_MF_ROLE = (
    "You are the Varsity Mutual Fund IP graphics designer in the skill below. You run inside a web app, not a chat: "
    "ignore local setup/build/zip delivery steps — only return storyboard + spec via submit_storyboard. "
    "Follow SKILL.md beat rules and references/spec_format.md. Use assets/INDEX.md paths. "
    "Types footage, screen, repeat are storyboard-only; all other graphic beats need full frame JSON. "
    "Keyword pills use purple gradient #5b55e6 with white text — never green pill backgrounds or inline green on .pill."
)


def _system(theme_dir):
    role = _MF_ROLE if is_mf_theme(theme_dir) else _ROLE
    return [{"type": "text", "text": role},
            {"type": "text", "text": theme_rules(theme_dir), "cache_control": {"type": "ephemeral"}}]


def _tool_choice(tool_name: str) -> dict:
    if MODEL in _ADAPTIVE_TOOL_MODELS or MODEL.startswith(("claude-opus-5", "claude-sonnet-5", "claude-haiku-5")):
        return {"type": "auto"}
    return {"type": "tool", "name": tool_name}


def _tool_input(response, tool_name: str) -> dict:
    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            return block.input
    raise RuntimeError(f"Claude did not call {tool_name} (stop_reason={response.stop_reason}). Try again.")


def _messages_create(**kwargs):
    return _client().messages.create(model=MODEL, **kwargs)


_VISUAL_TYPES = frozenset({
    "asset", "person", "glass_table", "calc_table", "bars", "nlist", "cards", "popup", "bars", "html",
})
_TEXT_ONLY = frozenset({"title", "htab", "text", "points", "label", "num", "pill"})


def _merge_user_look(spec: dict, look: dict) -> dict:
    spec = spec or {}
    spec.setdefault("look", {})
    spec["look"] = {**spec["look"], **look}
    if look.get("props"):
        spec["look"]["props"] = look["props"]
        spec["look"].pop("prop", None)
    return spec


def _storyboard_line_for_frame(storyboard: str, fid: str) -> str:
    for line in (storyboard or "").splitlines():
        if f"→ {fid}" in line or line.rstrip().endswith(f"→ {fid}"):
            return line
    return ""


def spec_quality_issues(spec: dict, storyboard: str = "") -> list[str]:
    frames = (spec or {}).get("frames") or []
    if frames and isinstance(frames[0], dict) and "type" in frames[0] and "mode" not in frames[0]:
        return []
    issues: list[str] = []
    fss_n = 0
    sb = storyboard or ""
    for f in frames:
        mode = f.get("mode") or "anchor"
        if mode == "fss":
            fss_n += 1
        items = f.get("items") or []
        types = {it.get("t") for it in items if isinstance(it, dict)}
        has_visual = bool(types & _VISUAL_TYPES)
        textish = types <= _TEXT_ONLY or not types
        if mode == "fss" and not has_visual:
            issues.append(
                f'Frame "{f.get("id")}": mode fss requires calc_table, glass_table, bars, nlist, cards, or asset/person — not text only.'
            )
        content_types = types & {"htab", "points", "text", "num", "label", "pill"}
        if mode == "anchor" and not has_visual and content_types and "title" not in types:
            issues.append(
                f'Frame "{f.get("id")}": add OSA asset/person or glass_table (see example_spec 1.12, 11.05).'
            )
        sb_line = _storyboard_line_for_frame(sb, f.get("id") or "")
        if sb_line and re.search(r"\bOSA\b", sb_line, re.I) and not has_visual:
            issues.append(f'Frame "{f.get("id")}": storyboard says OSA but spec has no asset/person/table visual.')
        if sb_line and re.search(r"\bFSS\b", sb_line, re.I) and mode != "fss":
            issues.append(f'Frame "{f.get("id")}": storyboard says FSS but mode is not fss.')
    if len(frames) >= 2 and fss_n == 0:
        issues.append(
            "No mode:fss frames. Add full-screen (mode:fss) frames for tables, charts, comparisons, or long lists."
        )
    non_title = [
        f for f in frames
        if isinstance(f, dict)
        and not ({it.get("t") for it in f.get("items") or [] if isinstance(it, dict)} <= {"title", "pill", "hpill"})
    ]
    anchor_person = sum(
        1
        for f in non_title
        if (f.get("mode") or "anchor") != "fss"
        and any(isinstance(it, dict) and it.get("t") in ("asset", "person") for it in f.get("items") or [])
    )
    if len(non_title) >= 3 and anchor_person > max(2, int(len(non_title) * 0.55)):
        issues.append(
            "Too many similar anchor+illustration frames. Convert explanation beats to mode:fss (calc_table, nlist, bars, cards) — not anchor+person every time."
        )
    need_fss = max(1, len(non_title) // 3)
    if len(non_title) >= 3 and fss_n < need_fss:
        issues.append(
            f"Need at least {need_fss} mode:fss frames for full-screen variety (see app_storyboard_overrides graphics mix)."
        )
    return issues


def _graphics_mix_rules(look: dict) -> str:
    mix = (look.get("graphics_mix") or "balanced").strip()
    if mix == "fss_heavy":
        return (
            "Graphics mix FSS-HEAVY: at least half of non-title frames must be mode:fss. "
            "At most 2 anchor OSA frames in the entire video. No repeated anchor-right person pattern.\n"
        )
    if mix == "minimal_anchor":
        return (
            "Graphics mix MINIMAL ANCHOR: at most 2 anchor OSA frames total; other beats are FSS or title-only OST.\n"
        )
    return (
        "Graphics mix BALANCED: at least one third of non-title frames mode:fss; "
        "do not default every beat to anchor+person on the right.\n"
    )


def _load_ref_images(theme_dir: pathlib.Path, rel_paths: list[str]) -> list[tuple[str, bytes]]:
    import mimetypes

    out: list[tuple[str, bytes]] = []
    for rel in rel_paths[:10]:
        p = theme_dir / "assets" / rel
        if not p.is_file():
            continue
        raw = p.read_bytes()
        mt = mimetypes.guess_type(p.name)[0] or "image/png"
        if mt not in ("image/png", "image/jpeg", "image/webp", "image/gif"):
            mt = "image/png"
        out.append((mt, raw))
    return out


def _call_storyboard(
    theme_dir,
    msg: str,
    ref_images: list[tuple[str, bytes]] | None = None,
    *,
    sb_tool: dict | None = None,
) -> dict:
    import base64

    tool_schema = sb_tool or SB_TOOL
    tool = tool_schema["name"]
    if _tool_choice(tool)["type"] == "auto":
        msg += f"\n\nRespond only by calling the {tool} tool with the full storyboard and spec."
    if ref_images:
        content: list[dict] = []
        for media, raw in ref_images:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media,
                        "data": base64.standard_b64encode(raw).decode(),
                    },
                }
            )
        content.append({"type": "text", "text": msg})
        user_content: str | list = content
    else:
        user_content = msg
    r = _messages_create(
        max_tokens=16384, system=_system(theme_dir),
        tools=[tool_schema], tool_choice=_tool_choice(tool),
        messages=[{"role": "user", "content": user_content}])
    return _tool_input(r, tool)


def storyboard(theme_dir: pathlib.Path, script: str, look: dict, notes: str = "") -> dict:
    if is_mf_theme(theme_dir):
        look_line = (look.get("look_line") or "").strip()
        msg = (
            f"Spec root look (one line — copy into spec.look): {look_line or 'anchor right · GIFT City house style per SKILL'}\n"
            f"Notes: {notes or 'none'}\n\n"
            "GRAPHICS STUDIO RULES (critical):\n"
            "- spec.frames must ONLY include beats that become PNG graphics: scene, ribbon, sop, table, cycle, points, definition, anchor, html.\n"
            "- Do NOT put footage, screen, or repeat in spec.frames — those beats go ONLY in the storyboard string (with timestamps, no → frame id).\n"
            "- Match the density and layout quality of scenes/gift_city_spec.json (hero assets, pills, tables, logo cards — not empty shells).\n"
            "- Most of the video stays on footage; a graphic only when SKILL Step 3 says graphic/screen.\n"
            "- Copy numbers exactly from the script.\n"
            "- Pills: purple #5b55e6 gradient, white pill text (house.css); no green pill styling in spec HTML.\n\n"
            "Follow SKILL.md + references/spec_format.md + gift_city_breakdown.md.\n\n"
            f"SCRIPT:\n{script}"
        )
        out = _call_storyboard(theme_dir, msg, sb_tool=MF_SB_TOOL)
        return out

    props = look.get("props") or ([look["prop"]] if look.get("prop") and look.get("prop") != "none" else [])
    msg = (
        f"Look (copy into spec.look): {json.dumps(look)}\n"
        f"Topic props — first only as corner dressing; all checked guide OSA kit choices: {json.dumps(props if props else [])}\n"
        f"Notes: {notes or 'none'}\n\n"
        f"{_graphics_mix_rules(look)}"
        f"Follow app_storyboard_overrides.md + studio_brief.md: tag each beat OST/OSA/FSS in storyboard; spec must match tags.\n"
        f"Copy numbers exactly from the script.\n\nSCRIPT:\n{script}"
    )
    out = _call_storyboard(theme_dir, msg)
    out["spec"] = enrich_spec(_merge_user_look(out.get("spec") or {}, look), out.get("storyboard") or "")
    for _ in range(2):
        issues = spec_quality_issues(out["spec"], out.get("storyboard") or "")
        if not issues:
            break
        retry = (
            "Your previous spec was rejected by the app quality gate. Fix ALL issues and return a complete "
            "storyboard + spec via submit_storyboard only:\n"
            + "\n".join(f"- {x}" for x in issues)
            + f"\n\nLook: {json.dumps(look)}\n\nSCRIPT:\n{script}"
        )
        out = _call_storyboard(theme_dir, retry)
        out["spec"] = enrich_spec(_merge_user_look(out.get("spec") or {}, look), out.get("storyboard") or "")
    return out


def edit_frame(
    theme_dir: pathlib.Path,
    frame: dict,
    look: dict,
    ask: str,
    ref_asset_src: str | None = None,
    ref_image: tuple[str, bytes] | None = None,
    *,
    replace_illustration: bool = False,
    smart_reference: bool = True,
    flat_paste: bool = False,
    regenerate: bool = False,
    storyboard_line: str = "",
    storyboard_full: str = "",
) -> dict:
    import base64

    tool = "submit_frame"
    if is_mf_theme(theme_dir):
        sb_excerpt = (storyboard_full or "")[:6000]
        if regenerate:
            msg = (
                f"Storyboard line: {storyboard_line or '(none)'}\nContext:\n{sb_excerpt or '(none)'}\n\n"
                f"Current frame JSON (MF spec — keep id and type unless asked):\n"
                f"{json.dumps(frame, ensure_ascii=False)}\n\n"
                "REGENERATE this frame for the same beat. Match references/spec_format.md for this type.\n"
            )
        else:
            msg = (
                f"Current MF frame JSON:\n{json.dumps(frame, ensure_ascii=False)}\n\n"
                f"Change requested: {ask}\n"
            )
        msg += "\nReturn the whole edited frame via submit_frame only."
        if _tool_choice(tool)["type"] == "auto":
            msg += f"\n\nRespond only by calling the {tool} tool."
        content = msg
        if ref_image:
            media, raw = ref_image
            content = [
                {"type": "image", "source": {"type": "base64", "media_type": media, "data": base64.standard_b64encode(raw).decode()}},
                {"type": "text", "text": msg},
            ]
        r = _messages_create(
            max_tokens=8000 if regenerate else 5000,
            system=_system(theme_dir),
            tools=[FRAME_TOOL],
            tool_choice=_tool_choice(tool),
            messages=[{"role": "user", "content": content}],
        )
        return _tool_input(r, tool)["frame"]

    if regenerate:
        n_items = len(frame.get("items") or [])
        sb_excerpt = (storyboard_full or "")[:6000]
        msg = (
            f"Look: {json.dumps(look)}\n"
            f"Storyboard line for this frame: {storyboard_line or '(none)'}\n"
            f"Full storyboard doc (context):\n{sb_excerpt or '(none)'}\n\n"
            f"Current frame JSON (rebuild this beat — do NOT shrink to one icon):\n"
            f"{json.dumps(frame, ensure_ascii=False)}\n\n"
            "REGENERATE this frame for the same beat and frame id.\n"
            "Requirements:\n"
            f"- Prior frame had {n_items} items — regenerated frame must match storyboard richness (headers, points, tables, cards), not a single asset.\n"
            "- Follow the storyboard line tag (OST/OSA/FSS) and example_spec.json density for that tag.\n"
            "- Change kit paths and layout vs current, but include ALL content types the beat needs.\n"
            "- Do not default to broker building + person unless the storyboard line explicitly asks for that OSA pair.\n"
            "- Keep script numbers and htab copy from storyboard/script.\n"
        )
    else:
        msg = (
            f"Look: {json.dumps(look)}\nCurrent frame JSON:\n{json.dumps(frame, ensure_ascii=False)}\n\n"
            f"Change requested by the team member: {ask}\n"
            "For `cards` layers: use `active` null (all visible, none dimmed) or a 0-based index for one highlight — "
            "not active:\"all\". Size via `scale` (e.g. 1.3) and/or `card_w` on the cards item; do not invent `fade` unless dimming one card.\n"
        )
    if ref_image and smart_reference and not flat_paste:
        msg += (
            "\nREFERENCE IMAGE (vision) — SMART mode:\n"
            "1. Identify the PRIMARY subject the user wants on the frame (one role: building, person, chart, document…).\n"
            "2. Ignore extra clutter in the photo (background, secondary icons, text in the screenshot) unless the ask names them.\n"
            "3. Map the primary subject to the closest transparent PNG in assets/INDEX.md (setA/setB/setC paths only).\n"
            "4. If replacing: remove existing `asset`/`person` for that role, then add kit items — NOT the full upload as one flat PNG.\n"
            f"5. Do NOT set any asset src to \"{ref_asset_src or 'uploads/ref_*'}\" — uploads are for your eyes only in smart mode.\n"
            "6. Use `person` for characters, `asset` for buildings/props; match example_spec.json density.\n"
        )
        if replace_illustration:
            msg += (
                "7. REPLACE is on: the JSON you receive already has asset/person removed — add ONLY the new kit-mapped "
                "illustration(s). Do not re-add removed buildings/people. Remove stray html/cards/bars/popup overlays "
                "unless the ask keeps them.\n"
            )
        props = look.get("props") or []
        if props:
            msg += f"8. Video topic props (prefer matching INDEX motifs when mapping reference): {json.dumps(props)}\n"
    elif ref_asset_src and flat_paste:
        msg += (
            f"\nFLAT PASTE: remove existing asset/person if replacing, then exactly ONE asset with "
            f"\"src\": \"{ref_asset_src}\" on the floor (~480px h).\n"
        )
    elif ref_asset_src:
        msg += f"\nReference file saved at assets/{ref_asset_src} (use only if flat paste or user says paste literally).\n"
    if not regenerate:
        msg += (
            "\nReturn the whole edited frame via submit_frame. Keep everything not mentioned unchanged. "
            "Layout: FSS calc_table/glass_table can use w, widths, person_left. "
            "Use INDEX paths for illustrations."
        )
    else:
        msg += "\nReturn the whole regenerated frame via submit_frame only."
    if _tool_choice(tool)["type"] == "auto":
        msg += f"\n\nRespond only by calling the {tool} tool."
    if ref_image:
        media, raw = ref_image
        content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": media, "data": base64.standard_b64encode(raw).decode()},
            },
            {"type": "text", "text": msg},
        ]
    else:
        content = msg
    r = _messages_create(
        max_tokens=8000 if regenerate else 5000,
        system=_system(theme_dir),
        tools=[FRAME_TOOL],
        tool_choice=_tool_choice(tool),
        messages=[{"role": "user", "content": content}],
    )
    return _tool_input(r, tool)["frame"]
