#!/usr/bin/env python3
"""
C2A Elegant - UI Demo

Showcases the beautiful interface without requiring Ollama/LLM setup.
Run this to see what the training experience looks like.
"""

import time
from elegant_ui import ElegantUI, Colors, Symbols
from constraint_archetypes import ARCHETYPES

def demo():
    ui = ElegantUI()
    
    # 1. Splash Screen
    ui.show_splash()
    time.sleep(2)
    
    # 2. Archetype Introduction
    velocity = ARCHETYPES['velocity']
    ui.show_archetype_moment(velocity)
    
    # 3. Demo Scenario
    print(f"\n{Colors.CYAN}Generating a demo scenario...{Colors.RESET}\n")
    time.sleep(1)
    
    demo_scenario = {
        'title': 'The 30-Minute Developer',
        'emotional_hook': 'Your growth depends on making these minutes count',
        'situation': '''You've wanted to become a skilled programmer for years. 

You have a full-time job, family commitments, and countless other demands. After careful analysis, you've found exactly 30 minutes per day that could be dedicated to learning.

Every tutorial you find assumes hours of focused practice. Every course demands weekend projects. Every bootcamp requires full-time commitment.

The constraint feels crushing: how can 30 minutes possibly be enough?

But here you are. With these 30 minutes. And a choice.''',
        'hint': 'What if the limitation is actually the design constraint?'
    }
    
    ui.show_scenario(demo_scenario)
    
    # 4. Demo Transmutation Input (simulated)
    print(f"\n{Colors.BRIGHT_YELLOW}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.BRIGHT_YELLOW}{Symbols.TRANSMUTE}  Transmutation Demo{Colors.RESET}")
    print(f"{Colors.BRIGHT_YELLOW}{'═' * 60}{Colors.RESET}\n")
    
    print(f"{Colors.CYAN}In actual training, you'd type your transmutation here with a 90-second timer.{Colors.RESET}")
    print(f"{Colors.DIM}For demo purposes, we'll show example scores...{Colors.RESET}\n")
    
    input(f"{Colors.DIM}Press Enter to see score reveal...{Colors.RESET}")
    
    # 5. Score Reveal Demo
    demo_score = {
        'overall_score': 87,
        'reframing_score': 28,
        'novelty_score': 22,
        'practicality_score': 21,
        'sophistication_score': 16,
        'pattern_identified': 'Constraint as Design Parameter',
        'breakthrough_moment': True,
        'what_worked': 'You recognized that the time limit itself becomes a forcing function for focus and deliberate practice. The constraint is not something to work around—it actively shapes optimal learning architecture.',
        'growth_edge': 'Explore how multiple constraints interact. What happens when you combine time scarcity with information asymmetry? Can constraint combinations create emergent advantages?'
    }
    
    ui.show_score_reveal(demo_score)
    
    time.sleep(2)
    
    # 6. Feedback Panel
    ui.show_feedback_panel(demo_score)
    
    # 7. Level Progress
    ui.show_level_progress(current_level=15, next_level=17, progress_bar=0.75)
    
    input(f"\n{Colors.DIM}Press Enter to see archetype gallery...{Colors.RESET}")
    
    # 8. Archetype Gallery
    ui.clear_screen()
    
    print(f"\n{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}THE FIVE ARCHETYPAL CONSTRAINTS{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}\n")
    
    for archetype in ARCHETYPES.values():
        print(f"{archetype.color_code}{archetype.symbol} {archetype.name.upper()}{Colors.RESET}")
        print(f"{Colors.DIM}{archetype.essence}{Colors.RESET}")
        print()
        time.sleep(0.5)
    
    input(f"{Colors.DIM}Press Enter to see example transmutations...{Colors.RESET}")
    
    # 9. Example Transmutations
    ui.clear_screen()
    
    print(f"\n{Colors.BRIGHT_MAGENTA}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.BRIGHT_MAGENTA}EXAMPLE TRANSMUTATIONS{Colors.RESET}")
    print(f"{Colors.BRIGHT_MAGENTA}Same scenario, different quality levels{Colors.RESET}")
    print(f"{Colors.BRIGHT_MAGENTA}{'═' * 60}{Colors.RESET}\n")
    
    examples = [
        {
            'score': 45,
            'response': "I'll just accept that progress will be slow and be patient.",
            'why': "This is coping, not transmutation. No advantage created.",
            'color': Colors.RED
        },
        {
            'score': 68,
            'response': "The time limit forces prioritization. I'll focus only on essentials.",
            'why': "Good optimization, but not true transmutation.",
            'color': Colors.YELLOW
        },
        {
            'score': 87,
            'response': "Turn the 30-minute constraint into a design parameter. Create a 'learning kata'—a single repeatable exercise that builds muscle memory. The time limit becomes a forcing function for deliberate practice.",
            'why': "Reframes constraint as design parameter. Novel, practical, meta-aware.",
            'color': Colors.GREEN
        },
        {
            'score': 95,
            'response': "The 30-minute window is actually ideal for spaced repetition. If I had unlimited time, I'd binge and forget. Build a 'constraint-based curriculum': each session is one atomic concept. The daily gap becomes the spacing. The limitation creates the optimal learning architecture.",
            'why': "Multiple reframing levels. Systemic thinking. Novel synthesis. Constraint becomes the FEATURE.",
            'color': Colors.BRIGHT_GREEN
        }
    ]
    
    for i, ex in enumerate(examples, 1):
        print(f"{ex['color']}╔{'═' * 58}╗{Colors.RESET}")
        print(f"{ex['color']}║{Colors.RESET} {Colors.BOLD}Example {i}: Score {ex['score']}/100{Colors.RESET}{' ' * (45 - len(str(ex['score'])))} {ex['color']}║{Colors.RESET}")
        print(f"{ex['color']}╠{'═' * 58}╣{Colors.RESET}")
        
        # Wrap response
        import textwrap
        wrapped = textwrap.wrap(ex['response'], width=54)
        for line in wrapped:
            padding = 54 - len(line)
            print(f"{ex['color']}║{Colors.RESET}  {line}{' ' * padding}  {ex['color']}║{Colors.RESET}")
        
        print(f"{ex['color']}║{' ' * 58}║{Colors.RESET}")
        print(f"{ex['color']}║{Colors.RESET}  {Colors.DIM}Why: {ex['why'][:50]}{Colors.RESET}")
        
        # Continue why if needed
        if len(ex['why']) > 50:
            remaining = ex['why'][50:]
            wrapped_why = textwrap.wrap(remaining, width=50)
            for line in wrapped_why:
                padding = 50 - len(line)
                print(f"{ex['color']}║{Colors.RESET}       {Colors.DIM}{line}{' ' * padding}{Colors.RESET}")
        
        print(f"{ex['color']}╚{'═' * 58}╝{Colors.RESET}\n")
        time.sleep(0.5)
    
    input(f"{Colors.DIM}Press Enter to see the vision...{Colors.RESET}")
    
    # 10. Final Vision
    ui.clear_screen()
    
    print(f"\n\n")
    
    vision_lines = [
        "This is C2A Elegant.",
        "",
        "Not just training software.",
        "A philosophy embodied in code.",
        "",
        "Every constraint you face is an invitation.",
        "Every limitation is a design parameter.",
        "Every obstacle is a teacher.",
        "",
        "The constraint is not the enemy.",
        "The constraint is the way.",
        "",
        "Transform. Transmute. Transcend.",
    ]
    
    for i, line in enumerate(vision_lines):
        if line:
            centered = line.center(ui.width)
            if i < 3:
                print(Colors.gradient_text(centered, 51, 129))
            elif i > len(vision_lines) - 4:
                print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{centered}{Colors.RESET}")
            else:
                print(f"{Colors.CYAN}{centered}{Colors.RESET}")
        else:
            print()
        time.sleep(0.4)
    
    print(f"\n\n")
    
    print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}Ready to begin your journey?{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}\n")
    
    print(f"  {Colors.GREEN}1.{Colors.RESET} Install dependencies: {Colors.DIM}pip install -r requirements_elegant.txt{Colors.RESET}")
    print(f"  {Colors.GREEN}2.{Colors.RESET} Pull the model: {Colors.DIM}ollama pull qwen2.5:32b{Colors.RESET}")
    print(f"  {Colors.GREEN}3.{Colors.RESET} Start training: {Colors.DIM}python c2a_elegant_main.py{Colors.RESET}")
    
    print(f"\n{Colors.GOLD}{Symbols.INSIGHT} See README_ELEGANT.md for full documentation{Colors.RESET}")
    print(f"{Colors.GOLD}{Symbols.INSIGHT} See QUICKSTART.md for quick start guide{Colors.RESET}\n")


if __name__ == "__main__":
    print(f"\n{Colors.BRIGHT_CYAN}C2A Elegant - UI Demo{Colors.RESET}")
    print(f"{Colors.DIM}This showcases the interface without requiring LLM setup{Colors.RESET}\n")
    
    input(f"Press Enter to begin demo...")
    
    demo()
