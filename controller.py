import math
from typing import Tuple, Dict

class SupervisoryController:
    def __init__(self, energy_budget: float = 100.0, lambda_energy: float = 0.45):
        self.energy_budget = energy_budget
        self.lambda_energy = lambda_energy
        self.E_t = energy_budget
        self.D_t = 0.0
        self.M_t = "stabilize"

    def select_mode(self, H_t: float, context_length: int) -> Tuple[str, float, Dict[str, float]]:
        E_proxy = context_length * 0.003
        budget_remaining = self.E_t / max(self.energy_budget, 1e-9)

        score_stab = -3.2 * H_t - self.lambda_energy * E_proxy * 1.1
        score_expl = -0.8 * H_t - self.lambda_energy * E_proxy * 5.0   # ← Much more expensive
        score_comp = -3.5 * H_t - self.lambda_energy * E_proxy * 0.3

        # Strong preemptive rules to stem waste
        if budget_remaining < 0.35 or self.D_t > 10:
            mode = "stabilize"
            temperature = 0.3
        elif budget_remaining < 0.6 or self.D_t > 5:
            mode = "stabilize"
            temperature = 0.4
        elif H_t < 3.0:                          # Low entropy = stabilize
            mode = "stabilize"
            temperature = 0.35
        elif score_expl > score_stab and score_expl > score_comp and budget_remaining > 0.5:
            mode = "explore"
            temperature = 0.85
        else:
            mode = "stabilize"
            temperature = 0.4

        self.M_t = mode
        return mode, temperature, {"stabilize": score_stab, "explore": score_expl, "compress": score_comp}

    def update_state(self, tokens_generated: int, mode: str, failure_detected: bool = False):
        if mode == "stabilize":
            cost_multiplier = 1.0
        elif mode == "explore":
            cost_multiplier = 6.5          # ← Significantly higher cost for creative mode
        else:
            cost_multiplier = 0.4

        energy_cost = tokens_generated * 0.06 * cost_multiplier   # slightly higher base too

        penalty = 0.0
        if failure_detected:
            penalty = 7.0 * self.lambda_energy
            self.D_t += penalty

        self.E_t -= (energy_cost + penalty)
        self.D_t *= 0.96

        # Prevent negative energy (hard clamp)
        if self.E_t < 0:
            self.E_t = 0.0

        return energy_cost, penalty

    def get_state(self) -> dict:
        return {
            "energy_remaining": float(self.E_t),
            "error_debt": float(self.D_t),
            "last_mode": str(self.M_t),
            "budget_remaining_pct": float((self.E_t / max(self.energy_budget, 1e-9)) * 100.0)
        }