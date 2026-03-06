# C2A LLM Pack

This pack is a minimal context bundle to onboard another LLM quickly.

## Read order (fastest)
1. c2a_runtime/C2A.py - backend API, state authority, scheduler + speed gate integration.
2. ui/c2a_training.html - Training Grounds UI (screens, menu, model tab, backend calls).
3. c2a_runtime/scaffolding_scheduler.py + c2a_runtime/progression.py - level formula + feature retirement and gates.
4. c2a_runtime/speed_track.py + c2a_runtime/real_world_log.py + c2a_runtime/active_lesson.py - core training loops.
5. c2a_runtime/llm_client.py, llm_scenario_engine.py, llm_transmutation_judge.py - LLM generation + judging.
6. src-tauri/src/main.rs + src-tauri/tauri.conf.json - desktop wrapper and backend startup behavior.

## System shape
- Backend authority: Python (c2a_runtime/C2A.py) owns session state, progression, scaffold schedule, speed gate.
- Frontend: single-page HTML UI (ui/c2a_training.html) renders and calls backend APIs.
- Desktop: Tauri wraps local web UI and spawns Python backend process.
- LLM model selection: persisted in backend state (llm_model) and set from UI Model Settings tab.

## Key APIs
- GET /api/state
- GET /api/models
- POST /api/state/model
- POST /api/state/select-archetype
- POST /api/state/domain
- POST /api/scenario
- POST /api/evaluate
- POST /api/speedtrack/start
- POST /api/speedtrack/finish
- POST /api/realworld/add

## Notes
- This pack excludes large/non-core files on purpose.
- If you need full historical context, add docs/ separately.
