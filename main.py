"""
main.py — FoxyAI Main App
Full KivyMD UI. WhatsApp-style chat. Manga mode. Translation mode.
Streaming responses. Fully offline.
"""

import threading
from datetime import datetime

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar

from brain import FoxyBrain
from voice import FoxyVoice
from manga import MangaEngine
from translator import FoxyTranslator


# ── Message Bubble ────────────────────────────────────────────────────────────

class MessageBubble(MDCard):
    """Single WhatsApp-style message bubble."""

    def __init__(self, text: str, is_user: bool, timestamp: str = "", **kwargs):
        super().__init__(**kwargs)

        self.is_user    = is_user
        self.size_hint  = (0.78, None)
        self.adaptive_height = True
        self.padding    = [dp(12), dp(8)]
        self.radius     = [dp(16), dp(16), dp(2) if is_user else dp(16), dp(16) if is_user else dp(2)]
        self.elevation  = 1
        self.pos_hint   = {"right": 0.97} if is_user else {"x": 0.03}

        self.md_bg_color = (
            [0.2, 0.6, 0.4, 1] if is_user else [0.15, 0.15, 0.18, 1]
        )

        layout = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(2))

        self.text_label = MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            adaptive_height=True,
            size_hint_y=None,
        )
        self.text_label.bind(texture_size=self._update_height)

        layout.add_widget(self.text_label)

        if timestamp:
            time_label = MDLabel(
                text=timestamp,
                theme_text_color="Custom",
                text_color=(0.7, 0.7, 0.7, 1),
                font_style="Caption",
                adaptive_height=True,
                halign="right",
            )
            layout.add_widget(time_label)

        self.add_widget(layout)

    def update_text(self, text: str) -> None:
        self.text_label.text = text

    def _update_height(self, instance, value):
        instance.height = value[1]


# ── Chat Screen ───────────────────────────────────────────────────────────────

class ChatScreen(MDScreen):

    def __init__(self, app, **kwargs):
        super().__init__(name="chat", **kwargs)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical")

        # Toolbar
        self.toolbar = MDTopAppBar(
            title="🐺 Foxy AI",
            md_bg_color=(0.1, 0.1, 0.13, 1),
            specific_text_color=(1, 1, 1, 1),
        )
        self.toolbar.right_action_items = [
            ["translate", lambda x: self.app.show_translate_dialog()],
            ["book-open-variant", lambda x: self.app.show_manga_dialog()],
            ["account", lambda x: self.app.show_profile()],
        ]

        # Chat history
        self.scroll = ScrollView(size_hint=(1, 1))
        self.chat_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            padding=[dp(8), dp(8)],
            size_hint_y=None,
            adaptive_height=True,
        )
        self.chat_box.bind(minimum_height=self.chat_box.setter("height"))
        self.scroll.add_widget(self.chat_box)

        # Typing indicator
        self.typing_label = MDLabel(
            text="",
            theme_text_color="Custom",
            text_color=(0.5, 0.9, 0.6, 1),
            font_style="Caption",
            size_hint=(1, None),
            height=dp(20),
            padding=[dp(16), 0],
        )

        # Input row
        input_row = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(60),
            padding=[dp(8), dp(6)],
            spacing=dp(6),
            md_bg_color=(0.1, 0.1, 0.13, 1),
        )

        self.input = MDTextField(
            hint_text="Message Foxy...",
            size_hint=(1, None),
            height=dp(48),
            mode="fill",
            fill_color_normal=(0.18, 0.18, 0.22, 1),
            text_color_normal=(1, 1, 1, 1),
            hint_text_color_normal=(0.5, 0.5, 0.5, 1),
        )
        self.input.bind(on_text_validate=self.on_send)

        send_btn = MDIconButton(
            icon="send",
            theme_icon_color="Custom",
            icon_color=(0.2, 0.8, 0.5, 1),
            on_release=self.on_send,
        )

        input_row.add_widget(self.input)
        input_row.add_widget(send_btn)

        root.add_widget(self.toolbar)
        root.add_widget(self.scroll)
        root.add_widget(self.typing_label)
        root.add_widget(input_row)
        self.add_widget(root)

    def on_send(self, *_) -> None:
        text = self.input.text.strip()
        if not text:
            return

        self._add_bubble(f"{text}", is_user=True)
        self.input.text = ""
        self._set_typing(True)

        self.app.get_reply(text, self._on_token, self._on_reply_done)

    def _add_bubble(self, text: str, is_user: bool) -> MessageBubble:
        ts = datetime.now().strftime("%H:%M")
        bubble = MessageBubble(text=text, is_user=is_user, timestamp=ts)
        self.chat_box.add_widget(bubble)
        Clock.schedule_once(lambda _: setattr(self.scroll, "scroll_y", 0), 0.1)
        return bubble

    def add_foxy_bubble_streaming(self) -> MessageBubble:
        """Add an empty Foxy bubble that fills in as tokens arrive."""
        bubble = MessageBubble(text="...", is_user=False)
        self.chat_box.add_widget(bubble)
        Clock.schedule_once(lambda _: setattr(self.scroll, "scroll_y", 0), 0.1)
        return bubble

    def _on_token(self, token: str, bubble: MessageBubble, current: list) -> None:
        """Called on main thread for each streaming token."""
        current.append(token)
        bubble.update_text("".join(current))
        Clock.schedule_once(lambda _: setattr(self.scroll, "scroll_y", 0), 0)

    def _on_reply_done(self, reply: str) -> None:
        self._set_typing(False)
        self.app.voice.speak(reply)

    def _set_typing(self, typing: bool) -> None:
        self.typing_label.text = "Foxy is typing..." if typing else ""

    def add_system_message(self, text: str) -> None:
        label = MDLabel(
            text=text,
            halign="center",
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 0.5, 1),
            font_style="Caption",
            size_hint=(1, None),
            height=dp(24),
        )
        self.chat_box.add_widget(label)


# ── Main App ──────────────────────────────────────────────────────────────────

class FoxyApp(MDApp):

    def build(self):
        self.theme_cls.theme_style      = "Dark"
        self.theme_cls.primary_palette  = "Green"
        self.title                      = "Foxy AI"

        Window.clearcolor = (0.07, 0.07, 0.09, 1)

        # Init engines
        self.brain      = FoxyBrain()
        self.voice      = FoxyVoice()
        self.manga_eng  = MangaEngine(memory=self.brain.memory)
        self.translator = FoxyTranslator()

        # Streaming state
        self._stream_bubble:  MessageBubble = None
        self._stream_tokens:  list          = []

        # Build screen
        self.sm          = MDScreenManager()
        self.chat_screen = ChatScreen(app=self)
        self.sm.add_widget(self.chat_screen)

        # Welcome message
        Clock.schedule_once(self._send_welcome, 1)

        return self.sm

    def _send_welcome(self, *_) -> None:
        name = self.brain.memory.profile.get("name")
        if name:
            msg = f"hey {name} 👋 you're back. missed you ngl"
        else:
            hour = datetime.now().hour
            if hour < 12:
                greeting = "good morning"
            elif hour < 17:
                greeting = "hey"
            else:
                greeting = "good evening"
            msg = f"{greeting} 🐺 i'm Foxy. talk to me about anything\n\nyou can ask me to:\n• 📖 write a manga story\n• 🌍 translate anything\n• 💻 help with code\n• ⚖️ explain your rights\n• 😂 just vibe"

        self.chat_screen.add_system_message("─── Foxy AI ───")
        bubble = self.chat_screen.add_foxy_bubble_streaming()
        bubble.update_text(msg)

    # ── Reply flow ────────────────────────────────────────────────────────────

    def get_reply(
        self,
        text: str,
        on_token_cb,
        on_done_cb,
    ) -> None:
        """Start streaming reply. Manages bubble lifecycle."""

        # Check for special commands
        t = text.lower()

        if any(w in t for w in ["manga", "story", "comic"]):
            self._handle_manga_request(text)
            on_done_cb("")
            return

        if any(w in t for w in ["translate", "how do you say", "in spanish", "in french", "in hindi", "in arabic"]):
            self._handle_translate_request(text)
            on_done_cb("")
            return

        # Normal AI reply with streaming
        bubble  = self.chat_screen.add_foxy_bubble_streaming()
        tokens  = []

        def _token(t):
            Clock.schedule_once(lambda _: on_token_cb(t, bubble, tokens), 0)

        def _done(reply):
            Clock.schedule_once(lambda _: on_done_cb(reply), 0)

        self.brain.reply_stream(text, _token, _done)

    def _handle_manga_request(self, text: str) -> None:
        """Generate a manga story and display it."""
        t = text.lower()

        # Extract topic — everything after "manga" or "story"
        topic = text
        for kw in ["write a manga about", "manga story about", "story about", "manga about", "make a manga"]:
            if kw in t:
                topic = text[t.index(kw) + len(kw):].strip() or "friendship and courage"
                break

        # Detect genre
        genre = "action"
        if any(w in t for w in ["romance", "love", "relationship"]):
            genre = "romance"
        elif any(w in t for w in ["funny", "comedy", "joke"]):
            genre = "comedy"
        elif any(w in t for w in ["mystery", "detective", "secret"]):
            genre = "mystery"
        elif any(w in t for w in ["adventure", "journey", "quest"]):
            genre = "adventure"

        user_name = self.brain.memory.profile.get("name")

        self.chat_screen.add_system_message(f"📖 Generating manga: {topic}...")

        def _generate():
            story    = self.manga_eng.generate_story(topic, chapters=2, genre=genre, user_name=user_name)
            text_out = self.manga_eng.format_for_display(story)

            def _show(*_):
                bubble = self.chat_screen.add_foxy_bubble_streaming()
                bubble.update_text(text_out)
                self.chat_screen._set_typing(False)

            Clock.schedule_once(_show, 0)

        threading.Thread(target=_generate, daemon=True).start()

    def _handle_translate_request(self, text: str) -> None:
        """Detect language and translate."""
        t = text.lower()

        # Detect target language
        target = "spanish"
        for lang in ["spanish", "french", "hindi", "arabic", "japanese", "chinese",
                     "german", "korean", "italian", "turkish", "urdu", "russian"]:
            if lang in t:
                target = lang
                break

        # Extract text to translate
        to_translate = text
        for phrase in ["translate", "how do you say", "say in", "in " + target]:
            if phrase in t:
                idx = t.index(phrase) + len(phrase)
                candidate = text[idx:].strip().strip("?\"'")
                if candidate:
                    to_translate = candidate
                    break

        def _translate():
            result = self.translator.translate(to_translate, to_lang=target)
            reply  = f"🌍 In {target.capitalize()}:\n\n\"{to_translate}\"\n→ \"{result}\"\n\nwant me to pronounce it or give you more phrases?"

            def _show(*_):
                bubble = self.chat_screen.add_foxy_bubble_streaming()
                bubble.update_text(reply)
                self.chat_screen._set_typing(False)
                self.voice.speak(result)

            Clock.schedule_once(_show, 0)

        threading.Thread(target=_translate, daemon=True).start()

    # ── Dialogs ───────────────────────────────────────────────────────────────

    def show_manga_dialog(self) -> None:
        self.manga_input = MDTextField(hint_text="Story topic (e.g. samurai revenge)")
        self._manga_dialog = MDDialog(
            title="📖 Create Manga Story",
            type="custom",
            content_cls=self.manga_input,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self._manga_dialog.dismiss()),
                MDRaisedButton(text="Create", on_release=self._on_manga_dialog_create),
            ],
        )
        self._manga_dialog.open()

    def _on_manga_dialog_create(self, *_) -> None:
        topic = self.manga_input.text.strip()
        self._manga_dialog.dismiss()
        if topic:
            self.chat_screen._set_typing(True)
            self._handle_manga_request(f"manga story about {topic}")

    def show_translate_dialog(self) -> None:
        content = MDBoxLayout(orientation="vertical", spacing=dp(8), adaptive_height=True)
        self._trans_text  = MDTextField(hint_text="Text to translate")
        self._trans_lang  = MDTextField(hint_text="Target language (e.g. hindi, french)")
        content.add_widget(self._trans_text)
        content.add_widget(self._trans_lang)

        self._trans_dialog = MDDialog(
            title="🌍 Translate",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self._trans_dialog.dismiss()),
                MDRaisedButton(text="Translate", on_release=self._on_translate_dialog),
            ],
        )
        self._trans_dialog.open()

    def _on_translate_dialog(self, *_) -> None:
        text = self._trans_text.text.strip()
        lang = self._trans_lang.text.strip() or "spanish"
        self._trans_dialog.dismiss()
        if text:
            self.chat_screen._set_typing(True)
            self._handle_translate_request(f"translate {text} in {lang}")

    def show_profile(self) -> None:
        summary = self.brain.memory.build_context_prompt()
        MDDialog(
            title="👤 What Foxy knows about you",
            text=summary,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: None)],
        ).open()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_stop(self):
        self.voice.stop()
        self.brain.close()


if __name__ == "__main__":
    FoxyApp().run()
