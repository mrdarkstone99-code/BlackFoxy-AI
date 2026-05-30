"""
translator.py — FoxyAI Live Offline Translator
Uses argostranslate. No internet after install.
Supports 50+ languages.
"""

import threading
from typing import Optional


# ── Supported languages ───────────────────────────────────────────────────────
# argostranslate language codes
LANGUAGES = {
    "english":    "en",
    "hindi":      "hi",
    "spanish":    "es",
    "french":     "fr",
    "arabic":     "ar",
    "portuguese": "pt",
    "russian":    "ru",
    "japanese":   "ja",
    "chinese":    "zh",
    "german":     "de",
    "korean":     "ko",
    "italian":    "it",
    "turkish":    "tr",
    "dutch":      "nl",
    "polish":     "pl",
    "thai":       "th",
    "vietnamese": "vi",
    "indonesian": "id",
    "malay":      "ms",
    "urdu":       "ur",
    "bengali":    "bn",
    "tamil":      "ta",
    "telugu":     "te",
    "swahili":    "sw",
    "greek":      "el",
}

# Travel phrases — pre-built for instant use without LLM
TRAVEL_PHRASES: dict[str, list[dict]] = {
    "basic": [
        {"en": "Hello",                     "use": "greeting anyone"},
        {"en": "Thank you",                 "use": "showing gratitude"},
        {"en": "Sorry / Excuse me",         "use": "getting past someone or apologizing"},
        {"en": "I don't understand",        "use": "when you're lost in translation"},
        {"en": "Do you speak English?",     "use": "finding someone who can help"},
        {"en": "Where is the bathroom?",    "use": "most important travel phrase"},
        {"en": "How much does this cost?",  "use": "shopping or market"},
        {"en": "I need help",               "use": "emergency or confusion"},
        {"en": "Call the police",           "use": "emergency"},
        {"en": "I am lost",                 "use": "navigation"},
    ],
    "food": [
        {"en": "I am vegetarian",           "use": "ordering food"},
        {"en": "No spicy please",           "use": "ordering food"},
        {"en": "Water please",              "use": "restaurant"},
        {"en": "The bill please",           "use": "paying at restaurant"},
        {"en": "This is delicious",         "use": "complimenting food"},
        {"en": "I am allergic to...",       "use": "food safety"},
    ],
    "transport": [
        {"en": "Take me to...",             "use": "taxi or tuk-tuk"},
        {"en": "Stop here please",          "use": "in a taxi"},
        {"en": "How far is...?",            "use": "distance check"},
        {"en": "Is this the right bus?",    "use": "public transport"},
        {"en": "Airport please",            "use": "taxi to airport"},
    ],
    "emergency": [
        {"en": "I need a doctor",           "use": "medical emergency"},
        {"en": "Call an ambulance",         "use": "serious medical"},
        {"en": "I've been robbed",          "use": "theft"},
        {"en": "I need the embassy",        "use": "lost passport or serious trouble"},
        {"en": "My phone was stolen",       "use": "theft"},
    ],
}


# ── Translator ────────────────────────────────────────────────────────────────

class FoxyTranslator:
    """
    Offline translation using argostranslate.
    Install language packs once, translate forever.
    """

    def __init__(self):
        self._ready = False
        self._init_thread = threading.Thread(
            target=self._init_argos,
            daemon=True,
            name="FoxyTranslator-Init"
        )
        self._init_thread.start()

    def _init_argos(self) -> None:
        try:
            import argostranslate.package
            import argostranslate.translate
            self._argos_translate = argostranslate.translate
            self._ready = True
            print("[Translator] argostranslate ready")
        except ImportError:
            print("[Translator] argostranslate not installed — install with: pip install argostranslate")
        except Exception as e:
            print(f"[Translator] Init error: {e}")

    def install_language(self, from_code: str, to_code: str) -> bool:
        """
        Download and install a language pair.
        Only needs internet once. After that it's offline.
        """
        try:
            import argostranslate.package
            argostranslate.package.update_package_index()
            available = argostranslate.package.get_available_packages()
            pkg = next(
                (p for p in available if p.from_code == from_code and p.to_code == to_code),
                None
            )
            if pkg:
                pkg.install()
                print(f"[Translator] Installed {from_code} → {to_code}")
                return True
            print(f"[Translator] Package {from_code} → {to_code} not found")
            return False
        except Exception as e:
            print(f"[Translator] Install error: {e}")
            return False

    def translate(
        self,
        text: str,
        to_lang: str = "en",
        from_lang: str = "en",
    ) -> str:
        """Translate text offline."""
        if not self._ready:
            return f"[translator loading... try again in a moment]"

        # Normalize language name to code
        to_code   = LANGUAGES.get(to_lang.lower(), to_lang)
        from_code = LANGUAGES.get(from_lang.lower(), from_lang)

        if from_code == to_code:
            return text

        try:
            result = self._argos_translate.translate(text, from_code, to_code)
            return result
        except Exception as e:
            return f"[translation error: {e}]"

    def detect_and_translate(self, text: str, target_lang: str = "en") -> dict:
        """
        Translate text to target language.
        Returns dict with original, translated, and target language.
        """
        translated = self.translate(text, to_lang=target_lang)
        return {
            "original":   text,
            "translated": translated,
            "target":     target_lang,
        }

    def travel_help(self, situation: str, target_lang: str) -> list[dict]:
        """
        Returns translated travel phrases for a given situation.
        situation: 'basic', 'food', 'transport', 'emergency'
        """
        phrases = TRAVEL_PHRASES.get(situation, TRAVEL_PHRASES["basic"])
        result = []
        for phrase in phrases:
            translated = self.translate(phrase["en"], to_lang=target_lang)
            result.append({
                "english":    phrase["en"],
                "translated": translated,
                "use":        phrase["use"],
                "language":   target_lang,
            })
        return result

    def foxy_travel_reply(self, user_text: str, target_lang: str) -> str:
        """
        Smart travel assistant reply.
        Detects what the user needs and gives translated phrases.
        """
        t = user_text.lower()

        if any(w in t for w in ["food", "eat", "restaurant", "hungry", "drink"]):
            situation = "food"
        elif any(w in t for w in ["bus", "taxi", "train", "transport", "go to", "how far"]):
            situation = "transport"
        elif any(w in t for w in ["help", "emergency", "doctor", "police", "stolen", "lost"]):
            situation = "emergency"
        else:
            situation = "basic"

        phrases = self.travel_help(situation, target_lang)
        lang_display = target_lang.capitalize()

        lines = [f"🌍 Travel phrases in {lang_display}:\n"]
        for p in phrases[:5]:  # show top 5
            lines.append(f"• \"{p['english']}\"")
            lines.append(f"  → {p['translated']}")
            lines.append(f"  ({p['use']})\n")

        return "\n".join(lines)

    @staticmethod
    def supported_languages() -> list[str]:
        return sorted(LANGUAGES.keys())
