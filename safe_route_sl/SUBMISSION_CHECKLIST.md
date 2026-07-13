# SafeRouteSL Submission Checklist

Use this checklist immediately before submission and again before the live demonstration.

## Installation check

- [ ] A clean Python 3.11+ virtual environment can be created.
- [ ] `python -m pip install -r requirements.txt` completes successfully.
- [ ] The application works without SimpleAI installed.
- [ ] Optional SimpleAI status is readable when SimpleAI is installed.

## Test check

- [ ] `.venv/bin/python -m pytest -q` passes.
- [ ] The documented coverage command completes and its result is recorded.
- [ ] `git diff --check` passes.
- [ ] Python source and Streamlit pages pass syntax/import validation.

## Demo check

- [ ] Home and all four sidebar pages load without source exceptions.
- [ ] Interactive Simulation manual navigation and automatic playback work.
- [ ] Bridge Flooded produces a replanning example.
- [ ] Algorithm Comparison displays its table, charts, and summary insights.
- [ ] Toolkit Validation displays BFS, UCS, and A* results with conditional A* wording where applicable.
- [ ] Approximate timing is never presented as a scientific benchmark.

## Screenshot checklist

- [ ] Home page and navigation.
- [ ] Interactive search playback with graph and state panel.
- [ ] Bridge Flooded route or blocked-road state.
- [ ] Comparison table and representative charts.
- [ ] Toolkit Validation results.
- [ ] Problem Model sections and dataset tables.

## Assignment report checklist

- [ ] Problem, state space, actions, transitions, goal test, constraints, and costs are explained.
- [ ] BFS, DFS, UCS, Greedy Best-First, and A* behavior is discussed accurately.
- [ ] Custom implementation, NetworkX validation, and optional SimpleAI roles are distinguished.
- [ ] Synthetic dataset and scenario assumptions are documented.
- [ ] Results, limitations, references, and testing evidence are included.

## Viva preparation checklist

- [ ] Explain why BFS minimizes edges but not weighted cost.
- [ ] Explain UCS accumulated cost and Greedy heuristic-only ordering.
- [ ] Explain A* values `g(n)`, `h(n)`, and `f(n)`.
- [ ] Explain why alternate equal paths can all be correct.
- [ ] Explain why Haversine validation is conditional for composite cost modes.
- [ ] Explain why replay does not rerun the search algorithm.

## Disclaimer check

- [ ] State that all data is synthetic and educational.
- [ ] State that safety and balanced totals are composite scores, not physical units.
- [ ] State that SafeRouteSL must not be used for real navigation or emergency decisions.

## Backup and Git check

- [ ] Generated caches, coverage files, `.DS_Store`, and virtual environments are not included in the submission.
- [ ] No credentials, Streamlit secrets, or personal files are committed.
- [ ] `git status` contains only intended source and documentation changes.
- [ ] The final commit exists locally and a backup or remote copy is available.
- [ ] The submitted archive or repository opens and contains `README.md`, `DEMO_SCRIPT.md`, and this checklist.
