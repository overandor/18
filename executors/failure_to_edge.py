#!/usr/bin/env python3
# ===============================================================
#  Deterministic Liquidity Kernel — Failure→Edge Monolith
#  Purpose: Convert rejected / failed states into real edge
# ===============================================================

import asyncio, time, math, random
from decimal import Decimal
from dataclasses import dataclass
from typing import Dict, List, Optional

# ----------- Configurable constants -----------------------------
CONF = dict(
    rebate_bps=2,           # maker rebate
    cancel_penalty_bps=0.3,   # expected cost of cancel
    staleness_kappa=0.02,     # tax per second of staleness
    max_slippage_bps=8,       # per-leg max slip tolerance
    gas_floor_wei=5e9,        # minimum gas price in wei
    gas_tip_wei=2e9,
)

# ===============================================================
#   Structures
# ===============================================================

@dataclass
class Quote:
    bid: Decimal
    ask: Decimal
    ts: float
    venue: str
    depth: Decimal

@dataclass
class Signal:
    edge_bps: Decimal
    theta_bps: Decimal
    priority: bool
    qpos: Decimal      # queue position proxy
    fade: Decimal      # fade speed proxy

@dataclass
class Costs:
    roundtrip_bps: Decimal
    staleness_tax_bps: Decimal

# ===============================================================
#   Utility
# ===============================================================

def bps(x): return Decimal(x) / Decimal(1e4)

def now(): return time.time()

# ===============================================================
#   Core Models
# ===============================================================

def fill_prob(qpos: Decimal, fade: Decimal) -> Decimal:
    """λ = exp(-fade * qpos) simple decay model"""
    return Decimal(math.exp(-float(fade * qpos)))

def adverse_selection_bps(qpos: Decimal, fade: Decimal) -> Decimal:
    """expected adverse price move proportional to fade"""
    return Decimal(5) * fade * qpos  # example calibration

def expected_ev_maker(qpos, fade, rebate_bps, cancel_penalty_bps) -> Decimal:
    lam = fill_prob(qpos, fade)
    adverse = adverse_selection_bps(qpos, fade)
    return rebate_bps * lam - adverse - cancel_penalty_bps

# ===============================================================
#   Decision Kernel
# ===============================================================

def decide(signal: Signal, costs: Costs) -> str:
    """Return TAKer / MAKER / ABSTAIN decision."""
    edge = signal.edge_bps
    theta = costs.roundtrip_bps + costs.staleness_tax_bps
    taker_ok = edge > theta

    ev_maker = expected_ev_maker(signal.qpos, signal.fade,
                                 CONF["rebate_bps"], CONF["cancel_penalty_bps"])

    if taker_ok and signal.priority:
        return "TAKER"
    if ev_maker > 0:
        return "MAKER"
    return "ABSTAIN"

# ===============================================================
#   Failure→Edge Conversions
# ===============================================================

async def handle_low_vol(signal: Signal, costs: Costs):
    """Low-vol regime → maker EV quoting"""
    ev = expected_ev_maker(signal.qpos, signal.fade,
                           CONF["rebate_bps"], CONF["cancel_penalty_bps"])
    if ev > 0:
        return {"action": "MAKER_QUOTE", "ev_bps": float(ev)}
    return {"action": "NO_TRADE"}

async def handle_staleness(quotes: List[Quote], edge_raw: Decimal):
    """Route to venue with min θ' = θ + κτ"""
    best = None
    best_theta = Decimal("inf")
    for q in quotes:
        tau = Decimal(now() - q.ts)
        theta_prime = (Decimal(4) + CONF["staleness_kappa"] * tau)  # dummy θ base=4bps
        if theta_prime < best_theta:
            best_theta, best = theta_prime, q.venue
    return {"route": best, "theta_prime": float(best_theta)}

async def handle_partial_fok(venues: Dict[str, Quote], qty_left: Decimal):
    """Optimize split across venues"""
    alloc = {}
    total_depth = sum(v.depth for v in venues.values())
    for name, q in venues.items():
        w = q.depth / total_depth
        alloc[name] = float(qty_left * w)
    return {"alloc": alloc}

async def handle_gas_spike(expected_profit_wei: Decimal, basefee: Decimal):
    """Gas-aware scheduling"""
    gas_cost = Decimal(CONF["gas_floor_wei"]) * basefee + CONF["gas_tip_wei"]
    if expected_profit_wei >= gas_cost:
        return {"execute": True, "margin": float(expected_profit_wei - gas_cost)}
    return {"execute": False, "reason": "gas_floor_not_met"}

# ===============================================================
#   Async Orchestration Loop (Mocked)
# ===============================================================

async def run_kernel():
    while True:
        # Mock signal generation
        sig = Signal(
            edge_bps=Decimal(random.uniform(0, 12)),
            theta_bps=Decimal(6),
            priority=random.choice([True, False]),
            qpos=Decimal(random.uniform(0.1, 1.0)),
            fade=Decimal(random.uniform(0.05, 0.2)),
        )
        costs = Costs(
            roundtrip_bps=Decimal(6),
            staleness_tax_bps=Decimal(random.uniform(0, 2)),
        )

        decision = decide(sig, costs)
        if decision == "ABSTAIN":
            # Route failure to edge
            out = await handle_low_vol(sig, costs)
        elif decision == "MAKER":
            out = {"action": "POST_MAKER", "ev_bps": float(expected_ev_maker(sig.qpos, sig.fade,
                                                                             CONF["rebate_bps"],
                                                                             CONF["cancel_penalty_bps"]))}
        else:
            out = {"action": "TAKER_EXEC"}

        print({
            "edge_bps": float(sig.edge_bps),
            "theta_bps": float(costs.roundtrip_bps + costs.staleness_tax_bps),
            "decision": decision,
            **out
        })
        await asyncio.sleep(1.0)

# ===============================================================
#   Entry
# ===============================================================

if __name__ == "__main__":
    try:
        asyncio.run(run_kernel())
    except KeyboardInterrupt:
        print("Exiting kernel loop.")
