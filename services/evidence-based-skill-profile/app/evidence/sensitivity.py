"""SMAA-style sensitivity analysis of the confidence score (TAF tasks 7 and 10).

SMAA (Lahdelma, Hokkanen & Salminen, 1998, European Journal of Operational Research 106(1):
137-143) handles decisions whose weights are not known exactly: instead of one weight vector, it
samples many that respect what IS known and reports how stable the results are.

What is known here is only the ORDER of the kinds of evidence. Weight vectors are drawn uniformly
from all vectors that keep that order (sorted uniform samples from the simplex); the Rank Order
Centroid used by the service is exactly the centre of this set. The other settings are drawn from
plausible ranges. For each draw every skill's confidence is recomputed and compared with the
service's default result:

    level stability   share of draws in which a skill keeps its level (strong/moderate/weak)
    rank stability    Kendall's tau between default and sampled confidences within a profile
    mean change       mean absolute change of the confidence
"""
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy.stats import kendalltau

from app.evidence.fusion import (
    DEFAULT_SETTINGS, EVIDENCE_RANKING, Evidence, FusionSettings, Kind, confidence_level, fuse,
    kind_strengths,
)

TOP_STRENGTH_RANGE = (0.80, 0.95)
REPEAT_DECAY_RANGE = (0.3, 0.7)
DIVERSITY_SHARE_RANGE = (0.0, 0.3)
STABLE_FROM = 0.8  # a skill is "stable" if it keeps its level in at least 80% of draws

# A profile: skill ID -> all evidence for that skill.
Profile = dict[str, list[Evidence]]


def ordered_weights(rng: np.random.Generator, n: int) -> list[float]:
    """A random weight vector, uniform over all vectors with w1 >= w2 >= ... >= wn summing to 1."""
    return sorted(rng.dirichlet(np.ones(n)), reverse=True)


def sample_settings(rng: np.random.Generator,
                    tiers: Sequence[Sequence[Kind]] = EVIDENCE_RANKING) -> FusionSettings:
    positions = sum(len(tier) for tier in tiers)
    return FusionSettings(
        strengths=kind_strengths(tiers, ordered_weights(rng, positions),
                                 rng.uniform(*TOP_STRENGTH_RANGE)),
        repeat_decay=rng.uniform(*REPEAT_DECAY_RANGE),
        diversity_share=rng.uniform(*DIVERSITY_SHARE_RANGE),
    )


@dataclass(frozen=True)
class SensitivityResult:
    draws: int
    skills: int
    level_stability: float          # mean share of draws keeping the default level
    stable_skills: float            # share of skills keeping their level in >= STABLE_FROM draws
    rank_stability: float           # mean Kendall's tau within profiles (profiles with 3+ skills)
    mean_change: float              # mean absolute change of confidence
    level_counts: dict[str, int]    # default levels, for context
    by_level: dict[str, float] = None  # level_stability split by the default level


def _confidences(profiles: Sequence[Profile], settings: FusionSettings) -> list[np.ndarray]:
    return [np.array([fuse(evidence, settings)[0] for evidence in profile.values()])
            for profile in profiles]


def analyse(profiles: Sequence[Profile], draws: int = 1000, seed: int = 7,
            tiers: Sequence[Sequence[Kind]] = EVIDENCE_RANKING,
            baseline: FusionSettings = DEFAULT_SETTINGS) -> SensitivityResult:
    rng = np.random.default_rng(seed)
    profiles = [p for p in profiles if p]
    base = _confidences(profiles, baseline)
    base_levels = [[confidence_level(c) for c in values] for values in base]
    same_level = [np.zeros(len(values)) for values in base]
    taus, changes = [], []
    for _ in range(draws):
        sampled = _confidences(profiles, sample_settings(rng, tiers))
        for i, (old, new) in enumerate(zip(base, sampled)):
            same_level[i] += [confidence_level(c) == level
                              for c, level in zip(new, base_levels[i])]
            changes.append(np.abs(new - old).mean())
            if len(old) >= 3 and np.ptp(old) > 0:
                taus.append(kendalltau(old, new).statistic)
    shares = np.concatenate(same_level) / draws
    levels = [level for row in base_levels for level in row]
    by_level = {str(level): float(np.mean([s for s, lv in zip(shares, levels) if lv == level]))
                for level in dict.fromkeys(levels)}
    return SensitivityResult(
        draws=draws,
        skills=len(shares),
        level_stability=float(shares.mean()),
        stable_skills=float((shares >= STABLE_FROM).mean()),
        rank_stability=float(np.nanmean(taus)) if taus else float("nan"),
        mean_change=float(np.mean(changes)),
        level_counts={str(level): levels.count(level) for level in dict.fromkeys(levels)},
        by_level=by_level,
    )


def compare(profiles: Sequence[Profile], other: FusionSettings,
            baseline: FusionSettings = DEFAULT_SETTINGS) -> SensitivityResult:
    """The same measures for one alternative setting (e.g. another evidence order) vs default."""
    profiles = [p for p in profiles if p]
    base, new = _confidences(profiles, baseline), _confidences(profiles, other)
    same = np.concatenate([[confidence_level(a) == confidence_level(b) for a, b in zip(x, y)]
                           for x, y in zip(base, new)])
    taus = [kendalltau(x, y).statistic for x, y in zip(base, new)
            if len(x) >= 3 and np.ptp(x) > 0]
    levels = [str(confidence_level(c)) for values in base for c in values]
    return SensitivityResult(
        draws=1, skills=len(same), level_stability=float(same.mean()),
        stable_skills=float(same.mean()),
        rank_stability=float(np.nanmean(taus)) if taus else float("nan"),
        mean_change=float(np.mean([np.abs(x - y).mean() for x, y in zip(base, new)])),
        level_counts={level: levels.count(level) for level in dict.fromkeys(levels)},
    )
