"""Who plays whom: one of the team's Varsity characters per person, the same in every frame of the video.

The characters are the team's six (assets/chars6/c1..c6, shared with the Varsity Hindi kits) plus c7, a second
woman (Character 3 with a green dress and black hair) so two women never become a man and a woman.
  women: c3 (coral), c7 (green)          men: c1, c2, c4, c6, c5
A person item can name its character outright ("who": "c3"); otherwise gender comes from "gender", "bindi",
long hair or the name, and characters are handed out in order of first appearance.
"""
from __future__ import annotations

import re

WOMEN = ["c3", "c7"]
MEN = ["c1", "c2", "c4", "c6", "c5"]
ALL = set(WOMEN + MEN)

_FEMALE_NAMES = set("""
priya neha anjali pooja puja sneha kavya riya ria ananya aisha ayesha meera mira sunita anita radha shreya divya isha
nisha lakshmi laxmi deepa deepika swati simran aditi tanvi sakshi shruti payal rekha geeta gita seema asha nidhi rashmi
megha sonia maya sara zara fatima nandini kritika preeti mansi ishita ritu jyoti kajal komal pallavi poonam rani
roshni sapna shalini shilpa shweta smita sonal sunaina tanya trisha usha vidya kiara kriti naina pinky pari tara
""".split())
_FEMALE_WORDS = re.compile(r"\b(mrs|ms|miss|woman|women|lady|girl|mother|mom|mum|maa|wife|sister|didi|aunt|aunty|daughter|she|her|grandma|dadi|nani)\b", re.I)
_MALE_WORDS = re.compile(r"\b(mr|man|men|boy|father|dad|papa|husband|brother|bhai|uncle|son|he|him|grandpa|dada|nana)\b", re.I)


def gender_of(item: dict) -> str:
    """'f' or 'm' for a person item (default 'm' only when nothing says otherwise)."""
    g = str(item.get("gender") or "").strip().lower()
    if g in ("f", "female", "woman", "w", "girl"):
        return "f"
    if g in ("m", "male", "man", "boy"):
        return "m"
    if item.get("bindi") or str(item.get("hair") or "").lower() in ("long", "bun", "ponytail", "plait"):
        return "f"
    name = str(item.get("name") or "")
    first = re.split(r"[\s'’]", name.strip().lower())[0] if name.strip() else ""
    if first in _FEMALE_NAMES or _FEMALE_WORDS.search(name):
        return "f"
    if _MALE_WORDS.search(name):
        return "m"
    return "m"


def _key(item: dict) -> str:
    name = str(item.get("name") or "").strip().lower()
    if name:
        return "name:" + name
    return "anon:" + gender_of(item) + ":" + str(item.get("color") or "").upper()


def build_cast(frames: list) -> dict:
    """{person key -> character id} for a whole video. Named people choose first (in order of first appearance),
    so an unnamed "you" figure never takes the character a named person needs; unnamed figures get what's left."""
    people = []
    for f in frames or []:
        for it in (f.get("items") or []) if isinstance(f, dict) else []:
            if isinstance(it, dict) and it.get("t") == "person" and not it.get("doodle") and not it.get("src"):
                if _key(it) not in [k for k, _ in people]:
                    people.append((_key(it), it))
    cast, used = {}, set()
    for named in (True, False):
        for k, it in people:
            if k.startswith("name:") != named:
                continue
            who = str(it.get("who") or "").lower()
            if who in ALL:
                cast[k] = who
            else:
                pool = WOMEN if gender_of(it) == "f" else MEN
                free = [c for c in pool if c not in used]
                cast[k] = free[0] if free else pool[len(cast) % len(pool)]
            used.add(cast[k])
    return cast


def character_for(item: dict, cast: dict) -> str:
    who = str(item.get("who") or "").lower()
    if who in ALL:
        return who
    return cast.get(_key(item)) or (WOMEN[0] if gender_of(item) == "f" else MEN[0])


# old spec poses -> rig poses
POSE_ALIASES = {"pointing": "point_right", "point": "point_right", "standing": "idle", "stand": "idle",
                "thinking": "think", "explaining": "explain", "holding": "hold", "giving": "give"}
