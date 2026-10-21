"""Evidence-fusion confidence score (TAF task 7).

Combines every piece of evidence for one skill into a confidence from 0 to 1, using four of the
five TAF factors (the fifth, student verification, is applied to the profile in task 8).

1-2. Source reliability and evidence context, as one ranking of the KINDS of evidence (a kind is a
     source type + evidence type). Only the order is decided; it follows one principle, "the more
     someone else can check it, the stronger it is": a separate document beats a line in the CV the
     student wrote, and checkable beats claimed. Certificates and portfolios share the top rank,
     because the evidence on which employers value more is mixed and depends on the field.

         1-2  certificate file          = portfolio / work sample (GitHub, designs, HR documents...)
         3    project or internship report
         4    academic document (transcript, syllabus)
         5    CV: certificate named
         6    CV: project or work described
         7    CV: course or degree named
         8    CV: skill listed
         9    CV: interest only ("interested in learning ...")

     The order is turned into weights with the Rank Order Centroid (Barron & Barrett, 1996,
     Management Science 42(11):1515-1523): w_k = (1/n) * sum_{i=k..n} 1/i. Tied kinds share the
     average of their positions' weights. The weights are scaled so the top kind has TOP_STRENGTH
     (0.9: even a certificate is not absolute proof), giving each kind's strength S.
3.   Repeated mentions: the k-th mention (from 0, strongest first) of the same kind in the same
     document counts REPEAT_DECAY ** k as much, so listing "Python" five times is not five proofs.
4.   Source diversity D: the share of source types that support the skill.

Each mention is also weighted by its match score M (task 4/5): how sure the extractor is that the
text really is this skill (1.0 for an exact dictionary match, lower for an AI meaning match).

    s(e) = S(kind) * M(e) * REPEAT_DECAY ** k
    E    = 1 - (1 - s1)(1 - s2) ... (1 - sn)        Noisy-OR (Pearl, 1988)
    C    = E * (1 - DIVERSITY_SHARE + DIVERSITY_SHARE * D)

Noisy-OR treats each piece of evidence as an independent chance that the student has the skill:
more evidence always raises E, missing evidence never lowers it, and E never reaches 1.

Every setting here (the ranking, TOP_STRENGTH, REPEAT_DECAY, DIVERSITY_SHARE) is tested by the
SMAA-style sensitivity analysis in scripts/sensitivity_analysis.py (Lahdelma et al., 1998).
"""
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from app.schemas.evidence import EvidenceType, SourceType
from app.schemas.extraction import ConfidenceLevel, EvidenceContribution

Kind = tuple[SourceType, EvidenceType]

# Strongest first; kinds in the same tier are tied.
EVIDENCE_RANKING: list[list[Kind]] = [
    [(SourceType.CERTIFICATE, EvidenceType.CERTIFICATE_SUPPORTED),
     (SourceType.PORTFOLIO_LINK, EvidenceType.PORTFOLIO_SUPPORTED)],
    [(SourceType.PROJECT_DESCRIPTION, EvidenceType.PROJECT_DEMONSTRATED)],
    [(SourceType.ACADEMIC_DOCUMENT, EvidenceType.ACADEMIC_EXPOSURE)],
    [(SourceType.CV, EvidenceType.CERTIFICATE_SUPPORTED)],
    [(SourceType.CV, EvidenceType.PROJECT_DEMONSTRATED)],
    [(SourceType.CV, EvidenceType.ACADEMIC_EXPOSURE)],
    [(SourceType.CV, EvidenceType.CV_SELF_REPORTED)],
    [(SourceType.CV, EvidenceType.UNVERIFIED_MENTION)],
]
TOP_STRENGTH = 0.9
REPEAT_DECAY = 0.5
DIVERSITY_SHARE = 0.15
STRONG_FROM = 0.70
MODERATE_FROM = 0.40


def roc_weights(n: int) -> list[float]:
    """Rank Order Centroid weights for n ranked items, largest first; they sum to 1."""
    return [sum(1 / i for i in range(k, n + 1)) / n for k in range(1, n + 1)]


def tier_weights(tiers: Sequence[Sequence[Kind]],
                 weights: Sequence[float] | None = None) -> dict[Kind, float]:
    """Weight of every kind: positions are numbered across tiers, tied kinds share the average of
    their positions' weights. `weights` (one per position, largest first) defaults to ROC."""
    positions = sum(len(tier) for tier in tiers)
    weights = list(weights) if weights is not None else roc_weights(positions)
    result, position = {}, 0
    for tier in tiers:
        share = sum(weights[position:position + len(tier)]) / len(tier)
        result.update({kind: share for kind in tier})
        position += len(tier)
    return result


def kind_strengths(tiers: Sequence[Sequence[Kind]] = EVIDENCE_RANKING,
                   weights: Sequence[float] | None = None,
                   top_strength: float = TOP_STRENGTH) -> dict[Kind, float]:
    """Strength of each kind of evidence: its weight scaled so the strongest kind = top_strength."""
    raw = tier_weights(tiers, weights)
    top = max(raw.values())
    return {kind: top_strength * value / top for kind, value in raw.items()}


@dataclass(frozen=True)
class FusionSettings:
    """All settings of the score in one place, so the sensitivity analysis can vary them."""

    strengths: dict[Kind, float] = field(default_factory=kind_strengths)
    repeat_decay: float = REPEAT_DECAY
    diversity_share: float = DIVERSITY_SHARE

    def strength(self, source: SourceType, evidence_type: EvidenceType) -> float:
        """Strength of a kind. A kind outside the ranking (e.g. "interested in" inside a
        certificate) counts as the same evidence type written in a CV; unknown types as the
        weakest kind."""
        for kind in ((source, evidence_type), (SourceType.CV, evidence_type)):
            if kind in self.strengths:
                return self.strengths[kind]
        return min(self.strengths.values())


DEFAULT_SETTINGS = FusionSettings()


@dataclass(frozen=True)
class Evidence:
    """One mention of a skill: which document, what kind of document, how it was used, and how
    sure the extractor is that the text is this skill."""

    document: str
    source: SourceType
    evidence_type: EvidenceType
    match_score: float = 1.0


def noisy_or(strengths: Iterable[float]) -> float:
    """1 - product of (1 - s): the chance that at least one piece of evidence holds."""
    doubt = 1.0
    for strength in strengths:
        doubt *= 1.0 - strength
    return 1.0 - doubt


def source_diversity(sources: Iterable[SourceType]) -> float:
    return len(set(sources)) / len(SourceType)


def confidence_level(confidence: float) -> ConfidenceLevel:
    if confidence >= STRONG_FROM:
        return ConfidenceLevel.STRONG
    if confidence >= MODERATE_FROM:
        return ConfidenceLevel.MODERATE
    return ConfidenceLevel.WEAK


def fuse(evidence: Iterable[Evidence], settings: FusionSettings = DEFAULT_SETTINGS,
         ) -> tuple[float, list[EvidenceContribution]]:
    """Confidence for one skill from all its evidence.

    Also returns what each kind of evidence added, strongest first, so every score can be
    explained to the student and the panel.
    """
    per_document: dict[tuple[str, SourceType, EvidenceType], list[float]] = {}
    for item in evidence:
        base = settings.strength(item.source, item.evidence_type) * item.match_score
        per_document.setdefault((item.document, item.source, item.evidence_type), []).append(base)
    grouped: dict[Kind, list[float]] = {}
    for (_, source, evidence_type), bases in per_document.items():
        grouped.setdefault((source, evidence_type), []).extend(
            base * settings.repeat_decay**k for k, base in enumerate(sorted(bases, reverse=True))
        )
    contributions = sorted(
        (
            EvidenceContribution(source=source, evidence_type=evidence_type,
                                 mentions=len(strengths), strength=round(noisy_or(strengths), 3))
            for (source, evidence_type), strengths in grouped.items()
        ),
        key=lambda c: -c.strength,
    )
    combined = noisy_or(s for strengths in grouped.values() for s in strengths)
    diversity = source_diversity(source for source, _ in grouped)
    share = settings.diversity_share
    confidence = combined * (1 - share + share * diversity)
    return round(confidence, 3), contributions
