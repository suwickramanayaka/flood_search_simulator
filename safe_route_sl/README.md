# SafeRouteSL

SafeRouteSL is an educational Streamlit application for demonstrating uninformed and informed search algorithms on a synthetic flood-evacuation routing problem inspired by Sri Lankan local-area planning.

This repository is currently in Phase 1 of development. It contains the project scaffold, core data models, shared constants, synthetic data files, and validation tests. The Streamlit interface and search algorithms will be added in later phases.

## Project Overview

The application will model a flood-affected local area as a weighted graph and let users compare how BFS, DFS, UCS, Greedy Best-First Search, and A\* behave under different flood scenarios.

## Local Problem Description

Seasonal flooding can block roads, increase travel time, and make some routes less safe than others. SafeRouteSL demonstrates how route choice changes when cost, risk, and accessibility are all considered together.

## Educational Purpose

The project is designed for classroom demonstration and viva-style explanation. It is not a real navigation or emergency-response tool.

## Features Planned For Later Phases

- Interactive graph simulation
- Step-by-step search playback
- Scenario-based route changes
- Comparison tables and charts
- NetworkX validation helpers

## Supported Algorithms Planned

- Breadth-First Search
- Depth-First Search
- Uniform-Cost Search
- Greedy Best-First Search
- A\* Search

## Technology Stack

- Python 3.11+
- Streamlit
- NetworkX
- Plotly
- Pandas
- NumPy
- Pytest
- SimpleAI

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run Tests

```bash
pytest
```

To run the more detailed coverage check used during development:

```bash
pytest --cov=services --cov=utils --cov=models --cov-report=term-missing
```

## Dataset

The `data/` folder contains synthetic CSV and JSON files for locations, roads, and scenarios. The dataset is intentionally fictional and small enough to inspect visually.

## Graph Data Format

Locations are stored in `data/locations.csv` with the fields `id`, `name`, `short_name`, `type`, `latitude`, `longitude`, `capacity`, `available`, and `description`.

Roads are stored in `data/roads.csv` with the fields `source`, `target`, `road_name`, `distance_km`, `travel_time_min`, `flood_risk`, `road_condition`, and `blocked`.

Flood risk uses a five-point ordinal scale:

- 1 = very low
- 2 = low
- 3 = moderate
- 4 = high
- 5 = severe

Supported road conditions are `excellent`, `good`, `fair`, `poor`, and `damaged`.

## Cost Functions

SafeRouteSL uses simple educational route costs:

- Distance mode: `cost = distance_km`
- Time mode: `cost = travel_time_min`
- Safety mode: `cost = distance_km + risk_weight * flood_risk + road_condition_penalty`
- Balanced mode: `cost = distance_km + 0.5 * travel_time_min + risk_weight * flood_risk + road_condition_penalty`

Blocked roads are excluded from traversal and are not treated as normal finite routes.

## Heuristic

The project uses the Haversine straight-line distance between the current node and goal node as the default heuristic for informed search. A zero heuristic is also supported for educational comparison.

## Scenario Structure

Scenarios are defined in `data/scenarios.json` as objects containing `id`, `name`, `description`, `edge_overrides`, and `node_overrides`. Scenario overrides are applied to graph copies so the base data remains unchanged.

## Development Notes

Phase 2 adds graph loading, validation, scenario application, route-cost helpers, and heuristics. It does not add search algorithms or Streamlit visualizations yet.

## Disclaimer

Educational simulation using synthetic data. Not for real emergency decision-making.
