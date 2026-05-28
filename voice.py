import pyttsx3
import threading
import queue
import logging

logger = logging.getLogger(__name__)


class FoxyVoice:
    """
    Thread-safe TTS wrapper around pyttsx3.

    pyttsx3's engine is not safe to call from multiple threads.
    This class owns a single dedicated worker thread and serializes
    all speech requests through a queue.
    """

    _STOP = object()  # sentinel to shut down the worker

    def __init__(self, rate: int = 150, volume: float = 1.0):
        self._queue: queue.Queue = queue.Queue()
        self._engine = self._make_engine(rate, volume)

        self._thread = threading.Thread(
            target=self._worker,
            daemon=True,
            name="FoxyVoice-TTS",
        )
        self._thread.start()

    # ── Public API ────────────────────────────────────────────────────────────

    def speak(self, text: str) -> None:
        """Queue a line of text to be spoken. Returns immediately."""
        if not text or not text.strip():
            return
        self._queue.put(text)

    def stop(self) -> None:
        """
        Cancel any queued speech and shut down the worker thread cleanly.
        Call this when your app is closing.
        """
        # Drain the queue so the worker isn't stuck mid-loop
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

        self._queue.put(self._STOP)
        self._thread.join(timeout=5)

    def set_rate(self, rate: int) -> None:
        """Change speech rate at runtime (words per minute)."""
        self._queue.put(("__set_rate__", rate))

    def set_volume(self, volume: float) -> None:
        """Change volume at runtime (0.0 – 1.0)."""
        self._queue.put(("__set_volume__", volume))

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _make_engine(rate: int, volume: float) -> pyttsx3.Engine:
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        engine.setProperty("volume", volume)
        return engine

    def _worker(self) -> None:
        """
        Runs on the dedicated TTS thread.
        Processes one item at a time so pyttsx3 is never called concurrently.
        """
        while True:
            item = self._queue.get()

            # Shutdown sentinel
            if item is se
