# SafeRouteSL Demonstration Script

Target duration: 7–10 minutes. Keep one browser window ready and use the sidebar to move between pages.

## 1. Project problem and local context — 45 seconds

Open the **SafeRouteSL** home page. Explain that the project models a small synthetic Sri Lankan local-road network where flooding can block roads, increase risk, or make an evacuation destination unavailable. State the educational disclaimer: this is not a real emergency-routing tool.

## 2. Graph, scenarios, and costs — 45 seconds

Open **Problem Model** briefly. Point out that nodes are locations and edges are roads with distance, travel time, flood risk, road condition, and blocked status. Mention **Normal Conditions**, **Bridge Flooded**, and **Severe Flooding**. Clarify that safety and balanced totals are educational composite scores rather than physical units.

## 3. BFS or DFS behavior — 60 seconds

Open **Interactive Simulation**. Select **Normal Conditions**, **Breadth-First Search**, **Millaniya Village** as the start, and an available evacuation goal such as **School Evacuation Centre**. Run the search. Explain that BFS uses a FIFO frontier and targets the fewest edges, not the lowest weighted cost. If demonstrating DFS instead, explain its LIFO deep exploration and lack of cost optimality.

## 4. Step-by-step playback — 60 seconds

Use **Next** and **Previous** while pointing to the current node, frontier, explored nodes, graph colours, explanation, and metrics. Use **Reset** to return to the Initialize record without rerunning the search. Start **Auto Play**, change **Playback Speed**, use **Pause**, and then select **Run to Completion**. Explain that playback navigates the stored `SearchStep` history.

## 5. UCS weighted optimal route — 50 seconds

Run the same endpoints with **Uniform-Cost Search** and a clearly stated optimization mode. Explain `g(n)` as accumulated route cost and the priority queue as the reason UCS expands the least-known-cost frontier entry. Contrast its weighted route with BFS's minimum-edge objective.

## 6. Greedy behavior — 40 seconds

Select **Greedy Best-First Search** with **Haversine Distance**. Explain that it prioritizes `h(n)` and can reach a goal quickly in some examples, but heuristic-only ordering does not guarantee the minimum weighted cost.

## 7. A* values — 50 seconds

Select **A* Search**. Show `g(n)`, `h(n)`, and `f(n) = g(n) + h(n)` in the current state. Explain that Zero Heuristic makes A* behave like UCS. Haversine supports distance-mode validation normally, while optimality is conditional for time, safety, and balanced composite costs.

## 8. Bridge-flooded replanning — 50 seconds

Change the scenario to **Bridge Flooded**. Point out that changing configuration clears the stale result. Run the search again and show that the blocked main bridge edge is excluded, causing the algorithm to explore or select an alternate route.

## 9. Algorithm Comparison — 60 seconds

Open **Algorithm Comparison** and run one comparison. Show all five readable paths in the Results Table, then the cost/path, search-effort, and approximate-runtime tabs. Read one tied-winner insight if present. Emphasize that algorithms optimize and explore differently and that no algorithm is universally best. Timing is approximate and educational, not a scientific benchmark.

## 10. Toolkit Validation — 60 seconds

Open **Toolkit Validation**. Run validation and show custom BFS against NetworkX unweighted shortest path, UCS against Dijkstra, and A* against NetworkX A*. Explain that BFS compares valid edge count, while UCS and A* compare valid weighted cost within tolerance. Different equal paths may both pass. Demonstrate or describe the **Conditional** warning for Haversine with Balanced Route.

## 11. Limitations and close — 35 seconds

Return to **Problem Model** or the home page. Summarize the limitations: synthetic small graph, predefined scenarios, ordinal risk, no live flood/map feeds, approximate timing, and conditional heuristic claims. Close by restating that custom algorithms power the simulator and NetworkX is used only as an academic reference.
