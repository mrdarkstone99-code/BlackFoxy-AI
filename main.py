import threading

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import ScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivy.clock import Clock

from brain import FoxyGodAI
from voice import FoxyVoice


class FoxyApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"

        self.ai = FoxyGodAI()
        self.voice = FoxyVoice()
        self.uid = "user"

        screen = MDScreen()

        root = MDBoxLayout(orientation="vertical", spacing=10, padding=20)

        # ── Chat history (scrollable) ────────────────────────────────────────
        self.scroll = ScrollView(size_hint=(1, 1))
        self.history = MDBoxLayout(
            orientation="vertical",
            spacing=8,
            size_hint_y=None,
            padding=[0, 8, 0, 8],
        )
        self.history.bind(minimum_height=self.history.setter("height"))
        self.scroll.add_widget(self.history)

        # ── Spinner (hidden until waiting for reply) ─────────────────────────
        self.spinner = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=("36dp", "36dp"),
            pos_hint={"center_x": 0.5},
        )
        self.spinner.opacity = 0          # hidden by default

        # ── Input row ────────────────────────────────────────────────────────
        input_row = MDBoxLayout(
            orientation="horizontal",
            spacing=8,
            size_hint=(1, None),
            height="56dp",
            adaptive_height=False,
        )
        self.input = MDTextField(
            hint_text="Ask Foxy…",
            size_hint=(1, None),
            height="56dp",
        )
        self.send_btn = MDRaisedButton(
            text="Send",
            size_hint=(None, None),
            size=("80dp", "56dp"),
            on_release=self.on_send,
        )
        input_row.add_widget(self.input)
        input_row.add_widget(self.send_btn)

        root.add_widget(self.scroll)
        root.add_widget(self.spinner)
        root.add_widget(input_row)
        screen.add_widget(root)

        return screen

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _add_bubble(self, text: str, align: str = "left") -> None:
        """Append a chat bubble to the history panel (call from main thread)."""
        label = MDLabel(
            text=text,
            halign=align,
            size_hint_y=None,
            adaptive_height=True,
            padding=["12dp", "8dp"],
        )
        self.history.add_widget(label)
        # Scroll to bottom after layout pass
        Clock.schedule_once(lambda _: setattr(self.scroll, "scroll_y", 0), 0.1)

    def _set_busy(self, busy: bool) -> None:
        """Toggle the spinner and disable the send button."""
        self.spinner.opacity = 1 if busy else 0
        self.send_btn.disabled = busy

    # ── Event handlers ───────────────────────────────────────────────────────

    def on_send(self, *_) -> None:
        text = self.input.text.strip()
        if not text:
            return

        self._add_bubble(f"You: {text}", align="right")
        self.input.text = ""
        self._set_busy(True)

        # Run AI + TTS off the main thread so the UI never freezes
        threading.Thread(
            target=self._reply_worker,
            args=(text,),
            daemon=True,
        ).start()

    def _reply_worker(self, text: str) -> None:
        """Runs on a background thread — no direct UI access here."""
        try:
            reply = self.ai.reply(self.uid, text)
        except Exception as e:
            reply = f"[error] {e}"

        # Schedule UI updates back on the main thread
        Clock.schedule_once(lambda _: self._on_reply(reply), 0)

    def _on_reply(self, reply: str) -> None:
        """Runs on the main thread after the AI responds."""
        self._set_busy(False)
        self._add_bubble(reply, align="left")

        # TTS can also block — push it off-thread too
        threading.Thread(
            target=self.voice.speak,
            args=(reply,),
            daemon=True,
        ).start()


if __name__ == "__main__":
    FoxyApp().run()
