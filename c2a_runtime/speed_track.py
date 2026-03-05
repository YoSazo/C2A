"""
speed_track.py
==============
The actual automaticity installer.

This is the core rep machine. Not a side feature. Not a bonus drill.
The primary vehicle for installing constraint transmutation below the
conscious layer through volume at speed.

Philosophy:
    Automaticity is not built through depth per rep.
    It is built through volume at speed with minimal conscious engagement.

    The Flash Drill was the seed of this. This is the elevation.

What this is NOT:
    - Not an LLM evaluation loop
    - Not a correction loop
    - Not a meta-reflection exercise
    - Not a scored training session

What this IS:
    - 20-50 constraints shown one at a time
    - User taps archetype (1-5 key) for each
    - No written response. No LLM. No feedback during drill.
    - Scored purely on speed distribution after completion
    - Takes ~5 minutes
    - Mandatory above Level 15 (enforced by ScaffoldingScheduler)

Retirement schedule (from ScaffoldingScheduler):
    Level 16-40:  Active, 20 reps, archetype labels shown
    Level 41-70:  Active, 50 reps, archetype labels shown
    Level 71-99:  Active, 50 reps, archetype labels HIDDEN (cold recognition)
    Level 100:    Full interface retired — Speed Track no longer presented

Speed gates (enforced by ScaffoldingScheduler):
    Level 15 gate: 50% of responses must be under 30s
    Level 40 gate: 50% of responses must be under 15s
    Level 70 gate: 50% of responses must be under 8s
"""

import time
import json
import os
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

from constraint_archetypes import ARCHETYPES, get_archetype
from scaffolding_scheduler import scheduler


# ─── Built-in constraint pool ────────────────────────────────────────────────
# These are abstract, domain-agnostic constraints.
# No real-world framing. Pure structural constraint.
# Used when LLM is not available or level >= 41.

CONSTRAINT_POOL = [
    # Scarcity
    ("Only one hour remains.", "scarcity"),
    ("The budget is half what you need.", "scarcity"),
    ("Three people must do the work of ten.", "scarcity"),
    ("The material runs out halfway through.", "scarcity"),
    ("Only the lowest-quality option is available.", "scarcity"),
    ("The space is a quarter of what was planned.", "scarcity"),
    ("One tool where five are needed.", "scarcity"),
    ("The signal is too weak to transmit.", "scarcity"),
    ("Two days where two weeks were assumed.", "scarcity"),
    ("The audience is ten instead of a thousand.", "scarcity"),

    # Velocity
    ("The deadline moved up by a week.", "velocity"),
    ("The decision must be made in thirty seconds.", "velocity"),
    ("The window closes in an hour.", "velocity"),
    ("The opportunity expires at midnight.", "velocity"),
    ("Every minute of delay costs the outcome.", "velocity"),
    ("The first mover wins everything.", "velocity"),
    ("The meeting starts in five minutes.", "velocity"),
    ("The launch cannot slip.", "velocity"),
    ("Momentum is lost if you stop now.", "velocity"),
    ("The tide turns in one hour.", "velocity"),

    # Asymmetry
    ("You know the problem but not the cause.", "asymmetry"),
    ("The other party has all the information.", "asymmetry"),
    ("You must decide without knowing the outcome.", "asymmetry"),
    ("The map does not match the territory.", "asymmetry"),
    ("You can see the effect but not the source.", "asymmetry"),
    ("The data arrives after the decision is needed.", "asymmetry"),
    ("You know what happened but not why.", "asymmetry"),
    ("The other side knows your position; you don't know theirs.", "asymmetry"),
    ("The signal exists but cannot be decoded.", "asymmetry"),
    ("You are the only one who doesn't know.", "asymmetry"),

    # Friction
    ("Every attempt meets resistance.", "friction"),
    ("The system rejects the input.", "friction"),
    ("The tool breaks on the hardest task.", "friction"),
    ("Every step forward creates two steps back.", "friction"),
    ("The path requires more force than available.", "friction"),
    ("The process takes ten times longer than expected.", "friction"),
    ("The environment actively works against the goal.", "friction"),
    ("Each layer of approval adds three weeks.", "friction"),
    ("The medium distorts the message.", "friction"),
    ("The connection fails at the critical moment.", "friction"),

    # Paradox
    ("Slowing down is the only way to go faster.", "paradox"),
    ("Admitting weakness is the only source of strength.", "paradox"),
    ("The solution requires creating the problem first.", "paradox"),
    ("Letting go is the only way to hold on.", "paradox"),
    ("The answer requires accepting there is no answer.", "paradox"),
    ("Moving backward is the only path forward.", "paradox"),
    ("The constraint disappears only when embraced.", "paradox"),
    ("Saying less communicates more.", "paradox"),
    ("The most direct route requires the longest detour.", "paradox"),
    ("Reducing options is the only way to expand them.", "paradox"),
]

ARCHETYPE_KEYS = {
    '1': 'scarcity',
    '2': 'velocity',
    '3': 'asymmetry',
    '4': 'friction',
    '5': 'paradox',
}

ARCHETYPE_SYMBOLS = {
    'scarcity':  '⧗',
    'velocity':  '⚡',
    'asymmetry': '⚖',
    'friction':  '⚙',
    'paradox':   '∞',
}

ARCHETYPE_COLORS = {
    'scarcity':  '\033[38;5;214m',   # orange
    'velocity':  '\033[38;5;226m',   # yellow
    'asymmetry': '\033[38;5;51m',    # cyan
    'friction':  '\033[38;5;196m',   # red
    'paradox':   '\033[38;5;135m',   # purple
}

RESET  = '\033[0m'
BOLD   = '\033[1m'
DIM    = '\033[2m'
GREEN  = '\033[38;5;82m'
YELLOW = '\033[38;5;226m'
RED    = '\033[38;5;196m'
CYAN   = '\033[38;5;51m'
WHITE  = '\033[97m'


# ─── Data structures ─────────────────────────────────────────────────────────

@dataclass
class RepResult:
    """Result of a single Speed Track rep."""
    constraint_text: str
    correct_archetype: str
    user_archetype: str
    correct: bool
    duration_seconds: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SpeedTrackSession:
    """Complete record of one Speed Track session."""
    session_id: str
    level: int
    reps: int
    archetype_labels_shown: bool
    results: list = field(default_factory=list)

    # Computed after session
    total_duration_seconds: float = 0.0
    accuracy: float = 0.0
    pct_under_8s: float = 0.0
    pct_under_15s: float = 0.0
    pct_under_30s: float = 0.0
    median_response_s: float = 0.0
    fastest_s: float = 0.0
    slowest_s: float = 0.0

    completed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d['results'] = [asdict(r) for r in self.results]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'SpeedTrackSession':
        results = [RepResult(**r) for r in data.pop('results', [])]
        session = cls(**data)
        session.results = results
        return session


@dataclass
class SpeedStats:
    """
    Aggregated speed statistics across all Speed Track sessions.
    This is what ScaffoldingScheduler.apply_speed_gate() reads.
    """
    total_sessions: int = 0
    total_reps: int = 0
    overall_accuracy: float = 0.0
    pct_under_8s: float = 0.0
    pct_under_15s: float = 0.0
    pct_under_30s: float = 0.0
    median_response_s: float = 0.0
    archetype_accuracy: dict = field(default_factory=dict)
    weakest_archetype: Optional[str] = None
    recent_trend: str = 'insufficient_data'  # improving / plateau / declining

    def to_dict(self) -> dict:
        return asdict(self)


# ─── SpeedTrack ──────────────────────────────────────────────────────────────

class SpeedTrack:
    """
    The Speed Track drill.

    Instantiate once per run, call run_session() to execute a drill.
    Persists session history to memory_data/speed_track_sessions.json.
    """

    DATA_FILE = os.path.join('memory_data', 'speed_track_sessions.json')

    def __init__(self, data_dir: str = 'memory_data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.data_file = os.path.join(data_dir, 'speed_track_sessions.json')
        self.sessions: list = self._load_sessions()

    # ── Public API ────────────────────────────────────────────────────────────

    def run_session(self, level: int, custom_constraints: Optional[list] = None) -> SpeedTrackSession:
        """
        Run a complete Speed Track session for the given level.

        custom_constraints: optional list of (text, archetype) tuples.
            If None, draws from built-in CONSTRAINT_POOL.

        Returns the completed SpeedTrackSession with all stats computed.
        """
        state = scheduler.get_feature_state(level)
        reps = state.speed_track_reps
        show_labels = state.archetype_labels_in_speed

        if reps == 0:
            print(f"\n{YELLOW}Speed Track activates at Level 16.{RESET}\n")
            return None

        session_id = f"speed_{int(time.time())}"
        session = SpeedTrackSession(
            session_id=session_id,
            level=level,
            reps=reps,
            archetype_labels_shown=show_labels,
        )

        constraints = self._select_constraints(reps, custom_constraints)

        self._show_intro(reps, show_labels, level)
        input(f"\n  {DIM}Press ENTER to begin...{RESET}")

        results = []
        for i, (text, correct_arch) in enumerate(constraints):
            result = self._run_rep(i + 1, reps, text, correct_arch, show_labels)
            results.append(result)
            session.results = results
            self._show_rep_feedback(result, show_labels)

        session.results = results
        self._compute_stats(session)
        self._save_session(session)

        self._show_results(session, level)
        return session

    def get_speed_stats(self) -> SpeedStats:
        """
        Compute aggregated SpeedStats across all sessions.
        This is what ScaffoldingScheduler.apply_speed_gate() reads.
        """
        if not self.sessions:
            return SpeedStats()

        all_results = []
        for s in self.sessions:
            all_results.extend(s.results)

        if not all_results:
            return SpeedStats()

        durations = [r.duration_seconds for r in all_results]
        correct = [r for r in all_results if r.correct]

        stats = SpeedStats(
            total_sessions=len(self.sessions),
            total_reps=len(all_results),
            overall_accuracy=len(correct) / len(all_results) if all_results else 0.0,
            pct_under_8s=sum(1 for d in durations if d < 8) / len(durations),
            pct_under_15s=sum(1 for d in durations if d < 15) / len(durations),
            pct_under_30s=sum(1 for d in durations if d < 30) / len(durations),
            median_response_s=sorted(durations)[len(durations) // 2],
        )

        # Per-archetype accuracy
        for arch in ARCHETYPES:
            arch_results = [r for r in all_results if r.correct_archetype == arch]
            if arch_results:
                arch_correct = [r for r in arch_results if r.correct]
                stats.archetype_accuracy[arch] = len(arch_correct) / len(arch_results)

        if stats.archetype_accuracy:
            stats.weakest_archetype = min(
                stats.archetype_accuracy, key=stats.archetype_accuracy.get
            )

        # Trend: compare last 3 sessions to previous 3
        if len(self.sessions) >= 6:
            recent = self.sessions[-3:]
            prior  = self.sessions[-6:-3]
            recent_acc = sum(s.accuracy for s in recent) / 3
            prior_acc  = sum(s.accuracy for s in prior) / 3
            if recent_acc > prior_acc + 0.05:
                stats.recent_trend = 'improving'
            elif recent_acc < prior_acc - 0.05:
                stats.recent_trend = 'declining'
            else:
                stats.recent_trend = 'plateau'

        return stats

    def get_stats_dict(self) -> dict:
        """Returns speed stats as a plain dict for use in level gating."""
        return self.get_speed_stats().to_dict()

    # ── Session execution ─────────────────────────────────────────────────────

    def _run_rep(
        self,
        rep_num: int,
        total_reps: int,
        constraint_text: str,
        correct_archetype: str,
        show_labels: bool,
    ) -> RepResult:
        """Run a single rep. Returns RepResult."""
        self._clear_line()
        self._show_rep_header(rep_num, total_reps)
        self._show_constraint(constraint_text)

        if show_labels:
            self._show_archetype_menu()
        else:
            print(f"\n  {DIM}1-5  →  tap archetype{RESET}")

        start = time.time()
        user_key = self._get_single_keypress()
        duration = time.time() - start

        user_arch = ARCHETYPE_KEYS.get(user_key, '')
        correct = (user_arch == correct_archetype)

        return RepResult(
            constraint_text=constraint_text,
            correct_archetype=correct_archetype,
            user_archetype=user_arch,
            correct=correct,
            duration_seconds=round(duration, 2),
        )

    def _show_rep_feedback(self, result: RepResult, show_labels: bool):
        """Minimal per-rep feedback. Just enough to calibrate, not enough to engage."""
        symbol = '✓' if result.correct else '✗'
        color  = GREEN if result.correct else RED
        speed_indicator = self._speed_indicator(result.duration_seconds)

        if show_labels and not result.correct:
            correct_sym = ARCHETYPE_SYMBOLS.get(result.correct_archetype, '?')
            correct_col = ARCHETYPE_COLORS.get(result.correct_archetype, '')
            print(
                f"  {color}{symbol}{RESET}  {speed_indicator}  "
                f"{DIM}→ {correct_col}{correct_sym} {result.correct_archetype}{RESET}"
            )
        else:
            print(f"  {color}{symbol}{RESET}  {speed_indicator}")

        time.sleep(0.3)

    # ── Display helpers ───────────────────────────────────────────────────────

    def _show_intro(self, reps: int, show_labels: bool, level: int):
        """Show drill intro screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n{BOLD}{'─'*56}{RESET}")
        print(f"{BOLD}  ⚡ SPEED TRACK  {DIM}Level {level}{RESET}")
        print(f"{BOLD}{'─'*56}{RESET}")
        print(f"\n  {reps} constraints. Tap the archetype. No writing.")
        print(f"  No LLM. No feedback during drill.")

        if show_labels:
            print(f"\n  {DIM}Archetype keys:{RESET}")
            for key, arch in ARCHETYPE_KEYS.items():
                sym = ARCHETYPE_SYMBOLS[arch]
                col = ARCHETYPE_COLORS[arch]
                print(f"    {BOLD}{key}{RESET}  {col}{sym} {arch}{RESET}")
        else:
            print(f"\n  {DIM}No labels shown. Cold recognition.{RESET}")
            print(f"  {DIM}Keys: 1=scarcity  2=velocity  3=asymmetry  4=friction  5=paradox{RESET}")

        print(f"\n  {DIM}After the drill: speed distribution shown. That's all.{RESET}")

    def _show_rep_header(self, rep_num: int, total_reps: int):
        """Minimal rep counter."""
        pct = rep_num / total_reps
        bar_width = 40
        filled = int(bar_width * pct)
        bar = '█' * filled + '░' * (bar_width - filled)
        print(f"\n  {DIM}[{bar}] {rep_num}/{total_reps}{RESET}\n")

    def _show_constraint(self, text: str):
        """Display the constraint text prominently."""
        print(f"  {BOLD}{WHITE}{text}{RESET}\n")

    def _show_archetype_menu(self):
        """Compact archetype key reference."""
        parts = []
        for key, arch in ARCHETYPE_KEYS.items():
            sym = ARCHETYPE_SYMBOLS[arch]
            col = ARCHETYPE_COLORS[arch]
            parts.append(f"{BOLD}{key}{RESET}{col}{sym}{RESET}")
        print(f"  {' · '.join(parts)}")

    def _show_results(self, session: SpeedTrackSession, level: int):
        """Post-drill results. Speed distribution only. No per-rep breakdown."""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n{BOLD}{'─'*56}{RESET}")
        print(f"{BOLD}  ⚡ SPEED TRACK COMPLETE{RESET}")
        print(f"{BOLD}{'─'*56}{RESET}")

        print(f"\n  {BOLD}Accuracy:{RESET}   {self._pct_color(session.accuracy)}{session.accuracy:.0%}{RESET}")
        print(f"  {BOLD}Median:{RESET}     {session.median_response_s:.1f}s per rep")
        print(f"  {BOLD}Fastest:{RESET}    {session.fastest_s:.1f}s")

        print(f"\n  {BOLD}Speed distribution:{RESET}")
        print(f"  {self._dist_bar(session.pct_under_8s)}  under 8s   {DIM}(reflexive){RESET}")
        print(f"  {self._dist_bar(session.pct_under_15s)}  under 15s  {DIM}(fast){RESET}")
        print(f"  {self._dist_bar(session.pct_under_30s)}  under 30s  {DIM}(deliberate){RESET}")

        # Per-archetype accuracy
        arch_results = {}
        for r in session.results:
            arch = r.correct_archetype
            if arch not in arch_results:
                arch_results[arch] = {'correct': 0, 'total': 0}
            arch_results[arch]['total'] += 1
            if r.correct:
                arch_results[arch]['correct'] += 1

        if arch_results:
            print(f"\n  {BOLD}By archetype:{RESET}")
            for arch, counts in arch_results.items():
                acc = counts['correct'] / counts['total']
                sym = ARCHETYPE_SYMBOLS.get(arch, '?')
                col = ARCHETYPE_COLORS.get(arch, '')
                bar = self._dist_bar(acc)
                print(f"  {col}{sym} {arch:<12}{RESET}  {bar}  {acc:.0%}")

        # Speed gate status
        stats = self.get_speed_stats()
        gate_status = scheduler.check_speed_gate(level, stats.to_dict())
        print(f"\n  {BOLD}Speed gate:{RESET}")
        if gate_status.passed:
            print(f"  {GREEN}✓ {gate_status.message}{RESET}")
        else:
            print(f"  {YELLOW}⚠ {gate_status.message}{RESET}")
            print(f"  {DIM}  Current: {gate_status.current_value:.0%}  Target: {gate_status.threshold:.0%}{RESET}")

        print(f"\n{'─'*56}\n")

    # ── Stats computation ─────────────────────────────────────────────────────

    def _compute_stats(self, session: SpeedTrackSession):
        """Compute and store stats on the session object."""
        results = session.results
        if not results:
            return

        durations = [r.duration_seconds for r in results]
        correct   = [r for r in results if r.correct]

        session.accuracy       = len(correct) / len(results)
        session.pct_under_8s   = sum(1 for d in durations if d < 8) / len(durations)
        session.pct_under_15s  = sum(1 for d in durations if d < 15) / len(durations)
        session.pct_under_30s  = sum(1 for d in durations if d < 30) / len(durations)
        session.total_duration_seconds = sum(durations)
        session.median_response_s = sorted(durations)[len(durations) // 2]
        session.fastest_s      = min(durations)
        session.slowest_s      = max(durations)

    # ── Constraint selection ──────────────────────────────────────────────────

    def _select_constraints(self, n: int, custom: Optional[list]) -> list:
        """Select n constraints for the drill."""
        pool = custom if custom else CONSTRAINT_POOL

        # Shuffle and cycle if needed
        shuffled = random.sample(pool, min(len(pool), n))
        if len(shuffled) < n:
            extra = random.choices(pool, k=n - len(shuffled))
            shuffled.extend(extra)
        return shuffled[:n]

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load_sessions(self) -> list:
        if not os.path.exists(self.data_file):
            return []
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            return [SpeedTrackSession.from_dict(d) for d in data]
        except Exception:
            return []

    def _save_session(self, session: SpeedTrackSession):
        self.sessions.append(session)
        try:
            with open(self.data_file, 'w') as f:
                json.dump([s.to_dict() for s in self.sessions], f, indent=2)
        except Exception as e:
            print(f"{RED}Warning: could not save Speed Track session: {e}{RESET}")

    # ── Terminal helpers ──────────────────────────────────────────────────────

    def _get_single_keypress(self) -> str:
        """Get a single keypress without requiring Enter."""
        try:
            import sys
            if os.name == 'nt':
                import msvcrt
                key = msvcrt.getch().decode('utf-8', errors='ignore')
            else:
                import tty, termios
                fd = sys.stdin.fileno()
                old = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    key = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old)
            return key.strip()
        except Exception:
            # Fallback to line input
            return input().strip()[:1]

    def _clear_line(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def _speed_indicator(self, seconds: float) -> str:
        if seconds < 8:
            return f"{GREEN}⚡ {seconds:.1f}s{RESET}"
        elif seconds < 15:
            return f"{CYAN}✓ {seconds:.1f}s{RESET}"
        elif seconds < 30:
            return f"{YELLOW}○ {seconds:.1f}s{RESET}"
        else:
            return f"{RED}✗ {seconds:.1f}s{RESET}"

    def _dist_bar(self, pct: float) -> str:
        width = 20
        filled = int(width * pct)
        color = GREEN if pct >= 0.5 else (YELLOW if pct >= 0.3 else RED)
        return f"{color}{'█' * filled}{'░' * (width - filled)}{RESET} {pct:.0%}"

    def _pct_color(self, pct: float) -> str:
        if pct >= 0.85:
            return GREEN
        elif pct >= 0.70:
            return CYAN
        elif pct >= 0.50:
            return YELLOW
        return RED


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    level = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    track = SpeedTrack()
    track.run_session(level=level)
