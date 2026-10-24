# Theory

This is what C2A claims. Anything not written here, including everything in `docs/vision/`, is not part of the claim.

## Thesis

Problems aren't solved by eliminating constraints. They're solved by **trading constraints for better ones**. A "solution" is the point where you reach a constraint you're willing to accept.

Constraints move when you act on them. Fix one bottleneck and the limit shifts somewhere else, often somewhere hidden. Smallpox eradication moved the binding constraint from biology (a vaccine already existed) to manufacturing, logistics, surveillance, and persuasion.

Constraints are not strictly conserved like energy. Their size can shrink drastically: smallpox is gone. The claim is that constraints *transfer* and *change size*, and that the skill is moving a constraint to wherever it costs the least.

## The four skills C2A trains

1. **Seeing.** What is actually limiting this, including hidden and second-order constraints?
2. **Transmuting.** What are the possible trades? How can the constraint itself become the source of an advantage?
3. **Selecting.** Which trade is best, given the goal and what you're willing to pay? An LLM can't do this step for you, because it rests on your values and on owning the consequences.
4. **Domain independence.** Applying the same moves in any field, with an LLM supplying the domain knowledge in plain language.

## The human–LLM loop

```
field's constraint logic ──LLM translates──▶ plain language
                                                │
                                        human transmutes
                                                │
plain-language idea ──LLM translates back──▶ domain edit
                                                │
                              real verifier / real outcome checks it
                                                │
                   verifier failures become the next constraint ──▶ repeat
```

The loop repeats until the constraint left is one you accept. The LLM translates in both directions. It never decides whether the idea is right; a verifier or a real outcome does.

## Automaticity

The goal is for recognizing and transmuting constraints to become automatic, like recognizing a familiar face.

Automatic processing develops under **consistent mapping**: the same class of stimulus always calls for the same response, with practice and feedback. Under varied mapping, processing stays slow and effortful ([Schneider & Shiffrin, 1977](https://doi.org/10.1037/0033-295X.84.1.1); [Shiffrin & Schneider, 1977](https://doi.org/10.1037/0033-295X.84.2.127)). That is why C2A v2 is built on drills with fixed, real answers instead of LLM-invented scenarios scored on an LLM's opinion. An opinion score changes from one call to the next, so it isn't a consistent mapping.

A useful model is chess tactics: a finite set of patterns, plus common combinations of them, drilled until they fire instantly. C2A's unit of training is the **pattern** (a constraint→move pair, e.g. "scarcity forces focus"), not the five loose families (scarcity, velocity, asymmetry, friction, paradox) the patterns are grouped into.

## Relationship to IQ

General ability predicts performance most strongly early in learning a skill. On consistent tasks, its influence drops as the skill becomes automatic and other, more task-specific abilities take over ([Ackerman, 1988](https://doi.org/10.1037/0096-3445.117.3.288)).

**Prediction:** C2A training *flattens the IQ→performance slope* on drilled patterns. Trained people of average IQ should close much of the gap with untrained high-IQ people on those patterns.

IQ likely still matters for novel combinations, long chains of reasoning, and how fast new patterns are learned. C2A doesn't make IQ irrelevant. The claim is narrower: trained C2A plus an LLM can matter more for real-world outcomes than raw IQ alone, and because it is trainable, it's available to everyone.

## Where it should win, and where it shouldn't

| Problem type | Expected winner |
|---|---|
| Everyday, low-content problems | A trained C2A person beats an untrained high-IQ person |
| Routine work inside an expert's field | The expert + an LLM |
| Problems a field is stuck on | C2A + LLM has a real shot. Outsiders whose expertise is far from a problem's field are disproportionately likely to solve broadcast-search problems ([Jeppesen & Lakhani, 2010](https://doi.org/10.1287/orsc.1090.0491)) |
| Novel ideas that need real-world testing | Whoever judges better what to test. A C2A leader with expert teammates covers this |

## The team model

A C2A + LLM leader frames the problem and selects among trades. The LLM translates and fact-checks. Domain experts ground ideas in tacit, real-world experience and run the tests. Each role covers a gap in the others.

## Why noticing is the target

Transfer usually fails at *noticing* that a known structure applies, not at applying it once noticed. In [Gick & Holyoak (1980)](https://doi.org/10.1016/0010-0285(80)90013-4), most participants who had just read an analogous story failed to use it on the target problem until they were told it might help; with that hint, most succeeded.

C2A trains spontaneous noticing of constraints in unfamiliar situations, which is where transfer usually breaks. That's why drills rotate many different surface stories over the same pattern.

## Prior art

- **Theory of Constraints** (Goldratt & Cox, *The Goal*, 1984): every system has a bottleneck, and fixing one moves it.
- **Thomas Sowell**: "There are no solutions. There are only trade-offs." (*A Conflict of Visions*, 1987)
- **TRIZ** (Genrich Altshuller): inventive principles for resolving contradictions, extracted from patents.
- **Perceptual learning modules** ([Kellman, Massey & Son, 2010](https://doi.org/10.1111/j.1756-8765.2009.01053.x)): short, high-volume classification practice that builds expert-like pattern recognition.
- **Superforecasting research** ([Mellers et al., 2014](https://doi.org/10.1177/0956797614524255)): brief training improved forecasting accuracy when it was scored against real outcomes.

C2A's contribution is to combine these into one trainable, domain-general habit, paired with an LLM as a universal translator.

## Use and misuse

C2A is meant to be open and widely available. A capability that many people hold, with good norms, is safer than one held by a few. It should not be used as a gate for school admissions, jobs, or immigration. That would repeat the historical misuse of IQ testing.
