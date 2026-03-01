#!/usr/bin/env python3
"""
C2A Constraint Archetypes - The Five Fundamental Forces

Each archetype represents a primordial constraint pattern that echoes across
all domains of human experience. These are not "problems" but rather the
essential tensions that create the possibility of transformation.

"The constraint is not the enemy of creativity; it is the condition for it."
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class ConstraintArchetype:
    """A fundamental pattern of constraint that transcends specific contexts"""
    name: str
    symbol: str  # Unicode symbol for visual representation
    essence: str  # The core nature of this constraint
    universal_pattern: str  # How it manifests across domains
    transformation_keys: List[str]  # Common transmutation patterns
    color_code: str  # ANSI color for terminal display
    
    def __str__(self):
        return f"{self.symbol} {self.name}"


# The Five Archetypal Constraints
ARCHETYPES = {
    "scarcity": ConstraintArchetype(
        name="Scarcity",
        symbol="⧗",
        essence="The limitation of resources in the face of unlimited wants",
        universal_pattern="""
        When what you need exceeds what you have, the gap itself becomes
        a forcing function. Scarcity demands prioritization, creativity,
        and the discovery of alternative paths.
        """,
        transformation_keys=[
            "Focus through elimination",
            "Innovation from necessity",
            "Value through rarity",
            "Efficiency as artform",
            "Constraints breed resourcefulness"
        ],
        color_code="\033[38;5;208m"  # Orange
    ),
    
    "velocity": ConstraintArchetype(
        name="Velocity",
        symbol="⚡",
        essence="The compression of time against the expansion of aspiration",
        universal_pattern="""
        When time contracts, decisions crystallize. The urgency strips away
        the non-essential and forces you to trust instinct over analysis.
        Speed reveals what truly matters.
        """,
        transformation_keys=[
            "Clarity through urgency",
            "Intuition over analysis",
            "Momentum as strategy",
            "Minimum viable action",
            "Speed as filter for truth"
        ],
        color_code="\033[38;5;226m"  # Yellow
    ),
    
    "asymmetry": ConstraintArchetype(
        name="Asymmetry",
        symbol="⚖",
        essence="The imbalance between what you know and what you need to know",
        universal_pattern="""
        Incomplete information creates the space for interpretation, hypothesis,
        and intuitive leaps. What you don't know can become a source of power
        if you learn to navigate uncertainty.
        """,
        transformation_keys=[
            "Hypothesis as action",
            "Assumptions as experiments",
            "Questions as answers",
            "Unknown as opportunity",
            "Uncertainty as freedom"
        ],
        color_code="\033[38;5;51m"  # Cyan
    ),
    
    "friction": ConstraintArchetype(
        name="Friction",
        symbol="⚙",
        essence="The resistance between intention and execution",
        universal_pattern="""
        When the tool doesn't fit the task, when the path resists your movement,
        friction forces you to either find a new way or become stronger through
        the resistance itself. Opposition shapes form.
        """,
        transformation_keys=[
            "Resistance as teacher",
            "Indirection over force",
            "Constraint as compass",
            "Wrong tool as innovation prompt",
            "Friction reveals structure"
        ],
        color_code="\033[38;5;197m"  # Red
    ),
    
    "paradox": ConstraintArchetype(
        name="Paradox",
        symbol="∞",
        essence="The requirement to hold contradictory truths simultaneously",
        universal_pattern="""
        When forced to honor two opposing values, the tension creates a third way.
        Paradox is not a problem to solve but a dynamic to navigate. The both/and
        transcends the either/or.
        """,
        transformation_keys=[
            "Synthesis over choice",
            "Oscillation as strategy",
            "Tension as creative force",
            "Contradiction as completeness",
            "Third way emergence"
        ],
        color_code="\033[38;5;129m"  # Purple
    )
}


def get_archetype(name: str) -> Optional[ConstraintArchetype]:
    """Retrieve an archetype by name"""
    return ARCHETYPES.get(name.lower())


def get_random_archetype() -> ConstraintArchetype:
    """Get a random archetype for training"""
    import random
    return random.choice(list(ARCHETYPES.values()))


def display_archetype_gallery():
    """Beautiful display of all archetypes"""
    print("\n" + "═" * 70)
    print("  THE FIVE ARCHETYPAL CONSTRAINTS")
    print("  Fundamental Forces of Transformation")
    print("═" * 70 + "\n")
    
    for archetype in ARCHETYPES.values():
        print(f"{archetype.color_code}{archetype.symbol} {archetype.name.upper()}\033[0m")
        print(f"  Essence: {archetype.essence}")
        print(f"  Pattern: {archetype.universal_pattern.strip()[:150]}...")
        print()


if __name__ == "__main__":
    display_archetype_gallery()
