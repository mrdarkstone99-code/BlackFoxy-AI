"""
voice.py — FoxyAI Voice (Android Compatible)
Uses plyer for Android TTS. Falls back to pyttsx3 on desktop.
Thread-safe. Non-blocking.
"""

import threading
import queue
import logging

logger = logging.getLogger(__name__)


class FoxyVoice:
    """
    Thread-safe TTS that works on both Android (plyer) and desktop (pyttsx3).
    All speech goes through a queue — never blocks the UI.
    """

    _STOP = object()

    def __init__(self):
        self._queue:  queue.Queue = queue.Queue()
        self._engine              = None
        self._mode                = None
        self._ready               = False

        self._thread = threading.Thread(
            target=self._worker,
            daemon=True,
            name="FoxyVoice-TTS",
        )
        self._thread.start()

    # ── Public API ────────────────────────────────────────────────────────────

    def speak(self, text: str) -> None:
        """Queue text to speak. Returns immediately — never blocks."""
        if not text or not text.strip():
            return
        # Strip emoji for TTS
        clean = self._strip_emoji(text)
        self._queue.put(clean)

    def stop(self) -> None:
        """Shut down cleanly. Call from app on_stop."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        self._queue.put(self._STOP)
        self._thread.join(timeout=5)

    def set_rate(self, rate: int) -> None:
        self._queue.put(("__rate__", rate))

    def set_volume(self, volume: float) -> None:
        self._queue.put(("__volume__", volume))

    # ── Worker ────────────────────────────────────────────────────────────────

    def _worker(self) -> None:
        self._init_engine()

        while True:
            item = self._queue.get()

            if item is self._STOP:
                break

            if isinstance(item, tuple):
                self._handle_property(item)
                continue

            if not self._ready:
                continue

            try:
                self._speak_now(item)
            except Exception:
                logger.exception("TTS speak error")

    def _init_engine(self) -> None:
        """Try Android (plyer) first, fall back to pyttsx3."""
        # Try plyer (Android)
        try:
            from plyer import tts as plyer_tts
            # Test if it actually works
            self._plyer_tts = plyer_tts
            self._mode      = "plyer"
            self._ready     = True
            logger.info("[Voice] Using plyer TTS (Android)")
            return
        except Exception:
            pass

        # Fall back to pyttsx3 (desktop)
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate",   150)
            engine.setProperty("volume", 1.0)
            self._engine = engine
            self._mode   = "pyttsx3"
            self._ready  = True
            logger.info("[Voice] Using pyttsx3 TTS (desktop)")
            return
        except Exception:
            pass

        logger.warning("[Voice] No TTS engine available")

    def _speak_now(self, text: str) -> None:
        if self._mode == "plyer":
            self._plyer_tts.speak(text)
        elif self._mode == "pyttsx3":
            self._engine.say(text)
            self._engine.runAndWait()

    def _handle_property(self, item: tuple) -> None:
        prop, value = item
        if self._mode == "pyttsx3" and self._engine:
            if prop == "__rate__":
                self._engine.setProperty("rate", value)
            elif prop == "__volume__":
                self._engine.setProperty("volume", value)

    @staticmethod
    def _strip_emoji(text: str) -> str:
        """Remove emoji so TTS doesn't read unicode character names."""
        import re
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        return emoji_pattern.sub("", text).strip()
