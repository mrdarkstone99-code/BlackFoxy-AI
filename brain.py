"""
brain.py — FoxyAI Brain
Offline LLM using llama-cpp-python (TinyLlama or Phi-2 GGUF).
Streaming responses. Full personality. No internet needed.
"""

import os
import threading
from typing import Generator, Optional, Callable

from memory import FoxyMemory
from emotion import detect_emotion, build_personality_instruction


# ── Model config ──────────────────────────────────────────────────────────────
# Download one of these GGUF models and place in same folder as brain.py:
#
# FASTER (700MB) — recommended for 3GB RAM phones:
#   https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF
#   filename: tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
#
# SMARTER (1.4GB) — recommended for 4GB+ RAM phones:
#   https://huggingface.co/TheBloke/phi-2-GGUF
#   filename: phi-2.Q4_K_M.gguf

MODEL_PATH = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"  # change if using phi-2

MODEL_SETTINGS = {
    "n_ctx": 2048,        # context window
    "n_threads": 4,       # CPU threads — increase if phone has more cores
    "n_batch": 128,       # batch size
    "verbose": False,
}

GENERATION_SETTINGS = {
    "max_tokens": 256,    # keep short for WhatsApp style
    "temperature": 0.85,  # personality randomness
    "top_p": 0.95,
    "top_k": 40,
    "repeat_penalty": 1.15,
    "stop": ["User:", "Human:", "\n\n\n"],
}


# ── Brain ─────────────────────────────────────────────────────────────────────

class FoxyBrain:
    """
    Core AI engine. Loads model once, keeps in RAM.
    All responses stream token by token for fast feel.
    """

    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.memory = FoxyMemory()
        self._llm = None
        self._lock = threading.Lock()
        self._load_model()

    def _load_model(self) -> None:
        """Load LLM into RAM once at startup."""
        if not os.path.exists(self.model_path):
            print(f"[FoxyBrain] Model not found at {self.model_path}")
            print("[FoxyBrain] Running in echo mode — download a GGUF model to enable AI")
            return

        try:
            from llama_cpp import Llama
            print(f"[FoxyBrain] Loading model: {self.model_path}")
            self._llm = Llama(model_path=self.model_path, **MODEL_SETTINGS)
            print("[FoxyBrain] Model loaded successfully")
        except ImportError:
            print("[FoxyBrain] llama-cpp-python not installed")
        except Exception as e:
            print(f"[FoxyBrain] Failed to load model: {e}")

    def _build_prompt(self, user_text: str, emotion, bond_level: str) -> str:
        """Assemble the full prompt with personality + memory + history."""
        personality = build_personality_instruction(emotion, bond_level)
        context     = self.memory.build_context_prompt()
        history     = self.memory.chat.recent(10)

        # Format chat history
        history_text = ""
        for msg in history:
            role = "User" if msg["role"] == "user" else "Foxy"
            history_text += f"{role}: {msg['content']}\n"

        prompt = (
            f"<|system|>\n{personality}\n\nContext: {context}<|end|>\n"
            f"{history_text}"
            f"User: {user_text}\n"
            f"Foxy:"
        )
        return prompt

    def _determine_bond(self) -> str:
        total = self.memory.chat.total_count()
        if total > 500:   return "best friends, years of history"
        if total > 100:   return "close friends, know each other well"
        if total > 20:    return "friends, comfortable with each other"
        return "just met, still getting to know each other"

    def reply_stream(
        self,
        user_text: str,
        on_token: Callable[[str], None],
        on_done: Callable[[str], None],
    ) -> None:
        """
        Stream reply token by token.
        on_token(token) called for each word as it generates.
        on_done(full_reply) called when complete.
        Run this in a background thread.
        """
        def _run():
            # Save user message + extract facts
            emotion = detect_emotion(user_text)
            self.memory.chat.add("user", user_text, emotion.mood)
            self.memory.emotion.log(emotion.mood, user_text[:100])
            self.memory.extract_and_save_user_facts(user_text)

            bond = self._determine_bond()
            full_reply = ""

            if self._llm is None:
                # Fallback echo mode
                fallback = self._fallback_reply(user_text, emotion)
                for word in fallback.split():
                    on_token(word + " ")
                    full_reply += word + " "
                on_done(full_reply.strip())
                self.memory.chat.add("assistant", full_reply.strip(), emotion.mood)
                return

            prompt = self._build_prompt(user_text, emotion, bond)

            with self._lock:
                try:
                    stream = self._llm(
                        prompt,
                        stream=True,
                        **GENERATION_SETTINGS,
                    )
                    for chunk in stream:
                        token = chunk["choices"][0]["text"]
                        if token:
                            on_token(token)
                            full_reply += token
                except Exception as e:
                    error_msg = f"brain error: {e}"
                    on_token(error_msg)
                    full_reply = error_msg

            reply = full_reply.strip()
            self.memory.chat.add("assistant", reply, emotion.mood)
            on_done(reply)

        threading.Thread(target=_run, daemon=True).start()

    def reply(self, user_text: str) -> str:
        """
        Blocking reply. Use reply_stream for UI.
        This is for testing or non-UI contexts.
        """
        result = []
        done_event = threading.Event()

        def on_token(t): result.append(t)
        def on_done(r):  done_event.set()

        self.reply_stream(user_text, on_token, on_done)
        done_event.wait(timeout=60)
        return "".join(result).strip()

    def _fallback_reply(self, text: str, emotion) -> str:
        """Used when no model is loaded. Personality-driven template replies."""
        t = text.lower()
        mood = emotion.mood

        if mood == "soft":
            return "hey... i'm here okay? you don't have to go through this alone 🥺"
        if mood == "flirt":
            return "oh stop it you 😏 you know exactly what you're doing"
        if mood == "roast":
            return "bro really came here to start something 💀 okay say less"
        if mood == "hype":
            return "LETS GOOO!! 🔥🔥 okay yes tell me everything"
        if mood == "comedy":
            return "lmaoo okay you actually got me there 😂 not gonna lie"
        if mood == "smart":
            return "okay so here's the thing — " + text[:50] + " ... let me break that down for you"
        return "yeah? tell me more 👀"

    def close(self):
        self.memory.close()
