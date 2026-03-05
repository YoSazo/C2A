# C2A Runtime

This folder contains the files that actually run C2A.

## Start here
- `C2A.py` (runtime server)
- Root launcher: `../C2A.py` (kept for compatibility)

## Core engine files
- `llm_client.py`
- `llm_scenario_engine.py`
- `llm_transmutation_judge.py`
- `constraint_archetypes.py`
- `progression.py`

## Supporting runtime files
- `active_lesson.py`
- `real_world_log.py`
- `rlm_config.py`
- `rlm_engine.py`
- `scaffolding_scheduler.py`
- `speed_track.py`

## UI location
- Active UI: `../ui/c2a_training.html`
- Inspiration versions: `../ui/inspiration/`

## Launch
- Web: `python ../C2A.py`
- Desktop dev: `npm run tauri:dev`
- Desktop build: `npm run tauri:build`
