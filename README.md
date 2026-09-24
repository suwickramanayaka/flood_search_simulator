# SafeRouteSL

SafeRouteSL is an educational Streamlit application for exploring graph-search algorithms in a synthetic flood-evacuation setting inspired by Sri Lankan local-road planning.

## Problem and purpose

Flooding can block roads, increase travel time, raise route risk, or make an evacuation destination unavailable. SafeRouteSL models these changes on a small weighted graph and shows how different search strategies explore the same problem.

The project is designed for coursework demonstrations, algorithm comparison, and viva discussion. It makes internal search state visible; it is not intended to select real evacuation routes.

> **Disclaimer:** Educational simulation using synthetic data. Not for real emergency decision-making, public-safety planning, or navigation.

## Features

- Five custom Python search implementations
- Scenario-aware traversable graph construction
- Distance, time, safety, and balanced educational cost modes
- Haversine and zero heuristics
- Immutable recorded `SearchStep` history for deterministic replay
- Previous, Next, Reset, Run to Completion, Auto Play, Pause, and playback-speed controls
- Dynamic Plotly graph states, frontier details, explored nodes, and per-step metrics
- Algorithm comparison table, five charts, and tied-winner summary insights
- NetworkX reference validation for BFS, UCS/Dijkstra, and A*
- Optional SimpleAI availability diagnostics
- Human-readable location names and explicit no-route handling

## Supported algorithms

| Algorithm | Main behavior in SafeRouteSL |
|---|---|
| Breadth-First Search (BFS) | Finds a minimum-edge route on this finite graph; it does not optimize weighted cost. |
| Depth-First Search (DFS) | Explores deeply using deterministic ordering; it is not cost-optimal. |
| Uniform-Cost Search (UCS) | Expands by accumulated cost and finds a minimum-cost route for the non-negative costs used here. |
| Greedy Best-First Search | Expands by heuristic estimate and can return a non-optimal route. |
| A* Search | Uses `f(n) = g(n) + h(n)`; optimality depends on the suitability of the heuristic for the chosen cost mode. |

## Custom and toolkit architecture

The simulator always runs the custom implementations in `algorithms/`. They create the `SearchResult` and recorded `SearchStep` objects used by the UI and playback services.

NetworkX is a reference toolkit only:

- Custom BFS is checked against NetworkX unweighted shortest path by path validity and edge count.
- Custom UCS is checked against NetworkX Dijkstra by path validity and total cost within floating-point tolerance.
- Custom A* is checked against NetworkX A* by path validity and cost. Haversine validation is conditional outside distance mode.

Different toolkits may return different but equally valid paths. Equal edge count for BFS or matching weighted cost for UCS/A* can be more important than an identical node sequence. SimpleAI is optional; when absent, the application still starts and NetworkX remains the active reference.

## Application pages

1. **Interactive Simulation** — configure one custom search and navigate or automatically replay its stored history without rerunning the algorithm.
2. **Algorithm Comparison** — run all five algorithms under one configuration and inspect readable paths, costs, search effort, path length, and approximate educational execution time.
3. **Problem Model** — review the formal search problem, constraints, costs, heuristic, algorithm properties, data, scenarios, toolkit roles, and limitations.
4. **Toolkit Validation** — compare custom BFS, UCS, and A* results with their NetworkX references.

## Technology stack

- Python 3.11+
- Streamlit
- NetworkX
- Plotly
- Pandas
- Pytest and pytest-cov
- SimpleAI (optional diagnostics only)

## Project structure

```text
safe_route_sl/
├── app.py                         # Home page
├── algorithms/                    # Custom searches and optional toolkit adapters
├── data/                          # Synthetic locations, roads, and scenarios
├── models/                        # Graph, configuration, SearchStep, and SearchResult records
├── pages/                         # Four Streamlit application pages
├── services/                      # Graph, scenario, search, playback, comparison, and validation logic
├── tests/                         # Unit, integration, renderer, state, and static tests
├── utils/                         # Constants, costs, heuristics, formatting, and domain errors
├── visualizations/                # Plotly and Streamlit presentation helpers
├── DEMO_SCRIPT.md                 # 7–10 minute demonstration sequence
└── SUBMISSION_CHECKLIST.md        # Final submission checks
```

## Dataset structure

All data is fictional and intentionally compact.

- `data/locations.csv`: `id`, names, type, latitude, longitude, capacity, availability, and description.
- `data/roads.csv`: endpoints, road name, distance, travel time, flood risk, road condition, and blocked state.
- `data/scenarios.json`: scenario identity, description, edge overrides, and node overrides.

Flood risk is an ordinal educational scale from 1 (very low) to 5 (severe). Road conditions are `excellent`, `good`, `fair`, `poor`, or `damaged` and map to documented penalties.

## Flood scenarios

- **Normal Conditions** — baseline open-road comparison.
- **Bridge Flooded** — the main bridge route is blocked.
- **Severe Flooding** — several risk values increase so safer and shorter routes may differ.
- **Shelter Unavailable** — one evacuation destination cannot be selected.
- **Multiple Equal-Cost Paths** — exposes deterministic tie handling and alternate valid routes.

Scenario overrides are applied to graph copies; the base graph is not mutated.

## Cost functions

- **Shortest Distance:** `distance_km`
- **Fastest Travel Time:** `travel_time_min`
- **Safest Route:** `distance_km + risk_weight × flood_risk + road_condition_penalty`
- **Balanced Route:** `distance_km + 0.5 × travel_time_min + risk_weight × flood_risk + road_condition_penalty`

Blocked roads are excluded. Distance and time retain their stated data units. Safety and balanced totals are educational composite scores, not physical measurements or calibrated safety ratings.

## Heuristics

**Haversine Distance** estimates straight-line distance from a node to the goal. It is appropriate for normal distance-mode validation. For time, safety, or balanced costs, it remains an educational guide and A* optimality claims are conditional.

**Zero Heuristic** always returns zero, so A* behaves like UCS and provides a useful teaching comparison.

## Installation

From the `safe_route_sl` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows activation:

```powershell
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

SimpleAI is optional. Install it only if its availability diagnostic is required:

```bash
python -m pip install "simpleai>=0.8.3"
```

## Running the application

```bash
.venv/bin/python -m streamlit run app.py
```

Open `http://localhost:8501` if the browser does not open automatically.

## Running tests

```bash
.venv/bin/python -m pytest -q
```

Coverage used for submission checking:

```bash
.venv/bin/python -m pytest \
  --cov=algorithms \
  --cov=services \
  --cov=models \
  --cov=utils \
  --cov=visualizations \
  --cov-report=term-missing
```

## Example workflow

1. Open **Interactive Simulation**.
2. Select **Normal Conditions**, a start, an evacuation goal, and **Breadth-First Search**.
3. Select **Run Search**, then inspect Previous, Next, Auto Play, Pause, and speed controls.
4. Reset playback and use **Run to Completion** to inspect the final route and metrics.
5. Switch to **Bridge Flooded** and rerun to discuss replanning when an edge becomes blocked.
6. Open **Algorithm Comparison** to compare all five algorithms under one configuration.
7. Open **Toolkit Validation** to compare custom BFS, UCS, and A* with NetworkX.

## Screenshot placeholders

- `[Screenshot: Home page and sidebar navigation]`
- `[Screenshot: Interactive Simulation during step playback]`
- `[Screenshot: Bridge Flooded final route]`
- `[Screenshot: Algorithm Comparison table and charts]`
- `[Screenshot: Toolkit Validation results]`
- `[Screenshot: Problem Model sections and dataset tables]`

Screenshots are intentionally not generated or committed automatically.

## Known limitations

- The network, coordinates, capacities, road conditions, and flood values are synthetic.
- Scenarios are predefined and do not consume live weather, traffic, mapping, or emergency-service data.
- The graph is intentionally small for visual teaching.
- Approximate execution times are not controlled scientific benchmarks.
- Haversine is not guaranteed to be an admissible estimate for composite safety, balanced, or time costs.
- Results demonstrate algorithms and must not guide real evacuation decisions.

## Future improvements

- Validated real-world datasets developed with appropriate authorities
- Live map and hazard feeds with provenance and reliability controls
- Larger-network performance experiments in a controlled benchmark environment
- Accessibility, multilingual labels, and mobile-layout improvements
- Additional toolkit adapters that remain separate from the primary custom algorithms

## Assignment demonstration guide

Use [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) for a timed 7–10 minute walkthrough. Before presenting, complete [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md), run both test commands, capture the requested screenshots, and confirm the disclaimer is visible. Emphasize the distinction between minimum edges, minimum weighted cost, heuristic guidance, approximate timing, and conditional validation.
