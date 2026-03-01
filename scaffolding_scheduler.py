"""
scaffolding_scheduler.py
========================
The most important file in C2A.

Not because it does the most — because it determines when everything else
stops doing anything.

Every feature in C2A is scaffolding. Scaffolding is necessary to build the
skill but the goal is to make the scaffolding unnecessary. This file is the
retirement schedule.

Design philosophy:
    Every feature gets built with its own expiry date.
    The question is never "how do I build this feature."
    The question is always "how does this feature retire itself."

The scheduler is queried before every training decision. If a feature is
retired at the user's current level, it doesn't run. Not hidden. Not
optional. Retired.

What retires and when:
    Level 16:  Correction loop disabled. First attempt stands.
    Level 16:  Real-world log becomes available (optional).
    Level 20:  Meta-reflection disabled. The 'I' stops being invited back in.
    Level 20:  AI Researcher drops to every 10 sessions (was every session).
    Level 25:  Active lesson display during drill retired.
    Level 41:  LLM scenario generation retired. Real-world log becomes primary.
    Level 41:  Active lessons auto-retire after 5 attempts (not just mastery).
    Level 41:  AI Researcher drops to every 20 sessions.
    Level 71:  Archetype labels removed from Speed Track. Cold recognition only.
    Level 100: Full training interface retired. Logbook only.

The system is designed to make itself unnecessary.
Level 100 is not the top of the scaffolding. It's the point where the
scaffolding falls away entirely.
"""

from dataclasses import dataclass, field
from typing import Optional


# ─── Retirement Thresholds ────────────────────────────────────────────────────

CORRECTION_LOOP_RETIRES_AT         = 16
REAL_WORLD_LOG_AVAILABLE_AT        = 16
META_REFLECTION_RETIRES_AT         = 20
RESEARCHER_FREQUENCY_DROPS_AT      = 20   # every 10 sessions
ACTIVE_LESSON_DISPLAY_RETIRES_AT   = 25
LLM_SCENARIOS_RETIRE_AT            = 41
REAL_WORLD_LOG_MANDATORY_AT        = 41
ACTIVE_LESSON_ATTEMPT_EXPIRY_AT    = 41   # lessons expire after 5 attempts
RESEARCHER_FREQUENCY_DROPS_AGAIN   = 41   # every 20 sessions
ARCHETYPE_LABELS_RETIRE_AT         = 71   # Speed Track goes cold
FULL_INTERFACE_RETIRES_AT          = 100  # logbook only

# Researcher frequency schedule
RESEARCHER_EVERY_N_SESSIONS = {
    0:  1,   # Level 0-19:  every session
    20: 10,  # Level 20-40: every 10 sessions
    41: 20,  # Level 41+:   every 20 sessions
}

# Active lesson attempt expiry schedule
ACTIVE_LESSON_MAX_ATTEMPTS = {
    0:  None,  # Level 0-40:  never expires by attempt count
    41: 5,     # Level 41+:   retires after 5 attempts regardless of mastery
}

# Speed track rep count schedule
SPEED_TRACK_REPS = {
    0:  0,   # Level 0-15:  Speed Track not yet active
    16: 20,  # Level 16-40: 20 reps per session
    41: 50,  # Level 41-70: 50 reps per session
    71: 50,  # Level 71+:   50 reps, but archetype labels removed
}

# Speed gate thresholds: cannot advance past these levels without hitting speed
SPEED_GATES = {
    15: {'metric': 'pct_under_30s', 'threshold': 0.50,
         'message': "Speed gate at Level 15: 50% of responses must be under 30s."},
    40: {'metric': 'pct_under_15s', 'threshold': 0.50,
         'message': "Speed gate at Level 40: 50% of responses must be under 15s."},
    70: {'metric': 'pct_under_8s',  'threshold': 0.50,
         'message': "Speed gate at Level 70: 50% of responses must be under 8s."},
}


# ─── Feature State ────────────────────────────────────────────────────────────

@dataclass
class FeatureState:
    """
    Snapshot of which features are active at a given level.
    Built by ScaffoldingScheduler.get_feature_state(level).

    Every field has an expiry level. If level >= expiry, the feature is False.
    """
    level: int

    # ── Scaffolding features (start True, retire to False) ─────────────────
    correction_loop_active:       bool = True   # retires at 16
    meta_reflection_active:       bool = True   # retires at 20
    active_lesson_display_active: bool = True   # retires at 25
    llm_scenarios_active:         bool = True   # retires at 41

    # ── Graduated features (start False, activate then retire) ─────────────
    real_world_log_available:     bool = False  # available at 16
    real_world_log_mandatory:     bool = False  # mandatory at 41
    speed_track_active:           bool = False  # activates at 16
    archetype_labels_in_speed:    bool = True   # retires at 71

    # ── Terminal state ──────────────────────────────────────────────────────
    full_interface_active:        bool = True   # retires at 100

    # ── Computed values ─────────────────────────────────────────────────────
    researcher_every_n_sessions:  int  = 1
    speed_track_reps:             int  = 0
    active_lesson_max_attempts:   Optional[int] = None


@dataclass
class SpeedGateStatus:
    """Result of checking whether a level speed gate is passed."""
    gate_level: int
    metric: str
    threshold: float
    current_value: float
    passed: bool
    message: str
    blocked_at: Optional[int] = None  # level the user is locked to if blocked


# ─── ScaffoldingScheduler ─────────────────────────────────────────────────────

class ScaffoldingScheduler:
    """
    Central authority on which features are active at any given level.

    Query this before every training decision. If a feature is retired,
    it does not run. The system makes itself unnecessary on schedule.

    Usage:
        scheduler = ScaffoldingScheduler()
        state = scheduler.get_feature_state(user_level)

        if state.correction_loop_active:
            run_correction_loop()

        if state.real_world_log_mandatory:
            require_real_world_log()

        reps = state.speed_track_reps
        if reps > 0:
            run_speed_track(reps=reps)
    """

    def get_feature_state(self, level: int) -> FeatureState:
        """
        Return the complete feature state for a given level.
        This is the single source of truth for all training decisions.
        """
        state = FeatureState(level=level)

        # ── Scaffolding retirement ──────────────────────────────────────────
        state.correction_loop_active       = level < CORRECTION_LOOP_RETIRES_AT
        state.meta_reflection_active       = level < META_REFLECTION_RETIRES_AT
        state.active_lesson_display_active = level < ACTIVE_LESSON_DISPLAY_RETIRES_AT
        state.llm_scenarios_active         = level < LLM_SCENARIOS_RETIRE_AT
        state.full_interface_active        = level < FULL_INTERFACE_RETIRES_AT

        # ── Feature activation ──────────────────────────────────────────────
        state.real_world_log_available     = level >= REAL_WORLD_LOG_AVAILABLE_AT
        state.real_world_log_mandatory     = level >= REAL_WORLD_LOG_MANDATORY_AT
        state.speed_track_active           = level >= CORRECTION_LOOP_RETIRES_AT  # same gate
        state.archetype_labels_in_speed    = level < ARCHETYPE_LABELS_RETIRE_AT

        # ── Computed: researcher frequency ──────────────────────────────────
        state.researcher_every_n_sessions = self._get_researcher_frequency(level)

        # ── Computed: speed track reps ──────────────────────────────────────
        state.speed_track_reps = self._get_speed_track_reps(level)

        # ── Computed: active lesson max attempts ────────────────────────────
        state.active_lesson_max_attempts = self._get_lesson_max_attempts(level)

        return state

    def check_speed_gate(self, level: int, speed_stats: dict) -> SpeedGateStatus:
        """
        Check whether the user has passed the speed gate for their level.

        speed_stats should contain:
            pct_under_30s: float (0.0 - 1.0)
            pct_under_15s: float (0.0 - 1.0)
            pct_under_8s:  float (0.0 - 1.0)

        Returns SpeedGateStatus indicating whether the user is gated.

        If no speed data exists yet (new user), gates are not applied —
        the system gives benefit of the doubt until data exists.
        """
        # Find the highest gate that applies to this level
        active_gate_level = None
        for gate_level in sorted(SPEED_GATES.keys(), reverse=True):
            if level > gate_level:
                active_gate_level = gate_level
                break

        if active_gate_level is None:
            # No gate applies yet
            return SpeedGateStatus(
                gate_level=0,
                metric='none',
                threshold=0.0,
                current_value=1.0,
                passed=True,
                message="No speed gate at this level.",
            )

        gate = SPEED_GATES[active_gate_level]
        metric = gate['metric']
        threshold = gate['threshold']
        current = speed_stats.get(metric, None)

        # No speed data yet — don't block
        if current is None:
            return SpeedGateStatus(
                gate_level=active_gate_level,
                metric=metric,
                threshold=threshold,
                current_value=0.0,
                passed=True,
                message="No speed data yet. Complete Speed Track sessions to unlock gate check.",
            )

        passed = current >= threshold
        return SpeedGateStatus(
            gate_level=active_gate_level,
            metric=metric,
            threshold=threshold,
            current_value=current,
            passed=passed,
            message=gate['message'] if not passed else f"Speed gate passed: {metric} = {current:.0%}",
            blocked_at=active_gate_level if not passed else None,
        )

    def apply_speed_gate(self, raw_level: int, speed_stats: dict) -> int:
        """
        Apply speed gate to a computed level. Returns the actual effective level.

        If the user has not passed the speed gate for their raw level,
        their effective level is capped at the gate level.

        This is called by MemorySystem._calculate_level().
        """
        if not speed_stats:
            return raw_level  # No data, no gate applied

        status = self.check_speed_gate(raw_level, speed_stats)
        if not status.passed and status.blocked_at is not None:
            return status.blocked_at
        return raw_level

    def should_run_researcher(self, level: int, session_number: int) -> bool:
        """
        Returns True if the AI Researcher should observe this session.

        session_number: total sessions completed by the user (1-indexed).
        """
        every_n = self._get_researcher_frequency(level)
        return (session_number % every_n) == 0

    def get_retirement_schedule(self) -> list:
        """
        Returns the full retirement schedule as a list of dicts,
        sorted by level. Used for display in the UI.
        """
        return [
            {
                'level': CORRECTION_LOOP_RETIRES_AT,
                'event': 'Correction loop retired',
                'detail': 'First attempt stands. No retries.',
                'type': 'retirement',
            },
            {
                'level': REAL_WORLD_LOG_AVAILABLE_AT,
                'event': 'Real-world log unlocked',
                'detail': 'Log constraints encountered in daily life.',
                'type': 'activation',
            },
            {
                'level': CORRECTION_LOOP_RETIRES_AT,
                'event': 'Speed Track activated',
                'detail': '20 archetype-tap reps per session. No LLM.',
                'type': 'activation',
            },
            {
                'level': META_REFLECTION_RETIRES_AT,
                'event': 'Meta-reflection retired',
                'detail': "The 'I' is no longer invited back in.",
                'type': 'retirement',
            },
            {
                'level': META_REFLECTION_RETIRES_AT,
                'event': 'AI Researcher drops to every 10 sessions',
                'detail': 'Research overhead reduced.',
                'type': 'change',
            },
            {
                'level': ACTIVE_LESSON_DISPLAY_RETIRES_AT,
                'event': 'Active lesson display retired',
                'detail': 'Lessons no longer shown during drill.',
                'type': 'retirement',
            },
            {
                'level': LLM_SCENARIOS_RETIRE_AT,
                'event': 'LLM scenario generation retired',
                'detail': 'Real-world log becomes primary training mode.',
                'type': 'retirement',
            },
            {
                'level': REAL_WORLD_LOG_MANDATORY_AT,
                'event': 'Real-world log mandatory',
                'detail': 'Log 3 real constraints daily. LLM reviews weekly.',
                'type': 'change',
            },
            {
                'level': ACTIVE_LESSON_ATTEMPT_EXPIRY_AT,
                'event': 'Active lessons expire after 5 attempts',
                'detail': 'System trusts the reps, not conscious application.',
                'type': 'change',
            },
            {
                'level': RESEARCHER_FREQUENCY_DROPS_AGAIN,
                'event': 'AI Researcher drops to every 20 sessions',
                'detail': 'Minimal research overhead at this stage.',
                'type': 'change',
            },
            {
                'level': ARCHETYPE_LABELS_RETIRE_AT,
                'event': 'Archetype labels removed from Speed Track',
                'detail': 'Cold recognition only. No priming.',
                'type': 'retirement',
            },
            {
                'level': FULL_INTERFACE_RETIRES_AT,
                'event': 'Full training interface retired',
                'detail': 'Logbook only. The scaffolding is gone.',
                'type': 'retirement',
            },
        ]

    def describe_current_phase(self, level: int) -> dict:
        """
        Returns a human-readable description of the user's current phase.
        Used in the main menu status display.
        """
        if level < CORRECTION_LOOP_RETIRES_AT:
            return {
                'phase': 1,
                'name': 'Install',
                'description': 'Building the vocabulary. Archetypes become legible.',
                'next_event': f'Correction loop retires at Level {CORRECTION_LOOP_RETIRES_AT}.',
            }
        elif level < META_REFLECTION_RETIRES_AT:
            return {
                'phase': 2,
                'name': 'Groove (Early)',
                'description': 'Speed Track active. First attempts only. No retries.',
                'next_event': f'Meta-reflection retires at Level {META_REFLECTION_RETIRES_AT}.',
            }
        elif level < ACTIVE_LESSON_DISPLAY_RETIRES_AT:
            return {
                'phase': 2,
                'name': 'Groove (Mid)',
                'description': 'Conscious layer support reducing. Speed reps accumulating.',
                'next_event': f'Active lesson display retires at Level {ACTIVE_LESSON_DISPLAY_RETIRES_AT}.',
            }
        elif level < LLM_SCENARIOS_RETIRE_AT:
            return {
                'phase': 2,
                'name': 'Groove (Late)',
                'description': 'Minimal scaffolding. Speed is the primary metric.',
                'next_event': f'LLM scenarios retire at Level {LLM_SCENARIOS_RETIRE_AT}.',
            }
        elif level < ARCHETYPE_LABELS_RETIRE_AT:
            return {
                'phase': 3,
                'name': 'Pressure',
                'description': 'Real-world log is primary. 50 reps per session.',
                'next_event': f'Archetype labels removed at Level {ARCHETYPE_LABELS_RETIRE_AT}.',
            }
        elif level < FULL_INTERFACE_RETIRES_AT:
            return {
                'phase': 3,
                'name': 'Pressure (Cold)',
                'description': 'No labels. No priming. Cold recognition only.',
                'next_event': f'Full interface retires at Level {FULL_INTERFACE_RETIRES_AT}.',
            }
        else:
            return {
                'phase': 4,
                'name': 'Install Complete',
                'description': 'The scaffolding is gone. The logbook is all that remains.',
                'next_event': 'None. The operation runs on its own.',
            }

    def get_next_retirement(self, level: int) -> Optional[dict]:
        """
        Returns the next scheduled retirement event for this level.
        Used in the UI to give users visibility into what's coming.
        """
        schedule = sorted(self.get_retirement_schedule(), key=lambda x: x['level'])
        for event in schedule:
            if event['level'] > level:
                return event
        return None

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_researcher_frequency(self, level: int) -> int:
        """Returns how often (every N sessions) the researcher should observe."""
        result = 1
        for threshold, frequency in sorted(RESEARCHER_EVERY_N_SESSIONS.items()):
            if level >= threshold:
                result = frequency
        return result

    def _get_speed_track_reps(self, level: int) -> int:
        """Returns the number of Speed Track reps for this level."""
        result = 0
        for threshold, reps in sorted(SPEED_TRACK_REPS.items()):
            if level >= threshold:
                result = reps
        return result

    def _get_lesson_max_attempts(self, level: int) -> Optional[int]:
        """Returns the max attempts for an active lesson before auto-expiry."""
        result = None
        for threshold, max_attempts in sorted(ACTIVE_LESSON_MAX_ATTEMPTS.items()):
            if level >= threshold:
                result = max_attempts
        return result


# ─── Singleton ────────────────────────────────────────────────────────────────

# Single instance — import and use anywhere in the codebase
scheduler = ScaffoldingScheduler()


# ─── CLI for inspection ───────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys

    level = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    s = ScaffoldingScheduler()
    state = s.get_feature_state(level)
    phase = s.describe_current_phase(level)
    next_event = s.get_next_retirement(level)

    print(f"\n{'='*60}")
    print(f"  C2A Scaffolding Scheduler — Level {level}")
    print(f"{'='*60}")
    print(f"\n  Phase {phase['phase']}: {phase['name']}")
    print(f"  {phase['description']}")
    print(f"\n{'─'*60}")
    print(f"  FEATURE STATE")
    print(f"{'─'*60}")
    print(f"  Correction loop:          {'✓ ACTIVE' if state.correction_loop_active else '✗ RETIRED (lv.16)'}")
    print(f"  Meta-reflection:          {'✓ ACTIVE' if state.meta_reflection_active else '✗ RETIRED (lv.20)'}")
    print(f"  Active lesson display:    {'✓ ACTIVE' if state.active_lesson_display_active else '✗ RETIRED (lv.25)'}")
    print(f"  LLM scenarios:            {'✓ ACTIVE' if state.llm_scenarios_active else '✗ RETIRED (lv.41)'}")
    print(f"  Speed Track:              {'✓ ACTIVE' if state.speed_track_active else '✗ NOT YET (activates lv.16)'}")
    print(f"  Speed Track reps:         {state.speed_track_reps}")
    print(f"  Archetype labels (speed): {'✓ SHOWN' if state.archetype_labels_in_speed else '✗ HIDDEN (cold)'}")
    print(f"  Real-world log:           {'✓ AVAILABLE' if state.real_world_log_available else '✗ NOT YET (lv.16)'}")
    print(f"  Real-world log mandatory: {'✓ YES' if state.real_world_log_mandatory else '✗ OPTIONAL'}")
    print(f"  Lesson max attempts:      {state.active_lesson_max_attempts or 'None (no expiry)'}")
    print(f"  Researcher every N:       {state.researcher_every_n_sessions} sessions")
    print(f"  Full interface:           {'✓ ACTIVE' if state.full_interface_active else '✗ RETIRED (logbook only)'}")

    if next_event:
        print(f"\n{'─'*60}")
        print(f"  NEXT RETIREMENT: Level {next_event['level']}")
        print(f"  {next_event['event']}")
        print(f"  {next_event['detail']}")

    print(f"\n{'='*60}\n")
