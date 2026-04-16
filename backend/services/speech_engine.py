from __future__ import annotations
import random
from services.state import get_world

def current_room_tag(character) -> str:
    world = get_world()
    pos = character.position
    tile = world["grid"]["tiles"].get(f"{pos['x']},{pos['y']}", {})
    return tile.get("room_tag") or tile.get("tile_type") or "unknown"

def nearby_tagged_people(character, max_distance: int = 2):
    world = get_world()
    tagged = world.get("tagged_characters", {})
    pos = character.position
    out = []
    for char_id, c in tagged.items():
        if c["profile"]["id"] == character.profile.id:
            continue
        other_pos = c.get("position", {})
        dist = abs(other_pos.get("x", 999) - pos["x"]) + abs(other_pos.get("y", 999) - pos["y"])
        if dist <= max_distance:
            out.append(c)
    return out

def mood_bucket(character) -> str:
    s = character.state
    needs = s.needs
    if max(needs.hunger, needs.thirst, needs.bladder, needs.sleep) >= 90:
        return "urgent"
    if s.stress >= 70:
        return "stressed"
    if s.fatigue >= 75:
        return "tired"
    if s.mood.startswith("roaming_to"):
        return "wandering"
    if s.mood == "busy":
        return "busy"
    return "neutral"

def pick_line(character, activity_tag: str | None = None) -> str:
    room = current_room_tag(character)
    nearby = nearby_tagged_people(character)
    mood = mood_bucket(character)

    names = [p["profile"]["name"] for p in nearby]
    nearby_name = names[0] if names else None

    lines = []

    # Activity-specific
    if activity_tag == "conversation":
        lines += [
            "Hey, want to talk for a minute?",
            "What have you been up to lately?",
            "I was just thinking about something interesting.",
        ]
        if nearby_name:
            lines += [
                f"Hey {nearby_name}, got a moment?",
                f"{nearby_name}, I wanted to ask you something.",
            ]

    if activity_tag == "phone_call":
        lines += [
            "Hi, just calling to check in.",
            "Hey, I had a minute and thought I'd call.",
            "How are things on your side?",
        ]

    if activity_tag == "sleep":
        lines += [
            "I really need to lie down.",
            "I can barely keep my eyes open.",
        ]

    if activity_tag == "eat":
        lines += [
            "I should eat something.",
            "I'm getting really hungry.",
        ]

    if activity_tag == "hygiene":
        lines += [
            "I need a quick bathroom break.",
            "Be right back.",
        ]

    if activity_tag == "stress_relief":
        lines += [
            "I need to unwind a bit.",
            "Let me just relax for a moment.",
        ]

    if activity_tag == "cooking":
        lines += [
            "Let's see what I can make here.",
            "I could cook something decent.",
        ]

    if activity_tag == "general_study" or activity_tag == "psychology" or activity_tag == "history":
        lines += [
            "I want to focus on this for a while.",
            "Let me think this through carefully.",
        ]

    # Room-sensitive
    if room == "kitchen":
        lines += [
            "The kitchen smells nice.",
            "Maybe I can do something useful in here.",
        ]
    elif room == "living_room":
        lines += [
            "This feels like a good place to hang out.",
            "I could relax here for a bit.",
        ]
    elif room == "bedroom":
        lines += [
            "It's quieter in here.",
            "This room feels restful.",
        ]
    elif room == "bathroom":
        lines += [
            "Just a second.",
            "I'll be out in a moment.",
        ]
    elif room == "yard":
        lines += [
            "Fresh air helps.",
            "It's nice to be outside for a bit.",
        ]

    # Mood-sensitive
    if mood == "urgent":
        lines += [
            "I really need to deal with this now.",
            "This can't wait any longer.",
        ]
    elif mood == "stressed":
        lines += [
            "I'm feeling a bit tense.",
            "I need a moment to decompress.",
        ]
    elif mood == "tired":
        lines += [
            "I'm exhausted.",
            "My energy is crashing.",
        ]
    elif mood == "wandering":
        lines += [
            "Let's see what's over there.",
            "Maybe there's something interesting nearby.",
        ]
    elif mood == "neutral":
        lines += [
            "Alright.",
            "Let's see.",
        ]

    # Nearby-person-sensitive
    if nearby_name:
        lines += [
            f"Oh, hi {nearby_name}.",
            f"I didn't expect to run into you, {nearby_name}.",
        ]
        if room in {"living_room", "yard", "kitchen"}:
            lines += [
                f"{nearby_name}, this seems like a nice place to talk.",
            ]

    # Fallback
    if not lines:
        lines = ["Hmm.", "Okay.", "Let's do that."]

    return random.choice(lines)
