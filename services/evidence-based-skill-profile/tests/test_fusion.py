import pytest

from app.evidence.fusion import (
    EVIDENCE_RANKING, TOP_STRENGTH, Evidence, FusionSettings, confidence_level, fuse,
    kind_strengths, noisy_or, roc_weights, source_diversity, tier_weights,
)
from app.schemas.evidence import EvidenceType, SourceType
from app.schemas.extraction import ConfidenceLevel

PROJECT = EvidenceType.PROJECT_DEMONSTRATED
LISTED = EvidenceType.CV_SELF_REPORTED
CERTIFIED = EvidenceType.CERTIFICATE_SUPPORTED
PORTFOLIO = EvidenceType.PORTFOLIO_SUPPORTED
UNVERIFIED = EvidenceType.UNVERIFIED_MENTION
CV, CERTIFICATE, REPORT = SourceType.CV, SourceType.CERTIFICATE, SourceType.PROJECT_DESCRIPTION
GITHUB = SourceType.PORTFOLIO_LINK

LISTED_IN_CV = Evidence("cv.pdf", CV, LISTED)
USED_IN_CV = Evidence("cv.pdf", CV, PROJECT)
CERTIFICATE_PDF = Evidence("aws.pdf", CERTIFICATE, CERTIFIED)
PROJECT_REPORT = Evidence("report.pdf", REPORT, PROJECT)
REPOSITORY = Evidence("github.com/x/y", GITHUB, PORTFOLIO)

S = kind_strengths()
ONE_SOURCE = 0.85 + 0.15 * 1 / 5  # diversity factor with one source type
THREE_SOURCES = 0.85 + 0.15 * 3 / 5


def test_roc_matches_the_published_values():
    # Barron & Barrett (1996): 3 ranks -> .611 .278 .111; 4 ranks -> .521 .271 .146 .0625
    assert [round(w, 3) for w in roc_weights(3)] == [0.611, 0.278, 0.111]
    assert [round(w, 4) for w in roc_weights(4)] == [0.5208, 0.2708, 0.1458, 0.0625]
    for n in range(1, 12):
        weights = roc_weights(n)
        assert sum(weights) == pytest.approx(1.0)
        assert weights == sorted(weights, reverse=True)


def test_tied_kinds_share_the_average_of_their_positions():
    a, b, c = (CV, LISTED), (CV, PROJECT), (CV, CERTIFIED)
    weights = tier_weights([[a, b], [c]])
    roc = roc_weights(3)
    assert weights[a] == weights[b] == pytest.approx((roc[0] + roc[1]) / 2)
    assert weights[c] == pytest.approx(roc[2])


def test_kind_strengths_follow_the_ranking():
    assert S[(CERTIFICATE, CERTIFIED)] == S[(GITHUB, PORTFOLIO)] == TOP_STRENGTH
    order = [S[tier[0]] for tier in EVIDENCE_RANKING]
    assert order == sorted(order, reverse=True) and len(set(order)) == len(order)
    assert round(S[(CV, LISTED)], 3) == 0.091


def test_noisy_or_and_diversity():
    assert noisy_or([]) == 0.0
    assert noisy_or([0.3, 0.7]) == pytest.approx(1 - 0.7 * 0.3)
    assert source_diversity([CV, CV]) == 1 / 5
    assert source_diversity([CV, CERTIFICATE]) == 2 / 5


def test_worked_example_python():
    # Listed + used in the CV, a project report and a certificate file.
    confidence, _ = fuse([LISTED_IN_CV, USED_IN_CV, PROJECT_REPORT, CERTIFICATE_PDF])
    expected = noisy_or([S[(CV, LISTED)], S[(CV, PROJECT)], S[(REPORT, PROJECT)],
                         S[(CERTIFICATE, CERTIFIED)]]) * THREE_SOURCES
    assert confidence == round(expected, 3)
    assert confidence_level(confidence) == ConfidenceLevel.STRONG
    assert confidence_level(fuse([LISTED_IN_CV])[0]) == ConfidenceLevel.WEAK


def test_more_and_stronger_evidence_raise_confidence():
    listed = fuse([LISTED_IN_CV])[0]
    used = fuse([LISTED_IN_CV, USED_IN_CV])[0]
    reported = fuse([LISTED_IN_CV, USED_IN_CV, PROJECT_REPORT])[0]
    certified = fuse([LISTED_IN_CV, USED_IN_CV, PROJECT_REPORT, CERTIFICATE_PDF])[0]
    assert listed < used < reported < certified < 1.0


def test_a_portfolio_counts_as_much_as_a_certificate():
    assert fuse([REPOSITORY])[0] == fuse([CERTIFICATE_PDF])[0]
    real_work = fuse([LISTED_IN_CV, USED_IN_CV, PROJECT_REPORT, REPOSITORY])[0]
    assert confidence_level(real_work) == ConfidenceLevel.STRONG


def test_a_cv_alone_cannot_make_a_skill_strong():
    cv_only = fuse([LISTED_IN_CV] + [USED_IN_CV] * 3 + [Evidence("cv.pdf", CV, CERTIFIED)])[0]
    assert confidence_level(cv_only) != ConfidenceLevel.STRONG


def test_repeating_a_claim_adds_little_but_another_document_adds_more():
    once = fuse([LISTED_IN_CV])[0]
    five_times = fuse([LISTED_IN_CV] * 5)[0]
    assert once < five_times < fuse([USED_IN_CV])[0]
    two_cvs = fuse([LISTED_IN_CV, Evidence("cv2.pdf", CV, LISTED)])[0]
    assert two_cvs > fuse([LISTED_IN_CV] * 2)[0]


def test_an_unsure_match_is_weaker_evidence():
    certain = fuse([Evidence("cv.pdf", CV, PROJECT, 1.0)])[0]
    unsure = fuse([Evidence("cv.pdf", CV, PROJECT, 0.54)])[0]
    assert certain == fuse([USED_IN_CV])[0]  # match score 1.0 is the default
    assert unsure == round(S[(CV, PROJECT)] * 0.54 * ONE_SOURCE, 3)


def test_repeat_decay_counts_the_most_certain_mention_fully():
    _, evidence = fuse([Evidence("cv.pdf", CV, LISTED, 0.5), Evidence("cv.pdf", CV, LISTED, 1.0)])
    listed = S[(CV, LISTED)]
    assert evidence[0].mentions == 2
    assert evidence[0].strength == round(noisy_or([listed, listed * 0.5 * 0.5]), 3)


def test_contributions_explain_the_score():
    _, evidence = fuse([LISTED_IN_CV, USED_IN_CV, USED_IN_CV, CERTIFICATE_PDF])
    assert [(c.source, c.evidence_type) for c in evidence] == [
        (CERTIFICATE, CERTIFIED), (CV, PROJECT), (CV, LISTED),
    ]
    assert evidence[1].mentions == 2


def test_kinds_outside_the_ranking_fall_back_to_the_cv_kind():
    settings = FusionSettings()
    assert settings.strength(CERTIFICATE, UNVERIFIED) == S[(CV, UNVERIFIED)]
    assert settings.strength(CV, PORTFOLIO) == min(S.values())


def test_settings_can_be_changed_for_the_sensitivity_analysis():
    flat = FusionSettings(strengths={kind: 0.5 for kind in S}, repeat_decay=1.0,
                          diversity_share=0.0)
    assert fuse([LISTED_IN_CV, LISTED_IN_CV], flat)[0] == 0.75


def test_levels():
    assert confidence_level(0.70) == ConfidenceLevel.STRONG
    assert confidence_level(0.40) == ConfidenceLevel.MODERATE
    assert confidence_level(0.39) == ConfidenceLevel.WEAK
