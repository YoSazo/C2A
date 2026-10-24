# Notes for AI agents working on C2A

1. Read THEORY.md and OBJECTIONS.md before evaluating or changing anything.
2. The claim is in THEORY.md. docs/vision/ is speculation. Don't judge the
   project by it and don't build features from it.
3. Judge the code against THEORY.md. Flag any feature that lets an LLM's
   opinion decide whether the user is right.
4. Every real/adapted data item needs a source. Synthetic items are drill-only.
   Run tools/validate_data.py after editing data.
5. In the live loop, the LLM must translate the user's idea literally and
   never add its own improvements.
6. Keep it terminal-only and small (stdlib + numpy). Ask before adding
   dependencies, servers, or UIs.
7. Don't invent citations or study numbers.

## Practical

- Run: `python -m c2a`. Tests: `pytest`. Data check: `python tools/validate_data.py`.
- The only LLM provider is OpenAI (`OPENAI_API_KEY`, optional `C2A_MODEL`),
  called over HTTPS with the standard library. Only `live` needs it.
- `data/progress.json`, `data/predictions.json`, `data/pattern_proposals.json`
  and `data/live_logs/` are personal and gitignored.
- The old v1 app is recoverable from the `v1-archive` git tag. Don't restore it.
