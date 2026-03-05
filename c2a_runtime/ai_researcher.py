"""
AI Researcher Module - Opus as Cognitive Scientist

This module transforms the LLM from a judge into a co-researcher.
It observes, notes, analyzes, and proposes refinements to C2A.

The AI Researcher:
1. Observes each session
2. Generates multi-level notes (subject, pattern, system, theory)
3. Accumulates insights across sessions
4. Produces research reports
5. Proposes refinements to C2A protocol

This data becomes:
- Deep insight into the user's cognitive patterns
- Refinements to improve C2A for everyone
- Training data for a future "C2A Expert" chatbot
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from llm_client import LLMClient, create_client_from_env


@dataclass
class SubjectObservation:
    """Observation about the specific user"""
    session_id: int
    timestamp: str
    observation: str
    cognitive_patterns: List[str]
    strengths_noted: List[str]
    weaknesses_noted: List[str]
    recommendations: List[str]


@dataclass
class PatternObservation:
    """Observation about patterns across sessions"""
    session_range: str  # e.g., "45-50"
    timestamp: str
    observation: str
    trend_type: str  # "improvement", "plateau", "regression", "breakthrough"
    evidence: List[str]
    concern_level: str  # "none", "low", "medium", "high"


@dataclass
class SystemObservation:
    """Observation about C2A system itself"""
    session_id: int
    timestamp: str
    observation: str
    component_affected: str  # "detection", "transmutation", "scoring", "progression", etc.
    issue_type: str  # "gap", "inefficiency", "bug", "enhancement"
    severity: str  # "minor", "moderate", "major", "critical"
    proposed_change: Optional[str]


@dataclass
class TheoreticalObservation:
    """Observation about cognition generally"""
    session_id: int
    timestamp: str
    observation: str
    cognitive_domain: str  # "attention", "memory", "reasoning", "automaticity", etc.
    hypothesis: str
    testable_prediction: Optional[str]
    related_research: Optional[str]


@dataclass
class RefinementProposal:
    """Concrete proposal to improve C2A"""
    proposal_id: str
    timestamp: str
    title: str
    description: str
    rationale: str
    affected_component: str
    implementation_difficulty: str  # "easy", "medium", "hard"
    expected_impact: str  # "low", "medium", "high"
    how_to_test: str
    status: str  # "proposed", "testing", "implemented", "rejected"


class AIResearcher:
    """
    AI as Cognitive Scientist - Observes and analyzes C2A training.
    
    Generates insights at multiple levels:
    1. Subject observations (about this specific human)
    2. Pattern observations (trends across sessions)
    3. System observations (about C2A itself)
    4. Theoretical observations (about cognition)
    5. Refinement proposals (concrete improvements)
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        data_dir: Optional[str] = None
    ):
        """
        Initialize AI Researcher.
        
        Args:
            llm_client: LLM client to use (creates default if not provided)
            data_dir: Directory to store research notes
        """
        self.llm = llm_client or create_client_from_env()
        
        # Setup data directory
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent / "research_notes"
        
        self._setup_directories()
        
        # Load existing observations
        self.subject_observations: List[SubjectObservation] = []
        self.pattern_observations: List[PatternObservation] = []
        self.system_observations: List[SystemObservation] = []
        self.theoretical_observations: List[TheoreticalObservation] = []
        self.refinement_proposals: List[RefinementProposal] = []
        
        self._load_existing_notes()
    
    def _setup_directories(self):
        """Create directory structure for research notes"""
        dirs = [
            self.data_dir,
            self.data_dir / "session_notes",
            self.data_dir / "pattern_notes",
            self.data_dir / "system_notes",
            self.data_dir / "theoretical_notes",
            self.data_dir / "refinement_proposals",
            self.data_dir / "reports"
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def _load_existing_notes(self):
        """Load existing research notes from disk"""
        # Load subject observations
        subject_dir = self.data_dir / "session_notes"
        for f in subject_dir.glob("*.json"):
            try:
                with open(f, 'r') as file:
                    data = json.load(file)
                    self.subject_observations.append(SubjectObservation(**data))
            except:
                pass
        
        # Load other observation types similarly
        # (keeping it simple for now - full implementation would load all types)
    
    def observe_session(
        self,
        session_data: Dict[str, Any],
        all_sessions: List[Dict[str, Any]],
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate observations after a training session.
        
        This is the core method - called after each C2A session.
        
        Args:
            session_data: Data from the just-completed session
            all_sessions: All previous sessions (for pattern analysis)
            user_profile: User's profile and stats
            
        Returns:
            Dictionary containing all generated observations
        """
        
        session_id = session_data.get('session_id', len(all_sessions) + 1)
        timestamp = datetime.now().isoformat()
        
        # Build the research prompt
        prompt = self._build_observation_prompt(session_data, all_sessions, user_profile)
        
        # Get observations from LLM
        system_prompt = """You are a cognitive scientist studying a novel training protocol called C2A 
(Constraint-to-Advantage). You are observing a human subject going through the training.

Your role is to:
1. Observe objectively and rigorously
2. Note patterns in cognition
3. Identify what's working and what's not
4. Propose improvements based on evidence
5. Generate theoretical insights about human cognition

Be scientific. Cite specific evidence from the session data. Don't generate fluff.
If you have no observation at a level, say "No observation at this level."

Your notes will be used to:
- Help this specific user improve
- Refine C2A for all future users
- Potentially contribute to cognitive science research"""

        response = self.llm.chat(prompt, system=system_prompt)
        
        # Parse the response
        observations = self._parse_observations(response, session_id, timestamp)
        
        # Save observations
        self._save_observations(observations, session_id)
        
        return observations
    
    def _build_observation_prompt(
        self,
        session_data: Dict,
        all_sessions: List[Dict],
        user_profile: Dict
    ) -> str:
        """Build the prompt for generating observations"""
        
        # Summarize session history
        session_summary = self._summarize_sessions(all_sessions[-20:])  # Last 20 sessions
        
        # Calculate some quick stats
        total_sessions = len(all_sessions)
        avg_score = sum(s.get('session_score', 0) for s in all_sessions) / max(len(all_sessions), 1)
        
        prompt = f"""
═══════════════════════════════════════════════════════════════
C2A RESEARCH OBSERVATION REQUEST
═══════════════════════════════════════════════════════════════

SUBJECT PROFILE:
- Total sessions completed: {total_sessions}
- Current level: {user_profile.get('current_level', 1)}
- Average score: {avg_score:.1f}
- Archetype performance: {json.dumps(user_profile.get('archetype_performance', {}), indent=2)}

═══════════════════════════════════════════════════════════════
JUST COMPLETED SESSION (Session #{session_data.get('session_id', total_sessions + 1)}):
═══════════════════════════════════════════════════════════════

Level: {session_data.get('level', 'unknown')}
Archetype: {session_data.get('archetype', 'unknown')}
Scenario: {session_data.get('scenario_title', 'unknown')}

Detection Required: {session_data.get('detection_required', False)}
Detection Success: {session_data.get('detection_success', 'N/A')}
Detection User Answer: {session_data.get('detection_user_answer', 'N/A')}
Detection Correct Answer: {session_data.get('detection_correct_answer', 'N/A')}
Detection Confusion Type: {session_data.get('detection_confusion_type', 'N/A')}

Transmutations Provided:
{json.dumps(session_data.get('transmutations', []), indent=2)}

Session Score: {session_data.get('session_score', 0)}/100
Best Transmutation Score: {session_data.get('best_score', 0)}/100
Divergence Score: {session_data.get('divergence_score', 0)}

Meta-Reflection from Subject:
"{session_data.get('meta_reflection', 'None provided')}"

Breakthrough Moment: {session_data.get('breakthrough', False)}

═══════════════════════════════════════════════════════════════
RECENT SESSION HISTORY (Last 20 sessions summary):
═══════════════════════════════════════════════════════════════

{session_summary}

═══════════════════════════════════════════════════════════════
GENERATE RESEARCH OBSERVATIONS
═══════════════════════════════════════════════════════════════

Please generate observations at each level. Use this exact format:

## SUBJECT OBSERVATION
[Your observation about this specific human's cognition this session]

Cognitive Patterns Noted:
- [pattern 1]
- [pattern 2]

Strengths This Session:
- [strength 1]

Weaknesses This Session:
- [weakness 1]

Recommendations for Next Session:
- [recommendation 1]

---

## PATTERN OBSERVATION
[Only if you notice a multi-session trend. Otherwise write "No observation at this level."]

Trend Type: [improvement/plateau/regression/breakthrough]
Evidence:
- [specific evidence from session history]

Concern Level: [none/low/medium/high]

---

## SYSTEM OBSERVATION
[Only if you notice something about C2A itself that could be improved. Otherwise write "No observation at this level."]

Component Affected: [detection/transmutation/scoring/progression/scenarios/etc.]
Issue Type: [gap/inefficiency/bug/enhancement]
Severity: [minor/moderate/major/critical]

Proposed Change:
[Specific change you'd recommend]

---

## THEORETICAL OBSERVATION
[Only if you have a genuine insight about human cognition. Otherwise write "No observation at this level."]

Cognitive Domain: [attention/memory/reasoning/automaticity/etc.]
Hypothesis: [Your hypothesis]
Testable Prediction: [How we could test this]

---

## REFINEMENT PROPOSAL
[Only if you have a concrete, actionable proposal. Otherwise write "No observation at this level."]

Title: [Short title]
Description: [What to change]
Rationale: [Why this would help, with evidence]
Implementation Difficulty: [easy/medium/hard]
Expected Impact: [low/medium/high]
How to Test: [How we'd know if it worked]

═══════════════════════════════════════════════════════════════
"""
        
        return prompt
    
    def _summarize_sessions(self, sessions: List[Dict]) -> str:
        """Create a brief summary of recent sessions"""
        if not sessions:
            return "No previous sessions."
        
        lines = []
        for s in sessions:
            line = (
                f"Session {s.get('session_id', '?')}: "
                f"L{s.get('level', '?')} | "
                f"{s.get('archetype', '?')[:8]} | "
                f"Score: {s.get('session_score', 0)} | "
                f"Detection: {'✓' if s.get('detection_success', True) else '✗'}"
            )
            lines.append(line)
        
        return "\n".join(lines)
    
    def _parse_observations(
        self,
        response: str,
        session_id: int,
        timestamp: str
    ) -> Dict[str, Any]:
        """Parse LLM response into structured observations"""
        
        observations = {
            "session_id": session_id,
            "timestamp": timestamp,
            "raw_response": response,
            "subject_observation": None,
            "pattern_observation": None,
            "system_observation": None,
            "theoretical_observation": None,
            "refinement_proposal": None
        }
        
        # Parse each section (simplified parsing - production would be more robust)
        sections = response.split("---")
        
        for section in sections:
            section = section.strip()
            
            if "## SUBJECT OBSERVATION" in section:
                observations["subject_observation"] = self._parse_subject_observation(
                    section, session_id, timestamp
                )
            elif "## PATTERN OBSERVATION" in section:
                if "No observation at this level" not in section:
                    observations["pattern_observation"] = section
            elif "## SYSTEM OBSERVATION" in section:
                if "No observation at this level" not in section:
                    observations["system_observation"] = section
            elif "## THEORETICAL OBSERVATION" in section:
                if "No observation at this level" not in section:
                    observations["theoretical_observation"] = section
            elif "## REFINEMENT PROPOSAL" in section:
                if "No observation at this level" not in section:
                    observations["refinement_proposal"] = section
        
        return observations
    
    def _parse_subject_observation(
        self,
        section: str,
        session_id: int,
        timestamp: str
    ) -> Dict:
        """Parse subject observation section"""
        return {
            "session_id": session_id,
            "timestamp": timestamp,
            "content": section,
            "cognitive_patterns": self._extract_list(section, "Cognitive Patterns Noted:"),
            "strengths": self._extract_list(section, "Strengths This Session:"),
            "weaknesses": self._extract_list(section, "Weaknesses This Session:"),
            "recommendations": self._extract_list(section, "Recommendations for Next Session:")
        }
    
    def _extract_list(self, text: str, header: str) -> List[str]:
        """Extract a bulleted list after a header"""
        items = []
        try:
            if header in text:
                start = text.index(header) + len(header)
                remaining = text[start:].strip()
                lines = remaining.split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith("- "):
                        items.append(line[2:])
                    elif line.startswith("##") or line.startswith("---"):
                        break
                    elif line and not line.startswith("-"):
                        # Hit next section
                        if ":" in line:
                            break
        except:
            pass
        return items
    
    def _save_observations(self, observations: Dict, session_id: int):
        """Save observations to disk"""
        
        # Save full observation
        filepath = self.data_dir / "session_notes" / f"session_{session_id:04d}.json"
        with open(filepath, 'w') as f:
            json.dump(observations, f, indent=2, default=str)
        
        # Append to running log
        log_path = self.data_dir / "observation_log.jsonl"
        with open(log_path, 'a') as f:
            f.write(json.dumps({
                "session_id": session_id,
                "timestamp": observations["timestamp"],
                "has_subject": observations["subject_observation"] is not None,
                "has_pattern": observations["pattern_observation"] is not None,
                "has_system": observations["system_observation"] is not None,
                "has_theoretical": observations["theoretical_observation"] is not None,
                "has_refinement": observations["refinement_proposal"] is not None
            }) + "\n")
    
    def generate_research_report(
        self,
        all_sessions: List[Dict],
        user_profile: Dict
    ) -> str:
        """
        Generate a comprehensive research report.
        
        Called periodically (e.g., every 20 sessions) for deep analysis.
        """
        
        # Load all observations
        all_observations = self._load_all_observations()
        
        prompt = f"""
═══════════════════════════════════════════════════════════════
C2A RESEARCH REPORT REQUEST
═══════════════════════════════════════════════════════════════

You are generating a comprehensive research report on a C2A training subject.

SUBJECT SUMMARY:
- Total sessions: {len(all_sessions)}
- Current level: {user_profile.get('current_level', 1)}
- Training duration: {self._calculate_duration(all_sessions)}
- Average score: {sum(s.get('session_score', 0) for s in all_sessions) / max(len(all_sessions), 1):.1f}

ARCHETYPE PERFORMANCE:
{json.dumps(user_profile.get('archetype_performance', {}), indent=2)}

ALL RESEARCH OBSERVATIONS TO DATE:
{json.dumps(all_observations, indent=2, default=str)[:10000]}  # Truncated for context

SESSION SCORE PROGRESSION:
{self._format_score_progression(all_sessions)}

═══════════════════════════════════════════════════════════════

Generate a comprehensive research report with the following sections:

# C2A RESEARCH REPORT
## Subject: User_001 | Sessions: {len(all_sessions)} | Generated: {datetime.now().strftime('%Y-%m-%d')}

### 1. EXECUTIVE SUMMARY
[2-3 paragraphs: Is C2A working? Key findings? Overall assessment?]

### 2. SUBJECT COGNITIVE PROFILE
[Based on all observations, describe this human's cognitive patterns]
- Dominant strengths
- Persistent weaknesses
- Learning style observations
- Breakthrough moments

### 3. TRAINING PROGRESSION ANALYSIS
[How has the subject progressed?]
- Phase 1 (Transmutation): How did they do?
- Phase 2 (Detection): How did transition go?
- Phase 3/4: Current state
- Velocity/quality tradeoffs observed

### 4. C2A SYSTEM ANALYSIS
[Critical analysis of C2A itself based on this subject's data]
- What's working well
- What's not working
- Gaps identified
- Potential improvements

### 5. ACCUMULATED HYPOTHESES
[Theoretical insights generated during observation]
- About this subject's cognition
- About human cognition generally
- About constraint-thinking as a skill

### 6. REFINEMENT RECOMMENDATIONS
[Priority-ranked list of proposed changes to C2A]
1. [Highest priority]
2. [Second priority]
...

### 7. OPEN QUESTIONS
[What we still don't know and need more data on]

### 8. PREDICTIONS
[Based on current trajectory, what do you predict for this subject?]
- By session 100
- By session 180 (Level 100)
- Long-term

═══════════════════════════════════════════════════════════════
"""
        
        system_prompt = """You are a senior cognitive scientist writing a formal research report.
Be rigorous, evidence-based, and scientific. Cite specific session numbers when making claims.
This report may be used to improve C2A for thousands of future users."""

        report = self.llm.chat(prompt, system=system_prompt, max_tokens=8000)
        
        # Save report
        report_num = len(list((self.data_dir / "reports").glob("*.md"))) + 1
        report_path = self.data_dir / "reports" / f"report_{report_num:03d}_session_{len(all_sessions)}.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        return report
    
    def _load_all_observations(self) -> Dict:
        """Load all observations for report generation"""
        observations = {
            "subject": [],
            "pattern": [],
            "system": [],
            "theoretical": [],
            "refinements": []
        }
        
        session_dir = self.data_dir / "session_notes"
        for f in sorted(session_dir.glob("*.json")):
            try:
                with open(f, 'r') as file:
                    data = json.load(file)
                    if data.get("subject_observation"):
                        observations["subject"].append(data["subject_observation"])
                    if data.get("pattern_observation"):
                        observations["pattern"].append(data["pattern_observation"])
                    if data.get("system_observation"):
                        observations["system"].append(data["system_observation"])
                    if data.get("theoretical_observation"):
                        observations["theoretical"].append(data["theoretical_observation"])
                    if data.get("refinement_proposal"):
                        observations["refinements"].append(data["refinement_proposal"])
            except:
                pass
        
        return observations
    
    def _calculate_duration(self, sessions: List[Dict]) -> str:
        """Calculate training duration"""
        if not sessions:
            return "0 days"
        
        try:
            first = datetime.fromisoformat(sessions[0].get('timestamp', ''))
            last = datetime.fromisoformat(sessions[-1].get('timestamp', ''))
            days = (last - first).days
            return f"{days} days"
        except:
            return "unknown"
    
    def _format_score_progression(self, sessions: List[Dict]) -> str:
        """Format score progression for report"""
        if not sessions:
            return "No sessions yet"
        
        lines = []
        for i in range(0, len(sessions), 10):
            batch = sessions[i:i+10]
            avg = sum(s.get('session_score', 0) for s in batch) / len(batch)
            lines.append(f"Sessions {i+1}-{i+len(batch)}: Avg score {avg:.1f}")
        
        return "\n".join(lines)
    
    def get_latest_observations(self, n: int = 5) -> List[Dict]:
        """Get the most recent observations"""
        session_dir = self.data_dir / "session_notes"
        files = sorted(session_dir.glob("*.json"), reverse=True)[:n]
        
        observations = []
        for f in files:
            try:
                with open(f, 'r') as file:
                    observations.append(json.load(file))
            except:
                pass
        
        return observations
    
    def get_all_refinement_proposals(self) -> List[Dict]:
        """Get all refinement proposals"""
        proposals = []
        session_dir = self.data_dir / "session_notes"
        
        for f in sorted(session_dir.glob("*.json")):
            try:
                with open(f, 'r') as file:
                    data = json.load(file)
                    if data.get("refinement_proposal"):
                        proposals.append({
                            "session_id": data["session_id"],
                            "proposal": data["refinement_proposal"]
                        })
            except:
                pass
        
        return proposals
    
    def get_research_summary(self) -> Dict:
        """Get a quick summary of all research data"""
        session_dir = self.data_dir / "session_notes"
        report_dir = self.data_dir / "reports"
        
        session_files = list(session_dir.glob("*.json"))
        report_files = list(report_dir.glob("*.md"))
        
        # Count observations by type
        counts = {
            "total_sessions_observed": len(session_files),
            "total_reports": len(report_files),
            "subject_observations": 0,
            "pattern_observations": 0,
            "system_observations": 0,
            "theoretical_observations": 0,
            "refinement_proposals": 0
        }
        
        for f in session_files:
            try:
                with open(f, 'r') as file:
                    data = json.load(file)
                    if data.get("subject_observation"):
                        counts["subject_observations"] += 1
                    if data.get("pattern_observation"):
                        counts["pattern_observations"] += 1
                    if data.get("system_observation"):
                        counts["system_observations"] += 1
                    if data.get("theoretical_observation"):
                        counts["theoretical_observations"] += 1
                    if data.get("refinement_proposal"):
                        counts["refinement_proposals"] += 1
            except:
                pass
        
        return counts


# ═══════════════════════════════════════════════════════════════
# USAGE EXAMPLE
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("AI Researcher Module")
    print("=" * 60)
    
    # Initialize
    researcher = AIResearcher()
    
    # Show research summary
    summary = researcher.get_research_summary()
    print(f"\nResearch Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print(f"\nResearch notes directory: {researcher.data_dir}")
    print("\nTo generate observations, call researcher.observe_session() after each C2A session.")
