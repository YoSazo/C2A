#!/usr/bin/env python3
"""
Elegant UI - Beautiful Terminal Interface for C2A

Philosophy: The interface should feel like a conversation with a wise mentor,
not a command-line tool. Every element should inspire and guide.
"""

import os
import sys
import time
import shutil
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
import textwrap

from constraint_archetypes import ARCHETYPES, ConstraintArchetype


class Colors:
    """ANSI color codes for beautiful terminal output"""
    # Base colors
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # 256 color support
    ORANGE = "\033[38;5;208m"
    GOLD = "\033[38;5;220m"
    PURPLE = "\033[38;5;129m"
    PINK = "\033[38;5;213m"
    TEAL = "\033[38;5;51m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_DARK = "\033[48;5;234m"
    BG_BLUE = "\033[44m"
    
    @staticmethod
    def gradient_text(text: str, start_color: int = 51, end_color: int = 129, steps: Optional[int] = None) -> str:
        """Create gradient text effect"""
        if steps is None:
            steps = len(text)
        
        result = ""
        for i, char in enumerate(text):
            if char.isspace():
                result += char
            else:
                # Interpolate between colors
                ratio = i / max(steps - 1, 1)
                color = int(start_color + (end_color - start_color) * ratio)
                result += f"\033[38;5;{color}m{char}"
        
        return result + Colors.RESET


class Symbols:
    """Unicode symbols for visual richness"""
    # Constraint symbols
    CONSTRAINT = "⧗"
    TRANSMUTE = "⚗"
    INSIGHT = "💡"
    BREAKTHROUGH = "🌟"
    GROWTH = "📈"
    PATTERN = "🔮"
    
    # Progress symbols
    INCOMPLETE = "○"
    INPROGRESS = "◐"
    COMPLETE = "●"
    STAR = "★"
    STAR_EMPTY = "☆"
    
    # UI elements
    ARROW_RIGHT = "→"
    ARROW_UP = "↑"
    ARROW_DOWN = "↓"
    BULLET = "•"
    DIAMOND = "◆"
    
    # Status symbols
    SUCCESS = "✓"
    WARNING = "⚠"
    ERROR = "✗"
    INFO = "ℹ"
    QUESTION = "?"
    
    # Special
    INFINITY = "∞"
    DELTA = "Δ"
    LAMBDA = "λ"
    SIGMA = "Σ"


class ElegantUI:
    """Beautiful terminal interface with animated elements"""
    
    # Pattern colors for instant visual recognition
    PATTERN_COLORS = {
        "The Removal Test": Colors.BRIGHT_CYAN,
        "Transmute, Don't Substitute": Colors.BRIGHT_GREEN,
        "Root vs Symptom": Colors.BRIGHT_YELLOW,
        "Embrace, Don't Escape": Colors.BRIGHT_MAGENTA,
        "Beyond First Instinct": Colors.ORANGE,
        "Proactive Transmutation": Colors.BRIGHT_BLUE,
        "Multiple Angles": Colors.BRIGHT_GREEN,
        "What The Constraint Creates": Colors.BRIGHT_CYAN,
        "Pressure As Fuel": Colors.BRIGHT_YELLOW,
        "Scarcity's Hidden Gift": Colors.BRIGHT_GREEN,
        "Beyond Coping": Colors.BRIGHT_MAGENTA,
        "Finding The Advantage": Colors.BRIGHT_CYAN,
        "Beyond Identity": Colors.BRIGHT_MAGENTA,
        "Constraint-Driven Speed": Colors.BRIGHT_YELLOW,
        "What It Forces": Colors.BRIGHT_CYAN,
        "The Core Transmutation": Colors.WHITE,
        # Fallback for unrecognized patterns handled in method
    }
    
    def __init__(self):
        self.width = self.get_terminal_width()
        self.height = self.get_terminal_height()
    
    @staticmethod
    def get_terminal_width() -> int:
        """Get terminal width"""
        return shutil.get_terminal_size().columns
    
    @staticmethod
    def get_terminal_height() -> int:
        """Get terminal height"""
        return shutil.get_terminal_size().lines
    
    @staticmethod
    def clear_screen():
        """Clear terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_splash(self):
        """Show beautiful C2A splash screen"""
        self.clear_screen()
        
        # ASCII art with gradient
        art = [
            "  ██████╗██████╗  █████╗ ",
            " ██╔════╝╚════██╗██╔══██╗",
            " ██║      █████╔╝███████║",
            " ██║     ██╔═══╝ ██╔══██║",
            " ╚██████╗███████╗██║  ██║",
            "  ╚═════╝╚══════╝╚═╝  ╚═╝"
        ]
        
        tagline = "Constraint to Advantage"
        subtitle = "Transform limitation into liberation"
        
        # Center and display with gradient
        for line in art:
            centered = line.center(self.width)
            print(Colors.gradient_text(centered, 51, 129))
        
        print()
        print(Colors.BOLD + Colors.CYAN + tagline.center(self.width) + Colors.RESET)
        print(Colors.DIM + Colors.WHITE + subtitle.center(self.width) + Colors.RESET)
        print()
        
        # Animated loading bar
        self._show_loading_animation("Initializing consciousness", duration=1.5)
    
    def _show_loading_animation(self, message: str, duration: float = 1.0):
        """Show elegant loading animation"""
        steps = 30
        delay = duration / steps
        
        bar_width = min(40, self.width - 20)
        
        for i in range(steps + 1):
            filled = int((i / steps) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            
            # Center the loading bar
            padding = (self.width - bar_width - len(message) - 4) // 2
            line = " " * padding + message + " " + bar
            
            sys.stdout.write("\r" + line)
            sys.stdout.flush()
            time.sleep(delay)
        
        print()  # New line after loading
    
    def show_archetype_moment(self, archetype: ConstraintArchetype):
        """Beautiful display when entering an archetype"""
        self.clear_screen()
        
        border = "═" * (self.width - 4)
        print(f"\n{Colors.DIM}╔{border}╗{Colors.RESET}")
        
        # Archetype name with color
        title = f"{archetype.symbol}  {archetype.name.upper()}  {archetype.symbol}"
        colored_title = archetype.color_code + Colors.BOLD + title + Colors.RESET
        padding = (self.width - len(title) - 4) // 2
        print(f"{Colors.DIM}║{Colors.RESET}{' ' * padding}{colored_title}{' ' * padding}{Colors.DIM}║{Colors.RESET}")
        
        print(f"{Colors.DIM}╚{border}╝{Colors.RESET}\n")
        
        # Essence (wrapped)
        self.print_wrapped(archetype.essence, 
                          prefix=Colors.ITALIC + Colors.CYAN,
                          suffix=Colors.RESET,
                          indent=4)
        
        print()
        
        # Universal pattern
        print(f"{Colors.DIM}Universal Pattern:{Colors.RESET}")
        self.print_wrapped(archetype.universal_pattern.strip(),
                          indent=2,
                          prefix=Colors.WHITE)
        
        print()
        input(f"{Colors.DIM}Press Enter to begin...{Colors.RESET}")
    
    def show_scenario(self, scenario: Dict):
        """Display scenario with beautiful formatting"""
        self.clear_screen()
        
        # Title bar
        title = scenario.get('title', 'Unknown Scenario')
        self._print_section_header(title)
        
        # Emotional hook (if present)
        hook = scenario.get('emotional_hook')
        if hook:
            print(f"\n{Colors.GOLD}{Symbols.INSIGHT} {hook}{Colors.RESET}\n")
        
        # Situation (the main content)
        situation = scenario.get('situation', 'No situation provided')
        self._print_story_box(situation)
        
        # Hint
        hint = scenario.get('hint', '')
        if hint:
            print(f"\n{Colors.DIM}{Symbols.QUESTION} Hint: {Colors.ITALIC}{hint}{Colors.RESET}\n")
    
    def _print_section_header(self, text: str, symbol: str = "◆"):
        """Print a beautiful section header"""
        line_width = min(self.width - 4, 70)
        
        # Calculate padding
        total_len = len(text) + len(symbol) * 2 + 4
        if total_len < line_width:
            padding = (line_width - total_len) // 2
            line = "─" * padding + f" {symbol} {text} {symbol} " + "─" * padding
        else:
            line = f"{symbol} {text} {symbol}"
        
        print(f"\n{Colors.BRIGHT_CYAN}{line}{Colors.RESET}\n")
    
    def _print_story_box(self, text: str):
        """Print text in a beautiful story box"""
        box_width = min(self.width - 8, 70)
        
        # Wrap text
        paragraphs = text.split('\n')
        wrapped_lines = []
        for para in paragraphs:
            if para.strip():
                wrapped = textwrap.wrap(para.strip(), width=box_width - 4)
                wrapped_lines.extend(wrapped)
                wrapped_lines.append('')  # Paragraph spacing
        
        # Remove trailing empty line
        if wrapped_lines and wrapped_lines[-1] == '':
            wrapped_lines = wrapped_lines[:-1]
        
        # Print box
        top_border = "┌" + "─" * (box_width - 2) + "┐"
        bottom_border = "└" + "─" * (box_width - 2) + "┘"
        
        print(f"{Colors.DIM}{top_border}{Colors.RESET}")
        
        for line in wrapped_lines:
            padding = box_width - len(line) - 4
            print(f"{Colors.DIM}│{Colors.RESET} {line}{' ' * padding} {Colors.DIM}│{Colors.RESET}")
        
        print(f"{Colors.DIM}{bottom_border}{Colors.RESET}")
    
    def get_transmutation_input(
        self,
        prompt: str,
        number: int,
        total: int,
        time_limit: int = 90,
        word_limit: int = 30
    ) -> Tuple[str, float]:
        """Get transmutation input with beautiful formatting and timer
        
        Note: Timer updates are disabled during input to prevent cursor conflicts
        with multi-line text. Time is shown before and after input.
        
        The HAIKU CONSTRAINT: Forces pure signal, no rambling.
        - word_limit: Maximum words allowed (default 30)
        - Exceeding triggers rejection and re-prompt
        """
        
        # Header
        print(f"\n{Colors.BRIGHT_YELLOW}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_YELLOW}{Symbols.TRANSMUTE}  Transmutation {number}/{total}{Colors.RESET}")
        print(f"{Colors.BRIGHT_YELLOW}{'═' * 60}{Colors.RESET}\n")
        
        print(f"{Colors.CYAN}{prompt}{Colors.RESET}")
        print(f"{Colors.DIM}⏱️ {time_limit}s limit  |  📝 {word_limit} words max  |  Pure signal only.{Colors.RESET}\n")
        
        # Start timer
        start_time = time.time()
        
        # Input loop with word limit enforcement
        while True:
            # Get input (no live timer - it conflicts with multi-line input)
            # Use \001 and \002 to wrap ANSI codes so readline ignores them for line length calculation
            try:
                input_prompt = f"\001{Colors.BRIGHT_WHITE}\002❯ \001{Colors.RESET}\002"
                response = input(input_prompt)
            except (EOFError, KeyboardInterrupt):
                response = ""
                break
            
            # Check word count
            word_count = len(response.split())
            
            if word_count > word_limit:
                print(f"\n{Colors.RED}✖ TOO MUCH THINKING ({word_count}/{word_limit} words){Colors.RESET}")
                print(f"{Colors.YELLOW}Cut the preamble. State the transmutation directly.{Colors.RESET}")
                print(f"{Colors.DIM}Tip: No 'Ok so...', 'Well since...', 'I think...' - just the insight.{Colors.RESET}\n")
                continue  # Ask again
            else:
                break  # Accept input
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Show duration feedback
        print()
        if duration <= time_limit:
            mins, secs = divmod(int(duration), 60)
            print(f"{Colors.GREEN}{Symbols.SUCCESS} Completed in {mins:02d}:{secs:02d} ({duration:.1f}s) | {word_count} words{Colors.RESET}")
        else:
            overtime = duration - time_limit
            mins, secs = divmod(int(overtime), 60)
            print(f"{Colors.RED}{Symbols.WARNING} Overtime: +{mins:02d}:{secs:02d} (+{overtime:.1f}s) | {word_count} words{Colors.RESET}")
        
        return response, duration
    
    def show_score_reveal(self, score_data: Dict):
        """Animated score reveal"""
        self.clear_screen()
        
        print(f"\n{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{' ' * 20}TRANSMUTATION ANALYSIS{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}\n")
        
        # Overall score with animation
        overall = score_data.get('overall_score', 0)
        self._animate_score("Overall Score", overall, 100)
        
        print()
        
        # Component scores
        components = [
            ('Reframing', score_data.get('reframing_score', 0), 30),
            ('Novelty', score_data.get('novelty_score', 0), 25),
            ('Practicality', score_data.get('practicality_score', 0), 25),
            ('Sophistication', score_data.get('sophistication_score', 0), 20)
        ]
        
        for name, score, max_score in components:
            self._show_component_score(name, score, max_score)
            time.sleep(0.2)
        
        print()
        
        # Pattern identified
        pattern = score_data.get('pattern_identified', 'Unknown pattern')
        print(f"{Colors.PURPLE}{Symbols.PATTERN} Pattern: {Colors.ITALIC}{pattern}{Colors.RESET}\n")
        
        # Breakthrough moment
        if score_data.get('breakthrough_moment', False):
            self._show_breakthrough_animation()
    
    def _animate_score(self, label: str, score: int, max_score: int):
        """Animate score counting up"""
        steps = 20
        delay = 0.03
        
        for i in range(steps + 1):
            current = int((i / steps) * score)
            percentage = (current / max_score) * 100
            
            # Color based on percentage
            if percentage >= 85:
                color = Colors.BRIGHT_GREEN
            elif percentage >= 70:
                color = Colors.BRIGHT_CYAN
            elif percentage >= 60:
                color = Colors.BRIGHT_YELLOW
            else:
                color = Colors.BRIGHT_RED
            
            sys.stdout.write(f"\r{color}{Colors.BOLD}{label}: {current}/{max_score}{Colors.RESET}")
            sys.stdout.flush()
            time.sleep(delay)
        
        print()
    
    def _show_component_score(self, name: str, score: int, max_score: int):
        """Show component score with bar"""
        bar_width = 20
        filled = int((score / max_score) * bar_width)
        
        # Color gradient
        percentage = (score / max_score) * 100
        if percentage >= 80:
            color = Colors.GREEN
        elif percentage >= 60:
            color = Colors.CYAN
        elif percentage >= 40:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"  {name:.<20} {color}{score:>2}/{max_score:<2}  {bar}{Colors.RESET}")
    
    def _show_breakthrough_animation(self):
        """Show breakthrough animation"""
        print(f"\n{Colors.BRIGHT_YELLOW}{'═' * 60}{Colors.RESET}")
        
        message = "🌟 BREAKTHROUGH MOMENT 🌟"
        
        # Pulse animation
        for _ in range(3):
            print(f"\r{Colors.BOLD}{Colors.BRIGHT_YELLOW}{message.center(60)}{Colors.RESET}", end='')
            sys.stdout.flush()
            time.sleep(0.3)
            print(f"\r{Colors.DIM}{message.center(60)}{Colors.RESET}", end='')
            sys.stdout.flush()
            time.sleep(0.3)
        
        print(f"\r{Colors.BOLD}{Colors.BRIGHT_YELLOW}{message.center(60)}{Colors.RESET}")
        print(f"{Colors.BRIGHT_YELLOW}{'═' * 60}{Colors.RESET}\n")
    
    def show_feedback_panel(self, feedback: Dict):
        """Show beautiful feedback panel"""
        print(f"\n{Colors.BRIGHT_BLUE}┌{'─' * 58}┐{Colors.RESET}")
        print(f"{Colors.BRIGHT_BLUE}│{Colors.RESET}{Colors.BOLD} GROWTH INSIGHTS{' ' * 43}{Colors.BRIGHT_BLUE}│{Colors.RESET}")
        print(f"{Colors.BRIGHT_BLUE}├{'─' * 58}┤{Colors.RESET}")
        
        # What worked
        what_worked = feedback.get('what_worked', '')
        if what_worked:
            print(f"{Colors.BRIGHT_BLUE}│{Colors.RESET}{Colors.GREEN} ✓ What Worked:{' ' * 44}{Colors.BRIGHT_BLUE}│{Colors.RESET}")
            self._print_wrapped_in_box(what_worked, Colors.WHITE)
            print(f"{Colors.BRIGHT_BLUE}│{' ' * 58}│{Colors.RESET}")
        
        # Growth edge
        growth_edge = feedback.get('growth_edge', '')
        if growth_edge:
            print(f"{Colors.BRIGHT_BLUE}│{Colors.RESET}{Colors.YELLOW} ↑ Growth Edge:{' ' * 43}{Colors.BRIGHT_BLUE}│{Colors.RESET}")
            self._print_wrapped_in_box(growth_edge, Colors.YELLOW)
        
        print(f"{Colors.BRIGHT_BLUE}└{'─' * 58}┘{Colors.RESET}\n")
    
    def _print_wrapped_in_box(self, text: str, color: str):
        """Print wrapped text inside a box"""
        wrapped = textwrap.wrap(text, width=54)
        for line in wrapped:
            padding = 54 - len(line)
            print(f"{Colors.BRIGHT_BLUE}│{Colors.RESET}  {color}{line}{Colors.RESET}{' ' * padding}  {Colors.BRIGHT_BLUE}│{Colors.RESET}")
    
    def show_level_progress(self, current_level: int, next_level: int, progress_bar: float = 0.0):
        """Show level progress with beautiful visualization"""
        print(f"\n{Colors.BRIGHT_MAGENTA}╔{'═' * 58}╗{Colors.RESET}")
        print(f"{Colors.BRIGHT_MAGENTA}║{Colors.RESET}  {Colors.BOLD}MASTERY LEVEL{Colors.RESET}{' ' * 44}{Colors.BRIGHT_MAGENTA}║{Colors.RESET}")
        print(f"{Colors.BRIGHT_MAGENTA}╠{'═' * 58}╣{Colors.RESET}")
        
        # Current level
        level_display = f"Level {current_level}/100"
        stars = self._get_level_stars(current_level)
        
        print(f"{Colors.BRIGHT_MAGENTA}║{Colors.RESET}  {Colors.GOLD}{Colors.BOLD}{level_display}{Colors.RESET}  {Colors.GOLD}{stars}{Colors.RESET}{' ' * (44 - len(level_display) - len(stars))}{Colors.BRIGHT_MAGENTA}║{Colors.RESET}")
        
        # Progress bar
        bar_width = 50
        filled = int(progress_bar * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        print(f"{Colors.BRIGHT_MAGENTA}║{Colors.RESET}  {Colors.CYAN}{bar}{Colors.RESET}  {Colors.BRIGHT_MAGENTA}║{Colors.RESET}")
        
        # Next level indicator
        if next_level > current_level:
            print(f"{Colors.BRIGHT_MAGENTA}║{Colors.RESET}  {Colors.GREEN}{Symbols.ARROW_UP} Advancing to Level {next_level}{Colors.RESET}{' ' * (40 - len(str(next_level)))}{Colors.BRIGHT_MAGENTA}║{Colors.RESET}")
        elif next_level < current_level:
            print(f"{Colors.BRIGHT_MAGENTA}║{Colors.RESET}  {Colors.YELLOW}Consolidating at Level {current_level}{Colors.RESET}{' ' * (35 - len(str(current_level)))}{Colors.BRIGHT_MAGENTA}║{Colors.RESET}")
        else:
            print(f"{Colors.BRIGHT_MAGENTA}║{Colors.RESET}  {Colors.CYAN}Maintaining Level {current_level}{Colors.RESET}{' ' * (40 - len(str(current_level)))}{Colors.BRIGHT_MAGENTA}║{Colors.RESET}")
        
        print(f"{Colors.BRIGHT_MAGENTA}╚{'═' * 58}╝{Colors.RESET}\n")
    
    def _get_level_stars(self, level: int) -> str:
        """Get star representation of level"""
        if level >= 90:
            return "★★★★★"
        elif level >= 70:
            return "★★★★☆"
        elif level >= 50:
            return "★★★☆☆"
        elif level >= 30:
            return "★★☆☆☆"
        elif level >= 10:
            return "★☆☆☆☆"
        else:
            return "☆☆☆☆☆"
    
    def print_wrapped(self, text: str, width: Optional[int] = None, 
                     indent: int = 0, prefix: str = "", suffix: str = ""):
        """Print wrapped text with formatting"""
        if width is None:
            width = min(self.width - indent - 4, 70)
        
        paragraphs = text.split('\n')
        for para in paragraphs:
            if para.strip():
                wrapped = textwrap.wrap(para.strip(), width=width)
                for line in wrapped:
                    print(' ' * indent + prefix + line + suffix)
            else:
                print()
    
    def show_menu(self, title: str, options: List[Tuple[str, str, bool]], 
                  status_line: Optional[str] = None):
        """Show beautiful menu with options
        
        Args:
            title: Menu title
            options: List of (key, description, enabled) tuples
            status_line: Optional status line to show above menu
        """
        self.clear_screen()
        
        # Title
        print(f"\n{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}{title.center(60)}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}\n")
        
        # Status line
        if status_line:
            print(f"{Colors.GOLD}{status_line}{Colors.RESET}\n")
        
        # Options
        for key, description, enabled in options:
            if enabled:
                print(f"  {Colors.BRIGHT_WHITE}[{key}]{Colors.RESET} {Colors.CYAN}{description}{Colors.RESET}")
            else:
                print(f"  {Colors.DIM}[{key}] {description} 🔒{Colors.RESET}")
        
        print()
    
    def show_pattern_tag(self, pattern_name: str, score: int, velocity_score: int = None):
        """
        Show pattern as colored visual tag - instant feedback
        
        Args:
            pattern_name: The pattern identified by the judge
            score: Overall score 0-100
            velocity_score: Optional velocity score 0-100
        """
        # Get color for this pattern (fallback to WHITE for unrecognized)
        color = self.PATTERN_COLORS.get(pattern_name, Colors.WHITE)
        
        # Symbol based on score
        if score >= 85:
            symbol = "★"  # Excellent
        elif score >= 70:
            symbol = "✓"  # Good
        elif score >= 60:
            symbol = "○"  # Okay
        else:
            symbol = "✗"  # Needs work
        
        # Build the tag
        tag_width = max(40, len(pattern_name) + 12)
        top_line = "╔" + "═" * tag_width + "╗"
        bottom_line = "╚" + "═" * tag_width + "╝"
        
        # Main line: [PATTERN NAME] SYMBOL SCORE
        pattern_display = f"[{pattern_name.upper()}]"
        score_display = f"{symbol} {score}/100"
        
        # Add velocity if provided
        if velocity_score is not None:
            score_display += f" ⚡{velocity_score}"
        
        middle_content = f" {pattern_display} {score_display}"
        padding = tag_width - len(pattern_display) - len(score_display) - 2
        middle_line = f"║{middle_content}{' ' * max(0, padding)}║"
        
        # Print the tag
        print(f"\n{color}{top_line}{Colors.RESET}")
        print(f"{color}{middle_line}{Colors.RESET}")
        print(f"{color}{bottom_line}{Colors.RESET}\n")
    
    def show_correction_prompt(self, what_missed: str, growth_edge: str, attempt: int, max_attempts: int):
        """
        Show correction opportunity after failed attempt
        
        Args:
            what_missed: What the user missed (from judge)
            growth_edge: Specific thing to try (from judge)
            attempt: Current attempt number
            max_attempts: Total attempts allowed
        """
        print(f"\n{Colors.YELLOW}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.YELLOW}⚡ CORRECTION OPPORTUNITY - Attempt {attempt}/{max_attempts}{Colors.RESET}")
        print(f"{Colors.YELLOW}{'═' * 60}{Colors.RESET}\n")
        
        print(f"{Colors.RED}✗ What you missed:{Colors.RESET}")
        self.print_wrapped(what_missed, indent=2, prefix=Colors.WHITE, suffix=Colors.RESET)
        print()
        
        print(f"{Colors.CYAN}→ Try this:{Colors.RESET}")
        self.print_wrapped(growth_edge, indent=2, prefix=Colors.BRIGHT_WHITE, suffix=Colors.RESET)
        print()
        
        print(f"{Colors.YELLOW}Apply this correction now (60 seconds):{Colors.RESET}")
    
    def show_improvement_delta(self, score_before: int, score_after: int):
        """Show improvement between attempts"""
        delta = score_after - score_before
        
        if delta > 0:
            print(f"\n{Colors.GREEN}↑ +{delta} points improvement! ✓{Colors.RESET}")
        elif delta < 0:
            print(f"\n{Colors.YELLOW}↓ {delta} points (sometimes corrections take practice){Colors.RESET}")
        else:
            print(f"\n{Colors.YELLOW}→ Same score (keep refining){Colors.RESET}")


if __name__ == "__main__":
    # Test UI
    ui = ElegantUI()
    
    # Test new pattern tag methods first
    print("\n=== Testing New Pattern Tag Methods ===\n")
    
    ui.show_pattern_tag("The Removal Test", 78, 85)
    ui.show_pattern_tag("Beyond First Instinct", 92)
    ui.show_pattern_tag("Unknown Pattern", 55)  # Test fallback color
    
    ui.show_correction_prompt(
        "You treated this as coping - finding ways to work around the constraint rather than leveraging it.",
        "Ask: would removing the constraint also remove the advantage you created?",
        1,
        2
    )
    
    ui.show_improvement_delta(65, 78)
    ui.show_improvement_delta(78, 78)
    ui.show_improvement_delta(78, 70)
    
    input("\nPress Enter to continue with other tests...")
    
    # Test splash
    ui.show_splash()
    time.sleep(1)
    
    # Test archetype display
    from constraint_archetypes import ARCHETYPES
    ui.show_archetype_moment(ARCHETYPES['velocity'])
    
    # Test scenario
    test_scenario = {
        'title': 'The 30-Minute Developer',
        'emotional_hook': 'Your growth depends on making these minutes count',
        'situation': '''You've wanted to become a skilled programmer for years. 
        
You have a full-time job, family commitments, and countless other demands. After careful analysis, you've found exactly 30 minutes per day that could be dedicated to learning.

Every tutorial you find assumes hours of focused practice. Every course demands weekend projects. The constraint feels crushing: how can 30 minutes possibly be enough?

But here you are, with these 30 minutes, and the choice of whether to use them or dismiss them as insufficient.''',
        'hint': 'What if the limitation is actually the design constraint?'
    }
    
    ui.show_scenario(test_scenario)
    
    # Test score reveal
    test_score = {
        'overall_score': 87,
        'reframing_score': 28,
        'novelty_score': 22,
        'practicality_score': 21,
        'sophistication_score': 16,
        'pattern_identified': 'Constraint as Design Parameter',
        'breakthrough_moment': True,
        'what_worked': 'You recognized that the time limit itself becomes a forcing function for focus and deliberate practice.',
        'growth_edge': 'Explore how multiple constraints can interact to create even more sophisticated transmutations.'
    }
    
    input("\nPress Enter to see score reveal...")
    ui.show_score_reveal(test_score)
    
    time.sleep(2)
    
    # Test feedback panel
    ui.show_feedback_panel(test_score)
    
    # Test level progress
    ui.show_level_progress(current_level=15, next_level=17, progress_bar=0.75)
    
    input("\nPress Enter to continue...")
