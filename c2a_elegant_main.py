#!/usr/bin/env python3
"""
C2A Elegant - The Beautiful Constraint-to-Advantage Training System

This is the main orchestrator that brings together:
- Archetypal constraints (the foundation)
- LLM scenario generation (infinite variety)
- Sophisticated LLM judging (quality evaluation)
- RLM processing (infinite context)
- Beautiful UI (inspiring experience)

Philosophy: "Elegance is not optional; it is the medium through which transformation occurs."
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Core imports
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install: pip install chromadb sentence-transformers ollama")
    sys.exit(1)

# C2A imports
from constraint_archetypes import ARCHETYPES, get_archetype, get_random_archetype
from llm_scenario_engine import LLMScenarioEngine, ConstraintScenario
from llm_transmutation_judge import TransmutationJudge, TransmutationScore, SessionEvaluation
from elegant_ui import ElegantUI, Colors, Symbols
from rlm_engine import RLMConstraintAnalyzer, RLMQuery
from ai_researcher import AIResearcher
from llm_client import LLMClient, create_client_from_env
from active_lesson import ActiveLessonManager

# Desktop integration for full immersion
try:
    from c2a_desktop import C2ADesktop
    HAS_DESKTOP_INTEGRATION = True
except ImportError:
    HAS_DESKTOP_INTEGRATION = False
    C2ADesktop = None


class MemorySystem:
    """Elegant memory system with ChromaDB backend"""
    
    def __init__(self, collection_name: str = "c2a_elegant"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedder = None
        self.initialize()
    
    def initialize(self):
        """Initialize ChromaDB and embeddings"""
        try:
            data_dir = Path(__file__).parent / "memory_data"
            data_dir.mkdir(exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=str(data_dir))
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "C2A Elegant training sessions"}
            )
            
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            
        except Exception as e:
            print(f"Memory initialization error: {e}")
            raise
    
    def store_session(self, session_data: Dict):
        """Store training session in memory"""
        
        # Create rich embedding text
        session_text = f"""
        C2A Session {session_data['session_id']}
        Archetype: {session_data['archetype']}
        Scenario: {session_data['scenario_title']}
        Transmutations: {' | '.join(session_data['transmutations'])}
        Best Score: {session_data['best_score']}
        Session Score: {session_data['session_score']}
        Patterns: {', '.join(session_data.get('patterns', []))}
        Timestamp: {session_data['timestamp']}
        """.strip()
        
        # Generate embedding
        embedding = self.embedder.encode(session_text).tolist()
        
        # Store
        self.collection.add(
            embeddings=[embedding],
            documents=[session_text],
            metadatas=[{
                "session_id": str(session_data['session_id']),
                "archetype": session_data['archetype'],
                "level": session_data['level'],
                "session_score": session_data['session_score'],
                "best_score": session_data['best_score'],
                "timestamp": session_data['timestamp'],
                "breakthrough": session_data.get('breakthrough', False)
            }],
            ids=[f"session_{session_data['session_id']}"]
        )
    
    def _calculate_level(self, total_sessions: int, avg_score: float) -> int:
        """
        Calculate mastery level based on sessions and performance.
        
        Formula: Level = (Sessions × 0.5) + (Average Score ÷ 10)
        
        This means:
        - ~180-190 sessions to reach Level 100 (with good scores)
        - Higher scores = faster progression
        - Consistent training is key
        
        Level milestones:
        - Level 1-10:  Constraints given explicitly
        - Level 11-20: Constraints hidden, must identify
        - Level 21+:   Personal mode unlocks (force_personal)
        - Level 90+:   Grandmaster territory
        - Level 100:   Physics Arena unlocks
        """
        calculated = int((total_sessions * 0.5) + (avg_score / 10))
        return max(1, min(100, calculated))
    
    def get_user_stats(self) -> Dict:
        """Get user statistics from memory"""
        try:
            results = self.collection.get(include=["metadatas"])
            
            if not results['metadatas']:
                return {
                    'total_sessions': 0,
                    'current_level': 1,
                    'archetype_performance': {},
                    'average_score': 0
                }
            
            metadatas = results['metadatas']
            
            # Calculate stats
            total_sessions = len(metadatas)
            
            scores = [m.get('session_score', 0) for m in metadatas]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Calculate level using the proper formula
            current_level = self._calculate_level(total_sessions, avg_score)
            
            # Archetype performance
            archetype_perf = {}
            for m in metadatas:
                arch = m.get('archetype', 'unknown')
                score = m.get('session_score', 0)
                
                if arch not in archetype_perf:
                    archetype_perf[arch] = []
                archetype_perf[arch].append(score)
            
            # Average per archetype
            archetype_avg = {
                arch: sum(scores) / len(scores) 
                for arch, scores in archetype_perf.items()
            }
            
            return {
                'total_sessions': total_sessions,
                'current_level': current_level,
                'archetype_performance': archetype_avg,
                'average_score': avg_score,
                'recent_sessions': metadatas[-10:] if len(metadatas) >= 10 else metadatas
            }
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                'total_sessions': 0,
                'current_level': 1,
                'archetype_performance': {},
                'average_score': 0
            }


class C2AElegant:
    """The main C2A Elegant training system"""

    def __init__(self, model: str = "qwen2.5:32b", llm_client: Optional[LLMClient] = None):
        self.model = model
        self.ui = ElegantUI()
        self.memory = MemorySystem()

        # Unified LLM client (local Ollama / Anthropic / NVIDIA NIM)
        self.llm = llm_client or create_client_from_env()

        self.scenario_engine = LLMScenarioEngine(model=model, llm_client=self.llm)
        self.judge = TransmutationJudge(model=model, llm_client=self.llm)
        # Use simplified RLM (no code generation) - works on 12GB VRAM!
        self.rlm_analyzer = RLMConstraintAnalyzer(
            self.memory, 
            model=model,
            use_simplified=True  # Perfect for RTX 3060
        )
        
        # AI Researcher - Opus as Cognitive Scientist
        # Observes sessions and generates insights about cognition & C2A
        self.researcher = AIResearcher()
        
        # Active Lesson Manager - Tracks the lesson the user is working on
        self.lesson_manager = ActiveLessonManager()
        
        # Desktop Integration - Full Immersion Mode
        # Updates Hyprland borders, Waybar, notifications, lock screen
        self.desktop = C2ADesktop() if HAS_DESKTOP_INTEGRATION else None
        
        # Session ID should continue from where we left off, not reset to 0
        # Use timestamp-based IDs to avoid collisions
        self.session_id = int(datetime.now().timestamp())
        self.all_sessions = []  # Track all sessions for researcher
    
    def get_adaptive_threshold(self, level: int, archetype_name: str, stats: Dict) -> int:
        """
        Calculate adaptive threshold based on user context.
        
        Beginners get lower bar, experts get higher bar.
        Struggling users get temporary relief.
        New archetypes get grace period.
        
        Args:
            level: Current user level (1-100)
            archetype_name: Current archetype being trained
            stats: User stats from memory.get_user_stats()
            
        Returns:
            Threshold score (50-85 range)
        """
        base = 70  # Default threshold
        
        # Check archetype experience
        archetype_perf = stats.get('archetype_performance', {})
        archetype_avg = archetype_perf.get(archetype_name, 0)
        
        # New archetype? Lower the bar significantly
        if archetype_avg == 0 or archetype_name not in archetype_perf:
            base -= 15
            print(f"{Colors.DIM}[First time with {archetype_name} - threshold lowered to {base}]{Colors.RESET}")
        
        # Struggling with this archetype? Lower bar
        elif archetype_avg < 60:
            base -= 10
            print(f"{Colors.DIM}[Developing {archetype_name} skills - threshold: {base}]{Colors.RESET}")
        
        # High level? Raise expectations
        if level > 70:
            base += 15
        elif level > 50:
            base += 10
        
        # Recent session struggles? Temporary relief
        recent_avg = stats.get('average_score', 70)
        if recent_avg < 60:
            base -= 5
            print(f"{Colors.DIM}[Recent struggles detected - threshold adjusted to {base}]{Colors.RESET}")
        
        # Bound the threshold (never below 50, never above 85)
        threshold = max(50, min(85, base))
        
        return threshold
    
    def run_transmutation_with_correction(
        self,
        scenario: ConstraintScenario,
        threshold: int,
        target_transmutations: int,
        active_lesson_prompt: str,
        level: int,
        user_profile: Dict
    ) -> tuple:
        """
        Run transmutation phase with 2-round correction opportunities.
        
        For each transmutation target:
        - Round 1: User attempts
        - If < threshold: Show correction, allow Round 2
        - Track all scores and pick best
        
        Args:
            scenario: The constraint scenario
            threshold: Adaptive threshold for this session
            target_transmutations: Number of transmutations to collect
            active_lesson_prompt: Active lesson for the judge
            level: Current user level
            user_profile: User profile for judge
        
        Returns:
            tuple: (transmutations, durations, individual_scores)
        """
        from typing import Tuple, List
        
        transmutations = []
        durations = []
        individual_scores = []
        
        # Clear screen for focused work
        print("\033[2J\033[H", end="")
        
        # Show scenario reminder - FULL scenario, properly wrapped
        print(f"{Colors.DIM}━━━ {scenario.title.upper()} ━━━{Colors.RESET}")
        # Use textwrap to properly display the full scenario
        import textwrap
        terminal_width = self.ui.get_terminal_width() - 4  # Leave margin
        wrapped_situation = textwrap.fill(scenario.situation, width=min(terminal_width, 80))
        print(f"{Colors.DIM}{wrapped_situation}{Colors.RESET}\n")
        
        # Show active lesson if exists
        if self.lesson_manager.has_active_lesson():
            lesson = self.lesson_manager.get_current_lesson()
            if lesson:
                print(f"{Colors.BRIGHT_YELLOW}🎯 ACTIVE LESSON: {lesson.title}{Colors.RESET}")
                print(f"{Colors.BRIGHT_YELLOW}   {lesson.practice_question}{Colors.RESET}\n")
        
        print(f"{Colors.BRIGHT_CYAN}Target: {target_transmutations} transmutation(s) | Threshold: {threshold}/100{Colors.RESET}\n")
        
        # For each transmutation target
        for trans_num in range(target_transmutations):
            print(f"\n{Colors.BRIGHT_WHITE}{'═' * 60}{Colors.RESET}")
            print(f"{Colors.BRIGHT_WHITE}Transmutation {trans_num + 1}/{target_transmutations}{Colors.RESET}")
            print(f"{Colors.BRIGHT_WHITE}{'═' * 60}{Colors.RESET}\n")
            
            # ROUND 1: Initial attempt
            trans_1, duration_1 = self.ui.get_transmutation_input(
                "Transmute:",
                trans_num + 1,
                target_transmutations,
                time_limit=90
            )
            
            if not trans_1.strip():
                continue
            
            # Evaluate Round 1
            print(f"\n{Colors.CYAN}Evaluating...{Colors.RESET}")
            score_1 = self.judge.evaluate_transmutation(
                trans_1,
                scenario.to_dict(),
                user_profile,
                level,
                active_lesson_prompt
            )
            
            # ═══════════════════════════════════════════════════════════════
            # VELOCITY GUILLOTINE - Apply time penalty to raw score
            # ═══════════════════════════════════════════════════════════════
            raw_score_1 = score_1.overall_score
            final_score_1, velocity_mult_1, velocity_msg_1 = self.judge.apply_velocity_penalty(
                raw_score_1, duration_1
            )
            score_1.overall_score = final_score_1  # Update with penalized score
            
            # Show pattern tag with velocity info
            self.ui.show_pattern_tag(
                score_1.pattern_identified,
                score_1.overall_score
            )
            
            # Show velocity penalty feedback
            if velocity_mult_1 != 1.0:
                if velocity_mult_1 > 1.0:
                    print(f"{Colors.GREEN}{velocity_msg_1} (Raw: {raw_score_1} → Final: {final_score_1}){Colors.RESET}")
                else:
                    print(f"{Colors.RED}{velocity_msg_1} (Raw: {raw_score_1} → Final: {final_score_1}){Colors.RESET}")
            
            # Check if it meets threshold
            if score_1.overall_score >= threshold:
                # SUCCESS - use this transmutation
                print(f"{Colors.GREEN}✓ Threshold met ({score_1.overall_score} >= {threshold}){Colors.RESET}")
                transmutations.append(trans_1)
                durations.append(duration_1)
                individual_scores.append(score_1)
            else:
                # FAILED - offer correction opportunity
                self.ui.show_correction_prompt(
                    score_1.what_missed,
                    score_1.growth_edge,
                    1,
                    2
                )
                
                # ROUND 2: Correction attempt
                trans_2, duration_2 = self.ui.get_transmutation_input(
                    "Retry:",
                    trans_num + 1,
                    target_transmutations,
                    time_limit=60
                )
                
                if trans_2.strip():
                    # Evaluate Round 2
                    print(f"\n{Colors.CYAN}Re-evaluating...{Colors.RESET}")
                    score_2 = self.judge.evaluate_transmutation(
                        trans_2,
                        scenario.to_dict(),
                        user_profile,
                        level,
                        active_lesson_prompt
                    )
                    
                    # VELOCITY GUILLOTINE - Apply time penalty to Round 2
                    raw_score_2 = score_2.overall_score
                    final_score_2, velocity_mult_2, velocity_msg_2 = self.judge.apply_velocity_penalty(
                        raw_score_2, duration_2
                    )
                    score_2.overall_score = final_score_2
                    
                    # Show pattern tag
                    self.ui.show_pattern_tag(
                        score_2.pattern_identified,
                        score_2.overall_score
                    )
                    
                    # Show velocity feedback for round 2
                    if velocity_mult_2 != 1.0:
                        if velocity_mult_2 > 1.0:
                            print(f"{Colors.GREEN}{velocity_msg_2} (Raw: {raw_score_2} → Final: {final_score_2}){Colors.RESET}")
                        else:
                            print(f"{Colors.RED}{velocity_msg_2} (Raw: {raw_score_2} → Final: {final_score_2}){Colors.RESET}")
                    
                    # Show improvement
                    self.ui.show_improvement_delta(score_1.overall_score, score_2.overall_score)
                    
                    # Use better of the two
                    if score_2.overall_score > score_1.overall_score:
                        transmutations.append(trans_2)
                        durations.append(duration_2)
                        individual_scores.append(score_2)
                        print(f"{Colors.GREEN}Using improved version ✓{Colors.RESET}")
                    else:
                        transmutations.append(trans_1)
                        durations.append(duration_1)
                        individual_scores.append(score_1)
                        print(f"{Colors.YELLOW}Using original attempt{Colors.RESET}")
                else:
                    # No retry provided - use Round 1
                    transmutations.append(trans_1)
                    durations.append(duration_1)
                    individual_scores.append(score_1)
        
        return transmutations, durations, individual_scores
    
    def run(self):
        """Main entry point"""
        self.ui.show_splash()
        time.sleep(1)
        
        self.main_menu()
    
    def main_menu(self):
        """Main menu loop"""
        while True:
            # Get user stats
            stats = self.memory.get_user_stats()
            current_level = stats['current_level']
            total_sessions = stats['total_sessions']
            
            # Determine current training phase
            if current_level <= 10:
                phase = "Phase 1: Transmutation"
            elif current_level <= 30:
                phase = "Phase 2: Detection"
            elif current_level <= 50:
                phase = "Phase 3: Personal Domain"
            else:
                phase = "Phase 4: Real Life"
            
            # Build status line
            status = f"Level {current_level}/100  |  {total_sessions} Sessions  |  {phase}"
            
            # Build menu options
            options = [
                ("1", "Begin Training Session", True),
                ("2", "⚡ Flash Drill (10s Reflex Training)", True),
                ("3", "Deep Analysis (RLM)", total_sessions >= 5),
                ("4", "View Progress", total_sessions > 0),
                ("5", "Research Dashboard (AI Insights)", total_sessions >= 3),
                ("6", "Archetype Gallery", True),
                ("7", "Set Your Domain", True),
                ("8", "Physics Arena (Level 100 Unlock)", current_level >= 100),
                ("9", "Exit", True)
            ]
            
            self.ui.show_menu("C2A ELEGANT", options, status)
            
            choice = input(f"\001{Colors.BRIGHT_WHITE}\002❯ \001{Colors.RESET}\002").strip()
            
            if choice == "1":
                self.training_session()
            elif choice == "2":
                self.flash_drill()
            elif choice == "3" and total_sessions >= 5:
                self.deep_analysis()
            elif choice == "4" and total_sessions > 0:
                self.view_progress()
            elif choice == "5" and total_sessions >= 3:
                self.research_dashboard()
            elif choice == "6":
                self.show_archetype_gallery()
            elif choice == "7":
                self.set_domain_menu()
            elif choice == "8" and current_level >= 100:
                self.physics_arena()
            elif choice == "9":
                self.exit_gracefully()
                break
            else:
                print(f"{Colors.RED}Invalid choice{Colors.RESET}")
                time.sleep(1)
    
    def flash_drill(self):
        """
        ⚡ FLASH DRILL - 10-15 second reflex training
        
        Purpose: Train pattern recognition below conscious thought level.
        Too fast for deliberation = pure transmutation instinct.
        
        No LLM scenario generation - uses pre-built constraint prompts for speed.
        """
        
        # Pre-built flash constraints (no LLM delay)
        flash_constraints = [
            ("SCARCITY", "No money. Car broken. Work 22 miles away."),
            ("VELOCITY", "Presentation in 5 minutes. Slides corrupted."),
            ("FRICTION", "Team lead hates your approach. Won't approve."),
            ("ASYMMETRY", "Competitor has 10x your budget. Same market."),
            ("PARADOX", "Client wants cheap AND premium. Both required."),
            ("SCARCITY", "One week to learn what takes 6 months."),
            ("VELOCITY", "Flight leaves in 90 minutes. Passport missing."),
            ("FRICTION", "New software. Zero documentation. Deadline tomorrow."),
            ("ASYMMETRY", "Junior dev. Senior's code review. They're hostile."),
            ("PARADOX", "Must be creative. Zero freedom allowed."),
            ("SCARCITY", "3 hours sleep. 12 hour workday ahead."),
            ("VELOCITY", "Email sent to wrong person. They're reading now."),
            ("FRICTION", "Perfect idea. No one believes you."),
            ("ASYMMETRY", "Introvert. Must network to survive."),
            ("PARADOX", "Need experience to get job. Need job to get experience."),
        ]
        
        import random
        
        print("\033[2J\033[H", end="")  # Clear screen
        
        print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}⚡ FLASH DRILL - Reflex Transmutation ⚡{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}\n")
        
        print(f"{Colors.YELLOW}Rules:{Colors.RESET}")
        print(f"{Colors.DIM}• 15 seconds max per drill{Colors.RESET}")
        print(f"{Colors.DIM}• 10 words max - pure signal only{Colors.RESET}")
        print(f"{Colors.DIM}• No thinking - just recognize the pattern{Colors.RESET}")
        print(f"{Colors.DIM}• Press Enter with empty response to exit{Colors.RESET}\n")
        
        input(f"{Colors.DIM}Press Enter to begin...{Colors.RESET}")
        
        # Shuffle constraints so we don't repeat until all are used
        available_constraints = flash_constraints.copy()
        random.shuffle(available_constraints)
        
        drill_count = 0
        total_time = 0
        
        while True:
            # If we've used all constraints, reshuffle
            if not available_constraints:
                available_constraints = flash_constraints.copy()
                random.shuffle(available_constraints)
                print(f"\n{Colors.DIM}[All constraints used - reshuffling]{Colors.RESET}")
            
            # Pop next constraint (no repeats until all used)
            archetype, constraint = available_constraints.pop()
            drill_count += 1
            
            print(f"\n{Colors.BRIGHT_WHITE}{'─' * 60}{Colors.RESET}")
            print(f"{Colors.BRIGHT_MAGENTA}⚡ DRILL #{drill_count}{Colors.RESET}")
            print(f"{Colors.BRIGHT_WHITE}{'─' * 60}{Colors.RESET}\n")
            
            print(f"{Colors.CYAN}[{archetype}]{Colors.RESET}")
            print(f"{Colors.BRIGHT_WHITE}{constraint}{Colors.RESET}\n")
            
            print(f"{Colors.RED}⏱️ 15 SECONDS - GO!{Colors.RESET}")
            
            start_time = time.time()
            
            try:
                response = input(f"\001{Colors.BRIGHT_WHITE}\002❯ \001{Colors.RESET}\002").strip()
            except (EOFError, KeyboardInterrupt):
                response = ""
            
            duration = time.time() - start_time
            total_time += duration
            
            if not response:
                print(f"\n{Colors.YELLOW}Flash Drill ended.{Colors.RESET}")
                break
            
            word_count = len(response.split())
            
            # Feedback
            if duration <= 10:
                time_feedback = f"{Colors.GREEN}⚡ {duration:.1f}s - REFLEXIVE!{Colors.RESET}"
            elif duration <= 15:
                time_feedback = f"{Colors.YELLOW}✓ {duration:.1f}s - Good{Colors.RESET}"
            else:
                time_feedback = f"{Colors.RED}✖ {duration:.1f}s - Too slow (thinking!){Colors.RESET}"
            
            if word_count <= 10:
                word_feedback = f"{Colors.GREEN}{word_count} words ✓{Colors.RESET}"
            else:
                word_feedback = f"{Colors.RED}{word_count} words (cut the fat!){Colors.RESET}"
            
            print(f"\n{time_feedback}  |  {word_feedback}")
        
        # Summary
        if drill_count > 1:
            avg_time = total_time / (drill_count - 1) if drill_count > 1 else 0
            print(f"\n{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}FLASH DRILL SUMMARY{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}")
            print(f"{Colors.WHITE}Drills completed: {drill_count - 1}{Colors.RESET}")
            print(f"{Colors.WHITE}Average time: {avg_time:.1f}s{Colors.RESET}")
            
            if avg_time <= 10:
                print(f"\n{Colors.GREEN}⚡ REFLEXIVE SPEED - You're training automaticity!{Colors.RESET}")
            elif avg_time <= 15:
                print(f"\n{Colors.YELLOW}✓ Good pace - keep pushing for sub-10s{Colors.RESET}")
            else:
                print(f"\n{Colors.RED}⚠ Still thinking too much - aim for pattern recognition, not analysis{Colors.RESET}")
        
        input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
    
    def training_session(self):
        """Run a complete training session"""
        
        # Get user profile for personalization
        stats = self.memory.get_user_stats()
        user_profile = {
            'domain': self._get_user_domain(),
            'total_sessions': stats['total_sessions'],
            'archetype_performance': stats['archetype_performance'],
            'recent_constraints': [],  # Could extract from memory
            'strengths': [],
            'weaknesses': self._identify_weak_archetypes(stats['archetype_performance'])
        }
        
        level = stats['current_level']
        
        # ═══════════════════════════════════════════════════════════════
        # TRAINING MODE SELECTION BASED ON LEVEL
        # ═══════════════════════════════════════════════════════════════
        # Level 1-10:  Constraint GIVEN (transmutation only)
        # Level 11-30: Constraint HIDDEN in scenario (detection + transmutation)
        # Level 31-50: Personal domain scenarios, constraint hidden
        # Level 51+:   Real Life Mode (you provide situation + identify constraint)
        # ═══════════════════════════════════════════════════════════════
        
        if level >= 51:
            # REAL LIFE MODE - User provides everything
            self._real_life_training_session(user_profile, level, stats)
            return
        
        # Select archetype (could be user choice or intelligent selection)
        archetype = self._select_training_archetype(user_profile, level)
        
        # ═══════════════════════════════════════════════════════════════
        # DESKTOP INTEGRATION: Session Start
        # Borders glow with archetype color, waybar updates, notification
        # ═══════════════════════════════════════════════════════════════
        if self.desktop:
            active_lesson_data = None
            if self.lesson_manager.has_active_lesson():
                lesson = self.lesson_manager.get_current_lesson()
                if lesson:
                    active_lesson_data = {
                        "title": lesson.title,
                        "practice_question": lesson.practice_question
                    }
            self.desktop.on_session_start(
                archetype=archetype.name.lower(),
                level=level,
                active_lesson=active_lesson_data
            )
        
        # Show archetype moment
        self.ui.show_archetype_moment(archetype)
        
        # Show current training phase
        self._show_training_phase(level)
        
        # Generate scenario (active lesson is shown during transmutation phase)
        print(f"\n{Colors.CYAN}Generating personalized scenario...{Colors.RESET}")
        scenario = self.scenario_engine.generate_scenario(
            user_profile,
            level,
            archetype,
            force_personal=(level >= 31)  # Personal domain at level 31+
        )
        
        # Display scenario
        self.ui.show_scenario(scenario.to_dict())
        
        # CONSTRAINT IDENTIFICATION PHASE (Level 11+)
        # If constraint is hidden, user must identify it first - FAILURE ENDS SESSION
        detection_data = None
        if scenario.hidden_constraint:
            identified, detection_data = self._constraint_identification_phase(scenario, level)
            if not identified:
                # Store failed detection for learning analytics
                self._store_failed_detection(scenario, detection_data, level)
                self._show_failed_identification_feedback(scenario, level)
                return
        
        # Calculate transmutation target based on level (scales with mastery)
        # Level 1-9: 1, Level 10-19: 2, Level 20-29: 3, ... Level 90+: 10
        target_transmutations = self._get_transmutation_target(level)
        
        # Get active lesson for judge
        active_lesson_prompt = self.lesson_manager.get_lesson_for_prompt()
        
        # Calculate adaptive threshold based on user context
        threshold = self.get_adaptive_threshold(level, archetype.name, stats)
        
        # ═══════════════════════════════════════════════════════════════
        # NEW: TWO-ROUND CORRECTION LOOP
        # Immediate feedback with retry opportunity for below-threshold scores
        # ═══════════════════════════════════════════════════════════════
        transmutations, durations, individual_scores = self.run_transmutation_with_correction(
            scenario=scenario,
            threshold=threshold,
            target_transmutations=target_transmutations,
            active_lesson_prompt=active_lesson_prompt,
            level=level,
            user_profile=user_profile
        )
        
        # Get meta-reflection
        print(f"\n{Colors.BRIGHT_CYAN}{'─' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}Meta-Cognitive Reflection{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'─' * 60}{Colors.RESET}\n")
        print(f"{Colors.CYAN}How did your thinking evolve during this session?{Colors.RESET}")
        meta_reflection = input(f"\001{Colors.BRIGHT_WHITE}\002❯ \001{Colors.RESET}\002")
        
        # Build session evaluation from individual scores (already evaluated in correction loop)
        print(f"\n{Colors.CYAN}Synthesizing session analysis...{Colors.RESET}")
        time.sleep(1.0)
        
        # If we have individual scores from the correction loop, build evaluation from them
        if individual_scores:
            # Calculate session-level metrics from individual scores
            session_score = sum(s.overall_score for s in individual_scores) // len(individual_scores)
            
            # Use the judge's session evaluation but pass our pre-evaluated scores
            evaluation = self.judge.evaluate_session(
                transmutations,
                scenario.to_dict(),
                user_profile,
                level,
                time_taken=sum(durations),
                meta_reflection=meta_reflection,
                active_lesson=active_lesson_prompt
            )
        else:
            # Fallback: no transmutations collected, create minimal evaluation
            evaluation = self.judge.evaluate_session(
                transmutations if transmutations else ["(no transmutation provided)"],
                scenario.to_dict(),
                user_profile,
                level,
                time_taken=sum(durations) if durations else 0,
                meta_reflection=meta_reflection,
                active_lesson=active_lesson_prompt
            )
        
        # Show results
        self._display_session_results(evaluation, scenario)
        
        # Store in memory (with detection data if applicable)
        self._store_session(
            scenario,
            transmutations,
            evaluation,
            level,
            meta_reflection,
            detection_data=detection_data
        )
        
        # Update active lesson based on evaluation
        self._update_active_lesson(evaluation, scenario)
        
        # Level progress - calculate actual progression
        new_total_sessions = stats['total_sessions'] + 1
        new_avg_score = ((stats['average_score'] * stats['total_sessions']) + evaluation.session_score) / new_total_sessions
        new_level = self.memory._calculate_level(new_total_sessions, new_avg_score)
        
        # Calculate progress toward next level
        # Sessions needed for level 100 with current avg score: solve for sessions in formula
        # 100 = (sessions * 0.5) + (avg_score / 10)
        # sessions = (100 - avg_score/10) / 0.5 = (100 - avg_score/10) * 2
        sessions_for_100 = max(1, (100 - new_avg_score / 10) * 2)
        progress = min(1.0, new_total_sessions / sessions_for_100)
        
        self.ui.show_level_progress(level, new_level, progress)
        
        # Show level up notification if leveled up
        leveled_up = new_level > level
        if leveled_up:
            print(f"\n{Colors.BRIGHT_GREEN}{'═' * 60}{Colors.RESET}")
            print(f"{Colors.BRIGHT_GREEN}⬆️  LEVEL UP! {level} → {new_level}{Colors.RESET}")
            print(f"{Colors.BRIGHT_GREEN}{'═' * 60}{Colors.RESET}")
        
        # ═══════════════════════════════════════════════════════════════
        # DESKTOP INTEGRATION: Session End
        # Return to neutral borders, update waybar, send notifications
        # ═══════════════════════════════════════════════════════════════
        if self.desktop:
            # Check if lesson was mastered this session
            lesson_mastered = False
            lesson_title = None
            if self.lesson_manager.has_active_lesson():
                lesson = self.lesson_manager.get_current_lesson()
                if lesson and lesson.demonstrated:
                    lesson_mastered = True
                    lesson_title = lesson.title
            
            # Check for breakthrough (high score + pattern recognition)
            breakthrough = evaluation.session_score >= 85
            pattern = evaluation.patterns_identified[0] if evaluation.patterns_identified else None
            
            self.desktop.on_session_end(
                score=evaluation.session_score,
                archetype=archetype.name.lower(),
                level=new_level,
                leveled_up=leveled_up,
                lesson_mastered=lesson_mastered,
                lesson_title=lesson_title,
                breakthrough=breakthrough,
                pattern=pattern
            )
        
        input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
    
    def _get_user_domain(self) -> str:
        """Get or set user's domain for personalized training"""
        domain_file = Path(__file__).parent / "memory_data" / "user_domain.txt"
        
        if domain_file.exists():
            return domain_file.read_text().strip()
        else:
            return "life optimization"  # Default
    
    def _set_user_domain(self, domain: str):
        """Save user's domain"""
        domain_file = Path(__file__).parent / "memory_data" / "user_domain.txt"
        domain_file.write_text(domain)
    
    def _show_training_phase(self, level: int):
        """Show current training phase information"""
        print(f"\n{Colors.BRIGHT_CYAN}{'─' * 60}{Colors.RESET}")
        
        if level <= 10:
            phase = "PHASE 1: TRANSMUTATION TRAINING"
            desc = "Constraint is GIVEN. Focus on transmutation quality."
            print(f"{Colors.BRIGHT_GREEN}{phase}{Colors.RESET}")
        elif level <= 30:
            phase = "PHASE 2: DETECTION + TRANSMUTATION"
            desc = "Constraint is HIDDEN. You must identify it first."
            print(f"{Colors.BRIGHT_YELLOW}{phase}{Colors.RESET}")
        elif level <= 50:
            phase = "PHASE 3: PERSONAL DOMAIN MASTERY"
            desc = "Personal scenarios in YOUR domain. Constraint hidden."
            print(f"{Colors.ORANGE}{phase}{Colors.RESET}")
        else:
            phase = "PHASE 4: REAL LIFE MODE"
            desc = "YOU provide the situation. YOU identify the constraint."
            print(f"{Colors.BRIGHT_MAGENTA}{phase}{Colors.RESET}")
        
        print(f"{Colors.DIM}{desc}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'─' * 60}{Colors.RESET}")
    
    def _constraint_identification_phase(self, scenario: ConstraintScenario, level: int) -> tuple:
        """
        Have user identify the hidden constraint - LLM validated
        
        Returns:
            tuple: (success: bool, detection_data: dict)
            detection_data contains tracking info for analysis
        """
        
        print(f"\n{Colors.ORANGE}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.ORANGE}⚠️  PHASE 1: IDENTIFY THE CONSTRAINT{Colors.RESET}")
        print(f"{Colors.ORANGE}{'═' * 60}{Colors.RESET}\n")
        
        print(f"{Colors.YELLOW}You must identify the PRIMARY constraint before transmuting.{Colors.RESET}")
        print(f"{Colors.YELLOW}Failure to identify = Session ends.{Colors.RESET}\n")
        
        # Show the 5 archetypes as a scanner reference
        print(f"{Colors.DIM}Use the 5 Archetypes as your scanner:{Colors.RESET}")
        print(f"{Colors.DIM}  ⧗ Scarcity  |  ⚡ Velocity  |  ⚖ Asymmetry  |  ⚙ Friction  |  ∞ Paradox{Colors.RESET}\n")
        
        print(f"{Colors.CYAN}What is the PRIMARY constraint in this situation?{Colors.RESET}")
        print(f"{Colors.DIM}(Name the archetype AND describe the specific constraint){Colors.RESET}")
        user_constraint = input(f"\001{Colors.BRIGHT_WHITE}\002❯ \001{Colors.RESET}\002").strip()
        
        # Initialize detection data for tracking
        detection_data = {
            'user_answer': user_constraint,
            'correct_answer': scenario.hidden_constraint,
            'correct_archetype': scenario.archetype,
            'user_archetype': self._extract_archetype_from_answer(user_constraint),
            'success': False,
            'partial_credit': 0,
            'confusion_type': None
        }
        
        if not user_constraint:
            print(f"\n{Colors.RED}❌ No constraint identified. Session ends.{Colors.RESET}")
            detection_data['confusion_type'] = 'no_answer'
            return False, detection_data
        
        # LLM-based validation for more sophisticated checking
        validation_result = self._validate_constraint_identification(
            user_constraint, 
            scenario.hidden_constraint,
            scenario.situation,
            scenario.archetype,
            level
        )
        
        # Update detection data with validation results
        detection_data['partial_credit'] = validation_result.get('partial_credit', 0)
        detection_data['success'] = validation_result['is_correct']
        
        # Determine confusion type if incorrect
        if not validation_result['is_correct']:
            detection_data['confusion_type'] = self._determine_confusion_type(
                detection_data['user_archetype'],
                scenario.archetype,
                validation_result.get('feedback', '')
            )
        
        if validation_result['is_correct']:
            print(f"\n{Colors.GREEN}{Symbols.SUCCESS} Constraint identified correctly!{Colors.RESET}")
            if validation_result.get('feedback'):
                print(f"{Colors.DIM}{validation_result['feedback']}{Colors.RESET}")
            return True, detection_data
        else:
            print(f"\n{Colors.RED}❌ Constraint not identified correctly.{Colors.RESET}")
            if validation_result.get('feedback'):
                print(f"{Colors.YELLOW}{validation_result['feedback']}{Colors.RESET}")
            return False, detection_data
    
    def _extract_archetype_from_answer(self, answer: str) -> str:
        """Extract which archetype the user mentioned in their answer"""
        answer_lower = answer.lower()
        
        archetype_keywords = {
            'scarcity': ['scarcity', 'scarce', 'limited', 'lack', 'not enough', 'resource'],
            'velocity': ['velocity', 'time', 'speed', 'deadline', 'fast', 'slow', 'urgent'],
            'asymmetry': ['asymmetry', 'information', 'unknown', 'uncertain', 'don\'t know', 'incomplete'],
            'friction': ['friction', 'resistance', 'obstacle', 'barrier', 'difficult', 'hard to'],
            'paradox': ['paradox', 'contradiction', 'both', 'either', 'conflicting', 'opposing']
        }
        
        for archetype, keywords in archetype_keywords.items():
            for keyword in keywords:
                if keyword in answer_lower:
                    return archetype
        
        return 'unknown'
    
    def _determine_confusion_type(self, user_archetype: str, correct_archetype: str, feedback: str) -> str:
        """Determine what type of detection confusion occurred"""
        
        if user_archetype == 'unknown':
            return 'no_archetype_identified'
        
        if user_archetype != correct_archetype:
            return f'archetype_confusion:{user_archetype}_for_{correct_archetype}'
        
        if 'symptom' in feedback.lower() or 'surface' in feedback.lower():
            return 'symptom_not_root'
        
        if 'secondary' in feedback.lower() or 'primary' in feedback.lower():
            return 'secondary_not_primary'
        
        return 'general_misidentification'
    
    def _validate_constraint_identification(
        self, 
        user_answer: str, 
        correct_constraint: str,
        situation: str,
        archetype: str,
        level: int
    ) -> Dict:
        """Use LLM to validate constraint identification"""
        
        # For lower levels, be more lenient. For higher levels, be strict.
        strictness = "lenient" if level < 20 else "moderate" if level < 40 else "strict"
        
        prompt = f"""You are validating a C2A constraint identification.

SITUATION:
{situation}

CORRECT CONSTRAINT: {correct_constraint}
ARCHETYPE: {archetype}

USER'S ANSWER: {user_answer}

STRICTNESS LEVEL: {strictness}

Evaluate if the user correctly identified the constraint. Consider:
1. Did they identify the CORE constraint (not a symptom)?
2. Did they recognize the correct archetype or constraint type?
3. Is their answer substantively correct, even if worded differently?

For {strictness} evaluation:
- lenient: Accept if they're in the right general direction
- moderate: Accept if they identified the core issue
- strict: Must identify the specific constraint and archetype

Respond in JSON:
{{
    "is_correct": true/false,
    "feedback": "Brief explanation of why correct/incorrect",
    "partial_credit": 0-100
}}
"""

        try:
            result_text = self.llm.chat(prompt)
            
            # Parse JSON from response
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                result = json.loads(result_text[json_start:json_end])
                return result
            else:
                # Fallback to keyword matching
                return self._keyword_validation(user_answer, correct_constraint)
                
        except Exception as e:
            # Fallback to simple keyword matching
            return self._keyword_validation(user_answer, correct_constraint)
    
    def _keyword_validation(self, user_answer: str, correct_constraint: str) -> Dict:
        """Fallback keyword-based validation"""
        correct_keywords = set(correct_constraint.lower().split())
        user_keywords = set(user_answer.lower().split())
        
        # Remove common words
        stopwords = {'the', 'a', 'an', 'is', 'are', 'of', 'to', 'and', 'in', 'that', 'it'}
        correct_keywords -= stopwords
        user_keywords -= stopwords
        
        overlap = correct_keywords.intersection(user_keywords)
        
        if len(overlap) >= 2 or len(overlap) >= len(correct_keywords) * 0.5:
            return {
                'is_correct': True,
                'feedback': 'Constraint identified.',
                'partial_credit': 80
            }
        elif len(overlap) >= 1:
            return {
                'is_correct': False,
                'feedback': f'Partially correct. The key constraint was: {correct_constraint}',
                'partial_credit': 40
            }
        else:
            return {
                'is_correct': False,
                'feedback': f'The constraint was: {correct_constraint}',
                'partial_credit': 0
            }
    
    def _store_failed_detection(self, scenario: ConstraintScenario, detection_data: Dict, level: int):
        """Store failed detection attempt for learning analytics"""
        
        self.session_id += 1
        
        failed_session_data = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'archetype': scenario.archetype,
            'scenario_title': scenario.title,
            'transmutations': [],  # No transmutations - failed at detection
            'meta_reflection': '',
            'session_score': 0,
            'best_score': 0,
            'divergence_score': 0,
            'meta_cognitive_score': 0,
            'velocity_score': 0,
            'patterns': [],
            'breakthrough': False,
            # Detection tracking - this is the key data
            'detection_required': True,
            'detection_success': False,
            'detection_user_answer': detection_data.get('user_answer', ''),
            'detection_correct_answer': scenario.hidden_constraint or '',
            'detection_correct_archetype': scenario.archetype,
            'detection_user_archetype': detection_data.get('user_archetype', ''),
            'detection_partial_credit': detection_data.get('partial_credit', 0),
            'detection_confusion_type': detection_data.get('confusion_type', 'unknown'),
            'session_type': 'failed_detection'  # Mark as failed detection session
        }
        
        self.memory.store_session(failed_session_data)
    
    def _show_failed_identification_feedback(self, scenario: ConstraintScenario, level: int):
        """Show feedback when constraint identification fails"""
        
        print(f"\n{Colors.RED}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.RED}SESSION ENDED - CONSTRAINT NOT IDENTIFIED{Colors.RESET}")
        print(f"{Colors.RED}{'═' * 60}{Colors.RESET}\n")
        
        print(f"{Colors.YELLOW}Learning Moment:{Colors.RESET}")
        print(f"{Colors.WHITE}Identifying constraints is the foundation of C2A.{Colors.RESET}")
        print(f"{Colors.WHITE}You cannot transmute what you cannot see.{Colors.RESET}\n")
        
        print(f"{Colors.CYAN}The Hidden Constraint Was:{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}{scenario.hidden_constraint}{Colors.RESET}\n")
        
        print(f"{Colors.CYAN}Archetype:{Colors.RESET} {scenario.archetype.upper()}\n")
        
        print(f"{Colors.CYAN}Hint for Next Time:{Colors.RESET}")
        print(f"  {Colors.DIM}{scenario.hint}{Colors.RESET}\n")
        
        # Show the 5 archetypes as a reminder
        print(f"{Colors.BRIGHT_CYAN}Remember the 5 Archetype Scanner:{Colors.RESET}")
        print(f"  {Colors.DIM}⧗ SCARCITY  - Resources < Wants{Colors.RESET}")
        print(f"  {Colors.DIM}⚡ VELOCITY  - Time compression{Colors.RESET}")
        print(f"  {Colors.DIM}⚖ ASYMMETRY - Incomplete information{Colors.RESET}")
        print(f"  {Colors.DIM}⚙ FRICTION  - Resistance to action{Colors.RESET}")
        print(f"  {Colors.DIM}∞ PARADOX   - Contradictory requirements{Colors.RESET}\n")
        
        print(f"{Colors.DIM}This session was NOT recorded. Try again.{Colors.RESET}")
        
        input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
    
    def _real_life_training_session(self, user_profile: Dict, level: int, stats: Dict):
        """
        REAL LIFE MODE (Level 51+)
        
        The user provides:
        1. Their current situation (what's happening in their life)
        2. The constraint they identify (using the 5 archetypes)
        3. Their transmutation(s)
        
        LLM validates constraint identification and judges transmutation quality.
        """
        
        self.ui.clear_screen()
        
        print(f"\n{Colors.BRIGHT_MAGENTA}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_MAGENTA}🔮 REAL LIFE MODE - Level {level}{Colors.RESET}")
        print(f"{Colors.BRIGHT_MAGENTA}{'═' * 60}{Colors.RESET}\n")
        
        print(f"{Colors.WHITE}You've reached the level where constraint-thinking{Colors.RESET}")
        print(f"{Colors.WHITE}should be applied to YOUR ACTUAL LIFE.{Colors.RESET}\n")
        
        print(f"{Colors.CYAN}This is the ultimate test:{Colors.RESET}")
        print(f"  1. YOU describe what's happening in your life")
        print(f"  2. YOU identify the constraint (archetype + description)")
        print(f"  3. YOU transmute it into advantage")
        print(f"  4. LLM validates and scores\n")
        
        print(f"{Colors.YELLOW}If your constraint identification is weak, session ends.{Colors.RESET}\n")
        
        # Show archetypes as scanner
        print(f"{Colors.BRIGHT_CYAN}The 5 Archetype Scanner:{Colors.RESET}")
        print(f"  ⧗ SCARCITY  - Do you have less than you need?")
        print(f"  ⚡ VELOCITY  - Is time compressing on you?")
        print(f"  ⚖ ASYMMETRY - Do you lack critical information?")
        print(f"  ⚙ FRICTION  - Is something resisting your intention?")
        print(f"  ∞ PARADOX   - Do you face contradictory requirements?\n")
        
        print(f"{Colors.BRIGHT_CYAN}{'─' * 60}{Colors.RESET}")
        
        # STEP 1: Get the situation from user
        print(f"\n{Colors.BRIGHT_WHITE}STEP 1: Describe Your Current Situation{Colors.RESET}")
        print(f"{Colors.DIM}What's happening in your life right now that involves a constraint?{Colors.RESET}")
        print(f"{Colors.DIM}(Be specific - the more detail, the better the training){Colors.RESET}\n")
        
        situation = input(f"\001{Colors.BRIGHT_WHITE}\002❯ \001{Colors.RESET}\002").strip()
        
        if not situation or len(situation) < 20:
            print(f"\n{Colors.YELLOW}Please provide more detail about your situation.{Colors.RESET}")
            input(f"{Colors.DIM}Press Enter to try again...{Colors.RESET}")
            return
        
        # STEP 2: User identifies the constraint
        print(f"\n{Colors.BRIGHT_WHITE}STEP 2: Identify the Constraint{Colors.RESET}")
        print(f"{Colors.DIM}Which archetype? What specifically is the constraint?{Colors.RESET}\n")
        
        user_constraint = input(f"\001{Colors.BRIGHT_WHITE}\002❯ \001{Colors.RESET}\002").strip()
        
        if not user_constraint:
            print(f"\n{Colors.RED}❌ No constraint identified. Session ends.{Colors.RESET}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")
            return
        
        # STEP 3: Validate constraint identification using LLM
        print(f"\n{Colors.CYAN}Validating your constraint identification...{Colors.RESET}")
        
        validation = self._validate_real_life_constraint(situation, user_constraint, level)
        
        if not validation['is_valid']:
            print(f"\n{Colors.RED}{'═' * 60}{Colors.RESET}")
            print(f"{Colors.RED}SESSION ENDED - CONSTRAINT IDENTIFICATION INSUFFICIENT{Colors.RESET}")
            print(f"{Colors.RED}{'═' * 60}{Colors.RESET}\n")
            
            print(f"{Colors.YELLOW}Feedback:{Colors.RESET}")
            print(f"  {Colors.WHITE}{validation['feedback']}{Colors.RESET}\n")
            
            if validation.get('suggested_constraint'):
                print(f"{Colors.CYAN}A stronger constraint identification might be:{Colors.RESET}")
                print(f"  {Colors.DIM}{validation['suggested_constraint']}{Colors.RESET}\n")
            
            print(f"{Colors.DIM}This session was NOT recorded. Refine your constraint-seeing.{Colors.RESET}")
            input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
            return
        
        # Constraint validated - proceed to transmutation
        print(f"\n{Colors.GREEN}{Symbols.SUCCESS} Constraint identification validated!{Colors.RESET}")
        if validation.get('feedback'):
            print(f"{Colors.DIM}{validation['feedback']}{Colors.RESET}")
        
        identified_archetype = validation.get('archetype', 'unknown')
        
        # Select archetype object for display
        archetype = ARCHETYPES.get(identified_archetype.lower(), get_random_archetype())
        self.ui.show_archetype_moment(archetype)
        
        # STEP 4: Transmutation phase
        print(f"\n{Colors.BRIGHT_YELLOW}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_YELLOW}STEP 3: TRANSMUTE THE CONSTRAINT{Colors.RESET}")
        print(f"{Colors.BRIGHT_YELLOW}{'═' * 60}{Colors.RESET}\n")
        
        print(f"{Colors.CYAN}Your Situation:{Colors.RESET}")
        print(f"  {Colors.DIM}{situation[:200]}{'...' if len(situation) > 200 else ''}{Colors.RESET}\n")
        
        print(f"{Colors.CYAN}Your Constraint:{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}{user_constraint}{Colors.RESET}\n")
        
        # Use level-based transmutation target (same formula as regular training)
        target_transmutations = self._get_transmutation_target(level)
        
        transmutations = []
        durations = []
        rejected_count = 0
        max_rejections = 3
        total_time_limit = 90  # 90 seconds TOTAL
        
        print(f"\n{Colors.BRIGHT_CYAN}{'─' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}⏱️  TOTAL TIME: 90 SECONDS for {target_transmutations} transmutation(s){Colors.RESET}")
        print(f"{Colors.DIM}That's ~{90 // target_transmutations} seconds per transmutation. Build velocity!{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'─' * 60}{Colors.RESET}\n")
        
        start_time = time.time()
        
        while len(transmutations) < target_transmutations:
            elapsed = time.time() - start_time
            remaining = total_time_limit - elapsed
            
            # Check if time has expired
            if remaining <= 0:
                print(f"\n{Colors.RED}⏱️  TIME EXPIRED! Only {len(transmutations)}/{target_transmutations} transmutations completed.{Colors.RESET}")
                break
            
            print(f"\n{Colors.YELLOW}⏱️  {remaining:.0f}s remaining | Transmutation {len(transmutations) + 1}/{target_transmutations}{Colors.RESET}")
            
            trans, duration = self.ui.get_transmutation_input(
                "Transmute:",
                len(transmutations) + 1,
                target_transmutations,
                time_limit=remaining
            )
            
            if not trans.strip():
                continue
            
            # Check for similarity to existing transmutations
            if self._is_too_similar(trans, transmutations):
                rejected_count += 1
                print(f"{Colors.RED}❌ REJECTED: Too similar. ({rejected_count} rejections) Try a different angle!{Colors.RESET}")
                
                if rejected_count >= max_rejections:
                    print(f"{Colors.RED}⚠️  {rejected_count}+ rejections. Diverge your thinking!{Colors.RESET}")
                continue
            
            # Valid distinct transmutation
            transmutations.append(trans)
            durations.append(duration)
            print(f"{Colors.GREEN}✓ {len(transmutations)}/{target_transmutations} accepted ({duration:.1f}s){Colors.RESET}")
        
        if not transmutations:
            print(f"\n{Colors.RED}No transmutations provided. Session cancelled.{Colors.RESET}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")
            return
        
        # Meta-reflection
        print(f"\n{Colors.BRIGHT_CYAN}{'─' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}Meta-Cognitive Reflection{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'─' * 60}{Colors.RESET}\n")
        print(f"{Colors.CYAN}How did identifying YOUR OWN constraint change your thinking?{Colors.RESET}")
        meta_reflection = input(f"\001{Colors.BRIGHT_WHITE}\002❯ \001{Colors.RESET}\002")
        
        # Create a pseudo-scenario for evaluation
        real_life_scenario = ConstraintScenario(
            title="Real Life Constraint",
            archetype=identified_archetype,
            situation=situation,
            hidden_constraint=user_constraint,
            explicit_constraint=None,
            emotional_hook="This is your actual life.",
            hint="You identified this yourself.",
            target_transmutations=target_transmutations,
            difficulty_level=level,
            personal_relevance_score=1.0
        )
        
        # Evaluate session
        print(f"\n{Colors.CYAN}Analyzing your transmutations...{Colors.RESET}")
        time.sleep(1.5)
        
        evaluation = self.judge.evaluate_session(
            transmutations,
            real_life_scenario.to_dict(),
            user_profile,
            level,
            time_taken=sum(durations),
            meta_reflection=meta_reflection
        )
        
        # Show results
        self._display_session_results(evaluation, real_life_scenario)
        
        # Store in memory
        self._store_session(
            real_life_scenario,
            transmutations,
            evaluation,
            level,
            meta_reflection
        )
        
        # Level progress
        new_total_sessions = stats['total_sessions'] + 1
        new_avg_score = ((stats['average_score'] * stats['total_sessions']) + evaluation.session_score) / new_total_sessions
        new_level = self.memory._calculate_level(new_total_sessions, new_avg_score)
        
        sessions_for_100 = max(1, (100 - new_avg_score / 10) * 2)
        progress = min(1.0, new_total_sessions / sessions_for_100)
        
        self.ui.show_level_progress(level, new_level, progress)
        
        if new_level > level:
            print(f"\n{Colors.BRIGHT_GREEN}{'═' * 60}{Colors.RESET}")
            print(f"{Colors.BRIGHT_GREEN}⬆️  LEVEL UP! {level} → {new_level}{Colors.RESET}")
            print(f"{Colors.BRIGHT_GREEN}{'═' * 60}{Colors.RESET}")
        
        input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
    
    def _validate_real_life_constraint(self, situation: str, user_constraint: str, level: int) -> Dict:
        """Validate that user identified a real constraint in their situation"""
        
        prompt = f"""You are a C2A (Constraint-to-Advantage) master validator.

A Level {level} user has described their life situation and identified what they believe is the constraint.

THEIR SITUATION:
{situation}

THEIR CONSTRAINT IDENTIFICATION:
{user_constraint}

Your task: Evaluate if they correctly identified a REAL constraint.

Criteria:
1. Is there actually a constraint present in the situation they described?
2. Did they identify the CORE constraint (not a symptom or side effect)?
3. Did they correctly classify the archetype? (Scarcity, Velocity, Asymmetry, Friction, Paradox)
4. Is their identification specific enough to be actionable?

For Level {level}, be {"moderately strict" if level < 70 else "very strict"} - they should demonstrate constraint-seeing ability.

Respond in JSON:
{{
    "is_valid": true/false,
    "archetype": "the archetype they identified or should have identified",
    "feedback": "explanation of why valid/invalid",
    "suggested_constraint": "if invalid, suggest a better constraint identification (or null if valid)",
    "constraint_quality_score": 0-100
}}
"""

        try:
            result_text = self.llm.chat(prompt)
            
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                return json.loads(result_text[json_start:json_end])
            else:
                # Default to accepting if LLM doesn't return proper JSON
                return {
                    'is_valid': True,
                    'archetype': 'unknown',
                    'feedback': 'Constraint accepted.',
                    'constraint_quality_score': 70
                }
                
        except Exception as e:
            # On error, be lenient
            return {
                'is_valid': True,
                'archetype': 'unknown',
                'feedback': 'Constraint accepted (validation unavailable).',
                'constraint_quality_score': 60
            }

    def _display_session_results(self, evaluation: SessionEvaluation, scenario: ConstraintScenario):
        """Display session results beautifully - streamlined view"""
        
        # Best transmutation score
        best = evaluation.best_transmutation()
        
        # Show score reveal (includes component breakdown)
        self.ui.show_score_reveal(best.to_dict())
        
        time.sleep(1.5)
        
        # Show feedback panel (what worked + growth edge)
        self.ui.show_feedback_panel(best.to_dict())
        
        # Compact session summary - just the key info, no redundant coaching
        print(f"\n{Colors.DIM}{'─' * 60}{Colors.RESET}")
        print(f"{Colors.DIM}Session: {scenario.archetype} | Score: {evaluation.session_score}/100{Colors.RESET}")
        print(f"{Colors.DIM}{'─' * 60}{Colors.RESET}")
    
    def _store_session(
        self,
        scenario: ConstraintScenario,
        transmutations: List[str],
        evaluation: SessionEvaluation,
        level: int,
        meta_reflection: str,
        detection_data: Optional[Dict] = None
    ):
        """Store session in memory with detection tracking"""
        
        self.session_id += 1
        
        # Extract patterns
        patterns = [score.pattern_identified for score in evaluation.transmutation_scores]
        
        session_data = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'archetype': scenario.archetype,
            'scenario_title': scenario.title,
            'transmutations': transmutations,
            'meta_reflection': meta_reflection,
            'session_score': evaluation.session_score,
            'best_score': evaluation.best_transmutation().overall_score,
            'divergence_score': evaluation.divergence_score,
            'meta_cognitive_score': evaluation.meta_cognitive_score,
            'velocity_score': evaluation.velocity_score,
            'patterns': patterns,
            'breakthrough': any(s.breakthrough_moment for s in evaluation.transmutation_scores),
            # Detection tracking (Phase 2+)
            'detection_required': scenario.hidden_constraint is not None,
            'detection_success': detection_data.get('success', True) if detection_data else True,
            'detection_user_answer': detection_data.get('user_answer', '') if detection_data else '',
            'detection_correct_answer': scenario.hidden_constraint or '',
            'detection_correct_archetype': scenario.archetype,
            'detection_user_archetype': detection_data.get('user_archetype', '') if detection_data else '',
            'detection_partial_credit': detection_data.get('partial_credit', 100) if detection_data else 100,
            'detection_confusion_type': detection_data.get('confusion_type', None) if detection_data else None
        }
        
        self.memory.store_session(session_data)
        
        # Track session for AI Researcher
        self.all_sessions.append(session_data)
        
        # AI Researcher: Generate observations (cognitive scientist mode)
        # This adds ~$0.20-0.30 per session but generates valuable insights
        try:
            stats = self.memory.get_user_stats()
            user_profile = {
                'current_level': stats['current_level'],
                'total_sessions': stats['total_sessions'],
                'archetype_performance': stats['archetype_performance'],
                'average_score': stats['average_score']
            }
            
            print(f"\n{Colors.DIM}🔬 AI Researcher analyzing session...{Colors.RESET}")
            observations = self.researcher.observe_session(
                session_data,
                self.all_sessions,
                user_profile
            )
            
            # Show brief insight if available
            if observations.get('subject_observation'):
                subj = observations['subject_observation']
                if isinstance(subj, dict) and subj.get('recommendations'):
                    print(f"{Colors.DIM}📝 Research note recorded.{Colors.RESET}")
            
            # Generate full research report every 20 sessions
            if stats['total_sessions'] > 0 and stats['total_sessions'] % 20 == 0:
                print(f"\n{Colors.CYAN}📊 Generating research report (Session {stats['total_sessions']})...{Colors.RESET}")
                self.researcher.generate_research_report(self.all_sessions, user_profile)
                print(f"{Colors.GREEN}✓ Research report saved to research_notes/reports/{Colors.RESET}")
                
        except Exception as e:
            # Don't let researcher errors break training
            pass
    
    def _update_active_lesson(self, evaluation: SessionEvaluation, scenario: ConstraintScenario):
        """
        Update the active lesson based on session evaluation.
        
        Logic:
        1. Check if any transmutation applied the current lesson
        2. If score >= 70 AND lesson applied -> lesson mastered, create new from growth_edge
        3. If no current lesson -> create new from growth_edge
        4. Otherwise -> keep current lesson, record attempt
        """
        best = evaluation.best_transmutation()
        
        # Check if any transmutation applied the lesson
        any_lesson_applied = any(s.lesson_applied for s in evaluation.transmutation_scores)
        
        # Check if there's a current lesson
        if self.lesson_manager.has_active_lesson():
            # Record the attempt
            result = self.lesson_manager.record_attempt(
                evaluation.session_score,
                any_lesson_applied
            )
            
            if result['status'] == 'mastered':
                # Show mastery message
                print(f"\n{Colors.BRIGHT_GREEN}{'═' * 60}{Colors.RESET}")
                print(f"{Colors.BRIGHT_GREEN}🎓 LESSON MASTERED: {result['lesson_title']}{Colors.RESET}")
                print(f"{Colors.BRIGHT_GREEN}   Completed in {result['attempts']} attempts!{Colors.RESET}")
                print(f"{Colors.BRIGHT_GREEN}{'═' * 60}{Colors.RESET}")
                
                # Create new lesson from this session's growth_edge
                self.lesson_manager.create_lesson_from_feedback(
                    self.session_id,
                    best.growth_edge,
                    best.pattern_identified,
                    scenario.archetype,
                    evaluation.session_score
                )
                print(f"\n{Colors.CYAN}📚 New lesson assigned: {self.lesson_manager.current_lesson.title}{Colors.RESET}")
            else:
                # Still working on current lesson
                print(f"\n{Colors.YELLOW}📚 Active Lesson: {self.lesson_manager.current_lesson.title}{Colors.RESET}")
                print(f"{Colors.DIM}   Attempts: {result['attempts']} | Best: {result['best_score']} | Need: {result['threshold']}+ with application{Colors.RESET}")
        else:
            # No active lesson - create one from this session
            self.lesson_manager.create_lesson_from_feedback(
                self.session_id,
                best.growth_edge,
                best.pattern_identified,
                scenario.archetype,
                evaluation.session_score
            )
            print(f"\n{Colors.CYAN}📚 First lesson assigned: {self.lesson_manager.current_lesson.title}{Colors.RESET}")
            print(f"{Colors.DIM}   {self.lesson_manager.current_lesson.description[:100]}...{Colors.RESET}")
    
    def _select_training_archetype(self, user_profile: Dict, level: int) -> any:
        """
        Select optimal archetype for training
        
        Priority order:
        1. If in detection phase (11+), target weakest DETECTION archetype
        2. Otherwise target weakest TRANSMUTATION archetype
        3. For early levels, cycle through all
        """
        
        archetype_perf = user_profile.get('archetype_performance', {})
        
        if level <= 5:
            # Cycle through all archetypes for foundational exposure
            session_count = user_profile.get('total_sessions', 0)
            archetype_names = list(ARCHETYPES.keys())
            return ARCHETYPES[archetype_names[session_count % 5]]
        
        elif level >= 11:
            # In detection phase - prioritize weak DETECTION archetypes
            detection_weakness = self._get_weakest_detection_archetype()
            if detection_weakness and detection_weakness in ARCHETYPES:
                # 70% chance to target detection weakness, 30% for variety
                import random
                if random.random() < 0.7:
                    return ARCHETYPES[detection_weakness]
            
            # Fall back to transmutation weakness
            if archetype_perf:
                weakest = min(archetype_perf.items(), key=lambda x: x[1])
                return ARCHETYPES[weakest[0]]
            
            return get_random_archetype()
        
        elif archetype_perf:
            # Target weakest transmutation performance
            weakest = min(archetype_perf.items(), key=lambda x: x[1])
            return ARCHETYPES[weakest[0]]
        
        else:
            return get_random_archetype()
    
    def _get_weakest_detection_archetype(self) -> Optional[str]:
        """Get the archetype with lowest detection accuracy"""
        try:
            results = self.memory.collection.get(include=["metadatas"])
            
            if not results['metadatas']:
                return None
            
            # Filter to detection sessions
            detection_sessions = [
                m for m in results['metadatas']
                if m.get('detection_required', False)
            ]
            
            if not detection_sessions:
                return None
            
            # Calculate detection accuracy per archetype
            archetype_stats = {}
            for meta in detection_sessions:
                arch = meta.get('detection_correct_archetype', 'unknown')
                success = meta.get('detection_success', False)
                
                if arch not in archetype_stats:
                    archetype_stats[arch] = {'total': 0, 'correct': 0}
                
                archetype_stats[arch]['total'] += 1
                if success:
                    archetype_stats[arch]['correct'] += 1
            
            # Find archetype with lowest accuracy (min 3 attempts to be valid)
            valid_archetypes = {
                arch: stats['correct'] / stats['total']
                for arch, stats in archetype_stats.items()
                if stats['total'] >= 3
            }
            
            if valid_archetypes:
                weakest = min(valid_archetypes.items(), key=lambda x: x[1])
                return weakest[0]
            
            return None
            
        except Exception as e:
            return None
    
    def _identify_weak_archetypes(self, archetype_perf: Dict) -> List[str]:
        """Identify weak archetypes from performance"""
        weak = []
        for arch, score in archetype_perf.items():
            if score < 70:
                weak.append(arch)
        return weak
    
    def _get_transmutation_target(self, level: int) -> int:
        """
        Calculate required transmutations based on level.
        
        Scaling:
        - Level 1-9:   1 transmutation
        - Level 10-19: 2 transmutations
        - Level 20-29: 3 transmutations
        - Level 30-39: 4 transmutations
        - Level 40-49: 5 transmutations
        - Level 50-59: 6 transmutations
        - Level 60-69: 7 transmutations
        - Level 70-79: 8 transmutations
        - Level 80-89: 9 transmutations
        - Level 90+:   10 transmutations (Grandmaster level)
        """
        return max(1, min(10, (level // 10) + 1))
    
    def _is_too_similar(self, new_input: str, existing: List[str], threshold: float = 0.6) -> bool:
        """
        Check if new transmutation is too similar to existing ones.
        
        Uses Jaccard similarity on word sets + substring matching.
        Returns True if too similar (should be rejected).
        """
        if not new_input or not existing:
            return False
        
        new_lower = new_input.lower().strip()
        new_words = set(new_lower.split())
        
        # Remove common stopwords for better comparison
        stopwords = {'the', 'a', 'an', 'is', 'are', 'of', 'to', 'and', 'in', 'that', 'it', 'for', 'as', 'this', 'can', 'be', 'by'}
        new_words -= stopwords
        
        for ex in existing:
            ex_lower = ex.lower().strip()
            ex_words = set(ex_lower.split()) - stopwords
            
            # Exact match
            if new_lower == ex_lower:
                return True
            
            # Jaccard similarity
            if len(new_words) > 0 and len(ex_words) > 0:
                intersection = new_words.intersection(ex_words)
                union = new_words.union(ex_words)
                similarity = len(intersection) / len(union)
                
                if similarity > threshold:
                    return True
            
            # Substring check for longer inputs
            if len(new_lower) > 30 and len(ex_lower) > 30:
                if new_lower in ex_lower or ex_lower in new_lower:
                    return True
        
        return False
    
    def deep_analysis(self):
        """Deep RLM-powered analysis"""
        
        self.ui.clear_screen()
        
        print(f"\n{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}DEEP ANALYSIS (Recursive Language Model){Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}\n")
        
        print(f"{Colors.CYAN}Select analysis type:{Colors.RESET}\n")
        print(f"  {Colors.BRIGHT_WHITE}[1]{Colors.RESET} Plateau Pattern Analysis")
        print(f"  {Colors.BRIGHT_WHITE}[2]{Colors.RESET} Archetype Weakness Deep Dive")
        print(f"  {Colors.BRIGHT_WHITE}[3]{Colors.RESET} Breakthrough Moments Discovery")
        print(f"  {Colors.BRIGHT_WHITE}[4]{Colors.RESET} Personalized Training Plan")
        print(f"  {Colors.BRIGHT_WHITE}[5]{Colors.RESET} {Colors.YELLOW}⚠️  Detection Accuracy Analysis (Critical){Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}[6]{Colors.RESET} {Colors.YELLOW}Detection Training Recommendations{Colors.RESET}")
        print(f"  {Colors.BRIGHT_WHITE}[7]{Colors.RESET} Back to Menu")
        
        choice = input(f"\n{Colors.BRIGHT_WHITE}❯ {Colors.RESET}").strip()
        
        stats = self.memory.get_user_stats()
        user_profile = {
            'total_sessions': stats['total_sessions'],
            'archetype_performance': stats['archetype_performance']
        }
        
        if choice == "1":
            print(f"\n{Colors.CYAN}Analyzing plateau patterns across your history...{Colors.RESET}\n")
            result = self.rlm_analyzer.analyze_plateau_patterns(user_profile)
            self.ui.print_wrapped(result, prefix=Colors.WHITE, indent=2)
            
        elif choice == "2":
            print(f"\n{Colors.CYAN}Deep diving into archetype weaknesses...{Colors.RESET}\n")
            result = self.rlm_analyzer.find_archetype_weaknesses(user_profile)
            self.ui.print_wrapped(result, prefix=Colors.WHITE, indent=2)
            
        elif choice == "3":
            print(f"\n{Colors.CYAN}Discovering breakthrough moments...{Colors.RESET}\n")
            result = self.rlm_analyzer.discover_breakthrough_moments(user_profile)
            self.ui.print_wrapped(result, prefix=Colors.WHITE, indent=2)
            
        elif choice == "4":
            print(f"\n{Colors.CYAN}Generating personalized training plan...{Colors.RESET}\n")
            result = self.rlm_analyzer.generate_personalized_training_plan(user_profile)
            self.ui.print_wrapped(result, prefix=Colors.WHITE, indent=2)
            
        elif choice == "5":
            print(f"\n{Colors.YELLOW}{'═' * 60}{Colors.RESET}")
            print(f"{Colors.YELLOW}DETECTION ACCURACY ANALYSIS{Colors.RESET}")
            print(f"{Colors.YELLOW}{'═' * 60}{Colors.RESET}\n")
            print(f"{Colors.CYAN}Analyzing your constraint detection patterns...{Colors.RESET}\n")
            print(f"{Colors.DIM}This is the KEY diagnostic for installing C2A on any brain.{Colors.RESET}")
            print(f"{Colors.DIM}Detection accuracy determines if the system transfers.{Colors.RESET}\n")
            
            result = self.rlm_analyzer.analyze_detection_accuracy(user_profile)
            
            # Show quick stats first
            quick_stats = result.get('quick_stats', {})
            if quick_stats.get('total_detection_attempts', 0) > 0:
                print(f"{Colors.BRIGHT_CYAN}Quick Stats:{Colors.RESET}")
                print(f"  Total Detection Attempts: {quick_stats.get('total_detection_attempts', 0)}")
                print(f"  Overall Accuracy: {quick_stats.get('overall_accuracy', 0)}%")
                print(f"  Weakest Archetype: {quick_stats.get('weakest_archetype', 'N/A')} ({quick_stats.get('weakest_archetype_accuracy', 0)}%)")
                if quick_stats.get('most_common_confusion'):
                    print(f"  Most Common Confusion: {quick_stats.get('most_common_confusion', 'N/A')} ({quick_stats.get('most_common_confusion_count', 0)} times)")
                print()
            
            # Show detailed analysis
            self.ui.print_wrapped(result.get('analysis', 'No analysis available.'), prefix=Colors.WHITE, indent=2)
            
        elif choice == "6":
            print(f"\n{Colors.YELLOW}{'═' * 60}{Colors.RESET}")
            print(f"{Colors.YELLOW}DETECTION TRAINING RECOMMENDATIONS{Colors.RESET}")
            print(f"{Colors.YELLOW}{'═' * 60}{Colors.RESET}\n")
            print(f"{Colors.CYAN}Generating personalized detection training plan...{Colors.RESET}\n")
            
            result = self.rlm_analyzer.get_detection_training_recommendations(user_profile)
            self.ui.print_wrapped(result, prefix=Colors.WHITE, indent=2)
        
        if choice in ["1", "2", "3", "4", "5", "6"]:
            input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
    
    def research_dashboard(self):
        """
        Research Dashboard - View AI Researcher insights
        
        Displays:
        - Research summary statistics
        - Recent observations
        - Refinement proposals
        - Option to generate full report
        """
        self.ui.clear_screen()
        
        print(f"\n{Colors.BRIGHT_MAGENTA}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_MAGENTA}🔬 AI RESEARCH DASHBOARD{Colors.RESET}")
        print(f"{Colors.BRIGHT_MAGENTA}{'═' * 60}{Colors.RESET}\n")
        
        print(f"{Colors.DIM}The AI Researcher observes your training as a cognitive scientist,{Colors.RESET}")
        print(f"{Colors.DIM}generating insights about your cognition and C2A effectiveness.{Colors.RESET}\n")
        
        # Get research summary
        summary = self.researcher.get_research_summary()
        
        print(f"{Colors.BRIGHT_CYAN}Research Statistics:{Colors.RESET}\n")
        print(f"  📊 Sessions Observed:        {summary['total_sessions_observed']}")
        print(f"  📝 Subject Observations:     {summary['subject_observations']}")
        print(f"  📈 Pattern Observations:     {summary['pattern_observations']}")
        print(f"  🔧 System Observations:      {summary['system_observations']}")
        print(f"  💡 Theoretical Observations: {summary['theoretical_observations']}")
        print(f"  🚀 Refinement Proposals:     {summary['refinement_proposals']}")
        print(f"  📄 Research Reports:         {summary['total_reports']}")
        
        print(f"\n{Colors.BRIGHT_CYAN}{'─' * 60}{Colors.RESET}")
        
        # Get recent observations
        recent = self.researcher.get_latest_observations(3)
        
        if recent:
            print(f"\n{Colors.BRIGHT_YELLOW}Recent Research Notes:{Colors.RESET}\n")
            
            for obs in recent:
                session_id = obs.get('session_id', '?')
                timestamp = obs.get('timestamp', '')[:10]
                
                print(f"  {Colors.CYAN}Session {session_id} ({timestamp}):{Colors.RESET}")
                
                # Show subject observation snippet
                subj = obs.get('subject_observation')
                if subj:
                    if isinstance(subj, dict):
                        # Show recommendations if available
                        recs = subj.get('recommendations', [])
                        if recs:
                            print(f"    {Colors.DIM}Recommendation: {recs[0][:60]}...{Colors.RESET}")
                    elif isinstance(subj, str):
                        # Show first line
                        first_line = subj.split('\n')[0][:60]
                        print(f"    {Colors.DIM}{first_line}...{Colors.RESET}")
                
                # Note if there are system/theoretical observations
                if obs.get('system_observation'):
                    print(f"    {Colors.YELLOW}⚠ System observation recorded{Colors.RESET}")
                if obs.get('theoretical_observation'):
                    print(f"    {Colors.GREEN}💡 Theoretical insight recorded{Colors.RESET}")
                if obs.get('refinement_proposal'):
                    print(f"    {Colors.MAGENTA}🚀 Refinement proposal recorded{Colors.RESET}")
                
                print()
        else:
            print(f"\n{Colors.DIM}No research notes yet. Complete more sessions!{Colors.RESET}\n")
        
        # Get refinement proposals
        proposals = self.researcher.get_all_refinement_proposals()
        
        if proposals:
            print(f"{Colors.BRIGHT_CYAN}{'─' * 60}{Colors.RESET}")
            print(f"\n{Colors.BRIGHT_GREEN}Refinement Proposals ({len(proposals)} total):{Colors.RESET}\n")
            
            for p in proposals[-3:]:  # Show last 3
                print(f"  {Colors.CYAN}From Session {p['session_id']}:{Colors.RESET}")
                proposal_text = p['proposal']
                if isinstance(proposal_text, str):
                    # Extract title if present
                    lines = proposal_text.split('\n')
                    for line in lines[:3]:
                        if line.strip():
                            print(f"    {Colors.DIM}{line[:70]}{Colors.RESET}")
                print()
        
        # Menu options
        print(f"\n{Colors.BRIGHT_CYAN}{'─' * 60}{Colors.RESET}")
        print(f"\n{Colors.BRIGHT_WHITE}Options:{Colors.RESET}\n")
        print(f"  {Colors.CYAN}1{Colors.RESET} - Generate Full Research Report")
        print(f"  {Colors.CYAN}2{Colors.RESET} - View Latest Session Notes (detailed)")
        print(f"  {Colors.CYAN}3{Colors.RESET} - View All Refinement Proposals")
        print(f"  {Colors.CYAN}4{Colors.RESET} - Return to Main Menu")
        
        choice = input(f"\n{Colors.BRIGHT_WHITE}❯ {Colors.RESET}").strip()
        
        if choice == "1":
            self._generate_research_report()
        elif choice == "2":
            self._view_latest_notes()
        elif choice == "3":
            self._view_all_proposals()
        # else return to menu
    
    def _generate_research_report(self):
        """Generate a comprehensive research report"""
        stats = self.memory.get_user_stats()
        
        if stats['total_sessions'] < 5:
            print(f"\n{Colors.YELLOW}Need at least 5 sessions for a meaningful report.{Colors.RESET}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")
            return
        
        print(f"\n{Colors.CYAN}Generating comprehensive research report...{Colors.RESET}")
        print(f"{Colors.DIM}This may take a minute...{Colors.RESET}\n")
        
        user_profile = {
            'current_level': stats['current_level'],
            'total_sessions': stats['total_sessions'],
            'archetype_performance': stats['archetype_performance'],
            'average_score': stats['average_score']
        }
        
        try:
            report = self.researcher.generate_research_report(
                self.all_sessions,
                user_profile
            )
            
            print(f"\n{Colors.GREEN}{'═' * 60}{Colors.RESET}")
            print(f"{Colors.GREEN}RESEARCH REPORT GENERATED{Colors.RESET}")
            print(f"{Colors.GREEN}{'═' * 60}{Colors.RESET}\n")
            
            # Show first part of report
            print(report[:2000])
            if len(report) > 2000:
                print(f"\n{Colors.DIM}... (report continues - saved to research_notes/reports/){Colors.RESET}")
            
            print(f"\n{Colors.GREEN}✓ Full report saved to research_notes/reports/{Colors.RESET}")
            
        except Exception as e:
            print(f"{Colors.RED}Error generating report: {e}{Colors.RESET}")
        
        input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
    
    def _view_latest_notes(self):
        """View the most recent session notes in detail"""
        recent = self.researcher.get_latest_observations(1)
        
        if not recent:
            print(f"\n{Colors.YELLOW}No research notes yet.{Colors.RESET}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")
            return
        
        obs = recent[0]
        
        print(f"\n{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}SESSION {obs.get('session_id', '?')} RESEARCH NOTES{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}\n")
        
        # Show raw response if available
        if obs.get('raw_response'):
            print(obs['raw_response'][:3000])
            if len(obs.get('raw_response', '')) > 3000:
                print(f"\n{Colors.DIM}... (truncated){Colors.RESET}")
        else:
            # Show structured data
            for key in ['subject_observation', 'pattern_observation', 'system_observation', 
                       'theoretical_observation', 'refinement_proposal']:
                if obs.get(key):
                    print(f"\n{Colors.BRIGHT_YELLOW}{key.upper().replace('_', ' ')}:{Colors.RESET}")
                    content = obs[key]
                    if isinstance(content, dict):
                        print(json.dumps(content, indent=2)[:1000])
                    else:
                        print(str(content)[:1000])
        
        input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
    
    def _view_all_proposals(self):
        """View all refinement proposals"""
        proposals = self.researcher.get_all_refinement_proposals()
        
        if not proposals:
            print(f"\n{Colors.YELLOW}No refinement proposals yet.{Colors.RESET}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")
            return
        
        print(f"\n{Colors.BRIGHT_GREEN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_GREEN}ALL REFINEMENT PROPOSALS ({len(proposals)}){Colors.RESET}")
        print(f"{Colors.BRIGHT_GREEN}{'═' * 60}{Colors.RESET}\n")
        
        for p in proposals:
            print(f"{Colors.CYAN}Session {p['session_id']}:{Colors.RESET}")
            print(f"{p['proposal'][:500]}")
            print(f"\n{Colors.DIM}{'─' * 40}{Colors.RESET}\n")
        
        input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
    
    def view_progress(self):
        """View progress and statistics"""
        
        stats = self.memory.get_user_stats()
        
        self.ui.clear_screen()
        
        print(f"\n{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}YOUR PROGRESS{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}\n")
        
        level = stats['current_level']
        sessions = stats['total_sessions']
        avg_score = stats['average_score']
        
        print(f"  {Colors.CYAN}Current Level:{Colors.RESET} {level}/100")
        print(f"  {Colors.CYAN}Total Sessions:{Colors.RESET} {sessions}")
        print(f"  {Colors.CYAN}Average Score:{Colors.RESET} {avg_score:.1f}/100")
        
        # Calculate sessions needed for Level 100
        if avg_score > 0:
            sessions_for_100 = int((100 - avg_score / 10) * 2)
            sessions_remaining = max(0, sessions_for_100 - sessions)
            print(f"\n  {Colors.YELLOW}Sessions to Level 100:{Colors.RESET} ~{sessions_remaining} more")
            print(f"  {Colors.DIM}(With current avg score of {avg_score:.1f}){Colors.RESET}")
        
        # Level milestones - Updated to reflect training phases
        print(f"\n{Colors.BRIGHT_CYAN}Training Phases:{Colors.RESET}\n")
        milestones = [
            (1, "Phase 1: Transmutation Training (constraints given)", 1 <= level <= 10),
            (11, "Phase 2: Detection + Transmutation (constraints hidden)", 11 <= level <= 30),
            (31, "Phase 3: Personal Domain Mastery", 31 <= level <= 50),
            (51, "Phase 4: Real Life Mode (you find constraints)", level >= 51),
            (90, "Grandmaster Territory", level >= 90),
            (100, "Physics Arena Unlocks", level >= 100),
        ]
        for lvl, desc, achieved in milestones:
            status = f"{Colors.GREEN}✓{Colors.RESET}" if achieved else f"{Colors.DIM}○{Colors.RESET}"
            color = Colors.GREEN if achieved else Colors.DIM
            print(f"  {status} Level {lvl}: {color}{desc}{Colors.RESET}")
        
        print(f"\n{Colors.BRIGHT_CYAN}Archetype Performance:{Colors.RESET}\n")
        
        for arch_name, arch_obj in ARCHETYPES.items():
            score = stats['archetype_performance'].get(arch_name, 0)
            bar_width = 20
            filled = int((score / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            
            print(f"  {arch_obj.symbol} {arch_name.capitalize():.<15} {score:>5.1f}  {bar}")
        
        # Formula explanation
        print(f"\n{Colors.DIM}{'─' * 60}{Colors.RESET}")
        print(f"{Colors.DIM}Level Formula: (Sessions × 0.5) + (Avg Score ÷ 10){Colors.RESET}")
        print(f"{Colors.DIM}Your calculation: ({sessions} × 0.5) + ({avg_score:.1f} ÷ 10) = {level}{Colors.RESET}")
        
        input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
    
    def show_archetype_gallery(self):
        """Show all archetypes"""
        
        self.ui.clear_screen()
        
        print(f"\n{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}THE FIVE ARCHETYPAL CONSTRAINTS{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}\n")
        
        for archetype in ARCHETYPES.values():
            print(f"{archetype.color_code}{archetype.symbol} {archetype.name.upper()}{Colors.RESET}")
            print(f"{Colors.DIM}{archetype.essence}{Colors.RESET}\n")
        
        input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")
    
    def set_domain_menu(self):
        """Set user's domain for personalized training"""
        
        self.ui.clear_screen()
        
        current_domain = self._get_user_domain()
        
        print(f"\n{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}SET YOUR DOMAIN{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}\n")
        
        print(f"{Colors.WHITE}Your domain determines the context for personalized scenarios.{Colors.RESET}")
        print(f"{Colors.WHITE}At Level 31+, scenarios will be generated specifically for YOUR domain.{Colors.RESET}\n")
        
        print(f"{Colors.CYAN}Current Domain:{Colors.RESET} {Colors.BRIGHT_WHITE}{current_domain}{Colors.RESET}\n")
        
        print(f"{Colors.DIM}Examples:{Colors.RESET}")
        print(f"  • software engineering")
        print(f"  • hotel business")
        print(f"  • music production")
        print(f"  • student life")
        print(f"  • freelance design")
        print(f"  • startup founder")
        print(f"  • healthcare professional\n")
        
        print(f"{Colors.CYAN}Enter your domain (or press Enter to keep current):{Colors.RESET}")
        new_domain = input(f"\001{Colors.BRIGHT_WHITE}\002❯ \001{Colors.RESET}\002").strip()
        
        if new_domain:
            self._set_user_domain(new_domain)
            print(f"\n{Colors.GREEN}✓ Domain updated to: {new_domain}{Colors.RESET}")
        else:
            print(f"\n{Colors.DIM}Domain unchanged.{Colors.RESET}")
        
        input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
    
    def physics_arena(self):
        """Launch Physics Arena (Level 100 unlock)"""
        
        self.ui.clear_screen()
        
        print(f"\n{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}⚡ PHYSICS ARENA - FAR TRANSFER VALIDATION{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'═' * 60}{Colors.RESET}\n")
        
        stats = self.memory.get_user_stats()
        current_level = stats['current_level']
        
        print(f"{Colors.GOLD}🏆 LEVEL 100 UNLOCKED - CERTIFIED C2A MASTER{Colors.RESET}\n")
        
        print(f"{Colors.CYAN}Welcome to the Physics Arena - where constraint thinking meets reality.{Colors.RESET}\n")
        
        print(f"{Colors.WHITE}In this arena, you solve physics problems with:{Colors.RESET}")
        print(f"  ✅ Pure constraint logic (your training)")
        print(f"  ✅ LLM handling technical jargon")
        print(f"  ✅ NO physics expertise required\n")
        
        print(f"{Colors.BRIGHT_YELLOW}How it works:{Colors.RESET}")
        print(f"  1. You see a physics constraint")
        print(f"  2. You describe a transmutation in English")
        print(f"  3. LLM writes Python physics code to test your idea")
        print(f"  4. Physics engine simulates reality")
        print(f"  5. Result: ✅ SUCCESS or ❌ FAILURE\n")
        
        print(f"{Colors.BRIGHT_MAGENTA}This proves far transfer:{Colors.RESET}")
        print(f"  • You solve problems in domains you never studied")
        print(f"  • Constraint patterns transfer universally")
        print(f"  • LLM bridges the technical gap")
        print(f"  • Your logic + AI implementation = Solutions\n")
        
        print(f"{Colors.DIM}The Physics Arena is implemented in c2a_game_physics.py{Colors.RESET}")
        print(f"{Colors.DIM}To launch: streamlit run c2a_game_physics.py{Colors.RESET}\n")
        
        print(f"{Colors.BRIGHT_GREEN}Example Problem:{Colors.RESET}")
        print(f"{Colors.CYAN}  Constraint: Heavy block falling, floor is lava, you have 3 beams{Colors.RESET}")
        print(f"{Colors.WHITE}  Your Input: 'Use falling momentum to compress beams into arch'{Colors.RESET}")
        print(f"{Colors.GREEN}  LLM: *generates Pymunk physics simulation*{Colors.RESET}")
        print(f"{Colors.BRIGHT_GREEN}  Result: ✅ SUCCESS - Arch redirects force horizontally{Colors.RESET}\n")
        
        choice = input(f"{Colors.BRIGHT_WHITE}Launch Physics Arena? (y/n): {Colors.RESET}").strip().lower()
        
        if choice == 'y':
            print(f"\n{Colors.CYAN}Launching Physics Arena...{Colors.RESET}")
            import subprocess
            import os
            
            try:
                # Check if streamlit is installed
                subprocess.run(["streamlit", "--version"], capture_output=True, check=True)
                
                # Launch the physics game
                physics_file = Path(__file__).parent / "c2a_game_physics.py"
                if physics_file.exists():
                    print(f"{Colors.GREEN}Starting Streamlit...{Colors.RESET}")
                    subprocess.Popen(["streamlit", "run", str(physics_file)])
                    print(f"{Colors.BRIGHT_GREEN}✓ Physics Arena launched in browser!{Colors.RESET}\n")
                else:
                    print(f"{Colors.RED}Error: c2a_game_physics.py not found{Colors.RESET}")
                    
            except subprocess.CalledProcessError:
                print(f"\n{Colors.YELLOW}Streamlit not installed.{Colors.RESET}")
                print(f"{Colors.CYAN}Install with: pip install streamlit pymunk{Colors.RESET}")
                print(f"{Colors.CYAN}Then run: streamlit run c2a_game_physics.py{Colors.RESET}\n")
            except Exception as e:
                print(f"\n{Colors.RED}Error launching: {e}{Colors.RESET}\n")
        
        input(f"{Colors.DIM}Press Enter to return to menu...{Colors.RESET}")
    
    def exit_gracefully(self):
        """Exit with style"""
        
        self.ui.clear_screen()
        
        print(f"\n\n")
        message = "The constraint is not the enemy."
        message2 = "The constraint is the way."
        
        print(Colors.gradient_text(message.center(self.ui.width), 51, 129))
        print(Colors.gradient_text(message2.center(self.ui.width), 51, 129))
        print(f"\n\n")
        
        time.sleep(2)


def main():
    """Main entry point"""
    
    print(f"{Colors.CYAN}Initializing C2A Elegant...{Colors.RESET}")
    
    try:
        system = C2AElegant(model="qwen2.5:32b")
        system.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Session interrupted. Your progress is saved.{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
