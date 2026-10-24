# Objections

The objections a skeptic raises first, with answers. Read [THEORY.md](THEORY.md) first for the claim being defended.

## "An LLM can do C2A itself, so why the human?"

An LLM can generate options and check facts. It can't choose which cost is worth accepting, own the decision, or bring tacit context it was never told. That's an argument, not evidence, so in domains with a real verifier the live loop measures it directly: human + LLM against LLM alone, same problem, same loop cap. Problems where the LLM alone does as well are marked as tutorials and don't count as evidence for the human's contribution.

## "Brain training doesn't transfer."

For most programs, that's correct. Meta-analyses find little or no far transfer from working-memory, chess, or music training ([Melby-Lervåg & Hulme, 2013](https://doi.org/10.1037/a0028228); [Sala & Gobet, 2017](https://doi.org/10.1177/0963721417712760); [Simons et al., 2016](https://doi.org/10.1177/1529100616661983)). C2A's bet is narrower. It doesn't try to raise general ability. It targets spontaneous *noticing* of a known structure, which is the step where transfer usually breaks. That bet will be tested on unfamiliar fields against an active control group ([TESTING.md](TESTING.md)). Until then it's a hypothesis.

## "Constraints aren't conserved. Smallpox is gone."

Agreed. The claim isn't strict conservation. It's that constraints *transfer* when you act on them (smallpox's limit moved from biology to logistics and persuasion) and that their size can change, sometimes to nearly zero.

## "Seeing and selecting constraints is just IQ."

Partly. General ability matters most early in learning a skill. On consistent tasks its influence drops as the skill becomes automatic ([Ackerman, 1988](https://doi.org/10.1037/0096-3445.117.3.288)). The claim is that constraint patterns can be drilled to that point. The test is whether the slope of performance against IQ is flatter in the trained group than in the control group. If it isn't, the claim fails.

## "Without domain knowledge you can't judge the LLM's output."

Right, which is why the user never has to. The LLM translates the user's idea back into domain terms, and a real verifier or a real outcome decides whether it works, not the LLM's opinion and not the user's guess. Before anything runs, the user confirms the LLM's plain-words restatement of the edit, so the LLM can't quietly substitute its own idea. For tacit knowledge that no verifier captures, the team model puts domain experts beside the C2A leader.

## "Famous historical cases test recall, not thinking."

Agreed. The famous cases (Apollo 13, Apple 1997, and so on) are tagged `"obscurity": "low"` and used only as tutorials. Evaluation uses obscure cases, forecasts that resolve in the future, and verifiers, where recall can't help.

## "LLM-judged scores can be gamed."

v1 had this flaw: an LLM invented the scenario and an LLM scored the answer 0–100. v2 doesn't use LLM scores anywhere in evaluation. Drills and select items have fixed answers, cases are self-marked against a documented outcome, and the live loop is scored by a physics verifier.

## "Isn't EMPROS / Empro / AGI the point?"

No. That's speculative long-range thinking, kept in [`docs/vision/`](docs/vision/), and it isn't part of the claim or supported by evidence. Judge the project by THEORY.md and by whether the tests in TESTING.md come out the way it predicts.
