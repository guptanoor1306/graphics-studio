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
# Anthropic rejects high max_tokens on non-streaming calls; studio uses stream only server-side.
_MAX_TOKENS_NONSTREAM = 16384


def is_mf_theme(theme_dir: pathlib.Path) -> bool:
    return (theme_dir / "templates" / "render.js").is_file()


def is_reel_theme(theme_dir: pathlib.Path) -> bool:
    return theme_dir.name == "zero1-reel-graphics"


def is_zo_product_theme(theme_dir: pathlib.Path) -> bool:
    return theme_dir.name == "zo-product-graphics"


def is_hindi_charts_theme(theme_dir: pathlib.Path) -> bool:
    return theme_dir.name == "varsity-hindi-graphics"


def is_hindi_fa_theme(theme_dir: pathlib.Path) -> bool:
    return theme_dir.name == "varsity-hindi-fa-graphics"


def is_hindi_theme(theme_dir: pathlib.Path) -> bool:
    return is_hindi_charts_theme(theme_dir) or is_hindi_fa_theme(theme_dir)


def theme_rules(theme_dir: pathlib.Path) -> str:
    """Skill rules + asset index + style guide so specs use kit buildings, people, etc."""
    parts = []
    if is_reel_theme(theme_dir):
        rels = (
            "SKILL.md",
            "references/spec_format.md",
            "references/studio_brief.md",
            "references/Reel_Graphics_Rules.md",
            "references/Moodboard_Inventory.md",
            "references/Zero1_Reel_Graphics_Template_Spec.md",
            "scenes/example_spec.json",
            "assets/INDEX.md",
        )
    elif is_zo_product_theme(theme_dir):
        rels = (
            "SKILL.md",
            "references/spec_format.md",
            "references/studio_brief.md",
            "references/kit_breakdown.md",
            "references/anchor_plates.md",
            "references/deep/video_breakdowns.md",
            "assets/plates/plates.json",
            "scenes/example_spec.json",
            "assets/INDEX.md",
        )
    elif is_mf_theme(theme_dir):
        rels = (
            "SKILL.md",
            "references/spec_format.md",
            "references/studio_brief.md",
            "references/style_guide.md",
            "references/gift_city_breakdown.md",
            "scenes/gift_city_spec.json",
            "assets/INDEX.md",
        )
    elif is_hindi_fa_theme(theme_dir):
        rels = (
            "SKILL.md",
            "references/spec_format.md",
            "references/storyboard_rules.md",
            "references/assets.md",
            "examples/example_spec.json",
        )
    elif is_hindi_charts_theme(theme_dir):
        rels = (
            "SKILL.md",
            "references/spec_format.md",
            "references/studio_brief.md",
            "references/storyboard_rules.md",
            "scenes/example_spec.json",
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
ZO_SB_TOOL = {
    "name": "submit_storyboard",
    "description": "Return the Product IP storyboard and spec.json (FSS + anchor osa/ost/tos frames).",
    "input_schema": {
        "type": "object",
        "properties": {
            "storyboard": {"type": "string"},
            "spec": {
                "type": "object",
                "properties": {
                    "look": {"type": "object"},
                    "frames": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["id", "items"],
                            "properties": {
                                "id": {"type": "string"},
                                "mode": {"type": "string", "enum": ["fss", "osa", "ost", "tos"]},
                                "items": {"type": "array", "minItems": 1},
                            },
                            "additionalProperties": True,
                        },
                    },
                },
                "required": ["frames"],
            },
        },
        "required": ["storyboard", "spec"],
    },
}
HI_FA_SB_TOOL = {
    "name": "submit_storyboard",
    "description": "Return Varsity Hindi Elements storyboard and spec.json (frames with mode fss|osa|osa_center|blur|takeaways and els[]).",
    "input_schema": {
        "type": "object",
        "properties": {
            "storyboard": {"type": "string"},
            "spec": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "cast": {"type": "object"},
                    "frames": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["id", "mode", "els"],
                            "additionalProperties": True,
                        },
                    },
                },
                "required": ["frames"],
            },
        },
        "required": ["storyboard", "spec"],
    },
}
HI_SB_TOOL = {
    "name": "submit_storyboard",
    "description": "Return Varsity Hindi Charts storyboard and spec.json (frames with mode side|main|fss|blur|scene|takeaways).",
    "input_schema": {
        "type": "object",
        "properties": {
            "storyboard": {"type": "string"},
            "spec": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "frames": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["id", "mode"],
                            "additionalProperties": True,
                        },
                    },
                },
                "required": ["frames"],
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
GRAPHIC_BATCH_TOOL = {
    "name": "submit_graphic_batch",
    "description": (
        "From a human storyboard PDF: normalized storyboard text (first batch) and the next batch of "
        "renderable spec frames only. Skip footage, screen, and repeat beats."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "storyboard": {
                "type": "string",
                "description": "Batch 1 only: full SB Doc from the PDF, one line per beat with skill tags.",
            },
            "frames": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "object", "additionalProperties": True},
            },
            "spec_meta": {
                "type": "object",
                "description": "Batch 1 only for MF/reel kits: title and one-line look string.",
                "properties": {
                    "title": {"type": "string"},
                    "look": {"type": "string"},
                },
            },
            "pdf_progress": {
                "type": "string",
                "description": "Where this batch ended in the PDF (page or beat id).",
            },
        },
        "required": ["frames"],
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

_REEL_ROLE = (
    "You are the Zero1 reel graphics designer in the skill below. You run inside Graphics Studio (web app), not a chat: "
    "ignore Figma fetch limits, zip delivery, and local render.py — only return storyboard + spec via submit_storyboard. "
    "Follow SKILL.md hard rules and references/spec_format.md. Canvas is 1080×1920; centre all content in the safe zone. "
    "One theme per reel; never Theme 2 Light Pop. Types footage, screen, repeat are storyboard-only. "
    "Every FSS/OST/anchor beat needs a renderable frame (type fss, html, ost, or anchor) with complete html."
)

_HI_FA_ROLE = (
    "You are the Varsity Hindi Elements graphics designer (Fundamental Analysis, Futures, and story-driven FA IP) in the skill below. "
    "You run inside Graphics Studio (web app), not a chat: ignore local CLI build, zip delivery, and contact-sheet steps — only return storyboard + spec via submit_storyboard. "
    "Follow SKILL.md, references/spec_format.md, references/storyboard_rules.md, and examples/example_spec.json patterns. "
    "Canvas 1920×1080. Frame modes: fss, osa, osa_center, blur, takeaways — each frame uses els[] with type (char, card, header, prop, osa, …), not Charts items[]. "
    "Footage, screen, and repeat beats are storyboard-only; every graphic beat needs a renderable frame. "
    "On-screen text is English; cast uses six team characters (c1–c6). Company logos via logo elements."
)

_HI_ROLE = (
    "You are the Varsity Hindi Charts graphics designer (Technical Analysis IP) in the skill below. You run inside Graphics Studio (web app), not a chat: "
    "ignore local CLI build, zip delivery, and contact-sheet steps — only return storyboard + spec via submit_storyboard. "
    "Follow SKILL.md, references/spec_format.md, references/storyboard_rules.md, and scenes/example_spec.json patterns. "
    "Canvas 1920×1080. Frame modes: side, main, fss, blur, scene, takeaways — NOT English anchor/FSS. "
    "Footage, screen, and repeat beats are storyboard-only; every graphic beat needs a renderable frame with kit items (kite, diagram, roto, table, …). "
    "Use props/ and plates/ paths from assets/INDEX.md. Green/red only on candle and bar bodies."
)

_ZO_ROLE = (
    "You are the Zerodha Online Product IP graphics designer in the skill below. You run inside Graphics Studio (web app), not a chat: "
    "ignore local zip delivery and CLI build steps — only return storyboard + spec via submit_storyboard. "
    "Follow SKILL.md, references/spec_format.md, kit_breakdown.md, anchor_plates.md, and video_breakdowns (patterns only). Canvas is 1920×1080. "
    "Design for the user's script: ~90% house toolkit (component types, plates, INDEX illustrations, layout grammar from kit_breakdown) "
    "and ~10% fresh creative choices (headlines, which objects, compare pairings, anchor copy) — do NOT clone scenes/example_spec.json or ship unrelated Devolvement/SIF frames. "
    "spec.frames = FSS (mode fss) + anchor (osa|ost|tos with lower, punch, scroll_list, …). Set spec.look.plate from anchor_plates.md (default m1_wide_centre). "
    "One primary anchor graphic per frame (one lower OR one punch OR one side list — avoid stacking multiple punchlines on wide-centre plates). "
    "Screen capture, footage, repeat are storyboard-only. Copy script numbers exactly (Indian ₹ grouping)."
)


def _system(theme_dir):
    if is_reel_theme(theme_dir):
        role = _REEL_ROLE
    elif is_zo_product_theme(theme_dir):
        role = _ZO_ROLE
    elif is_hindi_fa_theme(theme_dir):
        role = _HI_FA_ROLE
    elif is_hindi_charts_theme(theme_dir):
        role = _HI_ROLE
    elif is_mf_theme(theme_dir):
        role = _MF_ROLE
    else:
        role = _ROLE
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
    client = _client()
    max_tokens = int(kwargs.get("max_tokens") or _MAX_TOKENS_NONSTREAM)
    use_stream = max_tokens > _MAX_TOKENS_NONSTREAM
    create_kwargs = {**kwargs, "model": MODEL, "max_tokens": max_tokens}

    def _via_stream():
        with client.messages.stream(**create_kwargs) as stream:
            return stream.get_final_message()

    if use_stream:
        return _via_stream()
    try:
        return client.messages.create(**create_kwargs)
    except Exception as exc:
        err = str(exc).lower()
        if "stream" in err and ("required" in err or "streaming" in err):
            return _via_stream()
        raise


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


def _format_ts(seconds: float) -> str:
    s = max(0, int(seconds))
    return f"{s // 60}:{s % 60:02d}"


def episode_transcript_prompt_block(transcript: dict | None) -> str:
    """Text block for Claude: VO timing from uploaded episode audio."""
    if not transcript or not isinstance(transcript, dict):
        return ""
    segments = transcript.get("segments") or []
    lines: list[str] = []
    for seg in segments[:400]:
        if not isinstance(seg, dict):
            continue
        t = (seg.get("text") or "").strip()
        if not t:
            continue
        start = float(seg.get("start") or 0)
        end = float(seg.get("end") or start)
        lines.append(f"[{_format_ts(start)}–{_format_ts(end)}] {t}")
    if not lines:
        plain = (transcript.get("text") or "").strip()
        if not plain:
            return ""
        body = plain[:12000]
    else:
        body = "\n".join(lines)
    return (
        "\n\nVO TRANSCRIPT (from uploaded episode audio — use as authoritative timing; "
        "storyboard ~timestamps and graphic frame ids m.ss / m.ss_b should align to these beats. "
        "Pasted SCRIPT is for exact numbers and spelling; when wording differs slightly, keep script numbers "
        "but prefer transcript times):\n"
        f"{body}\n"
    )


def _inject_transcript(msg: str, transcript: dict | None) -> str:
    block = episode_transcript_prompt_block(transcript)
    if not block:
        return msg
    if "\nSCRIPT:\n" in msg:
        return msg.replace("\nSCRIPT:\n", block + "\nSCRIPT:\n", 1)
    return msg + block


_ZO_ITEM_TYPES = frozenset({
    "heading", "compare", "hub2", "hub_fan", "cards", "positions", "chart", "bars", "formula",
    "status", "phone", "week", "exchange", "notepad", "objstat", "calendar", "note",
    "kite_watchlist", "kite_depth", "kite_chart", "auction", "text", "img", "pillv", "row", "html",
    "lower", "punch", "bignum", "side_list", "scroll_list", "objcards", "ticket", "mini_table", "ladder",
})
_ZO_ANCHOR_MODES = frozenset({"osa", "ost", "tos"})


def spec_quality_issues(spec: dict, storyboard: str = "", *, theme: str = "") -> list[str]:
    if theme == "varsity-hindi-fa-graphics":
        issues: list[str] = []
        _fa_modes = {"fss", "osa", "osa_center", "blur", "takeaways"}
        for f in (spec or {}).get("frames") or []:
            if not isinstance(f, dict):
                continue
            fid = f.get("id") or "?"
            mode = f.get("mode")
            if mode not in _fa_modes:
                issues.append(f'Frame "{fid}": mode must be fss|osa|osa_center|blur|takeaways.')
            if not (f.get("els") or []):
                issues.append(f'Frame "{fid}": add els[] (see spec_format.md).')
        return issues
    if theme == "varsity-hindi-graphics":
        issues: list[str] = []
        for f in (spec or {}).get("frames") or []:
            if not isinstance(f, dict):
                continue
            fid = f.get("id") or "?"
            mode = f.get("mode")
            if mode not in {"side", "main", "fss", "blur", "scene", "takeaways"}:
                issues.append(f'Frame "{fid}": mode must be side|main|fss|blur|scene|takeaways.')
            if mode == "takeaways":
                if not f.get("items"):
                    issues.append(f'Frame "{fid}": takeaways mode needs items[] strings.')
            elif not (f.get("items") or f.get("extras")):
                issues.append(f'Frame "{fid}": add items[] (or extras[] for takeaways).')
        return issues
    if theme == "zo-product-graphics":
        issues: list[str] = []
        frames = (spec or {}).get("frames") or []
        for f in frames:
            if not isinstance(f, dict):
                continue
            fid = f.get("id") or "?"
            mode = str(f.get("mode") or "fss").strip().lower()
            if mode not in ({"fss"} | _ZO_ANCHOR_MODES):
                issues.append(f'Frame "{fid}": mode must be fss, osa, ost, or tos (not "{mode}").')
            items = f.get("items") or []
            if mode == "fss" and not items:
                issues.append(f'Frame "{fid}": FSS frame needs at least one items[] entry.')
            if mode in _ZO_ANCHOR_MODES:
                if mode == "tos" and not f.get("title") and not items:
                    issues.append(f'Frame "{fid}": TOS frame needs title and/or anchor items[].')
                elif mode != "tos" and not items:
                    issues.append(f'Frame "{fid}": anchor frame needs at least one items[] entry.')
                plate = f.get("plate") or (spec.get("look") or {}).get("plate") if isinstance(spec.get("look"), dict) else None
                from mf_studio import ZO_PLATE_KEYS, _ZO_SIDE_PANEL_TYPES

                if plate and plate not in ZO_PLATE_KEYS and plate not in ("default", ""):
                    issues.append(f'Frame "{fid}": unknown plate {plate!r} — use keys from anchor_plates.md.')
                if len(items) > 2 and not ({it.get("t") for it in items} & _ZO_SIDE_PANEL_TYPES):
                    issues.append(
                        f'Frame "{fid}": too many stacked anchor items — use one lower/punch OR move list to side_list/scroll_list on m1_close_left.'
                    )
            for it in items:
                if isinstance(it, dict) and it.get("t") and it["t"] not in _ZO_ITEM_TYPES:
                    issues.append(f'Frame "{fid}": unknown item type "{it["t"]}" — see spec_format.md.')
        if len(frames) >= 2 and not any(
            isinstance(f, dict) and ((f.get("items") or []) or (f.get("mode") == "tos" and f.get("title")))
            for f in frames
        ):
            issues.append("No renderable items in spec.frames.")
        return issues
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


def _call_with_pdf(
    theme_dir,
    msg: str,
    pdf_bytes: bytes,
    *,
    sb_tool: dict | None = None,
    page_images: list[tuple[str, bytes]] | None = None,
    max_tokens: int = 16384,
) -> dict:
    import base64

    tool_schema = sb_tool or GRAPHIC_BATCH_TOOL
    tool = tool_schema["name"]
    if _tool_choice(tool)["type"] == "auto":
        msg += f"\n\nRespond only by calling the {tool} tool."
    preface = ""
    if page_images:
        preface = (
            "The storyboard PDF is attached below as a document, followed by JPEG renders of each page "
            "(use these for timestamps, small type, and sketches).\n\n"
        )
    content: list[dict] = [
        {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": base64.standard_b64encode(pdf_bytes).decode(),
            },
        },
    ]
    for media, raw in (page_images or [])[:20]:
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
    content.append({"type": "text", "text": preface + msg})
    r = _messages_create(
        max_tokens=max_tokens,
        system=_system(theme_dir),
        tools=[tool_schema],
        tool_choice=_tool_choice(tool),
        messages=[{"role": "user", "content": content}],
    )
    return _tool_input(r, tool)


def _pdf_batch_rules(theme_dir: pathlib.Path, look: dict) -> str:
    if is_hindi_fa_theme(theme_dir):
        return (
            "GRAPHICS STUDIO RULES (Varsity Hindi Elements):\n"
            "- spec.frames: modes fss | osa | osa_center | blur | takeaways; each frame uses els[] per spec_format.md.\n"
            "- Footage/screen/repeat → storyboard only.\n"
            "- Set spec.cast for named people; char elements use who + pose + expr.\n"
            "Follow SKILL.md + spec_format.md + storyboard_rules.md.\n"
        )
    if is_hindi_charts_theme(theme_dir):
        return (
            "GRAPHICS STUDIO RULES (Varsity Hindi Charts):\n"
            "- spec.frames: modes side | main | fss | blur | scene | takeaways per spec_format.md.\n"
            "- Footage/screen/repeat → storyboard only.\n"
            "- Kite/diagram frames need valid gen/candles data; copy script numbers exactly.\n"
            "Follow SKILL.md + spec_format.md + studio_brief.md + storyboard_rules.md.\n"
        )
    if is_zo_product_theme(theme_dir):
        plate_hint = ""
        if isinstance(look, dict) and look.get("plate") and look.get("plate") not in ("default", ""):
            plate_hint = f"- Project look.plate is {look['plate']!r} — use on anchor frames unless a frame needs another key from anchor_plates.md.\n"
        else:
            plate_hint = "- Set spec.look.plate to m1_wide_centre (or f1_centre_circle for female-anchor concepts) per anchor_plates.md.\n"
        return (
            "GRAPHICS STUDIO RULES (Zerodha Online Product IP):\n"
            "- spec.frames: FSS (mode fss) AND anchor (mode osa | ost | tos). Every OSA/OST/TOS PDF beat → matching frame with plate + items.\n"
            "- Storyboard tags: FSS | OSA | OST | TOS | Screen | Footage | Repeat. Screen/footage/repeat NOT in frames.\n"
            f"{plate_hint}"
            "- ~90% kit grammar (kit_breakdown, INDEX assets, plates) ~10% script-specific wording/layout.\n"
            "- Anchor: one main item on wide-centre plates; side lists → m1_close_left; TOS → m1_tos + title.\n"
            "- Kite UI mocks where needed; copy numbers exactly from script/PDF.\n"
            "Follow SKILL.md + spec_format.md + kit_breakdown.md + anchor_plates.md + studio_brief.md.\n"
        )
    if is_mf_theme(theme_dir):
        look_line = (look.get("look_line") or "").strip()
        if is_reel_theme(theme_dir):
            return (
                f"Spec root look (one line): {look_line or 'Theme A · Cream Editorial per SKILL'}\n"
                "GRAPHICS STUDIO RULES (Zero1 reel):\n"
                "- Canvas 1080×1920. frames ONLY: fss, html, ost, anchor.\n"
                "- No footage/screen/repeat in frames — storyboard text only.\n"
                "- Number frames 01, 02… in PDF order. Rich `html` in safe zone; data-mf-path on major blocks.\n"
                "Follow SKILL.md + references/spec_format.md + Reel_Graphics_Rules.md.\n"
            )
        return (
            f"Spec root look (one line): {look_line or 'anchor right · GIFT City house style per SKILL'}\n"
            "GRAPHICS STUDIO RULES (MF kit):\n"
            "- frames ONLY for PNG graphics: scene, ribbon, sop, table, cycle, points, definition, anchor, html.\n"
            "- Footage/screen/repeat → storyboard string only.\n"
            "- Timestamp storyboard PDFs: ONE frame per distinct graphic PNG in the PDF (often ~15–25 total for a reel). "
            "Rows marked footage/screen/repeat, B-roll, VO-only, or “same chart continues” / minor chart tweaks → storyboard text ONLY — not a new frame.\n"
            "- When every graphic PNG is already in ALREADY GENERATED ids, return frames: [] and set pdf_progress to done.\n"
            "- Every frame object MUST include string `id` (01, 02, …) and string `type` from the skill.\n"
            "- Match gift_city_spec.json density; copy numbers from PDF and/or script.\n"
            "Follow SKILL.md + references/spec_format.md + gift_city_breakdown.md.\n"
        )
    props = look.get("props") or ([look["prop"]] if look.get("prop") and look.get("prop") != "none" else [])
    return (
        f"Look (use in frames): {json.dumps(look)}\n"
        f"Topic props: {json.dumps(props if props else [])}\n"
        f"{_graphics_mix_rules(look)}"
        "Follow app_storyboard_overrides.md + studio_brief.md: tag OST/OSA/FSS; frames must match tags.\n"
    )


def _normalize_pdf_batch_out(out: dict) -> dict:
    frames = out.get("frames")
    if not frames and isinstance(out.get("spec"), dict):
        frames = out["spec"].get("frames")
    if not isinstance(frames, list):
        frames = []
    out["frames"] = frames
    if not (out.get("storyboard") or "").strip() and isinstance(out.get("spec"), dict):
        out["storyboard"] = out["spec"].get("storyboard") or ""
    if not out.get("spec_meta") and isinstance(out.get("spec"), dict):
        sp = out["spec"]
        meta = {}
        if sp.get("title"):
            meta["title"] = sp["title"]
        if sp.get("look"):
            meta["look"] = sp["look"]
        if meta:
            out["spec_meta"] = meta
    return out


def _ensure_frame_ids(frames: list, occupied: set[str]) -> list[dict]:
    cleaned: list[dict] = []
    n = 1
    for fr in frames:
        if not isinstance(fr, dict):
            continue
        fid = str(fr.get("id") or "").strip()
        if not fid:
            while f"{n:02d}" in occupied:
                n += 1
            fid = f"{n:02d}"
            n += 1
            fr = {**fr, "id": fid}
        if fid in occupied:
            continue
        occupied.add(fid)
        cleaned.append(fr)
    return cleaned


def storyboard_pdf_batch(
    theme_dir: pathlib.Path,
    pdf_bytes: bytes,
    script: str,
    look: dict,
    notes: str = "",
    *,
    batch_size: int = 5,
    finish_all: bool = False,
    existing_spec: dict | None = None,
    existing_storyboard: str = "",
    episode_transcript: dict | None = None,
) -> dict:
    """Read human SB PDF; return next batch of frames (+ storyboard on first batch)."""
    from storyboard_pdf import raster_pages

    page_images = raster_pages(pdf_bytes)
    if finish_all:
        return _storyboard_pdf_finish_all(
            theme_dir,
            pdf_bytes,
            script,
            look,
            notes,
            batch_size=batch_size,
            existing_spec=existing_spec,
            existing_storyboard=existing_storyboard,
            episode_transcript=episode_transcript,
            page_images=page_images,
        )
    return _storyboard_pdf_batch_once(
        theme_dir,
        pdf_bytes,
        script,
        look,
        notes,
        batch_size=batch_size,
        existing_spec=existing_spec,
        existing_storyboard=existing_storyboard,
        episode_transcript=episode_transcript,
        page_images=page_images,
    )


def _storyboard_pdf_finish_all(
    theme_dir: pathlib.Path,
    pdf_bytes: bytes,
    script: str,
    look: dict,
    notes: str,
    *,
    batch_size: int,
    existing_spec: dict | None,
    existing_storyboard: str,
    episode_transcript: dict | None,
    page_images: list | None = None,
) -> dict:
    """Run repeated PDF batches (each non-streaming-safe) until no new frames."""
    working_spec = dict(existing_spec or {})
    storyboard = (existing_storyboard or "").strip()
    accumulated: list[dict] = []
    last_progress = ""
    raw_total = 0
    spec_meta: dict = {}
    for _ in range(40):
        out = _storyboard_pdf_batch_once(
            theme_dir,
            pdf_bytes,
            script,
            look,
            notes,
            batch_size=batch_size,
            existing_spec=working_spec,
            existing_storyboard=storyboard,
            episode_transcript=episode_transcript,
            page_images=page_images,
        )
        raw_total += out.get("raw_frame_count", 0)
        added = int(out.get("frames_added") or 0)
        if out.get("storyboard") and not storyboard:
            storyboard = out.get("storyboard") or ""
        meta = out.get("spec_meta")
        if isinstance(meta, dict) and meta and not spec_meta:
            spec_meta = meta
        if not added:
            break
        new_frames = list(out.get("frames") or [])
        accumulated.extend(new_frames)
        working_spec = {
            **working_spec,
            "frames": list(working_spec.get("frames") or []) + new_frames,
        }
        last_progress = out.get("pdf_progress") or last_progress
    return {
        "storyboard": storyboard,
        "frames": accumulated,
        "spec_meta": spec_meta,
        "pdf_progress": last_progress,
        "frames_added": len(accumulated),
        "raw_frame_count": raw_total,
    }


def _storyboard_pdf_batch_once(
    theme_dir: pathlib.Path,
    pdf_bytes: bytes,
    script: str,
    look: dict,
    notes: str,
    *,
    batch_size: int = 5,
    existing_spec: dict | None = None,
    existing_storyboard: str = "",
    episode_transcript: dict | None = None,
    page_images: list | None = None,
) -> dict:
    """Single Claude call for the next PDF graphics batch."""
    from storyboard_pdf import raster_pages

    existing_spec = existing_spec or {}
    existing_frames = existing_spec.get("frames") or []
    done_ids = [f["id"] for f in existing_frames if isinstance(f, dict) and f.get("id")]
    first_batch = not done_ids
    batch_size = max(1, min(10, int(batch_size)))
    if page_images is None:
        page_images = raster_pages(pdf_bytes)
    max_tokens = _MAX_TOKENS_NONSTREAM
    rules = _pdf_batch_rules(theme_dir, look)
    if first_batch:
        batch_line = (
            f"BATCH: Generate exactly up to {batch_size} renderable graphic frames from the START of the PDF "
            "(in story/time order)."
        )
    else:
        batch_line = (
            f"BATCH: Generate the NEXT up to {batch_size} renderable graphic frames after the last generated id, "
            "in PDF order."
        )
    if first_batch:
        msg = (
            "The attached PDF is the team's human storyboard (may include sketches, screenshots, timestamps, and notes).\n"
            "Read every page (document + page images). The PDF is the source of truth for WHICH beats need graphics.\n\n"
            f"Notes: {notes or 'none'}\n\n"
            f"{rules}\n"
            f"{batch_line} Put transcribed storyboard lines in `storyboard` (all beats you can read, not only this batch).\n"
            "Each item in `frames` MUST have a unique string `id` (e.g. 01, 02). Use submit_graphic_batch only.\n"
            "Voiceover script below is OPTIONAL — use it for exact numbers/wording when the PDF does not spell them out:\n\n"
            f"SCRIPT:\n{script.strip() or '(none — infer copy from PDF)'}"
        )
    else:
        msg = (
            "Same human storyboard PDF attached (document + page images).\n\n"
            f"Notes: {notes or 'none'}\n\n"
            f"{rules}\n"
            f"ALREADY GENERATED frame ids (do NOT duplicate): {json.dumps(done_ids)}\n\n"
            f"Existing storyboard text:\n{existing_storyboard[:12000]}\n\n"
            f"{batch_line} Return `frames` only (omit storyboard unless fixing a typo). Set pdf_progress.\n"
            f"Optional script:\n\n{script or '(none)'}"
        )
    msg = _inject_transcript(msg, episode_transcript)

    def _call(msg_text: str) -> dict:
        return _call_with_pdf(
            theme_dir,
            msg_text,
            pdf_bytes,
            page_images=page_images,
            max_tokens=max_tokens,
        )

    out = _call(msg)
    out = _normalize_pdf_batch_out(out)
    frames = _ensure_frame_ids(out.get("frames") or [], set(done_ids))
    if not frames and first_batch:
        retry = (
            msg
            + "\n\nRETRY: Your last response had no usable frames. Call submit_graphic_batch with a non-empty "
            "`frames` array. Each frame needs id + type (MF) or id + mode + items (Zo/varsity)."
        )
        out = _normalize_pdf_batch_out(_call(retry))
        frames = _ensure_frame_ids(out.get("frames") or [], set(done_ids))
    seen = set(done_ids)
    added = sum(1 for fr in frames if fr.get("id") not in seen)
    return {
        "storyboard": out.get("storyboard") or "",
        "frames": frames,
        "spec_meta": out.get("spec_meta") or {},
        "pdf_progress": out.get("pdf_progress") or "",
        "frames_added": added,
        "raw_frame_count": len(out.get("frames") or []),
    }


def storyboard(
    theme_dir: pathlib.Path,
    script: str,
    look: dict,
    notes: str = "",
    *,
    episode_transcript: dict | None = None,
) -> dict:
    if is_hindi_fa_theme(theme_dir):
        msg = _inject_transcript(
            (
            f"Notes: {notes or 'none'}\n\n"
            "GRAPHICS STUDIO RULES (Varsity Hindi Elements):\n"
            "- spec.frames[]: each graphic beat with id (timestamp like 0.21), mode, and els[] from spec_format.md.\n"
            "- Modes: fss (full set), osa / osa_center (presenter), blur, takeaways.\n"
            "- Footage, screen, repeat → storyboard string only — NOT in spec.frames.\n"
            "- Characters via type char; buildings/props from assets/; logos via type logo.\n"
            "- Match examples/example_spec.json density; on-screen copy in English.\n\n"
            "Follow SKILL.md + references/spec_format.md + references/storyboard_rules.md.\n\n"
            f"SCRIPT:\n{script}"
            ),
            episode_transcript,
        )
        out = _call_storyboard(theme_dir, msg, sb_tool=HI_FA_SB_TOOL)
        for _ in range(2):
            issues = spec_quality_issues(out["spec"], out.get("storyboard") or "", theme="varsity-hindi-fa-graphics")
            if not issues:
                break
            retry = _inject_transcript(
                (
                "Your previous Varsity Hindi Elements spec was rejected. Fix ALL issues; return storyboard + spec only:\n"
                + "\n".join(f"- {x}" for x in issues)
                + f"\n\nNotes: {notes or 'none'}\n\nSCRIPT:\n{script}"
                ),
                episode_transcript,
            )
            out = _call_storyboard(theme_dir, retry, sb_tool=HI_FA_SB_TOOL)
        return out
    if is_hindi_charts_theme(theme_dir):
        msg = _inject_transcript(
            (
            f"Notes: {notes or 'none'}\n\n"
            "GRAPHICS STUDIO RULES (Varsity Hindi Charts):\n"
            "- spec.frames[]: each graphic beat with id (timestamp like 2.49), mode, and items from spec_format.md.\n"
            "- Modes: side (presenter left), main (centre cam), fss (charts), blur (tables), scene (plates/scene_*), takeaways.\n"
            "- Footage, screen, repeat → storyboard string only — NOT in spec.frames.\n"
            "- Use kite/diagram/mini for charts; roto/title/bullets for teaching beats; assets from props/ and plates/.\n"
            "- Match examples/example_spec.json density; green/red only on candle/bar bodies.\n\n"
            "Follow SKILL.md + references/spec_format.md + references/storyboard_rules.md + studio_brief.md.\n\n"
            f"SCRIPT:\n{script}"
            ),
            episode_transcript,
        )
        out = _call_storyboard(theme_dir, msg, sb_tool=HI_SB_TOOL)
        for _ in range(2):
            issues = spec_quality_issues(out["spec"], out.get("storyboard") or "", theme="varsity-hindi-graphics")
            if not issues:
                break
            retry = _inject_transcript(
                (
                "Your previous Varsity Hindi spec was rejected. Fix ALL issues; return storyboard + spec only:\n"
                + "\n".join(f"- {x}" for x in issues)
                + f"\n\nNotes: {notes or 'none'}\n\nSCRIPT:\n{script}"
                ),
                episode_transcript,
            )
            out = _call_storyboard(theme_dir, retry, sb_tool=HI_SB_TOOL)
        return out
    if is_zo_product_theme(theme_dir):
        plate_hint = ""
        if isinstance(look, dict) and look.get("plate") and look.get("plate") not in ("default", ""):
            plate_hint = f"- Project look.plate is {look['plate']!r} — use on anchor frames unless a frame needs another key from anchor_plates.md.\n"
        else:
            plate_hint = "- Set spec.look.plate to m1_wide_centre (or f1_centre_circle for female-anchor concept videos) per anchor_plates.md.\n"
        msg = _inject_transcript(
            (
            f"Notes: {notes or 'none'}\n\n"
            "GRAPHICS STUDIO RULES (Zerodha Online Product IP):\n"
            "- spec.frames: FSS (mode fss) AND anchor (mode osa | ost | tos). Every OSA/OST/TOS storyboard beat → matching spec frame with plate + items.\n"
            "- Storyboard tags: FSS | OSA | OST | TOS | Screen | Footage | Repeat. Screen/footage/repeat NOT in spec.frames.\n"
            f"{plate_hint}"
            "- CREATIVE MIX: ~90% kit grammar (kit_breakdown + video_breakdowns component picks, plates, INDEX assets) "
            "~10% new for THIS script (wording, metaphors, which compare/chart). Do NOT reuse example_spec.json frame content for unrelated topics.\n"
            "- Anchor layout: one main item per frame on wide-centre plates; side lists → plate m1_close_left; TOS → m1_tos + title field.\n"
            "- Fewest frames; a/b/c only when the same picture gains new facts (max 3 states).\n"
            "- Kite UI: kite_watchlist, kite_depth, kite_chart, auction — vector mocks; script numbers exactly (Indian grouping).\n\n"
            "Follow SKILL.md + spec_format.md + kit_breakdown.md + anchor_plates.md + studio_brief.md.\n\n"
            f"SCRIPT:\n{script}"
            ),
            episode_transcript,
        )
        out = _call_storyboard(theme_dir, msg, sb_tool=ZO_SB_TOOL)
        from mf_studio import compact_zo_spec_for_studio

        spec = compact_zo_spec_for_studio(out.get("spec") or {})
        if isinstance(look, dict) and look.get("plate"):
            lk = spec.setdefault("look", {})
            if isinstance(lk, dict):
                lk.setdefault("plate", look["plate"])
        out["spec"] = spec
        for _ in range(2):
            issues = spec_quality_issues(out["spec"], out.get("storyboard") or "", theme="zo-product-graphics")
            if not issues:
                break
            retry = _inject_transcript(
                (
                "Your previous zo-product spec was rejected by the studio quality gate. Fix ALL issues; "
                "return storyboard + spec via submit_storyboard only:\n"
                + "\n".join(f"- {x}" for x in issues)
                + f"\n\nNotes: {notes or 'none'}\n\nSCRIPT:\n{script}"
                ),
                episode_transcript,
            )
            out = _call_storyboard(theme_dir, retry, sb_tool=ZO_SB_TOOL)
            spec = compact_zo_spec_for_studio(out.get("spec") or {})
            if isinstance(look, dict) and look.get("plate"):
                lk = spec.setdefault("look", {})
                if isinstance(lk, dict):
                    lk.setdefault("plate", look["plate"])
            out["spec"] = spec
        return out
    if is_mf_theme(theme_dir):
        look_line = (look.get("look_line") or "").strip()
        if is_reel_theme(theme_dir):
            msg = _inject_transcript(
                (
                f"Spec root look (one line — copy into spec.look): {look_line or 'Theme A · Cream Editorial per SKILL'}\n"
                f"Notes: {notes or 'none'}\n\n"
                "GRAPHICS STUDIO RULES (Zero1 reel):\n"
                "- Canvas 1080×1920. spec.frames ONLY for static graphics: fss, html, ost, anchor.\n"
                "- Do NOT put footage, screen, or repeat in spec.frames — storyboard text only.\n"
                "- Number frames 01, 02… in storyboard row order. Each graphic needs rich `html` (centred safe zone).\n"
                "- Copy numbers exactly from script / data sheet. One theme for the whole reel.\n"
                "- Use data-mf-path on major blocks in html for studio layer editing.\n\n"
                "Follow SKILL.md + references/spec_format.md + Reel_Graphics_Rules.md.\n\n"
                f"SCRIPT:\n{script}"
                ),
                episode_transcript,
            )
        else:
            msg = _inject_transcript(
                (
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
                ),
                episode_transcript,
            )
        out = _call_storyboard(theme_dir, msg, sb_tool=MF_SB_TOOL)
        return out

    props = look.get("props") or ([look["prop"]] if look.get("prop") and look.get("prop") != "none" else [])
    msg = _inject_transcript(
        (
        f"Look (copy into spec.look): {json.dumps(look)}\n"
        f"Topic props — first only as corner dressing; all checked guide OSA kit choices: {json.dumps(props if props else [])}\n"
        f"Notes: {notes or 'none'}\n\n"
        f"{_graphics_mix_rules(look)}"
        f"Follow app_storyboard_overrides.md + studio_brief.md: tag each beat OST/OSA/FSS in storyboard; spec must match tags.\n"
        f"Copy numbers exactly from the script.\n\nSCRIPT:\n{script}"
        ),
        episode_transcript,
    )
    out = _call_storyboard(theme_dir, msg)
    out["spec"] = enrich_spec(_merge_user_look(out.get("spec") or {}, look), out.get("storyboard") or "")
    for _ in range(2):
        issues = spec_quality_issues(out["spec"], out.get("storyboard") or "")
        if not issues:
            break
        retry = _inject_transcript(
            (
            "Your previous spec was rejected by the app quality gate. Fix ALL issues and return a complete "
            "storyboard + spec via submit_storyboard only:\n"
            + "\n".join(f"- {x}" for x in issues)
            + f"\n\nLook: {json.dumps(look)}\n\nSCRIPT:\n{script}"
            ),
            episode_transcript,
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
    if is_mf_theme(theme_dir) or is_zo_product_theme(theme_dir):
        kit = "Product IP" if is_zo_product_theme(theme_dir) else "MF"
        sb_excerpt = (storyboard_full or "")[:6000]
        if regenerate:
            msg = (
                f"Storyboard line: {storyboard_line or '(none)'}\nContext:\n{sb_excerpt or '(none)'}\n\n"
                f"Current frame JSON ({kit} spec — keep id unless asked):\n"
                f"{json.dumps(frame, ensure_ascii=False)}\n\n"
                "REGENERATE this frame for the same beat. Match references/spec_format.md.\n"
                "Make a visibly fresh version vs the current JSON: change layout emphasis, headline/sub copy, "
                "card labels, or component params while keeping the same beat facts and script numbers.\n"
            )
            if is_zo_product_theme(theme_dir):
                msg += (
                    "Zo Product IP: keep valid plate from anchor_plates.md; anchor = one primary item when possible. "
                    "~90% kit components, ~10% fresh copy vs the current JSON.\n"
                )
        else:
            msg = (
                f"Current frame JSON:\n{json.dumps(frame, ensure_ascii=False)}\n\n"
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
