"""Agreement metrics for 0-5 scores (same definitions as services/interview-service/evaluation/eval_mohler.py,
which can't be imported outside the service container)."""
import numpy as np


def pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.corrcoef(a, b)[0, 1]) if len(a) > 2 and a.std() and b.std() else float("nan")


def spearman(a, b):
    def ranks(x):
        x = np.asarray(x, float)
        order = np.argsort(x, kind="mergesort")
        r = np.empty(len(x))
        r[order] = np.arange(len(x))
        for v in np.unique(x):                      # average ranks for ties
            r[x == v] = r[x == v].mean()
        return r
    return pearson(ranks(a), ranks(b))


def qwk(a, b, k=6):
    a = np.clip(np.rint(a), 0, k - 1).astype(int)
    b = np.clip(np.rint(b), 0, k - 1).astype(int)
    observed = np.zeros((k, k))
    for x, y in zip(a, b):
        observed[x, y] += 1
    weights = np.array([[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)])
    expected = np.outer(observed.sum(1), observed.sum(0)) / max(observed.sum(), 1)
    denom = (weights * expected).sum()
    return float(1 - (weights * observed).sum() / denom) if denom else float("nan")


def agreement(human, model) -> dict:
    human, model = np.asarray(human, float), np.asarray(model, float)
    return {"n": int(len(human)), "pearson": round(pearson(human, model), 3),
            "spearman": round(spearman(human, model), 3), "qwk": round(qwk(human, model), 3),
            "mae": round(float(np.mean(np.abs(human - model))), 3),
            "mean_human": round(float(human.mean()), 2), "mean_model": round(float(model.mean()), 2)}
