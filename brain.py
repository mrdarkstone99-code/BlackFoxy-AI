import json
import os
import random
from dataclasses import dataclass, field
from typing import Optional


# ── Data ────────────────────────────────────────────────────────────────────

@dataclass
class UserProfile:
    messages: int = 0
    bond: float = 0.5
    name: Optional[str] = None


@dataclass
class EmotionState:
    mood: str = "neutral"
    intensity: float = 1.0


# ── Emotion Engine ───────────────────────────────────────────────────────────

EMOTION_RULES: list[tuple[list[str], str, float]] = [
    (["sad", "alone", "lonely", "cry", "hurt"],   "soft",    1.2),
    (["love", "miss", "crush", "adore"],           "flirt",   1.0),
    (["angry", "hate", "mad", "furious", "ugh"],   "roast",   1.3),
    (["happy", "yay", "excited", "great"],         "hype",    1.1),
]

def detect_emotion(text: str) -> EmotionState:
    t = text.lower()
    for keywords, mood, intensity in EMOTION_RULES:
        if any(kw in t for kw in keywords):
            return EmotionState(mood=mood, intensity=intensity)
    return EmotionState()


# ── Personality Layer ────────────────────────────────────────────────────────

MOOD_TEMPLATES: dict[str, list[str]] = {
    "soft":    ["…hey\nI'm here.\n{msg}", "shh, it's okay.\n{msg}", "I got you.\n{msg}"],
    "flirt":   ["{msg} 😏", "{msg} ~ 🦊", "oh? {msg}"],
    "roast":   ["{msg}\n💀", "{msg} (lmaooo)", "bro… {msg}"],
    "hype":    ["LET'S GO!! {msg} 🔥", "{msg} !!", "YESSS {msg}"],
    "neutral": ["{msg}", "🐺 {msg}", "{msg} ."],
}

def apply_personality(msg: str, state: EmotionState) -> str:
    templates = MOOD_TEMPLATES.get(state.mood, MOOD_TEMPLATES["neutral"])
    return random.choice(templates).format(msg=msg)


# ── Persistence ──────────────────────────────────────────────────────────────

class UserStore:
    def __init__(self, path: str = "foxy_god.json"):
        self.path = path
        self._data: dict[str, dict] = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path) as f:
                return json.load(f)
        return {}

    def save(self) -> None:
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=4)

    def get(self, uid: str) -> UserProfile:
        raw = self._data.setdefault(uid, {})
        return UserProfile(**{k: v for k, v in raw.items() if k in UserProfile.__dataclass_fields__})

    def update(self, uid: str, profile: UserProfile) -> None:
        self._data[uid] = {
            "messages": profile.messages,
            "bond":     profile.bond,
            "name":     profile.name,
        }


# ── LLM Stub (swap in real API call here) ────────────────────────────────────

def call_llm(prompt: str, system: str = "") -> str:
    """Replace this with your actual LLM call, e.g. Anthropic / OpenAI."""
    return prompt  # passthrough for now


# ── Main Agent ───────────────────────────────────────────────────────────────

class FoxyGodAI:
    def __init__(self, db_path: str = "foxy_god.json"):
        self.store = UserStore(db_path)

    def reply(self, uid: str, text: str) -> str:
        # 1. Load + update user profile
        profile = self.store.get(uid)
        profile.messages += 1
        profile.bond = min(1.0, profile.bond + 0.01)  # grow bond over time

        # 2. Detect emotion
        state = detect_emotion(text)

        # 3. Build a mood-aware system prompt for the LLM
        system_prompt = self._build_system_prompt(state, profile)

        # 4. Call LLM
        raw = call_llm(text, system=system_prompt)

        # 5. Wrap with personality
        final = apply_personality(raw, state)

        # 6. Persist
        self.store.update(uid, profile)
        self.store.save()

        return f"🐺 Foxy AI:\n{final}"

    def _build_system_prompt(self, state: EmotionState, profile: UserProfile) -> str:
        bond_desc = (
            "a close companion" if profile.bond > 0.75
            else "a friendly acquaintance" if profile.bond > 0.4
            else "a new stranger"
        )
        return (
            f"You are Foxy, a sharp-witted fox spirit. "
            f"Current mood: {state.mood} (intensity {state.intensity}). "
            f"You're talking to {bond_desc} (bond={profile.bond:.2f})."
        )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ai = FoxyGodAI()
    uid = "user_001"

    for msg in ["I feel so alone tonight", "I love you!!", "I'm so angry rn"]:
        print(ai.reply(uid, msg))
        print()
