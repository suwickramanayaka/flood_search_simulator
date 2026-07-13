"""Shared constants for SafeRouteSL."""

DISTANCE_MODE = "distance"
TIME_MODE = "time"
SAFETY_MODE = "safety"
BALANCED_MODE = "balanced"

ALGORITHM_NAMES = {
    "bfs": "Breadth-First Search",
    "dfs": "Depth-First Search",
    "ucs": "Uniform-Cost Search",
    "greedy": "Greedy Best-First Search",
    "astar": "A* Search",
}

SEARCH_ALGORITHM_LABELS = tuple(ALGORITHM_NAMES.values())

OPTIMIZATION_MODE_LABELS = {
    DISTANCE_MODE: "Shortest Distance",
    TIME_MODE: "Fastest Travel Time",
    SAFETY_MODE: "Safest Route",
    BALANCED_MODE: "Balanced Route",
}

HEURISTIC_LABELS = {
    "haversine": "Haversine Distance",
    "zero": "Zero Heuristic",
}

OPTIMIZATION_MODE_TO_LABEL = dict(OPTIMIZATION_MODE_LABELS)
HEURISTIC_TYPE_TO_LABEL = dict(HEURISTIC_LABELS)
OPTIMIZATION_LABEL_TO_MODE = {label: value for value, label in OPTIMIZATION_MODE_LABELS.items()}
HEURISTIC_LABEL_TO_TYPE = {label: value for value, label in HEURISTIC_LABELS.items()}

NODE_COLORS = {
    "current": "#2563eb",
    "frontier": "#facc15",
    "explored": "#9ca3af",
    "final_path": "#16a34a",
    "start": "#86efac",
    "goal": "#a855f7",
    "unvisited": "#ffffff",
    "unavailable": "#7f1d1d",
}

EDGE_COLORS = {
    "normal": "#9ca3af",
    "current_path": "#2563eb",
    "final_route": "#16a34a",
    "high_risk": "#f97316",
    "blocked": "#dc2626",
    "severe_risk": "#b91c1c",
}

ROAD_CONDITION_PENALTIES = {
    "excellent": 0,
    "good": 1,
    "fair": 3,
    "poor": 6,
    "damaged": 10,
}

FLOOD_RISK_LABELS = {
    1: "very low",
    2: "low",
    3: "moderate",
    4: "high",
    5: "severe",
}

SUPPORTED_HEURISTIC_TYPES = {"haversine", "zero"}
SUPPORTED_LOCATION_TYPES = {
    "village",
    "junction",
    "bridge",
    "temple",
    "shelter",
    "community_hall",
    "hospital",
    "school",
    "police_station",
    "relief_centre",
    "secretariat",
    "station",
    "market",
    "hall",
    "town",
    "hill",
    "riverside",
    "relief",
}

GOAL_LOCATION_TYPES = {"shelter", "hospital", "school", "community_hall", "temple", "relief_centre"}

