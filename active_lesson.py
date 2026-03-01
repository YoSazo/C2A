"""
Active Lesson System - The Curriculum That Follows You

This module implements the "lesson persistence" concept:
- Each session generates a growth_edge (what to work on)
- That becomes your Active Lesson
- The lesson is displayed before each session
- The judge checks if you applied it
- The lesson persists until you demonstrate mastery (score 70+ with application)

Philosophy: "The lesson follows you until you prove you've learned it."
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List


@dataclass
class ActiveLesson:
    """A lesson the user is currently working on"""
    lesson_id: str
    created_at: str
    source_session_id: int
    
    # The lesson itself
    title: str  # Short name like "The Removal Test"
    description: str  # Full explanation
    practice_question: str  # Question to ask before transmuting
    
    # Tracking
    archetype_origin: str  # Which archetype this came from
    attempts: int  # How many sessions they've tried with this lesson
    best_score_while_active: int  # Best score achieved while working on this
    demonstrated: bool  # Have they shown mastery?
    demonstrated_at: Optional[str]  # When they mastered it
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ActiveLesson':
        return cls(**data)


class ActiveLessonManager:
    """Manages the active lesson system"""
    
    MASTERY_THRESHOLD = 70  # Score needed to "pass" a lesson
    
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir:
            self.data_dir = data_dir
        else:
            self.data_dir = Path(__file__).parent / "memory_data"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.lesson_file = self.data_dir / "active_lesson.json"
        self.history_file = self.data_dir / "lesson_history.json"
        
        self.current_lesson: Optional[ActiveLesson] = None
        self.lesson_history: List[Dict] = []
        
        self._load()
    
    def _load(self):
        """Load current lesson and history from disk"""
        # Load current lesson
        if self.lesson_file.exists():
            try:
                with open(self.lesson_file, 'r') as f:
                    data = json.load(f)
                    if data:
                        self.current_lesson = ActiveLesson.from_dict(data)
            except Exception as e:
                print(f"Error loading active lesson: {e}")
                self.current_lesson = None
        
        # Load history
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.lesson_history = json.load(f)
            except:
                self.lesson_history = []
    
    def _save(self):
        """Save current lesson and history to disk"""
        # Save current lesson
        with open(self.lesson_file, 'w') as f:
            if self.current_lesson:
                json.dump(self.current_lesson.to_dict(), f, indent=2)
            else:
                json.dump(None, f)
        
        # Save history
        with open(self.history_file, 'w') as f:
            json.dump(self.lesson_history, f, indent=2)
    
    def get_current_lesson(self) -> Optional[ActiveLesson]:
        """Get the current active lesson"""
        return self.current_lesson
    
    def has_active_lesson(self) -> bool:
        """Check if there's an active lesson"""
        return self.current_lesson is not None and not self.current_lesson.demonstrated
    
    def create_lesson_from_feedback(
        self,
        session_id: int,
        growth_edge: str,
        pattern_identified: str,
        archetype: str,
        score: int
    ) -> ActiveLesson:
        """
        Create a new active lesson from session feedback.
        
        Only creates if:
        1. No current lesson exists, OR
        2. Current lesson has been demonstrated (mastered)
        
        Args:
            session_id: The session this feedback came from
            growth_edge: The growth_edge from the judge
            pattern_identified: The pattern name from the judge
            archetype: The archetype of the session
            score: The session score
        """
        # Generate a good title from the pattern
        title = self._generate_lesson_title(pattern_identified, growth_edge)
        
        # Generate a practice question
        practice_question = self._generate_practice_question(growth_edge)
        
        lesson = ActiveLesson(
            lesson_id=f"lesson_{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            created_at=datetime.now().isoformat(),
            source_session_id=session_id,
            title=title,
            description=growth_edge,
            practice_question=practice_question,
            archetype_origin=archetype,
            attempts=0,
            best_score_while_active=score,
            demonstrated=False,
            demonstrated_at=None
        )
        
        # If there's an existing lesson that was demonstrated, archive it
        if self.current_lesson and self.current_lesson.demonstrated:
            self._archive_lesson(self.current_lesson)
        
        # Set new lesson
        self.current_lesson = lesson
        self._save()
        
        return lesson
    
    def _generate_lesson_title(self, pattern: str, growth_edge: str) -> str:
        """Generate a memorable title for the lesson"""
        # Common patterns to title mappings
        pattern_lower = pattern.lower()
        growth_lower = growth_edge.lower()
        
        # Check pattern first
        if 'bridge' in pattern_lower or 'coping' in pattern_lower:
            return "The Removal Test"
        elif 'substitution' in pattern_lower:
            return "Transmute, Don't Substitute"
        elif 'surface' in pattern_lower or 'symptom' in pattern_lower:
            return "Root vs Symptom"
        elif 'avoid' in pattern_lower or 'escape' in pattern_lower:
            return "Embrace, Don't Escape"
        elif 'obvious' in pattern_lower or 'first' in pattern_lower:
            return "Beyond First Instinct"
        elif 'reactive' in pattern_lower:
            return "Proactive Transmutation"
        elif 'single' in pattern_lower or 'one' in pattern_lower:
            return "Multiple Angles"
        
        # Check growth_edge content for common themes
        if 'generate' in growth_lower or 'generates' in growth_lower:
            return "What The Constraint Creates"
        elif 'fuel' in growth_lower or 'pressure' in growth_lower:
            return "Pressure As Fuel"
        elif 'scarcity' in growth_lower or 'abundance' in growth_lower:
            return "Scarcity's Hidden Gift"
        elif 'alternative' in growth_lower and 'coping' in growth_lower:
            return "Beyond Coping"
        elif 'removal' in growth_lower or 'removing' in growth_lower:
            return "The Removal Test"
        elif 'advantage' in growth_lower:
            return "Finding The Advantage"
        elif 'identity' in growth_lower:
            return "Beyond Identity"
        elif 'velocity' in growth_lower or 'speed' in growth_lower:
            return "Constraint-Driven Speed"
        elif 'force' in growth_lower:
            return "What It Forces"
        else:
            # Fallback: use pattern name if it's short enough
            if len(pattern) <= 30 and pattern:
                return pattern.title()
            # Last resort: generic but meaningful
            return "The Core Transmutation"
    
    def _generate_practice_question(self, growth_edge: str) -> str:
        """Generate a question to ask before transmuting"""
        growth_lower = growth_edge.lower()
        
        if 'removal test' in growth_lower or 'removing' in growth_lower:
            return "If I removed this constraint, would my advantage also disappear?"
        elif 'pressure' in growth_lower or 'force' in growth_lower:
            return "How can I use this pressure as fuel, not just survive it?"
        elif 'generate' in growth_lower:
            return "What does this constraint GENERATE that its absence cannot?"
        elif 'symptom' in growth_lower or 'root' in growth_lower:
            return "Am I addressing the root constraint or just a symptom?"
        elif 'novel' in growth_lower or 'different' in growth_lower:
            return "What angle haven't I tried yet?"
        else:
            return "Am I truly transmuting, or just coping with this constraint?"
    
    def record_attempt(self, score: int, lesson_applied: bool) -> Dict:
        """
        Record an attempt at the current lesson.
        
        Args:
            score: The session score
            lesson_applied: Whether the judge determined the lesson was applied
            
        Returns:
            Dict with status: 'no_lesson', 'continue', 'mastered'
        """
        if not self.current_lesson:
            return {'status': 'no_lesson'}
        
        self.current_lesson.attempts += 1
        
        if score > self.current_lesson.best_score_while_active:
            self.current_lesson.best_score_while_active = score
        
        # Check for mastery: score >= threshold AND lesson was applied
        if score >= self.MASTERY_THRESHOLD and lesson_applied:
            self.current_lesson.demonstrated = True
            self.current_lesson.demonstrated_at = datetime.now().isoformat()
            self._save()
            return {
                'status': 'mastered',
                'attempts': self.current_lesson.attempts,
                'lesson_title': self.current_lesson.title
            }
        
        self._save()
        return {
            'status': 'continue',
            'attempts': self.current_lesson.attempts,
            'best_score': self.current_lesson.best_score_while_active,
            'threshold': self.MASTERY_THRESHOLD
        }
    
    def _archive_lesson(self, lesson: ActiveLesson):
        """Archive a completed lesson to history"""
        self.lesson_history.append({
            **lesson.to_dict(),
            'archived_at': datetime.now().isoformat()
        })
        self._save()
    
    def get_lesson_for_prompt(self) -> str:
        """Get a formatted string of the current lesson for LLM prompts"""
        if not self.current_lesson or self.current_lesson.demonstrated:
            return ""
        
        return f"""
ACTIVE LESSON FOR THIS USER:
Title: {self.current_lesson.title}
Description: {self.current_lesson.description}
Practice Question: {self.current_lesson.practice_question}
Attempts so far: {self.current_lesson.attempts}
Best score while working on this: {self.current_lesson.best_score_while_active}

The user should be working on this lesson. Check if they apply it in their transmutation.
"""
    
    def get_lesson_display(self) -> Optional[str]:
        """Get a formatted display of the current lesson for the UI"""
        if not self.current_lesson or self.current_lesson.demonstrated:
            return None
        
        lesson = self.current_lesson
        
        # Wrap description into multiple lines
        desc_lines = self._wrap_text_multiline(lesson.description, 59)
        question_lines = self._wrap_text_multiline(lesson.practice_question, 53)
        
        # Build the display
        lines = []
        lines.append("╔═══════════════════════════════════════════════════════════════╗")
        lines.append(f"║  🎯 YOUR ACTIVE LESSON                                        ║")
        lines.append("╠═══════════════════════════════════════════════════════════════╣")
        lines.append(f"║  {lesson.title:<61} ║")
        lines.append("║                                                               ║")
        
        # Add description lines
        for line in desc_lines:
            lines.append(f"║  {line:<61} ║")
        
        lines.append("║                                                               ║")
        lines.append("║  ┌─────────────────────────────────────────────────────────┐  ║")
        lines.append("║  │ Before you transmute, ask yourself:                     │  ║")
        
        # Add question lines
        for line in question_lines:
            lines.append(f"║  │ \"{line:<55}\" │  ║")
        
        lines.append("║  └─────────────────────────────────────────────────────────┘  ║")
        lines.append("║                                                               ║")
        lines.append(f"║  Attempts: {lesson.attempts:<3} | Best Score: {lesson.best_score_while_active:<3} | Need: {self.MASTERY_THRESHOLD}+ with application  ║")
        lines.append("╚═══════════════════════════════════════════════════════════════╝")
        
        return "\n".join(lines)
    
    def _wrap_text_multiline(self, text: str, width: int) -> list:
        """Wrap text into multiple lines that fit within width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= width:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Limit to 4 lines max to keep display compact
        if len(lines) > 4:
            lines = lines[:4]
            lines[-1] = lines[-1][:width-3] + "..."
        
        return lines if lines else [""]
    
    def _wrap_text(self, text: str, width: int) -> str:
        """Wrap text to fit within width (single line, truncate)"""
        if len(text) <= width:
            return text
        return text[:width-3] + "..."
    
    def get_mastered_lessons_count(self) -> int:
        """Get count of mastered lessons"""
        return len([l for l in self.lesson_history if l.get('demonstrated', False)])
    
    def get_stats(self) -> Dict:
        """Get statistics about lesson learning"""
        mastered = self.get_mastered_lessons_count()
        total_attempts = sum(l.get('attempts', 0) for l in self.lesson_history)
        
        return {
            'lessons_mastered': mastered,
            'total_attempts_across_lessons': total_attempts,
            'current_lesson': self.current_lesson.title if self.current_lesson else None,
            'current_attempts': self.current_lesson.attempts if self.current_lesson else 0
        }
