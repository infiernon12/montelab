## MonteLab — Copilot / AI Agent Instructions

Short, focused guidance to help an AI agent be productive in this repo.

1) Big-picture architecture
- UI: PySide6 desktop app. Entrypoints: `main.py` (standard) and `main_adaptive.py` (adaptive dockable UI).
- Services: `services/` hosts orchestration layers - `MLService` (ML pipeline) and `AnalysisService` (poker analysis glue).
- Core poker logic: `core/poker/` contains `HandEvaluator`, `EquityCalculator` (calls a pluggable `MonteCarloBackend`), `BoardAnalyzer`, `OutsCalculator`.
- Native Monte Carlo engine: C++ executable lives under `MonteCarlo-Poker-master/`. Python wrapper: `monte_carlo_engine_v3.py` (daemon process, singleton). `core/poker/monte_carlo_backend.py` adapts the daemon to `EquityCalculator`.

2) Developer workflows & quick commands
- Install dependencies (Python 3.10.11 recommended):
```powershell
python -m pip install -r requirements.txt
```
- Run app (uses license check; requires HWID/License to pass):
```powershell
python main.py        # normal UI
python main_adaptive.py  # adaptive UI variant
```
- Run the adaptive UI unit smoke tests:
```powershell
python test_adaptive_ui.py
```
- Native backend: to enable daemon mode the C++ executable and `lookup_tablev3.bin` must exist at `MonteCarlo-Poker-master/MonteCarloPoker.exe` and same folder. Build instructions: open the Visual Studio solution or use CMake in that folder (project provides VS project files).

3) Project-specific patterns and gotchas
- ML models are loaded by `services/ml_service.MLService.from_weights(yolo_path, resnet_path, device)`; weights expected under `models/` (example: `models/board_player_detector_v4.pt`). If models are missing the app gracefully disables detection (`ml_service.is_available == False`).
- Equity calculation is pluggable: `core.poker.EquityCalculator` accepts any backend implementing `MonteCarloBackend.calculate_equity(...)`. The current implementation `core/poker/monte_carlo_backend.py` delegates to the daemon in `monte_carlo_engine_v3.py` and will raise during init if the native engine is missing.
- Monte Carlo daemon behavior: `MonteCarloEngineDaemon` is a singleton and attempts to start a persistent C++ process with a READY handshake. It implements robust JSON validation and fallbacks to a legacy mode. Watch for these signals in logs (READY / marker lines).
- License flow: `main.py` calls `utils.hwid_generator.HWIDGenerator` and `utils.license_client.LicenseClient`. A hard-coded HMAC secret is present in the entrypoints — change/remove for development.
- Logging: modules use `logging.getLogger(__name__)`. Use INFO/DEBUG logs to trace flows; the app sets a basic logging config in `main.py` and `main_adaptive.py`.

4) Where to make changes for common tasks
- Add/replace ML models: put weights in `models/` and adjust `main.py` model paths.
- Swap backend for testing: create a mock backend implementing `MonteCarloBackend` and pass it to `EquityCalculator(backend=mock)` when constructing `AnalysisService` in tests.
- UI changes: see `ui/windows/`, `ui/dock_widgets.py` and `ui/ui_config.py` for layout, dock state and persistence patterns (tests exercise `UIConfigManager`).

5) Integration & edge cases to handle
- Offline/workbench mode: ML missing and C++ backend missing are explicit possibilities — code returns error dicts (e.g., `{"error": "Monte Carlo backend not available"}`) and the UI expects that. Favor returning the same error-shaped dict when implementing new simulation backends.
- Concurrency: `MonteCarloEngineDaemon` uses locks (`process_lock`) and is a singleton; avoid creating multiple daemon instances in tests.
- Input validation: poker functions validate card counts (2 hole cards, <=5 board cards), opponent counts (1-8). Reuse these checks when wiring new frontends.

6) Files to inspect when debugging a flow
- App startup & license: `main.py`, `main_adaptive.py`, `utils/hwid_generator.py`, `utils/license_client.py`, `ui/hwid_dialog.py`
- ML pipeline: `services/ml_service.py`, `ml/detector.py`, `ml/__init__.py` (detector and classifier classes)
- Poker core: `core/poker/*` and `core/domain/*` (`game_state.py`, `card.py`)
- Native engine wrapper: `monte_carlo_engine_v3.py`, and native project `MonteCarlo-Poker-master/`
- Analysis orchestration: `services/analysis_service.py`

7) Example prompts for the next tasks
- "Add a small mock MonteCarlo backend for unit tests that returns deterministic equity values and update `test_adaptive_ui.py` to use it." 
- "Trace a failing equity calculation: gather logs from `monte_carlo_engine_v3.py` and describe likely root causes (daemon dead, malformed JSON, duplicate cards)."

If any section is unclear or you want more examples (e.g., how to write a test that injects a mock backend), tell me which area to expand and I will iterate.
