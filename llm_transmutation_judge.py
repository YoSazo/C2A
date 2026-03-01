#!/usr/bin/env python3
"""
LLM Transmutation Judge - Sophisticated Evaluation System

This judges the QUALITY OF THINKING, not keyword matching.
It evaluates novelty, sophistication, practicality, and growth trajectory.

Philosophy: "Judge the dance, not the dancer's resemblance to a template."
"""

import json
from typing import Dict, List, Optional, Tuple

from llm_client import LLMClient, create_client_from_env
from dataclasses import dataclass, asdict
from datetime import datetime

from constraint_archetypes import ARCHETYPES


@dataclass
class TransmutationScore:
    """Structured score for a transmutation"""
    overall_score: int  # 0-100
    reframing_score: int  # 0-30
    novelty_score: int  # 0-25
    practicality_score: int  # 0-25
    sophistication_score: int  # 0-20
    
    # Qualitative feedback
    what_worked: str
    what_missed: str
    growth_edge: str
    pattern_identified: str
    
    # Comparative insights
    vs_user_history: str
    breakthrough_moment: bool
    
    # Active lesson tracking
    lesson_applied: bool  # Did they apply their active lesson?
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def __str__(self) -> str:
        return f"""
╔══════════════════════════════════════════════════════════════╗
║  TRANSMUTATION ANALYSIS                                      ║
╚══════════════════════════════════════════════════════════════╝

  Overall Score: {self.overall_score}/100  {'🔥' if self.overall_score >= 85 else '⭐' if self.overall_score >= 70 else '✓' if self.overall_score >= 60 else '→'}

  Component Scores:
  ├─ Reframing:       {self.reframing_score}/30    {self._bar(self.reframing_score, 30)}
  ├─ Novelty:         {self.novelty_score}/25    {self._bar(self.novelty_score, 25)}
  ├─ Practicality:    {self.practicality_score}/25    {self._bar(self.practicality_score, 25)}
  └─ Sophistication:  {self.sophistication_score}/20    {self._bar(self.sophistication_score, 20)}

  ✓ {self._wrap(self.what_worked, indent=2)}

  → {self._wrap(self.growth_edge, indent=2)}

  🔮 Pattern: {self.pattern_identified}
  {'  🌟 BREAKTHROUGH MOMENT' if self.breakthrough_moment else ''}
"""
    
    def _bar(self, score: int, max_score: int, width: int = 20) -> str:
        """Generate a visual bar for score"""
        filled = int((score / max_score) * width)
        bar = '█' * filled + '░' * (width - filled)
        return bar
    
    def _wrap(self, text: str, indent: int = 0, width: int = 60) -> str:
        """Wrap text with indentation"""
        import textwrap
        lines = textwrap.wrap(text, width=width)
        indent_str = ' ' * indent
        return '\n'.join([indent_str + line for line in lines])


@dataclass
class SessionEvaluation:
    """Evaluation of an entire session (multiple transmutations)"""
    transmutation_scores: List[TransmutationScore]
    session_score: int  # Overall session score
    divergence_score: int  # How diverse were the transmutations?
    meta_cognitive_score: int  # Evidence of meta-thinking
    velocity_score: int  # Speed of generation
    
    coaching_synthesis: str
    level_recommendation: int  # Suggested next level
    archetype_feedback: Dict[str, str]  # Feedback per archetype
    
    def best_transmutation(self) -> TransmutationScore:
        """Return the highest scoring transmutation"""
        return max(self.transmutation_scores, key=lambda t: t.overall_score)
    
    def to_dict(self) -> Dict:
        return {
            'transmutation_scores': [t.to_dict() for t in self.transmutation_scores],
            'session_score': self.session_score,
            'divergence_score': self.divergence_score,
            'meta_cognitive_score': self.meta_cognitive_score,
            'velocity_score': self.velocity_score,
            'coaching_synthesis': self.coaching_synthesis,
            'level_recommendation': self.level_recommendation,
            'archetype_feedback': self.archetype_feedback
        }


class TransmutationJudge:
    """LLM-powered judge that evaluates constraint transmutations"""

    def __init__(self, model: str = "qwen2.5:32b", llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or create_client_from_env()
        self.model = model  # retained for legacy/debug output
        self.evaluation_history = []
    
    def evaluate_transmutation(
        self,
        transmutation: str,
        scenario: Dict,
        user_profile: Dict,
        level: int,
        active_lesson: str = ""
    ) -> TransmutationScore:
        """
        Evaluate a single transmutation
        
        Args:
            transmutation: User's constraint-to-advantage transmutation
            scenario: The scenario context
            user_profile: User's history and patterns
            level: Current mastery level
            active_lesson: The active lesson prompt (if any)
        """
        
        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(
            transmutation, scenario, user_profile, level, active_lesson
        )
        
        # Get LLM evaluation
        response = self._query_llm(prompt)
        
        # Parse into structured score
        score = self._parse_evaluation_response(response, level)
        
        return score
    
    def evaluate_session(
        self,
        transmutations: List[str],
        scenario: Dict,
        user_profile: Dict,
        level: int,
        time_taken: Optional[float] = None,
        meta_reflection: Optional[str] = None,
        active_lesson: str = ""
    ) -> SessionEvaluation:
        """
        Evaluate an entire training session
        
        Args:
            transmutations: List of user's transmutations
            scenario: The scenario they worked on
            user_profile: User's history
            level: Current level
            time_taken: Total time for session (seconds)
            meta_reflection: User's meta-cognitive reflection
            active_lesson: The active lesson prompt (if any)
        """
        
        # Evaluate each transmutation
        individual_scores = []
        for trans in transmutations:
            score = self.evaluate_transmutation(trans, scenario, user_profile, level, active_lesson)
            individual_scores.append(score)
        
        # Calculate session-level metrics
        session_score = self._calculate_session_score(individual_scores)
        divergence_score = self._calculate_divergence(transmutations, individual_scores)
        meta_score = self._evaluate_meta_cognition(meta_reflection, individual_scores, level)
        velocity_score = self._calculate_velocity_score(time_taken, len(transmutations), level)
        
        # Generate coaching synthesis
        coaching = self._synthesize_coaching(
            individual_scores, scenario, user_profile, level
        )
        
        # Recommend next level
        next_level = self._recommend_level(
            session_score, divergence_score, meta_score, level
        )
        
        # Archetype-specific feedback
        archetype = scenario.get('archetype', 'unknown')
        archetype_feedback = self._generate_archetype_feedback(
            archetype, individual_scores, user_profile
        )
        
        evaluation = SessionEvaluation(
            transmutation_scores=individual_scores,
            session_score=session_score,
            divergence_score=divergence_score,
            meta_cognitive_score=meta_score,
            velocity_score=velocity_score,
            coaching_synthesis=coaching,
            level_recommendation=next_level,
            archetype_feedback=archetype_feedback
        )
        
        # Store in history
        self.evaluation_history.append({
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'session_score': session_score,
            'archetype': archetype
        })
        
        return evaluation
    
    def _build_evaluation_prompt(
        self,
        transmutation: str,
        scenario: Dict,
        user_profile: Dict,
        level: int,
        active_lesson: str = ""
    ) -> str:
        """Build the evaluation prompt for LLM"""
        
        # Extract context
        scenario_title = scenario.get('title', 'Unknown')
        situation = scenario.get('situation', 'No context')
        archetype = scenario.get('archetype', 'unknown')
        archetype_obj = ARCHETYPES.get(archetype)
        
        # User patterns
        recent_patterns = user_profile.get('recent_patterns', [])
        strong_patterns = user_profile.get('strengths', [])
        weak_patterns = user_profile.get('weaknesses', [])
        past_transmutations = user_profile.get('recent_transmutations', [])
        
        # Calibrate harshness based on level
        if level >= 80:
            evaluation_stance = """
CRITICAL EVALUATION MODE (Level 80+):
You are evaluating an ADVANCED practitioner. Be intellectually rigorous.
- If this transmutation echoes their past patterns, call it out directly
- Expect novel angles and meta-cognitive sophistication
- A "good" score at this level would be average at Level 30
- Only give 85+ if genuinely impressed
"""
        elif level >= 50:
            evaluation_stance = """
INTERMEDIATE EVALUATION MODE (Level 50-79):
You are evaluating a developing expert.
- Look for evidence of pattern transfer across domains
- Expect multiple conceptual angles per transmutation
- Push them toward deeper synthesis
- Be encouraging but maintain standards
"""
        elif level >= 11:
            evaluation_stance = """
DEVELOPING EVALUATION MODE (Level 11-49):
You are evaluating someone building constraint-thinking skills.
- Recognize genuine constraint reframing
- Focus on teaching core principles through feedback
- Be encouraging but maintain quality standards
- Guide them toward more sophisticated thinking
- Novelty expectations are moderate (compare to their recent history)
"""
        else:
            evaluation_stance = """
FOUNDATION BUILDING MODE (Level 1-10):
The constraint is GIVEN to this user. Their only job is TRANSMUTATION.
No excuses for weak transmutations - they don't have to find the constraint.

CRITICAL DISTINCTION - Enforce this strictly:

COPING (score < 50):
- "Work around it" - NOT transmutation
- "Deal with it" - NOT transmutation  
- "Accept it" - NOT transmutation
- "Minimize the damage" - NOT transmutation
- Finding a silver lining WITHOUT using the constraint - NOT transmutation

REAL TRANSMUTATION (score 60+):
- The constraint ITSELF becomes the source of advantage
- The constraint is FUEL, not just something to tolerate
- Removing the constraint would REMOVE the advantage
- The limitation is actively GENERATIVE

Example - Cold coffee:
- COPING: "Use it as a reminder to stretch" (the coldness isn't the advantage)
- TRANSMUTATION: "Coldness forces me to get up → movement generates energy → I'm MORE alert than if it was hot" (coldness IS the advantage)

Be encouraging in TONE but maintain STANDARDS.
Quality of transmutation must be real from Day 1.
What changes at higher levels is SPEED and NOVELTY, not basic quality.

Score calibration:
- Below 50: Coping/avoidance disguised as transmutation - REJECT
- 50-60: Weak transmutation (constraint acknowledged but barely leveraged)
- 60-75: Solid transmutation (constraint genuinely becomes advantage)
- 75-85: Strong transmutation (novel angle, clear insight)
- 85+: Excellent (would impress at any level)
"""
        
        prompt = f"""You are a world-class C2A (Constraint-to-Advantage) expert evaluating a transmutation.

{evaluation_stance}

SCENARIO: {scenario_title}
Archetype: {archetype_obj.symbol if archetype_obj else ''} {archetype.upper()}
Situation: {situation[:300]}...

USER'S TRANSMUTATION:
"{transmutation}"

USER CONTEXT (Level {level}):
- Recent transmutation patterns: {', '.join(recent_patterns[:3]) if recent_patterns else 'Unknown (new user)'}
- Demonstrated strengths: {', '.join(strong_patterns) if strong_patterns else 'Building foundation'}
- Growth edges: {', '.join(weak_patterns) if weak_patterns else 'Exploring'}
- Sample past transmutations: {'; '.join(past_transmutations[-2:]) if past_transmutations else 'None yet'}

EVALUATION CRITERIA:

1. REFRAMING (0-30 points):
   Does this genuinely transform constraint → advantage?
   - Not just "cope with" or "work around" the constraint
   - But actively USE the constraint as a generative force
   - The constraint itself becomes the source of power

2. NOVELTY (0-25 points):
   How fresh is this thinking FOR THIS USER?
   - Compare against their known patterns
   - Originality of angle/approach
   - Avoiding cliché or obvious moves

3. PRACTICALITY (0-25 points):
   Could this actually work in reality?
   - Not fantasy or wishful thinking
   - Grounded in real mechanics
   - Shows understanding of implementation

4. SOPHISTICATION (0-20 points):
   Evidence of higher-order thinking?
   - Meta-cognitive awareness
   - Systemic thinking
   - Paradox navigation
   - Second/third order effects

SCORING CALIBRATION FOR LEVEL {level}:
- Below {max(50, level - 15)}: Poor - Missing core reframing
- {max(50, level - 15)}-{max(65, level - 5)}: Average - Basic transmutation
- {max(65, level - 5)}-{min(85, level + 5)}: Good - Solid constraint thinking
- {min(85, level + 5)}+: Excellent - Breakthrough insight

{'ACTIVE LESSON CHECK:' + chr(10) + active_lesson + chr(10) + 'Evaluate if the user applied this lesson in their transmutation.' + chr(10) if active_lesson else ''}OUTPUT FORMAT (JSON):
{{
    "reframing_score": <0-30>,
    "novelty_score": <0-25>,
    "practicality_score": <0-25>,
    "sophistication_score": <0-20>,
    "what_worked": "<CONVERSATIONAL: Talk directly to them like a coach. 'I see you did X, that's good because...' Keep it 1-2 sentences, simple words.>",
    "what_missed": "<CONVERSATIONAL: 'But here's what you missed...' or 'You're still doing that thing where...' Be direct, simple.>",
    "growth_edge": "<CONVERSATIONAL: 'Next time, try asking yourself...' or 'The move here is to...' One clear actionable thing, simple language.>",
    "pattern_identified": "<Short name for their pattern, e.g. 'Substitution Coping' or 'Surface Trading'>",
    "vs_user_history": "<CONVERSATIONAL: 'Same mistake as last time' or 'This is better than before because...' or 'You keep doing X'>",
    "breakthrough_moment": <true/false - is this a significant leap for them?>,
    "lesson_applied": <true/false - did they apply their active lesson? (false if no active lesson)>
}}

VOICE: Talk like a direct coach, not a textbook. Use "you" and "I see". Short sentences. No jargon. Call out if they're repeating mistakes.
"""
        
        return prompt
    
    def _query_llm(self, prompt: str) -> str:
        """Query LLM with error handling"""
        try:
            return self.llm.chat(
                prompt,
                system=(
                    "You are a legendary C2A coach known for precise, insightful evaluations that accelerate growth. "
                    "You see patterns others miss. You are kind but never dishonest."
                )
            )
        except Exception as e:
            print(f"LLM Error during evaluation: {e}")
            return self._generate_fallback_evaluation()
    
    def _parse_evaluation_response(self, response: str, level: int) -> TransmutationScore:
        """Parse LLM evaluation into structured score"""
        
        try:
            # Extract JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
            else:
                # Fallback parsing
                data = self._parse_natural_language_evaluation(response)
            
            # Calculate overall score
            overall = (
                data.get('reframing_score', 15) +
                data.get('novelty_score', 12) +
                data.get('practicality_score', 12) +
                data.get('sophistication_score', 10)
            )
            
            return TransmutationScore(
                overall_score=overall,
                reframing_score=data.get('reframing_score', 15),
                novelty_score=data.get('novelty_score', 12),
                practicality_score=data.get('practicality_score', 12),
                sophistication_score=data.get('sophistication_score', 10),
                what_worked=data.get('what_worked', 'Analysis in progress'),
                what_missed=data.get('what_missed', 'Continue exploring'),
                growth_edge=data.get('growth_edge', 'Keep practicing'),
                pattern_identified=data.get('pattern_identified', 'Pattern emerging'),
                vs_user_history=data.get('vs_user_history', 'Building your profile'),
                breakthrough_moment=data.get('breakthrough_moment', False),
                lesson_applied=data.get('lesson_applied', False)
            )
            
        except Exception as e:
            print(f"Parse error: {e}")
            return self._generate_fallback_score()
    
    def _parse_natural_language_evaluation(self, text: str) -> Dict:
        """Parse evaluation from natural language if JSON fails"""
        # Simple heuristic scoring based on keywords
        score_data = {
            'reframing_score': 15,
            'novelty_score': 12,
            'practicality_score': 12,
            'sophistication_score': 10,
            'what_worked': text[:200],
            'what_missed': 'Continue exploring',
            'growth_edge': 'Practice deeper reframing',
            'pattern_identified': 'Emerging pattern',
            'vs_user_history': 'Building profile',
            'breakthrough_moment': False
        }
        
        # Try to extract scores from text
        import re
        score_patterns = [
            (r'reframing[:\s]+(\d+)', 'reframing_score'),
            (r'novelty[:\s]+(\d+)', 'novelty_score'),
            (r'practicality[:\s]+(\d+)', 'practicality_score'),
            (r'sophistication[:\s]+(\d+)', 'sophistication_score')
        ]
        
        for pattern, key in score_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score_data[key] = int(match.group(1))
        
        return score_data
    
    def _generate_fallback_evaluation(self) -> str:
        """Generate fallback evaluation if LLM fails - with actionable C2A-specific guidance"""
        return json.dumps({
            "reframing_score": 15,
            "novelty_score": 12,
            "practicality_score": 12,
            "sophistication_score": 10,
            "what_worked": "Your attempt was recorded but couldn't be fully analyzed due to a connection timeout.",
            "what_missed": "Unable to evaluate - try applying The Removal Test: if you removed the constraint, would your advantage disappear too? If not, you may be coping rather than transmuting.",
            "growth_edge": "Ask yourself: What does this constraint FORCE me to do that I couldn't have done otherwise? The advantage must be BORN from the constraint, not despite it.",
            "pattern_identified": "Evaluation Timeout",
            "vs_user_history": "Session interrupted",
            "breakthrough_moment": False
        })
    
    def _generate_fallback_score(self) -> TransmutationScore:
        """Generate fallback score object with actionable C2A-specific guidance"""
        return TransmutationScore(
            overall_score=50,
            reframing_score=15,
            novelty_score=12,
            practicality_score=12,
            sophistication_score=10,
            what_worked="Your attempt was recorded but couldn't be fully analyzed due to a connection issue.",
            what_missed="Unable to evaluate - check if you're transmuting or just coping. True transmutation means the constraint CREATES the advantage, not that you succeed despite it.",
            growth_edge="Try the Removal Test: imagine the constraint vanishes. Does your 'advantage' still exist? If yes, you found a workaround, not a transmutation. Go deeper.",
            pattern_identified="Evaluation Timeout",
            vs_user_history="Session interrupted",
            breakthrough_moment=False,
            lesson_applied=False
        )
    
    def _calculate_session_score(self, scores: List[TransmutationScore]) -> int:
        """Calculate overall session score"""
        if not scores:
            return 0
        
        # Weight best transmutation more heavily
        sorted_scores = sorted([s.overall_score for s in scores], reverse=True)
        
        if len(sorted_scores) == 1:
            return sorted_scores[0]
        
        # Best: 50%, Second: 30%, Rest: 20% split
        session_score = sorted_scores[0] * 0.5
        session_score += sorted_scores[1] * 0.3 if len(sorted_scores) > 1 else 0
        
        if len(sorted_scores) > 2:
            remaining_avg = sum(sorted_scores[2:]) / len(sorted_scores[2:])
            session_score += remaining_avg * 0.2
        
        return int(session_score)
    
    def _calculate_divergence(
        self,
        transmutations: List[str],
        scores: List[TransmutationScore]
    ) -> int:
        """Calculate how diverse/divergent the transmutations are"""
        
        if len(transmutations) <= 1:
            return 50  # Single answer = baseline
        
        # Simple divergence: average of novelty scores + uniqueness check
        avg_novelty = sum(s.novelty_score for s in scores) / len(scores)
        
        # Check for repeated words/patterns
        word_sets = [set(t.lower().split()) for t in transmutations]
        overlap_penalties = 0
        
        for i in range(len(word_sets)):
            for j in range(i + 1, len(word_sets)):
                overlap = len(word_sets[i].intersection(word_sets[j]))
                total = len(word_sets[i].union(word_sets[j]))
                if total > 0:
                    similarity = overlap / total
                    if similarity > 0.5:
                        overlap_penalties += 10
        
        # Divergence = novelty boosted by variety
        divergence = int((avg_novelty / 25 * 100) - overlap_penalties)
        return max(0, min(100, divergence))
    
    def _evaluate_meta_cognition(
        self,
        reflection: Optional[str],
        scores: List[TransmutationScore],
        level: int
    ) -> int:
        """Evaluate meta-cognitive awareness"""
        
        if not reflection:
            return 50  # No reflection = baseline
        
        # Check for meta-cognitive markers
        meta_markers = [
            'realized', 'noticed', 'pattern', 'thinking about thinking',
            'shifted', 'reframed', 'perspective', 'approach',
            'strategy', 'aware', 'conscious', 'deliberate'
        ]
        
        reflection_lower = reflection.lower()
        marker_count = sum(1 for marker in meta_markers if marker in reflection_lower)
        
        # Base score from markers
        base_score = min(70, 40 + marker_count * 5)
        
        # Boost for showing awareness of constraint patterns
        pattern_awareness_boost = 0
        for score in scores:
            if 'meta' in score.pattern_identified.lower() or 'aware' in score.what_worked.lower():
                pattern_awareness_boost += 10
        
        meta_score = min(100, base_score + pattern_awareness_boost)
        return meta_score
    
    def _calculate_velocity_score(
        self,
        time_taken: Optional[float],
        num_transmutations: int,
        level: int
    ) -> int:
        """Calculate velocity score based on speed"""
        
        if time_taken is None:
            return 75  # No timing data = baseline
        
        # Expected time: ~90 seconds per transmutation
        expected_time = num_transmutations * 90
        
        if time_taken <= expected_time:
            # Faster than expected = bonus
            ratio = time_taken / expected_time
            velocity = int(75 + (1 - ratio) * 25)  # 75-100 range
        else:
            # Slower than expected = penalty
            ratio = time_taken / expected_time
            velocity = int(75 - (ratio - 1) * 30)  # 75 down
        
        return max(0, min(100, velocity))
    
    def calculate_velocity_penalty(self, duration_seconds: float, target_seconds: int = 60) -> tuple:
        """
        THE VELOCITY GUILLOTINE - "Enough Thinking" Algorithm
        
        Transmutation is recognition, not deliberation. If you can't do it in 60 seconds,
        you're thinking, not transmuting. Thinking = Future (planning). Transmutation = Present.
        
        Scoring:
        - 0-30s:  BONUS 1.1x  "⚡ Reflexive Speed" 
        - 30-60s: No penalty  "✓ On Pace"
        - 60-90s: -10%        "⚠ Hesitation"
        - 90-120s: -30%       "⚠ Overthinking"  
        - 120s+:  -50% cap    "✖ Analysis Paralysis"
        
        Returns:
            (multiplier, message) tuple
        """
        if duration_seconds <= 30:
            return 1.1, "⚡ Reflexive Speed (+10%)"
        
        if duration_seconds <= target_seconds:
            return 1.0, "✓ On Pace"
        
        # The Guillotine: Score decays after target
        if duration_seconds <= 90:
            return 0.9, "⚠ Hesitation (-10%)"
        
        if duration_seconds <= 120:
            return 0.7, "⚠ Overthinking (-30%)"
        
        # Hard cap at 50% for extreme overtime
        return 0.5, "✖ Analysis Paralysis (-50%)"
    
    def apply_velocity_penalty(self, raw_score: int, duration_seconds: float) -> tuple:
        """
        Apply velocity penalty to raw score.
        
        Args:
            raw_score: The LLM-evaluated score (0-100)
            duration_seconds: Time taken to submit
            
        Returns:
            (final_score, velocity_multiplier, velocity_message)
        """
        multiplier, message = self.calculate_velocity_penalty(duration_seconds)
        final_score = int(raw_score * multiplier)
        return final_score, multiplier, message
    
    def _synthesize_coaching(
        self,
        scores: List[TransmutationScore],
        scenario: Dict,
        user_profile: Dict,
        level: int
    ) -> str:
        """Synthesize session-level coaching insights"""
        
        best = max(scores, key=lambda s: s.overall_score)
        avg_score = sum(s.overall_score for s in scores) / len(scores)
        
        # Identify common patterns
        patterns = [s.pattern_identified for s in scores]
        unique_patterns = set(patterns)
        
        # Build coaching message
        coaching = f"""Your transmutations averaged {avg_score:.0f}/100.

Your strongest transmutation scored {best.overall_score}/100 and demonstrated {best.pattern_identified}.

"""
        
        if len(unique_patterns) > 1:
            coaching += f"You explored {len(unique_patterns)} different constraint-thinking patterns this session, showing good cognitive flexibility.\n\n"
        else:
            coaching += "Consider exploring more diverse transmutation angles in your next session.\n\n"
        
        # Add specific guidance
        growth_edges = [s.growth_edge for s in scores]
        if growth_edges:
            coaching += f"Focus area: {growth_edges[0]}\n"
        
        return coaching
    
    def _recommend_level(
        self,
        session_score: int,
        divergence_score: int,
        meta_score: int,
        current_level: int
    ) -> int:
        """Recommend next level based on performance"""
        
        # Calculate composite performance
        composite = (session_score * 0.5 + divergence_score * 0.3 + meta_score * 0.2)
        
        if composite >= current_level + 10:
            # Strong performance - accelerate
            return min(100, current_level + 3)
        elif composite >= current_level:
            # Solid performance - advance
            return min(100, current_level + 1)
        elif composite >= current_level - 10:
            # Maintain level
            return current_level
        else:
            # Struggling - consolidate
            return max(1, current_level - 1)
    
    def _generate_archetype_feedback(
        self,
        archetype: str,
        scores: List[TransmutationScore],
        user_profile: Dict
    ) -> Dict[str, str]:
        """Generate feedback specific to the archetype"""
        
        archetype_obj = ARCHETYPES.get(archetype.lower())
        if not archetype_obj:
            return {}
        
        avg_score = sum(s.overall_score for s in scores) / len(scores) if scores else 50
        
        # Update user's archetype performance tracking
        archetype_history = user_profile.get('archetype_performance', {})
        archetype_history[archetype] = avg_score
        
        feedback = {
            'archetype': archetype,
            'performance': f"{avg_score:.0f}/100",
            'insight': f"Your work with {archetype_obj.name} constraints shows {self._performance_descriptor(avg_score)}."
        }
        
        return feedback
    
    def _performance_descriptor(self, score: float) -> str:
        """Convert score to qualitative descriptor"""
        if score >= 85:
            return "mastery"
        elif score >= 70:
            return "strong competence"
        elif score >= 60:
            return "developing skill"
        elif score >= 50:
            return "early understanding"
        else:
            return "opportunity for growth"


if __name__ == "__main__":
    # Test evaluation
    judge = TransmutationJudge()
    
    test_scenario = {
        'title': 'The 30-Minute Developer',
        'archetype': 'velocity',
        'situation': 'You want to learn advanced programming but only have 30 minutes per day...'
    }
    
    test_profile = {
        'recent_patterns': ['time chunking', 'priority filtering'],
        'strengths': ['analytical thinking'],
        'weaknesses': ['creative reframing'],
        'recent_transmutations': []
    }
    
    test_transmutation = "Use the 30-minute constraint to force extreme focus. Create a 'learning kata' - a single, repeatable exercise that builds muscle memory. The time limit becomes a forcing function for deliberate practice rather than passive consumption."
    
    print("Evaluating test transmutation...\n")
    score = judge.evaluate_transmutation(
        test_transmutation,
        test_scenario,
        test_profile,
        level=15
    )
    
    print(score)
