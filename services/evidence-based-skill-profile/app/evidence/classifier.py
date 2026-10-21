"""Evidence context classification v2: a SetFit model (TAF task 6).

SetFit (Tunstall et al., 2022) fine-tunes a pretrained sentence-transformer with few labelled
examples: it first learns from pairs of sentences (same evidence type or not), then fits a small
classifier on the sentence vectors. Here it starts from all-MiniLM-L6-v2 (the model already used
for the semantic skill index) and is trained on hand-labelled CV sentences by
scripts/train_evidence_model.py.

The model reads the CV section and the sentence together ("experience: Responsible for the Python
backend"), the same information the v1 rules use, so the two can be compared fairly. It is only
used for CVs; other document types keep their source-based type (a certificate is certificate
evidence whatever its wording).

The model decides the evidence type of every CV sentence; the v1 rules (app/evidence/rules.py) are
kept only as the baseline it is compared with, and as a fallback when no trained model exists.

It learns four types. The fifth, unverified_mention ("interested in learning Kubernetes"), did not
occur in a 144-sentence sample of the professional Kaggle resumes, so it cannot be learned yet;
adding real examples from student CVs to the labelled data and re-training adds it.
"""
import logging
from functools import lru_cache
from pathlib import Path

from app.config.settings import get_settings
from app.schemas.evidence import EvidenceType
from app.schemas.extraction import SectionType

logger = logging.getLogger(__name__)

MODEL_LABELS = [
    EvidenceType.PROJECT_DEMONSTRATED,
    EvidenceType.CV_SELF_REPORTED,
    EvidenceType.ACADEMIC_EXPOSURE,
    EvidenceType.CERTIFICATE_SUPPORTED,
]


def model_input(section: SectionType | str, sentence: str) -> str:
    return f"{section}: {sentence}"


class EvidenceClassifier:
    def __init__(self, model_dir: Path):
        from setfit import SetFitModel  # heavy import, load on first use

        self._model = SetFitModel.from_pretrained(str(model_dir))

    def predict(self, items: list[tuple[SectionType | str, str]]) -> list[EvidenceType]:
        if not items:
            return []
        labels = self._model.predict([model_input(s, t) for s, t in items])
        return [EvidenceType(str(label)) for label in labels]


@lru_cache
def get_evidence_classifier() -> EvidenceClassifier | None:
    """The trained SetFit classifier when settings ask for it, else None (rules are used)."""
    settings = get_settings()
    if settings.evidence_classifier != "setfit":
        return None
    if not settings.evidence_model_dir.exists():
        logger.warning("No evidence model in %s; falling back to the v1 rules. Train it with "
                       "python -m scripts.train_evidence_model", settings.evidence_model_dir)
        return None
    return EvidenceClassifier(settings.evidence_model_dir)
