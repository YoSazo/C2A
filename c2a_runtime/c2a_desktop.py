#!/usr/bin/env python3
"""
C2A Desktop Integration - Full Immersion Mode

Your desktop becomes a living reflection of your constraint transmutation journey.

Features:
- Dynamic border colors based on current archetype
- Waybar integration showing level, archetype, active lesson
- Wallpaper color shifts per archetype
- Notifications for C2A events (level up, breakthroughs, lessons)
- Lock screen displays active lesson

Philosophy: "The environment shapes the mind. Let your desktop embody transmutation."
"""

import json
import subprocess
import os
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class Archetype(Enum):
    """The Five Archetypal Constraints with their visual identities"""
    SCARCITY = "scarcity"
    VELOCITY = "velocity"
    ASYMMETRY = "asymmetry"
    FRICTION = "friction"
    PARADOX = "paradox"


@dataclass
class ArchetypeTheme:
    """Visual theme for each archetype"""
    name: str
    symbol: str
    primary_color: str      # Hex color for borders, accents
    secondary_color: str    # Gradient end color
    rgb_color: str          # For hyprctl (rgb format)
    rgb_secondary: str      # For gradient end
    hue_shift: int          # Degrees to shift wallpaper hue (0-360)
    urgency: str            # low, normal, critical - for notifications
    

# The Five Archetype Themes
ARCHETYPE_THEMES: Dict[str, ArchetypeTheme] = {
    "scarcity": ArchetypeTheme(
        name="Scarcity",
        symbol="⧗",
        primary_color="#ff8c00",      # Orange
        secondary_color="#ffb347",
        rgb_color="rgb(ff8c00)",
        rgb_secondary="rgb(ffb347)",
        hue_shift=30,                 # Warm orange shift
        urgency="normal"
    ),
    "velocity": ArchetypeTheme(
        name="Velocity",
        symbol="⚡",
        primary_color="#ffd700",      # Gold/Yellow
        secondary_color="#fff44f",
        rgb_color="rgb(ffd700)",
        rgb_secondary="rgb(fff44f)",
        hue_shift=50,                 # Yellow shift
        urgency="critical"            # Velocity is urgent!
    ),
    "asymmetry": ArchetypeTheme(
        name="Asymmetry",
        symbol="⚖",
        primary_color="#00ced1",      # Cyan/Teal
        secondary_color="#40e0d0",
        rgb_color="rgb(00ced1)",
        rgb_secondary="rgb(40e0d0)",
        hue_shift=180,                # Cyan shift
        urgency="normal"
    ),
    "friction": ArchetypeTheme(
        name="Friction",
        symbol="⚙",
        primary_color="#ff4757",      # Red/Pink
        secondary_color="#ff6b81",
        rgb_color="rgb(ff4757)",
        rgb_secondary="rgb(ff6b81)",
        hue_shift=0,                  # Red (no shift or full circle)
        urgency="normal"
    ),
    "paradox": ArchetypeTheme(
        name="Paradox",
        symbol="∞",
        primary_color="#9b59b6",      # Purple
        secondary_color="#be90d4",
        rgb_color="rgb(9b59b6)",
        rgb_secondary="rgb(be90d4)",
        hue_shift=280,                # Purple shift
        urgency="low"                 # Paradox is contemplative
    )
}

# Neutral theme when not in a session
NEUTRAL_THEME = ArchetypeTheme(
    name="Awareness",
    symbol="◯",
    primary_color="#4a4a5e",
    secondary_color="#6a6a7e",
    rgb_color="rgb(4a4a5e)",
    rgb_secondary="rgb(6a6a7e)",
    hue_shift=0,
    urgency="low"
)


class C2ADesktop:
    """
    Desktop integration controller for C2A.
    
    Manages:
    - Hyprland border colors
    - Waybar custom module data
    - Wallpaper transitions (swww or hyprpaper)
    - Desktop notifications
    - Lock screen configuration
    """
    
    def __init__(self):
        self.home = Path.home()
        self.c2a_dir = Path(__file__).parent
        self.config_dir = self.home / ".config"
        self.state_file = self.c2a_dir / "desktop_state.json"
        self.waybar_data_file = self.config_dir / "waybar" / "c2a_data.json"
        
        # Ensure waybar data directory exists
        self.waybar_data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize state
        self.state = self._load_state()
        
        # Check what tools are available
        self.has_swww = self._command_exists("swww")
        self.has_hyprctl = self._command_exists("hyprctl")
        self.has_notify = self._command_exists("notify-send")
        self.has_hyprlock = self._command_exists("hyprlock")
    
    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists in PATH"""
        try:
            subprocess.run(["which", cmd], capture_output=True, check=True)
            return True
        except:
            return False
    
    def _load_state(self) -> Dict:
        """Load persistent state"""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except:
                pass
        return {
            "current_archetype": None,
            "in_session": False,
            "level": 1,
            "total_sessions": 0,
            "last_score": 0,
            "streak": 0
        }
    
    def _save_state(self):
        """Save persistent state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _run_hyprctl(self, *args) -> bool:
        """Run a hyprctl command"""
        if not self.has_hyprctl:
            return False
        try:
            subprocess.run(["hyprctl"] + list(args), capture_output=True, check=True)
            return True
        except Exception as e:
            print(f"hyprctl error: {e}")
            return False
    
    def _notify(self, title: str, body: str, urgency: str = "normal", icon: str = None):
        """Send a desktop notification"""
        if not self.has_notify:
            return
        
        cmd = ["notify-send", title, body, "-u", urgency]
        if icon:
            cmd.extend(["-i", icon])
        
        # Add C2A branding
        cmd.extend(["-a", "C2A"])
        
        try:
            subprocess.run(cmd, capture_output=True)
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # BORDER CONTROL
    # ═══════════════════════════════════════════════════════════════════════════
    
    def set_borders(self, archetype: str = None):
        """
        Set Hyprland border colors based on archetype.
        
        Args:
            archetype: Archetype name, or None for neutral
        """
        theme = ARCHETYPE_THEMES.get(archetype, NEUTRAL_THEME) if archetype else NEUTRAL_THEME
        
        # Set active border with gradient
        self._run_hyprctl(
            "keyword", "general:col.active_border",
            f"{theme.rgb_color} {theme.rgb_secondary} 45deg"
        )
        
        # Set inactive border (dimmed version)
        self._run_hyprctl(
            "keyword", "general:col.inactive_border",
            "rgba(4a4a5eaa)"
        )
        
        self.state["current_archetype"] = archetype
        self._save_state()
    
    def pulse_borders(self, archetype: str):
        """
        Pulse the borders for emphasis (e.g., on level up).
        Uses animation speed change.
        """
        theme = ARCHETYPE_THEMES.get(archetype, NEUTRAL_THEME)
        
        # Speed up border animation temporarily
        self._run_hyprctl("keyword", "animations:animation", "borderangle, 1, 5, linear, loop")
        
        # Set bright colors
        self._run_hyprctl(
            "keyword", "general:col.active_border",
            f"{theme.rgb_color} {theme.rgb_secondary} 45deg"
        )
        
        # Reset after a moment (would need async, simplified here)
        # In practice, this could be done with a background process
    
    # ═══════════════════════════════════════════════════════════════════════════
    # WAYBAR INTEGRATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def update_waybar(self, 
                      level: int = None,
                      archetype: str = None,
                      active_lesson: str = None,
                      in_session: bool = None,
                      score: int = None,
                      streak: int = None):
        """
        Update Waybar C2A module data.
        
        Writes to ~/.config/waybar/c2a_data.json which the custom module reads.
        """
        # Update state
        if level is not None:
            self.state["level"] = level
        if in_session is not None:
            self.state["in_session"] = in_session
        if score is not None:
            self.state["last_score"] = score
        if streak is not None:
            self.state["streak"] = streak
        if archetype is not None:
            self.state["current_archetype"] = archetype
        
        self._save_state()
        
        # Get theme
        theme = ARCHETYPE_THEMES.get(self.state.get("current_archetype"), NEUTRAL_THEME)
        
        # Build waybar data
        waybar_data = {
            "text": self._build_waybar_text(theme),
            "tooltip": self._build_waybar_tooltip(theme, active_lesson),
            "class": self.state.get("current_archetype", "neutral"),
            "alt": theme.symbol
        }
        
        # Write for waybar custom module
        with open(self.waybar_data_file, 'w') as f:
            json.dump(waybar_data, f)
        
        # Signal waybar to refresh (SIGUSR2)
        try:
            subprocess.run(["pkill", "-SIGUSR2", "waybar"], capture_output=True)
        except:
            pass
    
    def _build_waybar_text(self, theme: ArchetypeTheme) -> str:
        """Build the main waybar display text"""
        level = self.state.get("level", 1)
        in_session = self.state.get("in_session", False)
        
        if in_session:
            return f"{theme.symbol} Lv.{level}"
        else:
            return f"◯ Lv.{level}"
    
    def _build_waybar_tooltip(self, theme: ArchetypeTheme, active_lesson: str = None) -> str:
        """Build the waybar tooltip with full info"""
        lines = [
            f"C2A - Constraint to Advantage",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Level: {self.state.get('level', 1)}",
            f"Sessions: {self.state.get('total_sessions', 0)}",
            f"Last Score: {self.state.get('last_score', 0)}",
            f"Streak: {self.state.get('streak', 0)}",
        ]
        
        if self.state.get("current_archetype"):
            lines.append(f"Current: {theme.symbol} {theme.name}")
        
        if active_lesson:
            lines.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"🎯 Active Lesson:")
            lines.append(f"   {active_lesson}")
        
        return "\n".join(lines)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # WALLPAPER CONTROL
    # ═══════════════════════════════════════════════════════════════════════════
    
    def set_wallpaper_tint(self, archetype: str = None):
        """
        Apply a color tint to the wallpaper based on archetype.
        
        Uses swww if available for smooth transitions, 
        otherwise falls back to hyprpaper with pre-generated images.
        """
        if self.has_swww:
            self._set_wallpaper_swww(archetype)
        else:
            # Fallback: we'll use CSS-like overlay via Hyprland decoration
            # or pre-tinted wallpapers
            self._set_wallpaper_hyprpaper(archetype)
    
    def _set_wallpaper_swww(self, archetype: str = None):
        """Use swww for smooth wallpaper transitions with color overlay"""
        theme = ARCHETYPE_THEMES.get(archetype, NEUTRAL_THEME) if archetype else NEUTRAL_THEME
        
        # swww can apply color filters during transition
        wallpaper = self.home / "Downloads/wallpapers/wallpaper5.jpg"
        
        # Transition with tint
        cmd = [
            "swww", "img", str(wallpaper),
            "--transition-type", "fade",
            "--transition-duration", "2",
            "--transition-fps", "60"
        ]
        
        try:
            subprocess.run(cmd, capture_output=True)
        except:
            pass
    
    def _set_wallpaper_hyprpaper(self, archetype: str = None):
        """Fallback using hyprpaper - requires pre-generated tinted wallpapers"""
        # For now, just use the base wallpaper
        # Full implementation would generate tinted versions
        pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # C2A EVENT NOTIFICATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def notify_session_start(self, archetype: str):
        """Notify when a C2A session starts"""
        theme = ARCHETYPE_THEMES.get(archetype, NEUTRAL_THEME)
        self._notify(
            f"{theme.symbol} C2A Session Started",
            f"Entering {theme.name} transmutation mode.\nConstraints are fuel.",
            theme.urgency
        )
        
        # Update borders and waybar
        self.set_borders(archetype)
        self.update_waybar(archetype=archetype, in_session=True)
    
    def notify_session_end(self, score: int, archetype: str):
        """Notify when a C2A session ends"""
        theme = ARCHETYPE_THEMES.get(archetype, NEUTRAL_THEME)
        
        # Determine message based on score
        if score >= 85:
            msg = "Masterful transmutation! 🌟"
            urgency = "normal"
        elif score >= 70:
            msg = "Solid transmutation. Keep flowing."
            urgency = "low"
        elif score >= 50:
            msg = "The river finds its path. Continue."
            urgency = "low"
        else:
            msg = "Every constraint teaches. Return when ready."
            urgency = "low"
        
        self._notify(
            f"{theme.symbol} Session Complete: {score}/100",
            msg,
            urgency
        )
        
        # Return to neutral borders
        self.set_borders(None)
        self.update_waybar(in_session=False, score=score)
    
    def notify_level_up(self, new_level: int, archetype: str):
        """Celebrate a level up!"""
        theme = ARCHETYPE_THEMES.get(archetype, NEUTRAL_THEME)
        
        # Level milestones
        if new_level % 10 == 0:
            msg = f"MILESTONE! Level {new_level} achieved!\n\"The constraint is not the enemy of creativity; it is the condition for it.\""
            urgency = "critical"
        else:
            msg = f"Level {new_level} unlocked.\nThe path deepens."
            urgency = "normal"
        
        self._notify(f"📈 LEVEL UP! → {new_level}", msg, urgency)
        
        # Pulse borders for celebration
        self.pulse_borders(archetype)
        self.update_waybar(level=new_level)
    
    def notify_lesson_mastered(self, lesson_title: str):
        """Celebrate mastering a lesson"""
        self._notify(
            f"🎯 Lesson Mastered!",
            f"\"{lesson_title}\"\n\nThe pattern is now part of you.",
            "normal"
        )
    
    def notify_breakthrough(self, pattern: str):
        """Celebrate a breakthrough moment"""
        self._notify(
            "🌟 BREAKTHROUGH!",
            f"Pattern recognized: {pattern}\n\n\"What was obstacle becomes path.\"",
            "critical"
        )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LOCK SCREEN / IDLE INTEGRATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def update_lockscreen_lesson(self, lesson_title: str, lesson_question: str):
        """
        Update hyprlock config to show the active lesson.
        
        Writes to ~/.config/hypr/hyprlock.conf
        """
        if not self.has_hyprlock:
            return
        
        hyprlock_conf = self.config_dir / "hypr" / "hyprlock.conf"
        
        # Generate hyprlock config with lesson
        config = self._generate_hyprlock_config(lesson_title, lesson_question)
        
        try:
            with open(hyprlock_conf, 'w') as f:
                f.write(config)
        except Exception as e:
            print(f"Error writing hyprlock config: {e}")
    
    def _generate_hyprlock_config(self, lesson_title: str, lesson_question: str) -> str:
        """Generate hyprlock configuration with active lesson display"""
        # Escape quotes in lesson text
        lesson_title = lesson_title.replace('"', '\\"')
        lesson_question = lesson_question.replace('"', '\\"')
        
        return f'''# C2A Hyprlock Configuration
# Auto-generated - Your desktop embodies transmutation

background {{
    monitor =
    path = ~/Downloads/wallpapers/wallpaper5.jpg
    blur_passes = 3
    blur_size = 8
    noise = 0.0117
    contrast = 0.8916
    brightness = 0.7
    vibrancy = 0.1696
    vibrancy_darkness = 0.0
}}

# Clock
label {{
    monitor =
    text = $TIME
    color = rgba(200, 200, 200, 1.0)
    font_size = 72
    font_family = JetBrainsMono Nerd Font
    position = 0, 200
    halign = center
    valign = center
}}

# Date
label {{
    monitor =
    text = cmd[update:3600000] date "+%A, %B %d"
    color = rgba(150, 150, 150, 0.8)
    font_size = 24
    font_family = JetBrainsMono Nerd Font
    position = 0, 120
    halign = center
    valign = center
}}

# C2A Active Lesson Title
label {{
    monitor =
    text = 🎯 {lesson_title}
    color = rgba(255, 200, 100, 1.0)
    font_size = 28
    font_family = JetBrainsMono Nerd Font
    position = 0, -50
    halign = center
    valign = center
}}

# C2A Active Lesson Question
label {{
    monitor =
    text = "{lesson_question}"
    color = rgba(200, 200, 200, 0.9)
    font_size = 18
    font_family = JetBrainsMono Nerd Font
    position = 0, -100
    halign = center
    valign = center
}}

# Input field
input-field {{
    monitor =
    size = 300, 50
    outline_thickness = 3
    dots_size = 0.33
    dots_spacing = 0.15
    dots_center = true
    outer_color = rgba(100, 100, 120, 0.8)
    inner_color = rgba(30, 30, 40, 0.9)
    font_color = rgb(200, 200, 200)
    fade_on_empty = true
    placeholder_text = <i>Transmute...</i>
    hide_input = false
    position = 0, -200
    halign = center
    valign = center
}}
'''

    # ═══════════════════════════════════════════════════════════════════════════
    # CONVENIENCE METHODS FOR C2A INTEGRATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def on_session_start(self, archetype: str, level: int, active_lesson: dict = None):
        """Called when a C2A session starts"""
        self.state["in_session"] = True
        self.state["current_archetype"] = archetype
        self.state["level"] = level
        
        lesson_title = active_lesson.get("title", "") if active_lesson else ""
        lesson_question = active_lesson.get("practice_question", "") if active_lesson else ""
        
        # Update everything
        self.set_borders(archetype)
        self.update_waybar(
            level=level,
            archetype=archetype,
            active_lesson=lesson_title,
            in_session=True
        )
        self.notify_session_start(archetype)
        
        if lesson_title:
            self.update_lockscreen_lesson(lesson_title, lesson_question)
    
    def on_session_end(self, 
                       score: int, 
                       archetype: str, 
                       level: int,
                       leveled_up: bool = False,
                       lesson_mastered: bool = False,
                       lesson_title: str = None,
                       breakthrough: bool = False,
                       pattern: str = None):
        """Called when a C2A session ends"""
        self.state["in_session"] = False
        self.state["total_sessions"] = self.state.get("total_sessions", 0) + 1
        self.state["last_score"] = score
        self.state["level"] = level
        
        # Update streak
        if score >= 70:
            self.state["streak"] = self.state.get("streak", 0) + 1
        else:
            self.state["streak"] = 0
        
        # Notify session end
        self.notify_session_end(score, archetype)
        
        # Check for special events
        if leveled_up:
            self.notify_level_up(level, archetype)
        
        if lesson_mastered and lesson_title:
            self.notify_lesson_mastered(lesson_title)
        
        if breakthrough and pattern:
            self.notify_breakthrough(pattern)
        
        # Return to neutral state
        self.set_borders(None)
        self.update_waybar(in_session=False, level=level, score=score)
        
        self._save_state()
    
    def sync_from_c2a_state(self):
        """
        Sync desktop state from C2A data files.
        
        Reads from:
        - memory_data/active_lesson.json
        - memory_data/lesson_history.json
        - User stats from memory system
        """
        # Read active lesson
        lesson_file = self.c2a_dir / "memory_data" / "active_lesson.json"
        if lesson_file.exists():
            try:
                with open(lesson_file) as f:
                    lesson_data = json.load(f)
                    if lesson_data:
                        self.update_waybar(
                            active_lesson=lesson_data.get("title", "")
                        )
                        self.update_lockscreen_lesson(
                            lesson_data.get("title", ""),
                            lesson_data.get("practice_question", "")
                        )
            except:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """CLI for testing desktop integration"""
    import sys
    
    desktop = C2ADesktop()
    
    if len(sys.argv) < 2:
        print("C2A Desktop Integration")
        print("=" * 40)
        print("\nUsage:")
        print("  c2a_desktop.py borders <archetype|neutral>")
        print("  c2a_desktop.py waybar")
        print("  c2a_desktop.py notify <event>")
        print("  c2a_desktop.py sync")
        print("  c2a_desktop.py demo")
        print("\nArchetypes: scarcity, velocity, asymmetry, friction, paradox")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "borders":
        archetype = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "neutral" else None
        desktop.set_borders(archetype)
        print(f"Borders set to: {archetype or 'neutral'}")
    
    elif cmd == "waybar":
        desktop.sync_from_c2a_state()
        print("Waybar updated from C2A state")
    
    elif cmd == "sync":
        desktop.sync_from_c2a_state()
        print("Desktop synced with C2A state")
    
    elif cmd == "demo":
        print("Running demo sequence...")
        import time
        
        for archetype in ["scarcity", "velocity", "asymmetry", "friction", "paradox"]:
            print(f"\n→ {archetype.upper()}")
            desktop.set_borders(archetype)
            desktop.update_waybar(archetype=archetype, in_session=True)
            time.sleep(2)
        
        print("\n→ NEUTRAL")
        desktop.set_borders(None)
        desktop.update_waybar(in_session=False)
        print("\nDemo complete!")
    
    elif cmd == "notify":
        event = sys.argv[2] if len(sys.argv) > 2 else "test"
        if event == "levelup":
            desktop.notify_level_up(42, "friction")
        elif event == "breakthrough":
            desktop.notify_breakthrough("The Removal Test")
        elif event == "lesson":
            desktop.notify_lesson_mastered("What The Constraint Creates")
        else:
            desktop._notify("C2A Test", "Desktop integration is working!", "normal")


if __name__ == "__main__":
    main()
