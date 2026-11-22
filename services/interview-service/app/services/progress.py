"""Progress across a student's interviews: score per interview over time, weakest topics and the concepts
missed in more than one interview (the gaps worth studying, linked to Skillaro lessons in the frontend)."""
from collections import Counter, defaultdict
from typing import Any, Dict, List

from app.services.evaluation_rag import overall_score


def _norm(concept: str) -> str:
    return " ".join(concept.lower().strip(" .").split())


def summarise_progress(student_id: str, sessions: List[Any], turns: List[Any]) -> Dict[str, Any]:
    """sessions: oldest first; turns: the evaluated role-question turns of those sessions."""
    by_session = defaultdict(list)
    for t in turns:
        by_session[t.session_id].append(t)

    history = []
    for s in sessions:
        ts = by_session.get(s.id, [])
        if not ts:
            continue                      # started but no answer evaluated
        avg = lambda attr: sum(float(getattr(t, attr)) for t in ts) / len(ts)
        tech, clar, expl = avg("technical_accuracy_score"), avg("clarity_score"), avg("explanation_quality_score")
        history.append({
            "session_id": str(s.id), "date": s.created_at.isoformat() if s.created_at else None,
            "target_role": s.target_role, "experience_level": s.experience_level, "answered": len(ts),
            "technical_accuracy": round(tech, 2), "overall_score": overall_score(tech, clar, expl),
        })

    # A concept counts once per interview, so one long interview can't dominate
    seen_in = Counter()
    label = {}
    for sid, ts in by_session.items():
        for concept in {_norm(c) for t in ts for c in (t.missing_concepts or []) if c and c.strip()}:
            seen_in[concept] += 1
        for t in ts:
            for c in t.missing_concepts or []:
                label.setdefault(_norm(c), c.strip(" ."))
    recurring = [{"concept": label[c], "interviews": n} for c, n in seen_in.most_common() if n >= 2][:8]
    recent = [{"concept": label[c], "interviews": n} for c, n in seen_in.most_common(8)]

    topic_scores = defaultdict(list)
    for t in turns:
        topic_scores[t.topic].append(float(t.technical_accuracy_score))
    topics = sorted(({"topic": k, "average": round(sum(v) / len(v), 2), "answers": len(v)}
                     for k, v in topic_scores.items()), key=lambda x: x["average"])

    trend = None
    if len(history) >= 2:
        trend = round(history[-1]["overall_score"] - history[0]["overall_score"], 2)
    return {"student_id": student_id, "interviews": history, "trend": trend,
            "recurring_gaps": recurring, "missed_concepts": recent, "weakest_topics": topics[:5]}
