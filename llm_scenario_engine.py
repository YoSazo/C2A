#!/usr/bin/env python3
"""
LLM Scenario Engine - Infinite Constraint Generation

This engine generates personalized, poetic constraint scenarios that evolve
with the user. Each scenario is crafted to be personally relevant, emotionally
engaging, and pedagogically precise.

Philosophy: Constraints should feel like koans, not homework.
"""

import json
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from llm_client import LLMClient, create_client_from_env

from constraint_archetypes import ARCHETYPES, ConstraintArchetype


@dataclass
class ConstraintScenario:
    """A generated constraint scenario"""
    title: str
    archetype: str
    situation: str
    hidden_constraint: Optional[str]  # For advanced levels - user must identify
    explicit_constraint: Optional[str]  # For beginner levels - given directly
    emotional_hook: str  # Why should the user care?
    hint: str
    target_transmutations: int
    difficulty_level: int
    personal_relevance_score: float  # 0-1, how relevant to user's history
    
    def to_dict(self) -> Dict:
        return asdict(self)


class LLMScenarioEngine:
    """Generates beautiful, personalized constraint scenarios using an LLM"""

    def __init__(self, model: str = "qwen2.5:32b", llm_client: Optional[LLMClient] = None):
        # Backwards compatible: if no client passed, pick from env or default local.
        self.llm = llm_client or create_client_from_env()
        self.model = model  # retained for legacy/debug output
        self.generation_history = []
        
    def generate_scenario(
        self,
        user_profile: Dict,
        level: int,
        archetype: Optional[ConstraintArchetype] = None,
        force_personal: bool = False
    ) -> ConstraintScenario:
        """
        Generate a constraint scenario tailored to the user
        
        Args:
            user_profile: User's history, domain, strengths, weaknesses
            level: Current mastery level (1-100)
            archetype: Specific archetype to explore (or random if None)
            force_personal: If True, make it deeply personal to user's stated domain
        """
        
        # Select archetype
        if archetype is None:
            archetype = self._select_optimal_archetype(user_profile, level)
        
        # Determine if constraint should be hidden (advanced) or explicit (beginner)
        hide_constraint = level >= 11
        
        # Build generation prompt
        prompt = self._build_generation_prompt(
            user_profile, level, archetype, hide_constraint, force_personal
        )
        
        # Generate scenario
        response = self._query_llm(prompt)
        
        # Parse and structure
        scenario = self._parse_scenario_response(response, archetype, level, hide_constraint)
        
        # Store in history to avoid repetition
        self.generation_history.append(scenario.title)
        
        return scenario
    
    def _select_optimal_archetype(self, user_profile: Dict, level: int) -> ConstraintArchetype:
        """
        Select the most pedagogically appropriate archetype
        
        Strategy:
        - Levels 1-5: Cycle through each archetype once (foundation)
        - Levels 6-20: Target weakest archetype based on history
        - Levels 21+: Weighted random (favor unexplored + weak areas)
        """
        
        # Get user's archetype performance if available
        archetype_scores = user_profile.get('archetype_performance', {})
        
        if level <= 5:
            # Foundational learning - ensure exposure to all archetypes
            session_count = user_profile.get('total_sessions', 0)
            archetype_names = list(ARCHETYPES.keys())
            return ARCHETYPES[archetype_names[session_count % 5]]
        
        elif level <= 20:
            # Target weakness
            if archetype_scores:
                weakest = min(archetype_scores.items(), key=lambda x: x[1])
                return ARCHETYPES[weakest[0]]
            else:
                return random.choice(list(ARCHETYPES.values()))
        
        else:
            # Advanced - weighted randomness favoring growth edges
            weights = []
            archetypes = list(ARCHETYPES.values())
            
            for arch in archetypes:
                score = archetype_scores.get(arch.name.lower(), 50)
                # Lower scores = higher weight (target weakness)
                weight = 100 - score
                weights.append(weight)
            
            return random.choices(archetypes, weights=weights)[0]
    
    def _build_generation_prompt(
        self,
        user_profile: Dict,
        level: int,
        archetype: ConstraintArchetype,
        hide_constraint: bool,
        force_personal: bool
    ) -> str:
        """Build the LLM prompt for scenario generation"""
        
        # Extract user context
        user_domain = user_profile.get('domain', 'general life')
        past_constraints = user_profile.get('recent_constraints', [])
        strengths = user_profile.get('strengths', [])
        weaknesses = user_profile.get('weaknesses', [])
        
        # Build avoidance list (don't repeat recent scenarios)
        avoid_list = "\n".join([f"- {title}" for title in self.generation_history[-10:]])
        
        prompt = f"""You are a master constraint designer for C2A (Constraint-to-Advantage) training.

Your task: Generate a constraint scenario that is a fast drill (skimmable in under 10 seconds).

CRITICAL INSTRUCTION: Scenarios must be under 75 words. Be direct, punchy, and visceral. Do not write poetry. Focus on the mechanical pressure of the situation.

ARCHETYPE: {archetype.symbol} {archetype.name.upper()}
Core Pattern: {archetype.essence}

USER CONTEXT:
- Level: {level}/100
- Domain: {user_domain}
- Demonstrated Strengths: {', '.join(strengths) if strengths else 'Unknown (new user)'}
- Growth Edges: {', '.join(weaknesses) if weaknesses else 'Exploring'}
- Recent Constraints Faced: {', '.join(past_constraints[-3:]) if past_constraints else 'None yet'}

GENERATION REQUIREMENTS:

1. EMOTIONAL RESONANCE (Critical):
   - This should feel REAL, not academic
   - {"Deeply personal to their domain: " + user_domain if force_personal else "Universally relatable but specific"}
   - Create genuine stakes (even if small-scale)
   - The user should CARE about solving this

2. ARCHETYPE ALIGNMENT:
   - Must embody the {archetype.name} archetype authentically
   - The constraint should feel inevitable, not arbitrary
   - Multiple valid transmutation paths exist

3. DIFFICULTY CALIBRATION (Level {level}):
   {"- BEGINNER: Constraint is obvious and stated clearly" if level <= 5 else ""}
   {"- INTERMEDIATE: Constraint requires minor insight to identify" if 6 <= level <= 10 else ""}
   {"- ADVANCED: Constraint is hidden in the situation, user must discover it" if level >= 11 else ""}
   - Complexity should match skill level
   - Should stretch but not overwhelm

4. AVOID REPETITION:
   Do NOT create scenarios similar to:
{avoid_list if avoid_list else "   (No prior scenarios - full creative freedom)"}

5. BREVITY + CLARITY (CRITICAL):
   - Scenarios must be under 75 words total.
   - 2-4 short sentences max.
   - No metaphors, no scenery, no vibe.
   - Mechanical facts only: actors, goal, constraint pressure, stakes.
   - Make the constraint detectable quickly.

OUTPUT FORMAT (JSON):
{{
    "title": "3-5 word title (concrete, not poetic)",
    "situation": "Under 75 words. 2-4 sentences max. Mechanical facts only.",
    "emotional_hook": "One short sentence: why this matters",
    {'hidden_constraint": "The constraint they must identify",' if hide_constraint else 'explicit_constraint": "The constraint stated clearly",'}
    "hint": "One short hint (not cryptic). Point toward a lever.",
    "target_transmutations": {max(1, min(10, level // 10 + 1))}
}}

Generate a scenario that makes the user think: "Oh, this is MY constraint."
"""
        
        return prompt
    
    def _query_llm(self, prompt: str) -> str:
        """Query the LLM with error handling"""
        try:
            return self.llm.chat(
                prompt,
                system=(
                    "You are a world-class C2A constraint designer running short, brutal drills. "
                    "Stop being a poet. Be a drill sergeant. "
                    "CRITICAL: Scenarios must be under 75 words, direct, punchy, and visceral. "
                    "No metaphors. No scenery. No vibe. Only mechanical pressure + stakes."
                )
            )
        except Exception as e:
            print(f"LLM Error: {e}")
            # Fallback to a simple templated scenario
            return self._generate_fallback_scenario()
    
    def _parse_scenario_response(
        self,
        response: str,
        archetype: ConstraintArchetype,
        level: int,
        hide_constraint: bool
    ) -> ConstraintScenario:
        """Parse LLM response into structured scenario"""
        
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
            else:
                # LLM didn't return JSON, try to parse naturally
                data = self._parse_natural_language_scenario(response)
            
            return ConstraintScenario(
                title=data.get('title', 'Untitled Constraint'),
                archetype=archetype.name.lower(),
                situation=data.get('situation', response[:500]),
                hidden_constraint=data.get('hidden_constraint') if hide_constraint else None,
                explicit_constraint=data.get('explicit_constraint') if not hide_constraint else None,
                emotional_hook=data.get('emotional_hook', 'Your growth depends on this.'),
                hint=data.get('hint', 'Look for what seems impossible.'),
                target_transmutations=data.get('target_transmutations', max(1, level // 10 + 1)),
                difficulty_level=level,
                personal_relevance_score=0.8  # Could be computed from user profile
            )
            
        except Exception as e:
            print(f"Parse error: {e}")
            return self._generate_fallback_scenario_object(archetype, level, hide_constraint)
    
    def _parse_natural_language_scenario(self, text: str) -> Dict:
        """Attempt to parse scenario from natural language response"""
        # Simple heuristic parsing - could be enhanced
        lines = text.split('\n')
        
        data = {
            'title': lines[0][:50] if lines else 'Generated Scenario',
            'situation': text[:400],
            'emotional_hook': 'Transform this constraint.',
            'hint': 'Look for the hidden advantage.',
            'target_transmutations': 3
        }
        
        # Try to find constraint mentions
        for line in lines:
            if 'constraint:' in line.lower():
                data['explicit_constraint'] = line.split(':', 1)[1].strip()
                break
        
        return data
    
    def _generate_fallback_scenario(self) -> str:
        """Generate a simple fallback if LLM fails"""
        return json.dumps({
            "title": "The Unexpected Limitation",
            "situation": "You face a significant constraint that limits your options.",
            "emotional_hook": "Your progress depends on finding a way forward.",
            "explicit_constraint": "Limited resources and time",
            "hint": "Consider what this limitation forces you to prioritize.",
            "target_transmutations": 3
        })
    
    def _generate_fallback_scenario_object(
        self,
        archetype: ConstraintArchetype,
        level: int,
        hide_constraint: bool
    ) -> ConstraintScenario:
        """Generate fallback scenario object"""
        return ConstraintScenario(
            title=f"The {archetype.name} Challenge",
            archetype=archetype.name.lower(),
            situation=f"A situation embodying {archetype.essence}",
            hidden_constraint="Discover the constraint" if hide_constraint else None,
            explicit_constraint="Resource limitation" if not hide_constraint else None,
            emotional_hook="Your growth depends on this.",
            hint="Look for the hidden advantage.",
            target_transmutations=max(1, level // 10 + 1),
            difficulty_level=level,
            personal_relevance_score=0.5
        )


class ScenarioValidator:
    """Validates that generated scenarios meet quality standards"""
    
    @staticmethod
    def validate_scenario(scenario: ConstraintScenario) -> Tuple[bool, List[str]]:
        """
        Validate scenario quality
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Check required fields
        if not scenario.title or len(scenario.title) < 3:
            issues.append("Title too short")
        
        # In drill mode scenarios are intentionally short; ensure it's not empty
        if not scenario.situation or len(scenario.situation) < 20:
            issues.append("Situation too short")
        
        if not scenario.hidden_constraint and not scenario.explicit_constraint:
            issues.append("No constraint defined")
        
        if scenario.target_transmutations < 1 or scenario.target_transmutations > 10:
            issues.append("Invalid transmutation target")
        
        # Check for generic/boring language
        boring_words = ['problem', 'issue', 'challenge', 'difficulty']
        if any(word in scenario.title.lower() for word in boring_words):
            issues.append("Title is generic (avoid: problem, issue, challenge)")
        
        return (len(issues) == 0, issues)


if __name__ == "__main__":
    # Test scenario generation
    engine = LLMScenarioEngine()
    
    test_profile = {
        'domain': 'software engineering',
        'total_sessions': 3,
        'recent_constraints': ['Time pressure on project', 'Limited team size'],
        'strengths': ['analytical thinking'],
        'weaknesses': ['creative reframing'],
        'archetype_performance': {
            'scarcity': 75,
            'velocity': 60,
            'asymmetry': 80,
            'friction': 55,
            'paradox': 70
        }
    }
    
    print("Generating test scenario...\n")
    scenario = engine.generate_scenario(test_profile, level=8)
    
    print(f"Title: {scenario.title}")
    print(f"Archetype: {scenario.archetype}")
    print(f"\nSituation:\n{scenario.situation}")
    print(f"\nEmotional Hook: {scenario.emotional_hook}")
    print(f"Hint: {scenario.hint}")
    print(f"Target Transmutations: {scenario.target_transmutations}")
    
    # Validate
    is_valid, issues = ScenarioValidator.validate_scenario(scenario)
    print(f"\nValidation: {'✓ PASS' if is_valid else '✗ FAIL'}")
    if issues:
        print("Issues:", ', '.join(issues))
