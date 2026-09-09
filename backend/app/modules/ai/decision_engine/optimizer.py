"""
AegisAI Decision Engine — Global Multi-Incident Assignment Optimizer.

Formulates and solves global resource-to-incident allocation as a
Maximum-Weight Bipartite Matching / Linear Sum Assignment problem.
"""

import numpy as np
import structlog

from app.modules.ai.schemas import DecisionCandidateDTO, IncidentStateDTO

logger = structlog.get_logger("aegis_ai.decision_engine.optimizer")

PRIORITY_WEIGHTS: dict[str, float] = {
    "CRITICAL": 2.5,
    "HIGH": 1.7,
    "MEDIUM": 1.0,
    "LOW": 0.6,
}


class GlobalAssignmentOptimizer:
    """
    Solves the global resource assignment problem using maximum weight
    bipartite matching (Hungarian algorithm formulation).
    """

    @classmethod
    def solve_optimal_assignment(
        cls,
        incidents: list[IncidentStateDTO],
        candidates_by_incident: dict[int, list[DecisionCandidateDTO]],
    ) -> dict[int, DecisionCandidateDTO]:
        """
        Computes globally optimal incident-to-resource matching.
        """
        if not incidents or not candidates_by_incident:
            return {}

        incident_list = [inc for inc in incidents if inc.incident_id in candidates_by_incident]
        all_resource_ids = sorted(
            {
                c.resource_id
                for cand_list in candidates_by_incident.values()
                for c in cand_list
                if c.constraints_passed
            }
        )

        if not incident_list or not all_resource_ids:
            return {}

        num_incidents = len(incident_list)
        num_resources = len(all_resource_ids)
        matrix_size = max(num_incidents, num_resources)

        cost_matrix = np.full((matrix_size, matrix_size), 1000.0)
        candidate_lookup: dict[tuple[int, int], DecisionCandidateDTO] = {}

        for i_idx, inc in enumerate(incident_list):
            p_weight = PRIORITY_WEIGHTS.get(inc.severity.upper(), 1.0)
            cand_list = candidates_by_incident.get(inc.incident_id, [])

            for cand in cand_list:
                if cand.constraints_passed and cand.resource_id in all_resource_ids:
                    r_idx = all_resource_ids.index(cand.resource_id)
                    utility = cand.suitability * p_weight
                    cost_matrix[i_idx, r_idx] = 100.0 - utility
                    candidate_lookup[(inc.incident_id, cand.resource_id)] = cand

        row_ind, col_ind = cls._hungarian_assignment(cost_matrix)

        assigned_matches: dict[int, DecisionCandidateDTO] = {}
        for r, c in zip(row_ind, col_ind, strict=False):
            if r < num_incidents and c < num_resources:
                inc = incident_list[r]
                res_id = all_resource_ids[c]
                cand = candidate_lookup.get((inc.incident_id, res_id))
                if cand and cand.constraints_passed and cost_matrix[r, c] < 900.0:
                    assigned_matches[inc.incident_id] = cand

        logger.info(
            "global_optimization_solved",
            total_incidents=num_incidents,
            assigned_count=len(assigned_matches),
        )
        return assigned_matches

    @staticmethod
    def _hungarian_assignment(cost_matrix: np.ndarray) -> tuple[list[int], list[int]]:
        """
        Pure Python + NumPy implementation of Kuhn-Munkres (Hungarian) algorithm.
        """
        n = cost_matrix.shape[0]
        u = np.zeros(n)
        v = np.zeros(n)
        p = np.zeros(n, dtype=int)
        way = np.zeros(n, dtype=int)

        for i in range(1, n + 1):
            p[0] = i
            j0 = 0
            minv = np.full(n + 1, np.inf)
            used = np.zeros(n + 1, dtype=bool)

            while True:
                used[j0] = True
                i0 = p[j0]
                delta = np.inf
                j1 = 0

                for j in range(1, n + 1):
                    if not used[j]:
                        cur = cost_matrix[i0 - 1, j - 1] - u[i0 - 1] - v[j - 1]
                        if cur < minv[j]:
                            minv[j] = cur
                            way[j] = j0
                        if minv[j] < delta:
                            delta = minv[j]
                            j1 = j

                for j in range(0, n + 1):
                    if used[j]:
                        if j > 0:
                            v[j - 1] -= delta
                        i_adj = p[j]
                        if i_adj > 0:
                            u[i_adj - 1] += delta
                    else:
                        minv[j] -= delta

                j0 = j1
                if p[j0] == 0:
                    break

            while True:
                j1 = way[j0]
                p[j0] = p[j1]
                j0 = j1
                if j0 == 0:
                    break

        row_ind = []
        col_ind = []
        for j in range(1, n + 1):
            if p[j] > 0:
                row_ind.append(p[j] - 1)
                col_ind.append(j - 1)

        return row_ind, col_ind
