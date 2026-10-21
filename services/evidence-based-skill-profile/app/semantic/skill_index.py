"""Semantic skill knowledge base: a FAISS vector index over the skill dictionary (TAF tasks 4, 5).

Each skill is stored as several vectors, one for each way it can be written:

    name           "Deep Learning"
    alias          "deep neural networks"
    description    "Deep Learning: Machine learning with multi-layer neural networks ..."

A query phrase is embedded and compared with all of them (cosine similarity, exact search with
faiss.IndexFlatIP). A skill's score is its best-matching vector, so "made neural networks" can
match the description even though it shares no words with the name.

Two indexes are built by scripts/build_skill_index.py:
    ssks  the C02 dictionary (SSKS skills with SK- IDs + C02 supplement): the main index
    esco  ESCO skills that SSKS does not have: a fallback that finds new-skill candidates
"""
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import faiss
import numpy as np

from app.extraction.matcher import SkillEntry
from app.semantic.encoder import Encoder

NAME, ALIAS, DESCRIPTION = "name", "alias", "description"


class SkillIndexError(RuntimeError):
    """The index is missing or was built with a different embedding model."""


@dataclass(frozen=True)
class IndexedText:
    skill_id: str
    name: str
    kind: str
    text: str


@dataclass(frozen=True)
class SkillHit:
    skill_id: str
    name: str
    score: float
    matched_text: str
    matched_kind: str


def texts_for(entry: SkillEntry) -> list[IndexedText]:
    texts = [IndexedText(entry.skill_id, entry.name, NAME, entry.name)]
    texts += [IndexedText(entry.skill_id, entry.name, ALIAS, alias) for alias in entry.aliases]
    if entry.description:
        texts.append(IndexedText(entry.skill_id, entry.name, DESCRIPTION,
                                 f"{entry.name}: {entry.description}"))
    return texts


class SkillIndex:
    def __init__(self, index: faiss.Index, rows: list[IndexedText], model_name: str):
        if index.ntotal != len(rows):
            raise SkillIndexError(f"Index has {index.ntotal} vectors but {len(rows)} rows")
        self.index = index
        self.rows = rows
        self.model_name = model_name

    @classmethod
    def build(cls, entries: list[SkillEntry], encoder: Encoder) -> "SkillIndex":
        rows = [text for entry in entries for text in texts_for(entry)]
        vectors = encoder.encode([row.text for row in rows])
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return cls(index, rows, encoder.model_name)

    def save(self, directory: Path, name: str) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / f"{name}.faiss"))
        meta = {"model": self.model_name, "rows": [asdict(row) for row in self.rows]}
        (directory / f"{name}.json").write_text(json.dumps(meta, ensure_ascii=False),
                                                encoding="utf-8")

    @classmethod
    def load(cls, directory: Path, name: str, model_name: str) -> "SkillIndex":
        index_path, meta_path = directory / f"{name}.faiss", directory / f"{name}.json"
        if not index_path.exists() or not meta_path.exists():
            raise SkillIndexError(f"No '{name}' index in {directory}; "
                              "run: python -m scripts.build_skill_index")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta["model"] != model_name:
            raise SkillIndexError(f"'{name}' index was built with {meta['model']}, not {model_name}; "
                              "rebuild it")
        rows = [IndexedText(**row) for row in meta["rows"]]
        return cls(faiss.read_index(str(index_path)), rows, meta["model"])

    def search(self, queries: list[str], encoder: Encoder, top_k: int = 5,
               min_score: float = 0.0) -> list[list[SkillHit]]:
        """For each query, the top_k skills by best cosine similarity, highest first."""
        if not queries:
            return []
        if encoder.model_name != self.model_name:
            raise SkillIndexError(f"Encoder {encoder.model_name} does not match index "
                              f"{self.model_name}")
        # Several vectors belong to one skill, so fetch extra and keep each skill's best.
        scores, positions = self.index.search(encoder.encode(queries), top_k * 8)
        results = []
        for row_scores, row_positions in zip(scores, positions):
            best: dict[str, SkillHit] = {}
            for score, position in zip(row_scores, row_positions):
                if position < 0 or score < min_score:
                    continue
                row = self.rows[position]
                if row.skill_id not in best:
                    best[row.skill_id] = SkillHit(row.skill_id, row.name, round(float(score), 4),
                                                  row.text, row.kind)
            results.append(sorted(best.values(), key=lambda h: -h.score)[:top_k])
        return results


def load_esco_entries(esco_path: Path, exclude_uris: set[str] = frozenset()) -> list[SkillEntry]:
    """ESCO skills (ID = concept URI) from skills_en.csv, leaving out the URIs in exclude_uris."""
    with esco_path.open(encoding="utf-8", newline="") as f:
        return [
            SkillEntry(
                skill_id=row["conceptUri"],
                name=row["preferredLabel"].strip(),
                aliases=tuple(a.strip() for a in row["altLabels"].splitlines() if a.strip()),
                description=" ".join(row["description"].split()),
            )
            for row in csv.DictReader(f)
            if row["status"] == "released" and row["conceptUri"] not in exclude_uris
        ]


def load_ssks_esco_uris(external_ids_path: Path) -> set[str]:
    """ESCO skill URIs that SSKS already has (so they are not repeated in the ESCO index)."""
    if not external_ids_path.exists():
        return set()
    with external_ids_path.open(encoding="utf-8", newline="") as f:
        return {
            row["external_id"] for row in csv.DictReader(f)
            if row["source_system"] == "ESCO" and row["canonical_entity_id"].startswith("SK-")
        }
