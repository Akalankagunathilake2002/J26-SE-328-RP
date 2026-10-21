import numpy as np
import pytest

from app.evidence.fusion import (
    EVIDENCE_RANKING, Evidence, FusionSettings, kind_strengths, roc_weights,
)
from app.evidence.sensitivity import (
    DIVERSITY_SHARE_RANGE, REPEAT_DECAY_RANGE, TOP_STRENGTH_RANGE, analyse, compare,
    ordered_weights, sample_settings,
)
from app.schemas.evidence import EvidenceType, SourceType

CV = SourceType.CV
LISTED, PROJECT = EvidenceType.CV_SELF_REPORTED, EvidenceType.PROJECT_DEMONSTRATED


def test_ordered_weights_keep_the_order_and_sum_to_one():
    rng = np.random.default_rng(1)
    for _ in range(50):
        weights = ordered_weights(rng, 9)
        assert sum(weights) == pytest.approx(1)
        assert weights == sorted(weights, reverse=True)


def test_roc_is_the_centre_of_the_sampled_weights():
    rng = np.random.default_rng(2)
    mean = np.mean([ordered_weights(rng, 4) for _ in range(20000)], axis=0)
    assert mean == pytest.approx(roc_weights(4), abs=0.01)


def test_sampled_settings_keep_the_ranking_and_the_ranges():
    rng = np.random.default_rng(3)
    for _ in range(50):
        settings = sample_settings(rng)
        tops = [settings.strengths[tier[0]] for tier in EVIDENCE_RANKING]
        assert tops == sorted(tops, reverse=True)
        certificate, portfolio = EVIDENCE_RANKING[0]
        assert settings.strengths[certificate] == settings.strengths[portfolio]
        assert TOP_STRENGTH_RANGE[0] <= max(tops) <= TOP_STRENGTH_RANGE[1]
        assert REPEAT_DECAY_RANGE[0] <= settings.repeat_decay <= REPEAT_DECAY_RANGE[1]
        assert DIVERSITY_SHARE_RANGE[0] <= settings.diversity_share <= DIVERSITY_SHARE_RANGE[1]


PROFILES = [{
    "python": [Evidence("cv", CV, LISTED), Evidence("cv", CV, PROJECT),
               Evidence("cert", SourceType.CERTIFICATE, EvidenceType.CERTIFICATE_SUPPORTED)],
    "java": [Evidence("cv", CV, LISTED)],
    "sql": [Evidence("cv", CV, LISTED), Evidence("cv", CV, PROJECT)],
}, {}]


def test_analyse_reports_stability():
    result = analyse(PROFILES, draws=200, seed=4)
    assert result.skills == 3 and result.draws == 200
    assert 0 <= result.level_stability <= 1 and 0 <= result.stable_skills <= 1
    assert result.rank_stability == pytest.approx(1.0)  # the order of these 3 never changes
    assert sum(result.level_counts.values()) == 3


def test_compare_with_identical_settings_changes_nothing():
    same = compare(PROFILES, FusionSettings(kind_strengths()))
    assert same.level_stability == 1.0 and same.mean_change == 0.0
