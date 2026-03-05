#!/usr/bin/env python3
"""C2A Desktop UI - Screen 1 (Minimal monochrome landing)."""

import json
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox


class C2ALandingApp(tk.Tk):
    """Desktop landing screen for C2A."""

    def __init__(self):
        super().__init__()
        self.title("C2A Desktop")
        self.geometry("1280x800")
        self.minsize(960, 640)

        self.project_root = Path(__file__).parent
        self.desktop_state_path = self.project_root / "desktop_state.json"
        self.lesson_path = self.project_root / "memory_data" / "active_lesson.json"

        self.colors = {
            "bg": "#f3f3f5",
            "surface": "#ffffff",
            "surface_alt": "#fafafa",
            "ink": "#0b0b0c",
            "muted": "#6d6e73",
            "line": "#e7e7ea",
            "button": "#0a0a0a",
            "button_text": "#ffffff",
            "badge": "#f0f0f3",
        }

        self.stats = self.load_stats()
        self.active_lesson = self.load_active_lesson()

        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=self.colors["bg"])
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.on_resize)

        self.start_btn = None

    def load_stats(self):
        """Load lightweight stats from desktop integration state."""
        default = {
            "level": 1,
            "total_sessions": 0,
            "streak": 0,
            "last_score": 0,
        }

        if not self.desktop_state_path.exists():
            return default

        try:
            with self.desktop_state_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            return {
                "level": int(data.get("level", default["level"])),
                "total_sessions": int(data.get("total_sessions", default["total_sessions"])),
                "streak": int(data.get("streak", default["streak"])),
                "last_score": int(data.get("last_score", default["last_score"])),
            }
        except Exception:
            return default

    def load_active_lesson(self):
        """Load active lesson title if present."""
        if not self.lesson_path.exists():
            return "No active lesson yet"

        try:
            with self.lesson_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            title = data.get("title")
            return title if title else "No active lesson yet"
        except Exception:
            return "No active lesson yet"

    def on_resize(self, event):
        """Redraw layout when window size changes."""
        width = max(event.width, 960)
        height = max(event.height, 640)

        self.canvas.delete("all")
        self.draw_layout(width, height)

    def draw_layout(self, width, height):
        """Draw the minimal monochrome landing layout."""
        self.canvas.create_rectangle(0, 0, width, height, fill=self.colors["bg"], outline="")

        card_w = min(1040, width - 96)
        card_h = min(640, height - 84)
        card_x1 = (width - card_w) / 2
        card_y1 = (height - card_h) / 2
        card_x2 = card_x1 + card_w
        card_y2 = card_y1 + card_h

        # Main squircle surface
        self.rounded_rect(
            card_x1,
            card_y1,
            card_x2,
            card_y2,
            38,
            self.colors["surface"],
            self.colors["line"],
            1,
        )

        # Header
        self.canvas.create_text(
            card_x1 + 56,
            card_y1 + 62,
            text="C2A",
            anchor="w",
            fill=self.colors["ink"],
            font=("SF Pro Display", 22, "bold"),
        )
        self.canvas.create_text(
            card_x1 + 56,
            card_y1 + 102,
            text="Constraint to Advantage",
            anchor="w",
            fill=self.colors["muted"],
            font=("SF Pro Text", 12),
        )

        # Top-right badge
        self.rounded_rect(
            card_x2 - 220,
            card_y1 + 42,
            card_x2 - 56,
            card_y1 + 88,
            18,
            self.colors["badge"],
            self.colors["line"],
            1,
        )
        self.canvas.create_text(
            card_x2 - 138,
            card_y1 + 65,
            text="Screen 1",
            anchor="center",
            fill=self.colors["muted"],
            font=("SF Pro Text", 11),
        )

        # Headline block
        self.canvas.create_text(
            card_x1 + 56,
            card_y1 + 190,
            text="Ready for your next session?",
            anchor="w",
            fill=self.colors["ink"],
            font=("SF Pro Display", 42, "bold"),
        )
        self.canvas.create_text(
            card_x1 + 56,
            card_y1 + 238,
            text="A focused start. No noise.",
            anchor="w",
            fill=self.colors["muted"],
            font=("SF Pro Text", 14),
        )

        self.draw_stats_row(card_x1 + 56, card_y1 + 286, card_w - 112)

        self.canvas.create_text(
            card_x1 + 56,
            card_y1 + 500,
            text=f"Active lesson: {self.active_lesson}",
            anchor="w",
            fill=self.colors["muted"],
            font=("SF Pro Text", 12),
        )

        button_width = 332
        button_height = 56
        button_x = card_x1 + 56
        button_y = card_y1 + 536

        self.start_btn = tk.Button(
            self,
            text="Begin Training Session",
            command=self.begin_session,
            bg=self.colors["button"],
            fg=self.colors["button_text"],
            activebackground="#222222",
            activeforeground=self.colors["button_text"],
            font=("SF Pro Text", 13, "bold"),
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            relief="flat",
            highlightthickness=0,
        )
        self.canvas.create_window(
            button_x,
            button_y,
            anchor="nw",
            width=button_width,
            height=button_height,
            window=self.start_btn,
        )

        self.canvas.create_text(
            button_x,
            button_y + button_height + 24,
            text="Launches the existing C2A trainer in a new console window.",
            anchor="w",
            fill=self.colors["muted"],
            font=("SF Pro Text", 10),
        )

    def draw_stats_row(self, x_start, y_start, available_width):
        """Draw KPI cards in minimal monochrome style."""
        items = [
            ("Level", str(self.stats["level"])),
            ("Sessions", str(self.stats["total_sessions"])),
            ("Streak", f"{self.stats['streak']} day"),
            ("Last Score", f"{self.stats['last_score']}/100"),
        ]

        gap = 12
        card_w = (available_width - (gap * (len(items) - 1))) / len(items)
        card_h = 126

        for index, (label, value) in enumerate(items):
            x1 = x_start + index * (card_w + gap)
            y1 = y_start
            x2 = x1 + card_w
            y2 = y1 + card_h

            self.rounded_rect(x1, y1, x2, y2, 26, self.colors["surface_alt"], self.colors["line"], 1)
            self.canvas.create_text(
                x1 + 22,
                y1 + 38,
                text=label,
                anchor="w",
                fill=self.colors["muted"],
                font=("SF Pro Text", 11),
            )
            self.canvas.create_text(
                x1 + 22,
                y1 + 82,
                text=value,
                anchor="w",
                fill=self.colors["ink"],
                font=("SF Pro Display", 24, "bold"),
            )

    def begin_session(self):
        """Launch the existing trainer from desktop UI."""
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "C2A Session", "cmd", "/k", "py -3 c2a_elegant_main.py"],
                cwd=str(self.project_root),
            )
            messagebox.showinfo("Session Started", "C2A trainer launched in a new window.")
        except Exception as exc:
            messagebox.showerror("Launch Failed", f"Could not launch C2A session:\n{exc}")

    def rounded_rect(self, x1, y1, x2, y2, radius, fill, outline, width=1):
        """Draw a rounded rectangle (squircle-like) on the canvas."""
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        self.canvas.create_polygon(points, smooth=True, fill=fill, outline=outline, width=width)


def main():
    app = C2ALandingApp()
    app.mainloop()


if __name__ == "__main__":
    main()