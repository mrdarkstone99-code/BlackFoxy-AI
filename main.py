from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.clock import Clock
import math
import random

Window.clearcolor = (0, 0, 0, 1)

class GlowingFoxVector(Widget):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw)
        
        # Power & Animation Matrix Variables
        self.pulse_scale = 1.0
        self.mouth_open = 0.0
        self.walk_cycle = 0.0
        self.morph_factor = 0.0  # 0.0 = Head Only, 1.0 = Full Body Strut
        self.glow_color = [0.0, 0.8, 1.0, 1.0] # Starts Cyan Neon
        
        Clock.schedule_interval(self.update_vectors, 1/60.0)
        self.trigger_idle_behavior()

    def update_vectors(self, dt: float) -> None:
        self.redraw()

    def redraw(self, *args) -> None:
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y + 40 # Shift up slightly for text layout
        
        with self.canvas:
            Color(*self.glow_color)
            
            # --- GEOMETRY A: FOX FACE VECTOR ---
            w_h, h_h = 120 * self.pulse_scale, 100 * self.pulse_scale
            head_points = [
                cx, cy + h_h,
                cx - w_h, cy + h_h,
                cx - (w_h*0.4), cy,
                cx, cy - h_h + (self.mouth_open * -20), # Dynamic jaw drop
                cx + (w_h*0.4), cy,
                cx + w_h, cy + h_h,
                cx, cy + h_h
            ]
            
            # --- GEOMETRY B: FULL BODY SWAGGER MORPH ---
            walk_offset = math.sin(self.walk_cycle) * 25
            body_points = [
                cx - 40, cy + 60,
                cx - 150, cy + 20,
                cx - 180, cy - 80 + abs(walk_offset),  # Moving back leg
                cx - 60, cy - 80 + walk_offset,        # Moving front leg
                cx + 20, cy - 40,
                cx + 80, cy + 10,
                cx - 40, cy + 60
            ]
            
            # Draw primary vector outline based on morph level
            Line(points=head_points if self.morph_factor < 0.5 else body_points, width=2.5, close=True)
            
            # Draw neon eyes when in face mode
            if self.morph_factor < 0.5:
                Line(points=[cx - 40, cy + 20, cx - 15, cy + 15], width=2.5)
                Line(points=[cx + 40, cy + 20, cx + 15, cy + 15], width=2.5)

    def trigger_idle_behavior(self) -> None:
        Animation.cancel_all(self)
        self.morph_factor = 0.0
        self.glow_color = [0.0, 0.8, 1.0, 1.0] # Standard Calm Cyan
        anim = Animation(pulse_scale=1.05, duration=1.8, t='in_out_sine') + \
               Animation(pulse_scale=0.95, duration=1.8, t='in_out_sine')
        anim.repeat = True
        anim.start(self)

    def trigger_talk_power(self, duration: float) -> None:
        """ Power Mode 2: Rapid vector jaw tracking for speaking """
        self.glow_color = [0.2, 1.0, 0.4, 1.0] # Shifts to bright energetic green
        self.mouth_anim = Animation(mouth_open=1.0, duration=0.1) + \
                          Animation(mouth_open=0.0, duration=0.1)
        self.mouth_anim.repeat = True
        self.mouth_anim.start(self)
        
        Clock.schedule_once(lambda dt: self.stop_talking(), duration)

    def stop_talking(self) -> None:
        if hasattr(self, 'mouth_anim'):
            self.mouth_anim.cancel(self)
        self.mouth_open = 0.0
        self.trigger_idle_behavior()

    def trigger_meltdown_walk(self) -> None:
        """ Power Mode 3: Geometry transformation into attitude body strut """
        Animation.cancel_all(self)
        self.glow_color = [1.0, 0.3, 0.3, 1.0] # Sparks Angry Neon Red
        
        morph_anim = Animation(morph_factor=1.0, duration=1.0, t='in_out_quad')
        morph_anim.start(self)
        
        Clock.schedule_interval(self.execute_walk_ticks, 1/60.0)
        # Return back to normal head mode after 5 seconds of stomping around
        Clock.schedule_once(lambda dt: self.reset_from_meltdown(), 5.0)

    def execute_walk_ticks(self, dt: float) -> None:
        if self.morph_factor > 0.8:
            self.walk_cycle += 0.2

    def reset_from_meltdown(self) -> None:
        Clock.unschedule(self.execute_walk_ticks)
        morph_back = Animation(morph_factor=0.0, duration=1.0, t='in_out_quad')
        morph_back.bind(on_complete=lambda *args: self.trigger_idle_behavior())
        morph_back.start(self)


class BlackFoxyBrainScreen(MDScreen):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        
        # Sarcastic Brain Roast Database
        self.roasts = [
            "Is that your actual code or did a cat step on your keyboard?",
            "Your layout looks like a website from 1998. Try again.",
            "I've seen smarter calculators than your current logic tree.",
            "Error 404: Your coding talent could not be located.",
            "Wow... typing words into a terminal. You must feel like a real hacker.",
            "Are we building an app or are you just testing my patience?",
            "That question was so basic I think my glowing circuits just melted a little."
        ]

        # Core Interface Structure Layout
        self.main_layout = MDBoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # 1. Add the vector graphic system container
        self.fox_widget = GlowingFoxVector()
        self.main_layout.add_widget(self.fox_widget)
        
        # 2. Sarcastic AI Dialog box text display area
        self.dialog_box = MDLabel(
            text="[ Foxy ]: Type something below so I can judge your life choices.",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="Subtitle1",
            size_hint_y=None,
            height=80
        )
        self.main_layout.add_widget(self.dialog_box)
        
        # 3. Interactive Input Field Box
        self.user_input = MDTextField(
            hint_text="Talk to the Fox...",
            line_color_focus=(0, 0.8, 1, 1),
            text_color_focus=(1, 1, 1, 1),
            current_hint_text_color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=50
        )
        self.main_layout.add_widget(self.user_input)
        
        # 4. Action Execution Buttons
        self.btn_layout = MDBoxLayout(orientation='horizontal', spacing=15, size_hint_y=None, height=50)
        
        self.send_btn = MDRaisedButton(
            text="Send Message", 
            md_bg_color=(0.0, 0.6, 0.9, 1.0),
            on_release=self.process_user_message
        )
        self.meltdown_btn = MDRaisedButton(
            text="Trigger Meltdown Mode", 
            md_bg_color=(0.9, 0.2, 0.2, 1.0),
            on_release=self.activate_full_rage
        )
        
        self.btn_layout.add_widget(self.send_btn)
        self.btn_layout.add_widget(self.meltdown_btn)
        self.main_layout.add_widget(self.btn_layout)
        
        self.add_widget(self.main_layout)

    def process_user_message(self, instance) -> None:
        text = self.user_input.text.strip()
        if not text:
            return
            
        # Select a random heavy roast from database
        selected_roast = random.choice(self.roasts)
        self.dialog_box.text = f"[ Foxy ]: {selected_roast}"
        self.user_input.text = "" # Clear field
        
        # Fire Power Mode 2 (Mouth lines animation based on text length)
        speak_time = max(2.5, len(selected_roast) * 0.05)
        self.fox_widget.trigger_talk_power(duration=speak_time)

    def activate_full_rage(self, instance) -> None:
        """ Manual push button to trigger power mode 3 vector morphing """
        self.dialog_box.text = "[ Foxy ]: ENOUGH! Your input is so bad I need to pace around the room."
        self.fox_widget.trigger_meltdown_walk()


class BlackFoxyApp(MDApp):
    def build(self) -> MDScreen:
        self.theme_cls.theme_style = "Dark"
        return BlackFoxyBrainScreen()

if __name__ == '__main__':
    BlackFoxyApp().run()
