"""
manga.py — FoxyAI Manga Story Engine
Give a topic → Foxy generates full chapters with dialogue.
Fully offline. No internet needed.
"""

import random
from dataclasses import dataclass, field
from typing import Optional

from memory import FoxyMemory


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class MangaPanel:
    panel_number: int
    scene:        str        # scene description
    dialogue:     list[str]  # list of speech bubbles
    action:       str        # action/sound effect text e.g. "SLASH!", "BOOM!"
    emotion:      str        # dominant emotion of panel


@dataclass
class MangaChapter:
    chapter_number: int
    title:          str
    panels:         list[MangaPanel]
    summary:        str


@dataclass
class MangaStory:
    title:      str
    topic:      str
    genre:      str
    characters: list[dict]
    chapters:   list[MangaChapter]


# ── Genre templates ───────────────────────────────────────────────────────────

GENRES = {
    "action": {
        "emotions":    ["determined", "fierce", "shocked", "victorious"],
        "actions":     ["SLASH!!", "BOOM!!", "CRASH!!", "THUD!!", "ROAR!!"],
        "scene_types": ["battle arena", "rooftop", "burning city", "dark alley"],
    },
    "romance": {
        "emotions":    ["nervous", "blushing", "happy", "longing"],
        "actions":     ["*heartbeat*", "*gasp*", "*blush*", "..."],
        "scene_types": ["school rooftop", "café", "park at sunset", "rain"],
    },
    "comedy": {
        "emotions":    ["shocked", "embarrassed", "laughing", "confused"],
        "actions":     ["WHAM!!", "BONK!!", "?!?!", "..."],
        "scene_types": ["classroom", "convenience store", "living room", "street"],
    },
    "mystery": {
        "emotions":    ["suspicious", "shocked", "focused", "afraid"],
        "actions":     ["*creaking sound*", "REVEAL!!", "...", "?!"],
        "scene_types": ["rainy street", "old mansion", "detective office", "alley"],
    },
    "adventure": {
        "emotions":    ["excited", "determined", "amazed", "scared"],
        "actions":     ["WHOOSH!!", "RUMBLE!!", "CRACK!!", "WOW!!"],
        "scene_types": ["ancient ruins", "forest", "ship deck", "mountain top"],
    },
}

# Character archetypes
CHARACTER_ARCHETYPES = [
    {"role": "hero",     "traits": ["brave", "kind", "reckless"],       "speech": "determined"},
    {"role": "rival",    "traits": ["proud", "strong", "secretly kind"],"speech": "cold"},
    {"role": "mentor",   "traits": ["wise", "mysterious", "old"],        "speech": "cryptic"},
    {"role": "friend",   "traits": ["loyal", "funny", "clumsy"],         "speech": "casual"},
    {"role": "villain",  "traits": ["cunning", "powerful", "bitter"],    "speech": "dramatic"},
    {"role": "love int", "traits": ["smart", "kind", "stubborn"],        "speech": "warm"},
]

# Dialogue templates by emotion and role
DIALOGUE_TEMPLATES = {
    "determined": [
        "I won't give up. Not now. Not ever.",
        "This is my fight. Stand back.",
        "I've made up my mind. Nothing can stop me now.",
        "Watch me. I'll prove everyone wrong.",
    ],
    "cold": [
        "Pathetic. You call that strength?",
        "Don't get in my way.",
        "I don't need anyone.",
        "You're not worth my time.",
    ],
    "cryptic": [
        "The answer you seek... lies within.",
        "Every path leads somewhere. Choose wisely.",
        "I've seen this before. It never ends well.",
        "Some truths are better left buried.",
    ],
    "casual": [
        "Bro wait up!! I'm coming too!!",
        "Did you have to make it so complicated?",
        "I told you this would happen!!",
        "Okay okay I got this. Probably.",
    ],
    "dramatic": [
        "You think you can defeat me?! FOOLS!!",
        "Everything you love will fall to dust.",
        "I am beyond your comprehension.",
        "This world... belongs to ME!",
    ],
    "warm": [
        "I believe in you. Always have.",
        "You're not alone in this. Remember that.",
        "Hey... are you okay?",
        "Whatever happens, I'm here.",
    ],
    "nervous": [
        "I... um... I wanted to say something...",
        "W-wait, this isn't what it looks like!",
        "M-my heart is going too fast right now...",
    ],
    "shocked": [
        "What?! That's impossible!!",
        "No way... no WAY!",
        "I... I can't believe this...",
    ],
}


# ── Story Engine ──────────────────────────────────────────────────────────────

class MangaEngine:
    """
    Generates complete manga stories from a topic.
    Works offline — pure Python logic + templates.
    When LLM is available, uses it to enrich dialogue.
    """

    def __init__(self, memory: Optional[FoxyMemory] = None, brain=None):
        self.memory = memory
        self.brain  = brain  # FoxyBrain instance — optional, enriches dialogue

    def generate_story(
        self,
        topic: str,
        chapters: int = 3,
        genre: str = "action",
        user_name: Optional[str] = None,
    ) -> MangaStory:
        """Generate a full manga story from a topic."""

        genre_data  = GENRES.get(genre, GENRES["action"])
        characters  = self._generate_characters(topic, user_name)
        title       = self._generate_title(topic, genre)

        chapter_list = []
        for i in range(1, chapters + 1):
            chapter = self._generate_chapter(i, topic, genre_data, characters)
            chapter_list.append(chapter)

        story = MangaStory(
            title=title,
            topic=topic,
            genre=genre,
            characters=characters,
            chapters=chapter_list,
        )

        # Save to memory
        if self.memory:
            chapters_data = [self._chapter_to_dict(c) for c in chapter_list]
            self.memory.manga.save(title, topic, chapters_data)

        return story

    def _generate_title(self, topic: str, genre: str) -> str:
        prefixes = {
            "action":    ["Fist of", "Shadow of", "Rise of", "Blade of", "Legend of"],
            "romance":   ["My Heart and", "Until I Met", "One Day with", "Forever with"],
            "comedy":    ["The Disaster Called", "My Stupid Life with", "Wait, Why is"],
            "mystery":   ["The Secret of", "Who Is", "The Truth Behind", "Case of"],
            "adventure": ["Journey to", "Quest for", "Beyond the", "In Search of"],
        }
        prefix = random.choice(prefixes.get(genre, prefixes["action"]))
        words  = topic.title().split()
        return f"{prefix} {' '.join(words[:2])}"

    def _generate_characters(self, topic: str, user_name: Optional[str]) -> list[dict]:
        chars = []
        archetypes = random.sample(CHARACTER_ARCHETYPES, min(4, len(CHARACTER_ARCHETYPES)))

        for i, arch in enumerate(archetypes):
            name = user_name if (i == 0 and user_name) else self._random_name()
            chars.append({
                "name":   name,
                "role":   arch["role"],
                "traits": arch["traits"],
                "speech": arch["speech"],
            })
        return chars

    def _generate_chapter(
        self,
        number: int,
        topic: str,
        genre_data: dict,
        characters: list[dict],
    ) -> MangaChapter:

        titles = [
            f"The Beginning",
            f"The Challenge",
            f"Breaking Point",
            f"Rising",
            f"The Truth",
            f"No Way Back",
            f"Final Stand",
        ]
        title = titles[min(number - 1, len(titles) - 1)]

        panels = []
        panel_count = random.randint(4, 6)

        for p in range(1, panel_count + 1):
            panel = self._generate_panel(p, genre_data, characters, topic)
            panels.append(panel)

        summary = f"Chapter {number}: {title} — {topic} intensifies as characters face new challenges."

        return MangaChapter(
            chapter_number=number,
            title=title,
            panels=panels,
            summary=summary,
        )

    def _generate_panel(
        self,
        number: int,
        genre_data: dict,
        characters: list[dict],
        topic: str,
    ) -> MangaPanel:

        emotion  = random.choice(genre_data["emotions"])
        action   = random.choice(genre_data["actions"]) if random.random() > 0.4 else ""
        scene    = random.choice(genre_data["scene_types"])

        # Pick 1-2 characters for this panel
        panel_chars = random.sample(characters, min(2, len(characters)))
        dialogue    = []

        for char in panel_chars:
            speech_style = char["speech"]
            lines        = DIALOGUE_TEMPLATES.get(speech_style, DIALOGUE_TEMPLATES["casual"])
            line         = random.choice(lines)
            dialogue.append(f"{char['name']}: \"{line}\"")

        return MangaPanel(
            panel_number=number,
            scene=scene,
            dialogue=dialogue,
            action=action,
            emotion=emotion,
        )

    def _random_name(self) -> str:
        first = ["Kai", "Ren", "Yuki", "Hana", "Zero", "Luna", "Ryu", "Sora", "Mika", "Jin"]
        return random.choice(first)

    def _chapter_to_dict(self, chapter: MangaChapter) -> dict:
        return {
            "chapter_number": chapter.chapter_number,
            "title":          chapter.title,
            "summary":        chapter.summary,
            "panels": [
                {
                    "panel_number": p.panel_number,
                    "scene":        p.scene,
                    "dialogue":     p.dialogue,
                    "action":       p.action,
                    "emotion":      p.emotion,
                }
                for p in chapter.panels
            ],
        }

    def format_for_display(self, story: MangaStory) -> str:
        """Format story as readable text for the chat UI."""
        lines = [
            f"📖 {story.title.upper()}",
            f"Genre: {story.genre.capitalize()} | Topic: {story.topic}",
            "",
            "CHARACTERS:",
        ]
        for c in story.characters:
            lines.append(f"  • {c['name']} — the {c['role']}")

        lines.append("")

        for chapter in story.chapters:
            lines.append(f"{'='*30}")
            lines.append(f"CHAPTER {chapter.chapter_number}: {chapter.title.upper()}")
            lines.append(f"{'='*30}")

            for panel in chapter.panels:
                lines.append(f"\n[ Panel {panel.panel_number} — {panel.scene} ]")
                if panel.action:
                    lines.append(f"  ** {panel.action} **")
                for d in panel.dialogue:
                    lines.append(f"  {d}")

            lines.append(f"\n{chapter.summary}\n")

        return "\n".join(lines)
