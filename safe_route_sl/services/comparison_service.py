"""Algorithm comparison service for SafeRouteSL."""

from __future__ import annotations

from dataclasses import dataclass, replace
from time import perf_counter

import networkx as nx

from models.configuration import SearchConfiguration
from services.search_service import get_algorithm, get_supported_algorithms, run_search
from utils.exceptions import SafeRouteError


@dataclass(frozen=True, slots=True)
class AlgorithmComparisonRecord:
	algorithm_name: str
	found: bool
	path: tuple[str, ...]
	total_cost: float
	nodes_expanded: int
	nodes_generated: int
	maximum_frontier_size: int
	execution_time_ms: float
	path_length_edges: int
	optimality_expected: bool
	completeness_expected: bool
	error_message: str | None = None


def compare_algorithms(
	graph: nx.Graph,
	base_configuration: SearchConfiguration,
	algorithm_names: tuple[str, ...] | None = None,
) -> tuple[AlgorithmComparisonRecord, ...]:
	requested_names = algorithm_names or get_supported_algorithms()
	records: list[AlgorithmComparisonRecord] = []

	for algorithm_name in requested_names:
		algorithm = None
		start_time = perf_counter()
		try:
			algorithm = get_algorithm(algorithm_name)
			configuration = replace(base_configuration, algorithm=algorithm_name)
			result = run_search(graph, configuration)
		except SafeRouteError as error:
			elapsed_ms = (perf_counter() - start_time) * 1000
			records.append(
				AlgorithmComparisonRecord(
					algorithm_name=algorithm_name,
					found=False,
					path=(),
					total_cost=float("inf"),
					nodes_expanded=0,
					nodes_generated=0,
					maximum_frontier_size=0,
					execution_time_ms=elapsed_ms,
					path_length_edges=0,
					optimality_expected=algorithm.optimality_expected if algorithm is not None else False,
					completeness_expected=algorithm.completeness_expected if algorithm is not None else False,
					error_message=str(error),
				)
			)
			continue

		elapsed_ms = max(result.execution_time_ms, (perf_counter() - start_time) * 1000)
		records.append(
			AlgorithmComparisonRecord(
				algorithm_name=algorithm_name,
				found=result.found,
				path=result.final_path,
				total_cost=result.total_cost,
				nodes_expanded=result.nodes_expanded,
				nodes_generated=result.nodes_generated,
				maximum_frontier_size=result.maximum_frontier_size,
				execution_time_ms=elapsed_ms,
				path_length_edges=result.path_length_edges,
				optimality_expected=result.optimality_expected,
				completeness_expected=result.completeness_expected,
				error_message=result.error_message,
			)
		)

	return tuple(records)
