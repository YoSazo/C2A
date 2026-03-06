"""
real_world_log.py
=================
The transfer confirmation system.

The Speed Track installs the operation through volume.
The real-world log confirms the transfer is happening.

Philosophy:
    Training sessions happen in a controlled environment.
    The only thing that actually matters is whether constraint
    transmutation is happening in life — spontaneously, without
    prompting, without a training interface.

    The physics conversation happened at Level 5. Spontaneously.
    The system wasn't tracking it. That was data lost.

    This file makes sure that never happens again.

What this is:
    A daily log of real constraints encountered and how they were
    transmuted. Available from Level 16 (optional). Mandatory at Level 41.

    The log asks three questions per constraint:
        1. What was the constraint?
        2. How did you transmute it?
        3. What new constraint did the trade produce?

    Question 3 is the most important. It confirms the loop is running —
    that the user understands every trade produces the next constraint.
    The loop never stops. The goal is to stop being surprised by it.

What this is NOT:
    - Not a scored exercise
    - Not an LLM evaluation loop (daily)
    - Not a reflection prompt
    - Not a lesson system

LLM involvement:
    Minimal and delayed. The LLM reviews a 20% random sample of entries
    weekly — not daily. It looks for one thing only: is the loop stopping?
    If yes, where? No scores. No achievements. Just a mirror.

Retirement schedule (from ScaffoldingScheduler):
    Level 16:  Available, optional
    Level 41:  Mandatory (3 entries per day)
    Level 100: Interface retired — logbook is all that remains

The logbook is what's left when all the scaffolding is gone.
"""

import json
import os
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Optional

from scaffolding_scheduler import scheduler

RESET  = '\033[0m'
BOLD   = '\033[1m'
DIM    = '\033[2m'
ITALIC = '\033[3m'
GREEN  = '\033[38;5;82m'
YELLOW = '\033[38;5;226m'
RED    = '\033[38;5;196m'
CYAN   = '\033[38;5;51m'
GOLD   = '\033[38;5;220m'
WHITE  = '\033[97m'


# ─── Data structures ─────────────────────────────────────────────────────────

@dataclass
class ConstraintEntry:
    """
    A single real-world constraint log entry.

    Three fields. That's all.
    The third field is the most important.
    """
    entry_id: str
    logged_at: str                    # ISO timestamp
    date_str: str                     # YYYY-MM-DD for daily grouping

    # The three questions
    constraint: str                   # What was the constraint?
    transmutation: str                # How did you transmute it?
    new_constraint: str               # What new constraint did the trade produce?

    # Optional metadata
    archetype_guess: Optional[str] = None   # User's archetype tag (optional)
    domain: Optional[str] = None            # Life / Work / Creative / etc.

    # LLM review fields (populated during weekly review)
    reviewed: bool = False
    review_notes: Optional[str] = None
    loop_continuing: Optional[bool] = None  # Is the loop still running?

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'ConstraintEntry':
        return cls(**data)


@dataclass
class DailyLog:
    """All entries for a single day."""
    date_str: str
    entries: list = field(default_factory=list)

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    @property
    def is_complete(self) -> bool:
        """A daily log is complete if it has at least 3 entries."""
        return len(self.entries) >= 3

    def to_dict(self) -> dict:
        return {
            'date_str': self.date_str,
            'entries': [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DailyLog':
        entries = [ConstraintEntry.from_dict(e) for e in data.get('entries', [])]
        log = cls(date_str=data['date_str'])
        log.entries = entries
        return log


@dataclass
class WeeklyReview:
    """LLM review of a week's log sample."""
    review_id: str
    reviewed_at: str
    week_start: str
    week_end: str
    entries_reviewed: int
    total_entries: int
    loop_assessment: str       # Is the loop running? If not, where is it stopping?
    patterns_noted: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ─── RealWorldLog ─────────────────────────────────────────────────────────────

class RealWorldLog:
    """
    The real-world constraint log.

    Available at Level 16. Mandatory at Level 41.
    LLM reviews 20% of entries weekly.
    The only question it answers: is the loop still running?
    """

    LOG_FILE     = 'real_world_log.json'
    REVIEWS_FILE = 'real_world_reviews.json'
    DAILY_MINIMUM = 3  # entries required when mandatory

    def __init__(self, data_dir: str = 'memory_data', llm_client=None):
        self.data_dir    = data_dir
        self.llm         = llm_client
        self.log_file    = os.path.join(data_dir, self.LOG_FILE)
        self.reviews_file = os.path.join(data_dir, self.REVIEWS_FILE)
        os.makedirs(data_dir, exist_ok=True)

        self.entries: list = self._load_entries()
        self.reviews: list = self._load_reviews()

    # ── Public API ─────────────────────────────────────────────────────────────

    def run_daily_log(self, level: int) -> list:
        """
        Interactive daily log session.

        Available at Level 16, mandatory at Level 41.
        Returns list of ConstraintEntry objects logged this session.
        """
        state = scheduler.get_feature_state(level)

        if not state.real_world_log_available:
            print(f"\n{YELLOW}Real-world log unlocks at Level 16.{RESET}\n")
            return []

        mandatory = state.real_world_log_mandatory
        today = self._today()
        existing_today = self._get_entries_for_date(today)
        already_logged = len(existing_today)

        self._show_intro(level, mandatory, already_logged)

        if mandatory and already_logged >= self.DAILY_MINIMUM:
            print(f"\n  {GREEN}✓ Today's log complete ({already_logged} entries).{RESET}")
            choice = input(f"\n  {DIM}Add another entry? (y/n): {RESET}").strip().lower()
            if choice != 'y':
                return []

        new_entries = []
        target = max(1, self.DAILY_MINIMUM - already_logged) if mandatory else 1

        while True:
            entry = self._log_one_entry(level, len(new_entries) + already_logged + 1)
            if entry is None:
                break
            new_entries.append(entry)
            self.entries.append(entry)
            self._save_entries()

            total_today = already_logged + len(new_entries)
            remaining = self.DAILY_MINIMUM - total_today

            if mandatory and remaining > 0:
                print(f"\n  {YELLOW}{remaining} more {'entry' if remaining == 1 else 'entries'} needed today.{RESET}")
                continue
            else:
                another = input(f"\n  {DIM}Log another constraint? (y/n): {RESET}").strip().lower()
                if another != 'y':
                    break

        self._show_session_summary(new_entries, already_logged, mandatory)
        return new_entries

    def get_today_status(self) -> dict:
        """Returns today's log status. Used by main menu display."""
        today = self._today()
        entries = self._get_entries_for_date(today)
        return {
            'date': today,
            'entries_logged': len(entries),
            'is_complete': len(entries) >= self.DAILY_MINIMUM,
            'entries': entries,
        }

    def run_weekly_review(self, level: int) -> Optional[WeeklyReview]:
        """
        Run LLM weekly review of a random 20% sample of entries.

        Called automatically when conditions are met (every 7 days).
        Returns WeeklyReview or None if no LLM available.
        """
        if not self.llm:
            print(f"\n{YELLOW}No LLM client available for weekly review.{RESET}\n")
            return None

        if not self.entries:
            print(f"\n{DIM}No entries to review yet.{RESET}\n")
            return None

        self._show_review_intro()

        # Sample 20% randomly, minimum 3
        sample_size = max(3, int(len(self.entries) * 0.20))
        sample = random.sample(self.entries, min(sample_size, len(self.entries)))

        prompt = self._build_review_prompt(sample, level)

        try:
            response = self.llm.chat(
                prompt=prompt,
                system=(
                    "You are a cognitive scientist studying whether constraint transmutation "
                    "is transferring from training into daily life. You are not a coach. "
                    "You are a researcher with one question: is the loop still running? "
                    "The loop: constraint → transmutation → new constraint → transmutation → ... "
                    "If the loop is stopping, where? Be precise. Be brief. No encouragement. "
                    "Only observation."
                )
            )
            review = self._parse_review_response(response, sample)
            self.reviews.append(review)
            self._save_reviews()
            self._show_review_results(review)

            # Mark sampled entries as reviewed
            sample_ids = {e.entry_id for e in sample}
            for entry in self.entries:
                if entry.entry_id in sample_ids:
                    entry.reviewed = True
            self._save_entries()

            return review

        except Exception as e:
            print(f"\n{RED}Weekly review failed: {e}{RESET}\n")
            return None

    def should_run_weekly_review(self) -> bool:
        """Returns True if 7+ days have passed since last review."""
        if not self.reviews:
            # First review after at least 7 days of entries
            if not self.entries:
                return False
            dates = sorted(set(e.date_str for e in self.entries))
            return len(dates) >= 7
        last = self.reviews[-1]
        last_date = datetime.fromisoformat(last.reviewed_at).date()
        return (date.today() - last_date).days >= 7

    def get_all_entries(self) -> list:
        return list(self.entries)

    def get_stats(self) -> dict:
        """Returns summary statistics for the log."""
        if not self.entries:
            return {
                'total_entries': 0,
                'days_logged': 0,
                'streak_days': 0,
                'total_reviews': 0,
                'loop_continuing_pct': None,
            }

        dates = sorted(set(e.date_str for e in self.entries))
        streak = self._calculate_streak(dates)

        reviewed = [e for e in self.entries if e.reviewed]
        loop_yes = [e for e in reviewed if e.loop_continuing is True]
        loop_pct = len(loop_yes) / len(reviewed) if reviewed else None

        return {
            'total_entries': len(self.entries),
            'days_logged': len(dates),
            'streak_days': streak,
            'total_reviews': len(self.reviews),
            'loop_continuing_pct': loop_pct,
        }

    # ── Interactive entry collection ───────────────────────────────────────────

    def _log_one_entry(self, level: int, entry_num: int) -> Optional[ConstraintEntry]:
        """Collect one constraint entry interactively. Returns None on skip/exit."""
        print(f"\n{BOLD}{'─'*56}{RESET}")
        print(f"{BOLD}  Entry {entry_num}{RESET}")
        print(f"{BOLD}{'─'*56}{RESET}")

        print(f"\n  {GOLD}What was the constraint?{RESET}")
        print(f"  {DIM}Be specific. Not 'I was busy' — what was the actual structural constraint?{RESET}")
        constraint = input(f"\n  → ").strip()
        if not constraint or constraint.lower() in ('q', 'quit', 'exit', 'skip'):
            return None

        print(f"\n  {GOLD}How did you transmute it?{RESET}")
        print(f"  {DIM}What was the trade? How did the constraint become fuel?{RESET}")
        transmutation = input(f"\n  → ").strip()
        if not transmutation:
            transmutation = "(not yet transmuted)"

        print(f"\n  {GOLD}What new constraint did the trade produce?{RESET}")
        print(f"  {DIM}Every trade produces the next constraint. What is it?{RESET}")
        print(f"  {DIM}If you don't know yet — that's the answer. Write that.{RESET}")
        new_constraint = input(f"\n  → ").strip()
        if not new_constraint:
            new_constraint = "(unknown — loop not yet visible)"

        # Optional archetype tag
        print(f"\n  {DIM}Archetype? (1=scarcity 2=velocity 3=asymmetry 4=friction 5=paradox) [enter to skip]{RESET}")
        arch_input = input(f"  → ").strip()
        arch_map = {'1': 'scarcity', '2': 'velocity', '3': 'asymmetry', '4': 'friction', '5': 'paradox'}
        archetype = arch_map.get(arch_input, None)

        now = datetime.now()
        entry = ConstraintEntry(
            entry_id=f"rwl_{int(now.timestamp())}_{entry_num}",
            logged_at=now.isoformat(),
            date_str=now.strftime('%Y-%m-%d'),
            constraint=constraint,
            transmutation=transmutation,
            new_constraint=new_constraint,
            archetype_guess=archetype,
        )
        return entry

    # ── Display ────────────────────────────────────────────────────────────────

    def _show_intro(self, level: int, mandatory: bool, already_logged: int):
        """Show intro screen for daily log."""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n{BOLD}{'─'*56}{RESET}")
        if mandatory:
            print(f"{BOLD}  📓 REAL-WORLD LOG  {DIM}Level {level} · Mandatory{RESET}")
        else:
            print(f"{BOLD}  📓 REAL-WORLD LOG  {DIM}Level {level} · Optional{RESET}")
        print(f"{BOLD}{'─'*56}{RESET}")

        if mandatory:
            print(f"\n  Log 3 constraints you encountered today.")
            print(f"  The only thing being tracked: is the loop still running?")
        else:
            print(f"\n  Log constraints you encountered today.")
            print(f"  Available from Level 16. Mandatory at Level 41.")
            print(f"  {DIM}The physics conversation happened at Level 5. Spontaneously.{RESET}")
            print(f"  {DIM}This tracks that transfer.{RESET}")

        if already_logged > 0:
            print(f"\n  {GREEN}✓ {already_logged} {'entry' if already_logged == 1 else 'entries'} logged today.{RESET}")

        print(f"\n  {DIM}Three questions per constraint:{RESET}")
        print(f"  {GOLD}1.{RESET} What was the constraint?")
        print(f"  {GOLD}2.{RESET} How did you transmute it?")
        print(f"  {GOLD}3.{RESET} What new constraint did the trade produce?")
        print(f"\n  {DIM}Type 'skip' or 'q' on the first question to exit.{RESET}")

    def _show_session_summary(self, new_entries: list, already_logged: int, mandatory: bool):
        """Show summary after logging session."""
        total = already_logged + len(new_entries)
        print(f"\n{BOLD}{'─'*56}{RESET}")
        print(f"{BOLD}  LOG COMPLETE{RESET}")
        print(f"{BOLD}{'─'*56}{RESET}")
        print(f"\n  {GREEN}✓ {len(new_entries)} new {'entry' if len(new_entries) == 1 else 'entries'} logged.{RESET}")
        print(f"  {DIM}Total today: {total}{RESET}")

        if mandatory and total < self.DAILY_MINIMUM:
            remaining = self.DAILY_MINIMUM - total
            print(f"\n  {YELLOW}⚠ {remaining} more {'entry' if remaining == 1 else 'entries'} needed to complete today's log.{RESET}")

        # Show the loop from the last entry
        if new_entries:
            last = new_entries[-1]
            print(f"\n  {DIM}Last entry loop:{RESET}")
            print(f"  {CYAN}Constraint:{RESET}     {last.constraint[:60]}{'...' if len(last.constraint) > 60 else ''}")
            print(f"  {CYAN}Transmutation:{RESET}  {last.transmutation[:60]}{'...' if len(last.transmutation) > 60 else ''}")
            print(f"  {CYAN}New constraint:{RESET} {last.new_constraint[:60]}{'...' if len(last.new_constraint) > 60 else ''}")
            print(f"\n  {DIM}The loop continues.{RESET}")

        if self.should_run_weekly_review():
            print(f"\n  {GOLD}⚡ Weekly review available. Run from main menu → Research Dashboard.{RESET}")

        print(f"\n{'─'*56}\n")

    def _show_review_intro(self):
        """Show intro for weekly LLM review."""
        print(f"\n{BOLD}{'─'*56}{RESET}")
        print(f"{BOLD}  🔬 WEEKLY REVIEW{RESET}")
        print(f"{BOLD}{'─'*56}{RESET}")
        print(f"\n  Reviewing a random 20% sample of your log entries.")
        print(f"  One question only: {BOLD}is the loop still running?{RESET}")
        print(f"  {DIM}Processing...{RESET}\n")

    def _show_review_results(self, review: WeeklyReview):
        """Display weekly review results."""
        print(f"\n{BOLD}{'─'*56}{RESET}")
        print(f"{BOLD}  WEEKLY REVIEW COMPLETE{RESET}")
        print(f"{BOLD}{'─'*56}{RESET}")
        print(f"\n  {DIM}Entries reviewed: {review.entries_reviewed} of {review.total_entries}{RESET}")
        print(f"\n  {BOLD}{GOLD}Loop Assessment:{RESET}")
        # Word-wrap the assessment
        words = review.loop_assessment.split()
        line = "  "
        for word in words:
            if len(line) + len(word) + 1 > 56:
                print(line)
                line = "  " + word + " "
            else:
                line += word + " "
        if line.strip():
            print(line)

        if review.patterns_noted:
            print(f"\n  {BOLD}Patterns observed:{RESET}")
            for p in review.patterns_noted[:3]:
                print(f"  {DIM}·{RESET} {p}")

        if review.recommendations:
            print(f"\n  {BOLD}One thing:{RESET}")
            print(f"  {YELLOW}{review.recommendations[0]}{RESET}")

        print(f"\n{'─'*56}\n")

    # ── LLM review ────────────────────────────────────────────────────────────

    def _build_review_prompt(self, sample: list, level: int) -> str:
        """Build the weekly review prompt."""
        entries_text = ""
        for i, e in enumerate(sample, 1):
            entries_text += f"\nEntry {i} ({e.date_str}):\n"
            entries_text += f"  Constraint: {e.constraint}\n"
            entries_text += f"  Transmutation: {e.transmutation}\n"
            entries_text += f"  New constraint produced: {e.new_constraint}\n"
            if e.archetype_guess:
                entries_text += f"  Archetype tagged: {e.archetype_guess}\n"

        return f"""You are reviewing a sample of real-world constraint log entries from a C2A user at Level {level}.

C2A trains constraint transmutation: the ability to see any constraint as fuel for advantage.
The conservation law: every transmutation produces a new constraint. The loop never stops.
A trained practitioner knows the loop is always running and stops being surprised by new constraints.

Review these {len(sample)} entries and answer:

1. IS THE LOOP RUNNING?
   Look for: Does entry 3 (new constraint) connect to what could become the next entry 1?
   Is the user tracking the chain, or treating each constraint as isolated?
   Are they surprised by new constraints, or expecting them?

2. WHERE IS IT STOPPING? (if it is)
   Is the transmutation step genuine (constraint becomes fuel) or coping (constraint is survived)?
   Is the new_constraint field being taken seriously or filled in perfunctorily?
   Is there a pattern of avoidance in any archetype?

3. PATTERNS NOTED (2-3 bullet points max)
   Factual observations only. No encouragement.

4. ONE RECOMMENDATION
   The single most important thing to address.

Entries:
{entries_text}

Respond in this exact format:
LOOP_ASSESSMENT: [2-4 sentences. Is it running? Where is it strong/weak?]
PATTERNS:
- [pattern 1]
- [pattern 2]
RECOMMENDATION: [one sentence]
"""

    def _parse_review_response(self, response: str, sample: list) -> WeeklyReview:
        """Parse LLM review response into WeeklyReview."""
        loop_assessment = ""
        patterns = []
        recommendation = ""

        lines = response.strip().split('\n')
        mode = None
        for line in lines:
            line = line.strip()
            if line.startswith('LOOP_ASSESSMENT:'):
                loop_assessment = line.replace('LOOP_ASSESSMENT:', '').strip()
                mode = 'loop'
            elif line.startswith('PATTERNS:'):
                mode = 'patterns'
            elif line.startswith('RECOMMENDATION:'):
                recommendation = line.replace('RECOMMENDATION:', '').strip()
                mode = None
            elif mode == 'loop' and line:
                loop_assessment += ' ' + line
            elif mode == 'patterns' and line.startswith('-'):
                patterns.append(line[1:].strip())

        if not loop_assessment:
            loop_assessment = response[:300]

        dates = sorted(set(e.date_str for e in sample))

        return WeeklyReview(
            review_id=f"review_{int(datetime.now().timestamp())}",
            reviewed_at=datetime.now().isoformat(),
            week_start=dates[0] if dates else self._today(),
            week_end=dates[-1] if dates else self._today(),
            entries_reviewed=len(sample),
            total_entries=len(self.entries),
            loop_assessment=loop_assessment.strip(),
            patterns_noted=patterns,
            recommendations=[recommendation] if recommendation else [],
        )

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load_entries(self) -> list:
        if not os.path.exists(self.log_file):
            return []
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            return [ConstraintEntry.from_dict(e) for e in data]
        except Exception:
            return []

    def _save_entries(self):
        try:
            with open(self.log_file, 'w') as f:
                json.dump([e.to_dict() for e in self.entries], f, indent=2)
        except Exception as e:
            print(f"{RED}Warning: could not save log entries: {e}{RESET}")

    def _load_reviews(self) -> list:
        if not os.path.exists(self.reviews_file):
            return []
        try:
            with open(self.reviews_file, 'r') as f:
                data = json.load(f)
            return [WeeklyReview(**r) for r in data]
        except Exception:
            return []

    def _save_reviews(self):
        try:
            with open(self.reviews_file, 'w') as f:
                json.dump([r.to_dict() for r in self.reviews], f, indent=2)
        except Exception as e:
            print(f"{RED}Warning: could not save reviews: {e}{RESET}")

    # ── Utilities ──────────────────────────────────────────────────────────────

    def _today(self) -> str:
        return date.today().strftime('%Y-%m-%d')

    def _get_entries_for_date(self, date_str: str) -> list:
        return [e for e in self.entries if e.date_str == date_str]

    def _calculate_streak(self, sorted_dates: list) -> int:
        """Calculate current consecutive-day streak."""
        if not sorted_dates:
            return 0
        today = date.today()
        streak = 0
        for i, d_str in enumerate(reversed(sorted_dates)):
            d = datetime.strptime(d_str, '%Y-%m-%d').date()
            expected = today - __import__('datetime').timedelta(days=i)
            if d == expected:
                streak += 1
            else:
                break
        return streak


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    level = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    log = RealWorldLog()
    log.run_daily_log(level=level)
