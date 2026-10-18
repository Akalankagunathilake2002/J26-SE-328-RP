"""Answer scorer: mode handling, calibration and fallbacks (app/services/answer_scorer.py)."""
import json

from app.core.config import settings
from app.services.answer_scorer import AnswerScorer


def make_scorer(tmp_path, config):
    (tmp_path / "scoring_config.json").write_text(json.dumps(config))
    return AnswerScorer(model_dir=tmp_path)


CONFIG = {"mode": "calibrated", "calibration": {"x": [1.0, 3.0, 5.0], "y": [0.5, 3.5, 4.9]}, "blend_weight_llm": 0.6}


def test_without_reference_answer_the_llm_score_is_kept(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SCORING_MODE", "auto")
    scorer = make_scorer(tmp_path, CONFIG)
    assert scorer.technical_accuracy(3.0, "q", None, "a") == (3.0, "llm")


def test_calibration_interpolates_and_clamps_to_interview_scale(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SCORING_MODE", "auto")
    scorer = make_scorer(tmp_path, CONFIG)
    assert scorer.technical_accuracy(4.0, "q", "ref", "a") == (4.2, "calibrated")
    # 0.5 on the 0-5 human scale is below the interview's 1-5 range
    assert scorer.technical_accuracy(1.0, "q", "ref", "a") == (1.0, "calibrated")


def test_forced_llm_mode_ignores_the_config(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SCORING_MODE", "llm")
    scorer = make_scorer(tmp_path, CONFIG)
    assert scorer.technical_accuracy(4.0, "q", "ref", "a") == (4.0, "llm")


def test_missing_model_falls_back_to_the_llm_score(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SCORING_MODE", "trained")
    scorer = make_scorer(tmp_path, CONFIG)        # no model.onnx in tmp_path
    assert scorer.technical_accuracy(3.5, "q", "ref", "a") == (3.5, "llm")


def test_blend_weights_calibrated_llm_and_trained_scores(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SCORING_MODE", "blend")
    scorer = make_scorer(tmp_path, CONFIG)
    monkeypatch.setattr(scorer, "trained_score", lambda q, r, a: 2.0)
    # 0.6 * calibrate(5.0)=4.9 + 0.4 * 2.0 = 3.74
    assert scorer.technical_accuracy(5.0, "q", "ref", "a") == (3.74, "blend")


def test_non_technical_roles_keep_the_llm_score(tmp_path, monkeypatch):
    # The scorer and calibration were fitted on computer-science answers
    monkeypatch.setattr(settings, "SCORING_MODE", "calibrated")
    scorer = make_scorer(tmp_path, CONFIG)
    assert scorer.technical_accuracy(4.0, "q", "ref", "a", role="HR Manager") == (4.0, "llm")
    assert scorer.technical_accuracy(4.0, "q", "ref", "a", role="Backend Developer") == (4.2, "calibrated")


def test_cv_keyword_fallback_recognises_non_technical_roles():
    from app.services.cv_service import _keyword_profile
    cv = ("Human resources generalist: recruitment, onboarding, payroll and employee relations; "
          "ran performance appraisal cycles and managed the HRIS. Final year student.")
    roles = ["Backend Developer", "HR Manager", "Finance Executive"]
    profile = _keyword_profile(cv, roles)
    assert profile["suggested_role"] == "HR Manager"
    assert "recruitment" in profile["skills"]
