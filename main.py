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
        
        self.pulse_scale = 1.0
        self.mouth_open = 0.0
        self.walk_cycle = 0.0
        self.morph_factor = 0.0  
        self.glow_color = [0.0, 0.8, 1.0, 1.0] 
        
        Clock.schedule_interval(self.update_vectors, 1/60.0)
        self.trigger_idle_behavior()

    def update_vectors(self, dt: float) -> None:
        self.redraw()

    def redraw(self, *args) -> None:
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y + 60 
        
        with self.canvas:
            Color(*self.glow_color)
            
            w_h, h_h = 120 * self.pulse_scale, 100 * self.pulse_scale
            head_points = [
                cx, cy + h_h,
                cx - w_h, cy + h_h,
                cx - (w_h*0.4), cy,
                cx, cy - h_h + (self.mouth_open * -20), 
                cx + (w_h*0.4), cy,
                cx + w_h, cy + h_h,
                cx, cy + h_h
            ]
            
            walk_offset = math.sin(self.walk_cycle) * 25
            body_points = [
                cx - 40, cy + 60,
                cx - 150, cy + 20,
                cx - 180, cy - 80 + abs(walk_offset),  
                cx - 60, cy - 80 + walk_offset,        
                cx + 20, cy - 40,
                cx + 80, cy + 10,
                cx - 40, cy + 60
            ]
            
            if self.morph_factor < 0.5:
                Line(points=head_points, width=2.5, close=True)
                Line(points=[cx - 40, cy + 20, cx - 15, cy + 15], width=2.5)
                Line(points=[cx + 40, cy + 20, cx + 15, cy + 15], width=2.5)
            else:
                Line(points=body_points, width=2.5, close=True)

    def trigger_idle_behavior(self) -> None:
        Animation.cancel_all(self)
        self.morph_factor = 0.0
        self.glow_color = [0.0, 0.8, 1.0, 1.0] 
        anim = Animation(pulse_scale=1.05, duration=1.8, t='in_out_sine') + \
               Animation(pulse_scale=0.95, duration=1.8, t='in_out_sine')
        anim.repeat = True
        anim.start(self)

    def trigger_talk_power(self, duration: float) -> None:
        self.glow_color = [0.2, 1.0, 0.4, 1.0] 
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
        Animation.cancel_all(self)
        self.glow_color = [1.0, 0.3, 0.3, 1.0] 
        morph_anim = Animation(morph_factor=1.0, duration=1.0, t='in_out_quad')
        morph_anim.start(self)
        Clock.schedule_interval(self.execute_walk_ticks, 1/60.0)
        Clock.schedule_once(lambda dt: self.reset_from_meltdown(), 6.0)

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
        
        self.roasts = [
            "Is that your actual code or did a cat step on your keyboard?",
            "Your layout looks like a website from 1998. Try again.",
            "I've seen smarter calculators than your current logic tree.",
            "Are we building an app or are you just testing my patience?",
            "That question was so basic I think my glowing circuits just melted a little."
        ]

        self.main_layout = MDBoxLayout(orientation='vertical', padding=20, spacing=15)
        
        self.fox_widget = GlowingFoxVector()
        self.main_layout.add_widget(self.fox_widget)
        
        self.dialog_box = MDLabel(
            text="[ Foxy ]: Ask me about your Legal Rights, Coding, Network Safety, or Forms.",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="Body1",
            size_hint_y=None,
            height=140
        )
        self.main_layout.add_widget(self.dialog_box)
        
        self.user_input = MDTextField(
            hint_text="Ask Foxy anything...",
            line_color_focus=(0, 0.8, 1, 1),
            text_color_focus=(1, 1, 1, 1),
            size_hint_y=None,
            height=50
        )
        self.main_layout.add_widget(self.user_input)
        
        self.btn_layout = MDBoxLayout(orientation='horizontal', spacing=15, size_hint_y=None, height=50)
        
        self.send_btn = MDRaisedButton(
            text="Send Inquiry", 
            md_bg_color=(0.0, 0.6, 0.9, 1.0),
            on_release=self.process_user_message
        )
        self.meltdown_btn = MDRaisedButton(
            text="Meltdown Mode", 
            md_bg_color=(0.9, 0.2, 0.2, 1.0),
            on_release=self.activate_full_rage
        )
        
        self.btn_layout.add_widget(self.send_btn)
        self.btn_layout.add_widget(self.meltdown_btn)
        self.main_layout.add_widget(self.btn_layout)
        
        self.add_widget(self.main_layout)

    def process_user_message(self, instance) -> None:
        text = self.user_input.text.strip().lower()
        if not text:
            return
            
        response = ""
        speak_time = 3.0

        if any(w in text for w in ["law", "rights", "police", "arrest", "court", "crime"]):
            legal_nodes = [
                "LAW ASSISTANT: If stopped, calmly ask: 'Am I free to go or am I being detained?'. If detained, you have the right to remain silent. Do not sign anything without consulting a legal representative.",
                "RIGHTS ASSISTANT: Protect against false accusations by maintaining silence. Explicitly state: 'I am invoking my right to remain silent'. Do not answer probing questions without counsel present.",
                "CIVIL PROTECTION: Authorities generally require a signed warrant to search private property or electronic devices. Assert your rights clearly and calmly without physical resistance."
            ]
            response = f"[ Foxy ]: {random.choice(legal_nodes)}"
            speak_time = 5.5

        elif any(w in text for w in ["code", "error", "syntax", "python", "github", "bug"]):
            coding_nodes = [
                "CODING BLUEPRINT: Check your indentation matrix. Python relies entirely on straight, aligned spacing structure. One stray space will derail the interpreter.",
                "COMPILATION ASSISTANT: Check your file naming schemas. Files like 'buildozer.spec' or 'main.py' must remain lowercase and sit directly inside the root folder repository.",
                "DEBUGGER ASSISTANT: When encountering a workflow crash, navigate into the failed Job logs, find the first red marker line, and isolate the syntax exception error."
            ]
            response = f"[ Foxy ]: {random.choice(coding_nodes)}"
            speak_time = 5.0

        elif any(w in text for w in ["wifi", "router", "password", "hack", "network"]):
            response = ("[ Foxy ]: SECURITY AUDITING: For home data defense, access your router panel "
                        "and immediately disable WPS (Wi-Fi Protected Setup), upgrade security configurations "
                        "to WPA3, and replace the factory-default administrator credentials.")
            speak_time = 5.0

        elif any(w in text for w in ["form", "fill", "details", "document", "paperwork"]):
            response = ("[ Foxy ]: FORM TRAINER: When completing paperwork, process layouts step-by-step. "
                        "Verify that field categories exactly match expected strings. Keep structural descriptions "
                        "clear, check submission rules, and avoid modifying strict structural text blocks.")
            speak_time = 5.5

        else:
            response = f"[ Foxy ]: {random.choice(self.roasts)}"
            speak_time = 3.5

        self.dialog_box.text = response
        self.user_input.text = ""
        self.fox_widget.trigger_talk_power(duration=speak_time)

    def activate_full_rage(self, instance) -> None:
        self.dialog_box.text = "[ Foxy ]: ENOUGH! My data banks are overloaded. Initiating structural behavior adjustment pacing sequence!"
        self.fox_widget.trigger_meltdown_walk()


class BlackFoxyApp(MDApp):
    def build(self) -> MDScreen:
        self.theme_cls.theme_style = "Dark"
        return BlackFoxyBrainScreen()

if __name__ == '__main__':
    BlackFoxyApp().run()
