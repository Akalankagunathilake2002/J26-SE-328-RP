"""Skill normalisation engine: any written skill term → one standard skill ID (TAF task 5).

A cascade, from the most to the least certain method; the first that succeeds wins:

1. exact      the term is a dictionary name or alias (case ignored)
2. cleaned    the same after removing versions and suffixes: "Python3", "Python 3.10" → python,
              "ReactJS", "React-based" → react, "Node JS" → node.js
3. fuzzy      a spelling mistake: Damerau-Levenshtein distance (a swap of two letters is one edit)
              of at most 1 edit for terms of 5-8 letters and 2 for longer ones; shorter terms and
              acronyms in capitals ("SPARC" is not "SPARK") are never fuzzy-matched, the first
              letter must be the same (typos rarely change it: "IT systems" is not "ML systems"),
              and a tie between two skills is not guessed.
4. semantic   same meaning in other words: the BERT sentence index (app/semantic) returns the
              closest skills, accepted when the best cosine >= SEMANTIC_MIN. Optionally a
              cross-encoder re-ranks the top candidates by reading the term and each skill's
              description together (settings.use_reranker; on: +1 paraphrase on the dev set).
5. esco       not in the C02 dictionary but close to an ESCO skill → new-skill candidate for SSKS
6. unmatched  nothing is close enough; better no answer than a wrong one

The thresholds are v1 values checked on data/evaluation/normalisation_dev.csv
(scripts/evaluate_normalisation.py) and are tuned again in task 10.
"""
import logging
import re
from functools import lru_cache
from typing import Protocol

from rapidfuzz import process
from rapidfuzz.distance import DamerauLevenshtein

from app.config.settings import get_settings
from app.extraction.matcher import SkillEntry, load_entries
from app.schemas.normalisation import Candidate, MatchMethod, NormalisedTerm
from app.semantic.encoder import Encoder
from app.semantic.skill_index import SkillHit, SkillIndex, SkillIndexError

logger = logging.getLogger(__name__)

FUZZY_MIN_LENGTH = 5
LONG_TERM_LENGTH = 9
SEMANTIC_MIN = 0.55
ESCO_MIN = 0.70
TOP_K = 5

EDGE_PUNCTUATION = " .,;:!?()[]{}'\"*•-"
VERSION = re.compile(r"(?<=[a-z+#])\s*v?\d+(?:\.\d+)*$")
SUFFIX = re.compile(r"[\s-]+(?:based|framework|library|programming language|programming|language)$")
JS_SUFFIX = re.compile(r"^(.+?)[\s.]?js$")


class Reranker(Protocol):
    def score(self, query: str, texts: list[str]) -> list[float]:
        ...


class CrossEncoderReranker:
    """A cross-encoder reads the query and a candidate together, which is more accurate than
    comparing two separate vectors, but slower, so it only re-ranks the top few candidates."""

    def __init__(self, model_name: str):
        from sentence_transformers import CrossEncoder  # heavy import, load on first use

        self._model = CrossEncoder(model_name, device="cpu")

    def score(self, query: str, texts: list[str]) -> list[float]:
        return [float(s) for s in self._model.predict([(query, text) for text in texts])]


def clean_term(term: str) -> str:
    return " ".join(term.casefold().strip(EDGE_PUNCTUATION).split())


def term_variants(term: str) -> list[str]:
    """The cleaned forms of a term to look up, without the term itself."""
    base = clean_term(term)
    stripped = VERSION.sub("", SUFFIX.sub("", base)).strip()
    variants = [stripped]
    for variant in (base, stripped):
        js = JS_SUFFIX.match(variant)
        if js:
            variants += [f"{js.group(1)}.js", js.group(1)]
    return [v for v in dict.fromkeys(variants) if v and v != base]


def _max_edits(term: str) -> int:
    if len(term) < FUZZY_MIN_LENGTH or term.isupper():
        return 0
    return 1 if len(term) < LONG_TERM_LENGTH else 2


class Normaliser:
    def __init__(
        self,
        entries: list[SkillEntry],
        encoder: Encoder | None = None,
        index: SkillIndex | None = None,
        reranker: Reranker | None = None,
        esco_index: SkillIndex | None = None,
        *,
        use_cleaning: bool = True,
        use_fuzzy: bool = True,
    ):
        self.entries = {entry.skill_id: entry for entry in entries}
        self.encoder, self.index, self.reranker, self.esco_index = (
            encoder, index, reranker, esco_index,
        )
        self.use_cleaning, self.use_fuzzy = use_cleaning, use_fuzzy
        # term → skill ID; a skill's name beats another skill's alias, then the lowest ID wins.
        ranked = sorted(
            ((t.casefold(), not by_name, e.skill_id)
             for e in entries
             for t, by_name in [(e.name, True)] + [(a, False) for a in e.aliases]),
            reverse=True,
        )
        self.terms = {term: skill_id for term, _, skill_id in ranked}
        self._term_list = list(self.terms)

    def _result(self, term: str, skill_id: str | None, method: MatchMethod, score: float,
                candidates: list[Candidate] | None = None) -> NormalisedTerm:
        name = self.entries[skill_id].name if skill_id in self.entries else None
        return NormalisedTerm(term=term, skill_id=skill_id, name=name, method=method,
                              score=round(score, 4), candidates=candidates or [])

    def _lexical(self, term: str) -> NormalisedTerm | None:
        cleaned = clean_term(term)
        if cleaned in self.terms:
            return self._result(term, self.terms[cleaned], MatchMethod.EXACT, 1.0)
        if self.use_cleaning:
            for variant in term_variants(term):
                if variant in self.terms:
                    return self._result(term, self.terms[variant], MatchMethod.CLEANED, 1.0)
        if self.use_fuzzy and (max_edits := _max_edits(term.strip(EDGE_PUNCTUATION))):
            found = [
                match for match in process.extract(
                    cleaned, self._term_list, scorer=DamerauLevenshtein.distance,
                    score_cutoff=max_edits, limit=10)
                if match[0][:1] == cleaned[:1]
            ]
            if found:
                best = min(distance for _, distance, _ in found)
                skills = {self.terms[t] for t, distance, _ in found if distance == best}
                if len(skills) == 1:
                    matched = next(t for t, distance, _ in found if distance == best)
                    score = DamerauLevenshtein.normalized_similarity(cleaned, matched)
                    return self._result(term, skills.pop(), MatchMethod.FUZZY, score)
        return None

    def _rerank(self, term: str, hits: list[SkillHit]) -> list[SkillHit]:
        if self.reranker is None or len(hits) < 2:
            return hits
        texts = [
            f"{hit.name}: {self.entries[hit.skill_id].description}"
            if hit.skill_id in self.entries and self.entries[hit.skill_id].description
            else hit.name
            for hit in hits
        ]
        scores = self.reranker.score(term, texts)
        return [hit for _, hit in sorted(zip(scores, hits), key=lambda pair: -pair[0])]

    def _semantic(self, terms: list[str]) -> list[NormalisedTerm]:
        if self.index is None or self.encoder is None:
            return [self._result(t, None, MatchMethod.UNMATCHED, 0.0) for t in terms]
        results = []
        esco_needed = []
        for term, hits in zip(terms, self.index.search(terms, self.encoder, TOP_K)):
            candidates = [Candidate(skill_id=h.skill_id, name=h.name, score=h.score) for h in hits]
            if hits and hits[0].score >= SEMANTIC_MIN:
                best = self._rerank(term, [h for h in hits if h.score >= SEMANTIC_MIN])[0]
                results.append(self._result(term, best.skill_id, MatchMethod.SEMANTIC,
                                            best.score, candidates))
            else:
                results.append(self._result(term, None, MatchMethod.UNMATCHED,
                                            hits[0].score if hits else 0.0, candidates))
                esco_needed.append(len(results) - 1)
        if self.esco_index is not None and esco_needed:
            queries = [terms[i] for i in esco_needed]
            for i, hits in zip(esco_needed, self.esco_index.search(queries, self.encoder, 1)):
                if hits and hits[0].score >= ESCO_MIN:
                    results[i] = NormalisedTerm(
                        term=terms[i], skill_id=hits[0].skill_id, name=hits[0].name,
                        method=MatchMethod.ESCO_CANDIDATE, score=round(hits[0].score, 4),
                        candidates=results[i].candidates,
                    )
        return results

    def normalise(self, terms: list[str]) -> list[NormalisedTerm]:
        results: list[NormalisedTerm | None] = [self._lexical(term) for term in terms]
        pending = [i for i, result in enumerate(results) if result is None]
        for i, result in zip(pending, self._semantic([terms[i] for i in pending])):
            results[i] = result
        return results


def _load_index(name: str) -> SkillIndex | None:
    settings = get_settings()
    try:
        return SkillIndex.load(settings.index_dir, name, settings.embedding_model)
    except SkillIndexError as error:
        logger.warning("Semantic matching without the %s index: %s", name, error)
        return None


@lru_cache
def get_normaliser() -> Normaliser:
    from app.semantic.encoder import get_encoder

    settings = get_settings()
    index = _load_index("ssks")
    encoder = get_encoder() if index is not None else None
    reranker = (CrossEncoderReranker(settings.reranker_model)
                if index is not None and settings.use_reranker else None)
    esco_index = _load_index("esco") if index is not None else None
    return Normaliser(load_entries(settings.dictionary_path), encoder, index, reranker, esco_index)
