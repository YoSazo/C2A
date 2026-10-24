# C2A: Constraint to Advantage

**Problems aren't solved by eliminating constraints. They're solved by trading constraints for better ones.** A solution is the point where you reach a constraint you're willing to accept. C2A is a terminal drill program that trains that trade until it's automatic, then pairs the trained person with an LLM that translates any field into plain language, while a real verifier, not the LLM, decides what works.

## The four skills

1. **Seeing**: what is actually limiting this, including hidden constraints?
2. **Transmuting**: what are the possible trades, and can the constraint become the advantage?
3. **Selecting**: which trade is best for this goal and this price? The human's job, not the LLM's.
4. **Domain independence**: the same moves in any field, with an LLM as translator.

## The loop

```
LLM: field → plain language  →  human: idea  →  LLM: idea → domain edit
        ▲                                                   │
        └──────── verifier failures = next constraint ◀─────┘
```

## Proven vs. hypothesis

| Statement | Status |
|---|---|
| Automaticity forms under consistent mapping with feedback ([Schneider & Shiffrin, 1977](https://doi.org/10.1037/0033-295X.84.1.1)) | Established research |
| General ability matters less once a consistent skill is automatic ([Ackerman, 1988](https://doi.org/10.1037/0096-3445.117.3.288)) | Established research |
| Transfer usually fails at noticing, not applying ([Gick & Holyoak, 1980](https://doi.org/10.1016/0010-0285(80)90013-4)) | Established research |
| Most brain training doesn't transfer far ([Sala & Gobet, 2017](https://doi.org/10.1177/0963721417712760)) | Established research, and the main risk to C2A |
| C2A drills make constraint noticing automatic | **Hypothesis**, see TESTING.md test 1 |
| C2A training flattens the IQ → performance slope | **Hypothesis**, the primary result in TESTING.md |
| A C2A-trained human + LLM beats the LLM alone on verifier-scored problems | **Hypothesis**, measured by `live` vs. `live --baseline` |

## Quick start

```bash
pip install -r requirements.txt
python -m c2a
```

| Command | What it does | LLM needed |
|---|---|---|
| `python -m c2a drill [--load] [--n 20]` | Pattern drills: press 1–4, timed, spaced repetition | No |
| `python -m c2a select` | Pick a trade, see what actually happened | No |
| `python -m c2a cases` | Predict a real case, see the outcome, self-mark | No |
| `python -m c2a live [--problem bridge_01]` | Fix a truss with an LLM translating, scored by a stiffness solver | Yes |
| `python -m c2a live --baseline --runs 5` | Same problem, LLM alone, for comparison | Yes |
| `python -m c2a log` | Log a real decision and prediction; follow up on outcomes | No |
| `python -m c2a stats` | Patterns mastered, reaction-time trend, real-world hit rate | No |
| `python tools/validate_data.py` | Check every data file | No |

Live mode uses OpenAI. Set `OPENAI_API_KEY` (and optionally `C2A_MODEL`, default `gpt-4o`). Everything else works offline.

## Read next

- [THEORY.md](THEORY.md): the full claim.
- [OBJECTIONS.md](OBJECTIONS.md): the skeptic's objections, answered.
- [TESTING.md](TESTING.md): how the claim will be tested.
- [docs/vision/](docs/vision/): speculation, not part of the claim.

The v1 app (LLM-scored scenarios, levels, desktop UI) is preserved at the `v1-archive` git tag.
