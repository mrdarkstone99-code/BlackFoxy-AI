"""
sketch.py — FoxyAI Manga Sketch Generator
Draws black and white manga-style panels using PIL + OpenCV.
100% offline. No AI image API needed.
Output: manga panel images saved as PNG.
"""

import os
import random
import math
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[Sketch] PIL not available — install Pillow")

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[Sketch] OpenCV not available — install opencv-python")


OUTPUT_DIR = "manga_output"
PANEL_W    = 400
PANEL_H    = 500
BG_COLOR   = (255, 255, 255)   # white
INK_COLOR  = (10,  10,  10)    # near-black ink
GRAY       = (180, 180, 180)


# ── Sketch Engine ─────────────────────────────────────────────────────────────

class MangaSketch:
    """
    Generates black and white manga panel images.
    Each panel includes: scene background, character silhouette,
    speech bubbles, action text, panel borders.
    """

    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow required: pip install Pillow")

        # Try to load a font — fall back to PIL default
        self.font_large  = self._load_font(28)
        self.font_medium = self._load_font(18)
        self.font_small  = self._load_font(13)
        self.font_action = self._load_font(32)

    def _load_font(self, size: int):
        try:
            return ImageFont.truetype("/system/fonts/DroidSans.ttf", size)
        except Exception:
            try:
                return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
            except Exception:
                return ImageFont.load_default()

    # ── Public API ────────────────────────────────────────────────────────────

    def draw_panel(
        self,
        panel_number:  int,
        scene:         str,
        dialogue:      list[str],
        action:        str = "",
        emotion:       str = "neutral",
        chapter:       int = 1,
        story_title:   str = "story",
    ) -> str:
        """
        Draw a single manga panel and save as PNG.
        Returns the file path.
        """
        img  = Image.new("RGB", (PANEL_W, PANEL_H), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # 1. Draw background scene lines
        self._draw_scene_bg(draw, scene, emotion)

        # 2. Draw character silhouette
        self._draw_character_silhouette(draw, emotion)

        # 3. Draw action lines (speed lines for action scenes)
        if emotion in ("fierce", "determined", "shocked", "victorious"):
            self._draw_speed_lines(draw)

        # 4. Draw action text (SLASH!! BOOM!! etc.)
        if action:
            self._draw_action_text(draw, action)

        # 5. Draw speech bubbles
        self._draw_speech_bubbles(draw, dialogue)

        # 6. Draw panel border
        self._draw_border(draw)

        # 7. Add panel number
        draw.text((8, 8), f"P{panel_number}", fill=GRAY, font=self.font_small)

        # Apply slight sketch filter
        img = self._apply_sketch_filter(img)

        # Save
        safe_title = "".join(c for c in story_title if c.isalnum() or c == "_")
        filename   = f"{safe_title}_ch{chapter}_p{panel_number}.png"
        filepath   = os.path.join(self.output_dir, filename)
        img.save(filepath)
        return filepath

    def draw_chapter(
        self,
        chapter_data: dict,
        story_title: str = "story",
    ) -> list[str]:
        """Draw all panels in a chapter. Returns list of file paths."""
        paths = []
        for panel in chapter_data.get("panels", []):
            path = self.draw_panel(
                panel_number = panel["panel_number"],
                scene        = panel["scene"],
                dialogue     = panel["dialogue"],
                action       = panel.get("action", ""),
                emotion      = panel.get("emotion", "neutral"),
                chapter      = chapter_data["chapter_number"],
                story_title  = story_title,
            )
            paths.append(path)
        return paths

    def draw_story(self, story_data: dict) -> list[str]:
        """Draw all panels in all chapters. Returns all file paths."""
        all_paths = []
        title = story_data.get("title", "story")
        for chapter in story_data.get("chapters", []):
            paths = self.draw_chapter(chapter, title)
            all_paths.extend(paths)
        return all_paths

    # ── Drawing helpers ───────────────────────────────────────────────────────

    def _draw_scene_bg(self, draw: ImageDraw.Draw, scene: str, emotion: str) -> None:
        """Draw background based on scene type."""
        scene = scene.lower()

        if "rooftop" in scene or "mountain" in scene:
            # Sky with clouds
            self._draw_sky(draw)
            self._draw_city_skyline(draw)

        elif "forest" in scene or "park" in scene:
            self._draw_nature_bg(draw)

        elif "rain" in scene:
            self._draw_rain_bg(draw)

        elif "dark" in scene or "alley" in scene or "mansion" in scene:
            self._draw_dark_bg(draw)

        else:
            # Generic interior — crosshatch pattern
            self._draw_crosshatch_bg(draw)

    def _draw_sky(self, draw: ImageDraw.Draw) -> None:
        # Gradient-ish sky with horizontal lines
        for y in range(0, PANEL_H // 2, 8):
            alpha = int(80 + y * 0.5)
            draw.line([(0, y), (PANEL_W, y)], fill=(alpha, alpha, alpha), width=1)

    def _draw_city_skyline(self, draw: ImageDraw.Draw) -> None:
        # Simple building silhouettes
        buildings = [
            (20, 180, 80, PANEL_H),
            (90, 150, 140, PANEL_H),
            (150, 200, 200, PANEL_H),
            (210, 130, 260, PANEL_H),
            (270, 170, 320, PANEL_H),
            (330, 140, 380, PANEL_H),
        ]
        for bx1, by1, bx2, by2 in buildings:
            draw.rectangle([bx1, by1, bx2, by2], fill=(40, 40, 40))
            # windows
            for wx in range(bx1 + 8, bx2 - 8, 14):
                for wy in range(by1 + 10, by2 - 10, 20):
                    if random.random() > 0.4:
                        draw.rectangle([wx, wy, wx + 6, wy + 10], fill=(200, 200, 160))

    def _draw_nature_bg(self, draw: ImageDraw.Draw) -> None:
        # Trees as triangles
        for x in range(0, PANEL_W, 60):
            h = random.randint(80, 150)
            draw.polygon(
                [(x + 30, PANEL_H - h - 50), (x, PANEL_H - 50), (x + 60, PANEL_H - 50)],
                fill=(30, 30, 30), outline=INK_COLOR
            )
        draw.rectangle([0, PANEL_H - 55, PANEL_W, PANEL_H], fill=(20, 20, 20))

    def _draw_rain_bg(self, draw: ImageDraw.Draw) -> None:
        for _ in range(80):
            x  = random.randint(0, PANEL_W)
            y  = random.randint(0, PANEL_H)
            x2 = x - random.randint(3, 8)
            y2 = y + random.randint(10, 20)
            draw.line([(x, y), (x2, y2)], fill=(150, 150, 180), width=1)

    def _draw_dark_bg(self, draw: ImageDraw.Draw) -> None:
        draw.rectangle([0, 0, PANEL_W, PANEL_H], fill=(30, 30, 30))
        # Brick pattern
        for row in range(0, PANEL_H, 20):
            offset = 20 if (row // 20) % 2 else 0
            for col in range(-offset, PANEL_W, 40):
                draw.rectangle(
                    [col + 2, row + 2, col + 38, row + 18],
                    outline=(60, 60, 60), width=1
                )

    def _draw_crosshatch_bg(self, draw: ImageDraw.Draw) -> None:
        for x in range(0, PANEL_W, 20):
            draw.line([(x, 0), (x, PANEL_H)], fill=(230, 230, 230), width=1)
        for y in range(0, PANEL_H, 20):
            draw.line([(0, y), (PANEL_W, y)], fill=(230, 230, 230), width=1)

    def _draw_character_silhouette(self, draw: ImageDraw.Draw, emotion: str) -> None:
        """Draw a simple human silhouette in manga style."""
        cx = PANEL_W // 2
        cy = PANEL_H // 2 + 30

        poses = {
            "determined": {"head_tilt": 0,   "arm_raise": True},
            "fierce":     {"head_tilt": -10, "arm_raise": True},
            "shocked":    {"head_tilt": 5,   "arm_raise": False},
            "nervous":    {"head_tilt": 3,   "arm_raise": False},
            "happy":      {"head_tilt": -5,  "arm_raise": True},
        }
        pose = poses.get(emotion, {"head_tilt": 0, "arm_raise": False})

        # Body
        draw.ellipse([cx - 22, cy - 140, cx + 22, cy - 96], fill=INK_COLOR)  # head
        draw.rectangle([cx - 18, cy - 95, cx + 18, cy - 20], fill=INK_COLOR)  # torso

        # Arms
        if pose["arm_raise"]:
            draw.line([(cx - 18, cy - 80), (cx - 45, cy - 120)], fill=INK_COLOR, width=8)
            draw.line([(cx + 18, cy - 80), (cx + 45, cy - 110)], fill=INK_COLOR, width=8)
        else:
            draw.line([(cx - 18, cy - 80), (cx - 40, cy - 40)], fill=INK_COLOR, width=8)
            draw.line([(cx + 18, cy - 80), (cx + 40, cy - 40)], fill=INK_COLOR, width=8)

        # Legs
        draw.line([(cx - 10, cy - 20), (cx - 18, cy + 50)], fill=INK_COLOR, width=10)
        draw.line([(cx + 10, cy - 20), (cx + 18, cy + 50)], fill=INK_COLOR, width=10)

        # Hair (spiky manga style)
        for angle in range(-60, 70, 20):
            rad = math.radians(angle)
            hx  = cx + int(25 * math.sin(rad))
            hy  = cy - 140 + int(-25 * math.cos(rad))
            draw.line([(cx, cy - 118), (hx, hy)], fill=INK_COLOR, width=3)

    def _draw_speed_lines(self, draw: ImageDraw.Draw) -> None:
        """Radial speed lines for action panels."""
        cx, cy = PANEL_W // 2, PANEL_H // 2
        for angle in range(0, 360, 12):
            rad    = math.radians(angle)
            r_in   = random.randint(60, 90)
            r_out  = random.randint(220, 300)
            x1 = cx + int(r_in  * math.cos(rad))
            y1 = cy + int(r_in  * math.sin(rad))
            x2 = cx + int(r_out * math.cos(rad))
            y2 = cy + int(r_out * math.sin(rad))
            draw.line([(x1, y1), (x2, y2)], fill=(200, 200, 200), width=1)

    def _draw_action_text(self, draw: ImageDraw.Draw, action: str) -> None:
        """Draw big dramatic action text."""
        x, y = PANEL_W // 2 - 60, 20
        # Shadow
        draw.text((x + 3, y + 3), action, fill=(100, 100, 100), font=self.font_action)
        # Main text
        draw.text((x, y), action, fill=INK_COLOR, font=self.font_action)

    def _draw_speech_bubbles(self, draw: ImageDraw.Draw, dialogue: list[str]) -> None:
        """Draw speech bubbles with text."""
        positions = [
            (10,  PANEL_H - 160),
            (PANEL_W // 2, PANEL_H - 120),
        ]

        for i, line in enumerate(dialogue[:2]):
            if i >= len(positions):
                break

            # Strip "Name: " prefix if present
            text = line.split(": ", 1)[-1].strip('"')
            if len(text) > 40:
                text = text[:40] + "..."

            bx, by = positions[i]
            bw, bh = min(180, 20 + len(text) * 7), 45

            # Bubble
            draw.ellipse([bx, by, bx + bw, by + bh], fill=BG_COLOR, outline=INK_COLOR, width=2)

            # Tail
            tail_x = bx + bw // 3
            draw.polygon(
                [(tail_x, by + bh), (tail_x + 10, by + bh), (tail_x + 5, by + bh + 15)],
                fill=BG_COLOR, outline=INK_COLOR
            )

            # Text
            draw.text((bx + 8, by + 10), text, fill=INK_COLOR, font=self.font_small)

    def _draw_border(self, draw: ImageDraw.Draw) -> None:
        """Draw thick manga panel border."""
        draw.rectangle([0, 0, PANEL_W - 1, PANEL_H - 1], outline=INK_COLOR, width=4)

    def _apply_sketch_filter(self, img: Image.Image) -> Image.Image:
        """Apply a slight sketch/ink texture effect."""
        if CV2_AVAILABLE:
            arr     = np.array(img)
            gray    = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            _, bw   = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            result  = cv2.cvtColor(bw, cv2.COLOR_GRAY2RGB)
            return Image.fromarray(result)

        # PIL fallback — just sharpen slightly
        return img.filter(ImageFilter.SHARPEN)
