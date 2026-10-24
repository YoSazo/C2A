# Testing the claims

Nothing in [THEORY.md](THEORY.md) is established yet. This is how it will be tested. No test here uses an LLM's opinion as a score.

## Design

- **Groups:** three IQ bands (roughly 80–90, 95–105, and 120+), crossed with **C2A-trained** vs. **active control**. The control group spends the same hours on case-study reading or generic critical-thinking material, so any effect can't be explained by time on task or expectation.
- **IQ measure:** [ICAR](https://icar-project.com/), the free, public-domain cognitive ability test ([Condon & Revelle, 2014](https://doi.org/10.1016/j.intell.2014.01.004)).
- **Preregistration:** predictions and analysis plan are published before data collection.
- **Blinding:** anyone scoring open-ended answers doesn't know which group the participant is in.

## Primary result

The **slope of performance against IQ** in each group. The prediction is that it's flatter in the trained group. If trained and control slopes are the same, the central claim fails, whatever happens to average scores.

## Tests

1. **Load test.** Drill accuracy and reaction time while holding a 7-digit number in mind (`python -m c2a drill --load`). If performance holds under load, the pattern is plausibly automatic.
2. **Hidden-constraint noticing.** A useful constraint is embedded in a messy situation, with no hint that it matters. Scored on whether the participant uses it.
3. **Future-resolving forecasts.** Questions that resolve after the answers are locked, scored with Brier scores.
4. **Cold-field sprint.** Hours of practice to reach expert-level recognition accuracy in an unfamiliar field. Both groups get identical field training.
5. **Live verifier loop.** Human + LLM vs. LLM alone on the same problems (`python -m c2a live` and `live --baseline`). Measures: solve rate, loops to solve, final cost vs. budget.
6. **$50 / 7 days.** A legal money-making challenge, scored by ending balance.
7. **Blind-pick business problems.** Owners of real small businesses choose among proposals without knowing who wrote them; the chosen proposal's result is tracked for 60 days.
8. **Team test.** One C2A leader plus four high-IQ members vs. five high-IQ members, on objectively scored problems, run many times.

## Pilot

The author plus about 10 people. Tests 1, 2, and 5, measured before and after 30 days of drills. The pilot only checks that the instruments work and gives effect-size estimates for planning the full study. It can't confirm the claim on its own: it has no control group and too few people per IQ band.

## What the program records

- `data/progress.json`: per-item answers, correctness, reaction time (ms), load vs. no-load, spaced-repetition state.
- `data/live_logs/`: every live run, every baseline run, every rejected translation.
- `data/predictions.json`: real-world decisions and predictions logged with `c2a log`, with outcomes filled in later.

All three are gitignored, because they hold personal data.
