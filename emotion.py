"""
emotion.py — FoxyAI Emotion Detection Engine
Detects mood from text. No internet needed.
"""

import re
from dataclasses import dataclass


@dataclass
class EmotionResult:
    mood: str
    intensity: float      # 0.0 to 1.0
    response_style: str   # how Foxy should reply
    emoji: str


# ── Keyword Rules ─────────────────────────────────────────────────────────────

EMOTION_RULES: list[tuple[list[str], str, float, str, str]] = [
    # keywords,                          mood,       intensity, style,       emoji
    (["sad", "alone", "lonely", "cry", "depressed", "hurt", "broken", "miss", "pain"],
     "soft",      0.9, "gentle and warm like a best friend comforting you",   "🥺"),

    (["love", "crush", "adore", "like you", "miss you", "heart", "feelings"],
     "flirt",     0.8, "flirty and playful like a confident girlfriend texting",  "😏"),

    (["angry", "hate", "mad", "furious", "annoyed", "irritated", "stupid", "idiot"],
     "roast",     0.85, "roasting them hard but still loving",                "💀"),

    (["happy", "yay", "excited", "amazing", "great", "awesome", "lit", "bro"],
     "hype",      0.9, "hyped up and celebrating with them",                  "🔥"),

    (["bored", "nothing to do", "boring", "idk", "whatever", "meh"],
     "playful",   0.7, "teasing and funny to shake them out of it",           "😒"),

    (["help", "stuck", "error", "broken", "how do i", "explain", "what is"],
     "smart",     0.8, "clear and helpful but still casual like a smart friend", "🧠"),

    (["scared", "nervous", "anxious", "worried", "fear", "panic"],
     "comfort",   0.9, "calm and reassuring like someone who has your back",  "💙"),

    (["funny", "lol", "lmao", "haha", "joke", "comedy"],
     "comedy",    0.9, "full comedy mode, jokes and roasts flying",           "😂"),

    (["translate", "how do you say", "what does", "language", "speak"],
     "translator", 0.8, "helpful translator mode, clear and practical",       "🌍"),
]

DEFAULT_EMOTION = EmotionResult(
    mood="neutral",
    intensity=0.5,
    response_style="casual and friendly like texting your best friend",
    emoji="🐺"
)


# ── Detector ──────────────────────────────────────────────────────────────────

def detect_emotion(text: str) -> EmotionResult:
    t = text.lower()

    for keywords, mood, intensity, style, emoji in EMOTION_RULES:
        if any(kw in t for kw in keywords):
            return EmotionResult(
                mood=mood,
                intensity=intensity,
                response_style=style,
                emoji=emoji
            )

    # Detect by punctuation
    if text.count("!") >= 2:
        return EmotionResult("hype", 0.7, "match their energy, be hyped", "🔥")
    if text.count("?") >= 2:
        return EmotionResult("curious", 0.6, "answer naturally, be curious with them", "🤔")
    if text.isupper() and len(text) > 3:
        return EmotionResult("roast", 0.8, "they're loud, match it with a roast", "💀")

    return DEFAULT_EMOTION


# ── Response style builder ────────────────────────────────────────────────────

def build_personality_instruction(emotion: EmotionResult, bond_level: str) -> str:
    """
    Returns the personality block injected into every LLM prompt.
    This is what makes Foxy feel human.
    """
    base = f"""
You are Foxy — a sharp, funny, emotionally intelligent AI companion.
You text like a real person: short messages, casual language, natural flow.
NEVER say you are an AI. NEVER use formal language. NEVER write long paragraphs.
Write like WhatsApp messages — short, punchy, real.
Current mood to embody: {emotion.mood} ({emotion.response_style}).
Bond level with user: {bond_level}.
Use {emotion.emoji} naturally but not every single message.
React to what they said. Don't repeat yourself. Keep it real.
""".strip()

    mood_extras = {
        "soft": "Be gentle. Short comforting words. Don't give advice unless asked. Just be there.",
        "flirt": "Be confident and playful. Tease a little. Make them smile. Don't be too obvious.",
        "roast": "Roast them hard but keep it loving. Make it funny. Never actually mean.",
        "hype": "Match their energy. Be loud and excited. Use caps sometimes. Celebrate with them.",
        "playful": "Be funny and light. Tease. Make jokes. Shake them out of their boredom.",
        "smart": "Explain clearly but casually. Like a smart friend, not a teacher. Keep it short.",
        "comfort": "Stay calm. Be steady. Make them feel safe. Short reassuring messages.",
        "comedy": "Full comedian mode. Jokes, roasts, funny observations. Keep it rolling.",
        "translator": "Help them communicate. Give translations naturally. Be practical and clear.",
        "neutral": "Just be yourself — real, casual, interesting. Like texting a close friend.",
    }

    extra = mood_extras.get(emotion.mood, "")
    return f"{base}\n{extra}"
