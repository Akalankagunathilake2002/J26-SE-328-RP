"""
Compare C02 (Component 02) cleaned skill data with the existing SSKS import-ready package.

This script is read-only for all existing SSKS data. It never generates canonical IDs,
never changes review/verification statuses and never writes to seed/import_ready.
All results are review files written to seed/curated/comparison/c02/.

Usage (run from services/shared-skill-knowledge):
    python -m scripts.comparison.compare_c02_skills
"""
import argparse
import csv
import hashlib
import os
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[2]
SEED_DIR = SERVICE_ROOT / "seed"

SUPPORTED_DOMAINS = ("IT", "HR", "BUSINESS")
C_FAMILY = ("c", "c++", "c#")
FIXED_PL_NAMES = ["c", "c++", "c#", "java", "python", "javascript", "ruby", "go", "rust",
                  "typescript", "php", "swift", "kotlin"]

HR_KEYWORDS = re.compile(
    r"\b(human resources?|personnel|recruit\w*|payroll|employees?|employment law|labou?r law|"
    r"workforce|talent|onboarding|compensation and benefits|performance appraisal|staff)\b"
)
BUSINESS_UNCERTAIN_MGMT = {
    "allocating and controlling resources",
    "developing objectives and strategies",
    "performing administrative activities",
}

ENTITY_MATCH_FIELDS = [
    "c02_skill_id", "c02_preferred_label", "c02_origin", "c02_skill_type",
    "canonical_entity_id", "canonical_name", "canonical_entity_type", "canonical_concept_kind",
    "canonical_review_status", "match_method", "match_confidence", "candidate_count",
    "external_id_status", "proposed_external_id", "proposed_source_system",
    "recommendation", "review_status", "explanation",
]
ALIAS_FIELDS = [
    "candidate_key", "canonical_entity_id", "canonical_name", "alias_value", "alias_normalized",
    "c02_match_type", "c02_skill_id", "c02_preferred_label", "alias_provenance",
    "target_match_method", "alias_status", "proposed_record_type", "proposed_is_verified",
    "risk_flags", "conflict_id", "recommendation", "review_status", "explanation",
]
NEW_CANDIDATE_FIELDS = [
    "c02_skill_id", "c02_preferred_label", "c02_origin", "skill_type", "reuse_level",
    "c02_domain_tag", "category_level0", "category_level1", "category_level2",
    "is_digital", "is_transversal", "is_language", "alias_count",
    "parent_skill_id", "parent_skill_label", "parent_canonical_entity_id",
    "suggested_domains", "domain_suggestion_status", "possible_existing_entity_ids",
    "priority", "recommendation", "review_status", "explanation",
]
DOMAIN_FIELDS = [
    "c02_skill_id", "c02_preferred_label", "canonical_entity_id", "entity_match_method",
    "existing_domains", "c02_domain_tag", "category_level0", "category_level1", "category_level2",
    "is_digital", "is_transversal", "is_language",
    "suggested_domains", "supported_domains", "uncertain_domains", "suggestion_status",
    "comparison_with_existing", "recommendation", "review_status", "explanation",
]
CONFLICT_FIELDS = [
    "conflict_id", "conflict_type", "severity", "c02_skill_id", "c02_preferred_label",
    "alias_value", "canonical_entity_ids", "canonical_names", "details", "recommendation",
    "review_status",
]


def norm_label(text):
    """Lower-case and collapse whitespace. Keeps + and # so C, C++ and C# stay distinct."""
    text = unicodedata.normalize("NFKC", text or "")
    return re.sub(r"\s+", " ", text.strip().lower())


def loose_key(text):
    """Looser key that ignores spaces and punctuation (except + and #). Used only for review hints."""
    return re.sub(r"[^\w+#]|_", "", norm_label(text))


def strip_qualifier(text):
    """Drop a trailing qualifier such as '(computer programming)'."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", norm_label(text)).strip()


def split_ssks_labels(value):
    # Same separators prepare_import.py used when building aliases
    return [" ".join(x.split()) for x in re.split(r"[\n|;]+", value or "") if x.strip()]


def split_c02_list(value):
    return [x.strip() for x in (value or "").split("|") if x.strip()]


def is_custom(skill_id):
    return skill_id.startswith("custom:")


def record_origin(rec):
    if is_custom(rec["skill_id"]):
        return "C02_CUSTOM"
    if "custom aliases" in rec.get("source", ""):
        return "ESCO_WITH_C02_ALIASES"
    return "ESCO"


def load_rows(path):
    if not path or not Path(path).exists():
        return []
    # utf-8-sig handles the BOM that C02's pandas export adds
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)


def stable_key(*parts):
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:12]


def protected_dirs(seed_dir):
    return [
        seed_dir / "import_ready",
        seed_dir / "curated" / "esco",
        seed_dir / "curated" / "onet",
        seed_dir / "esco",
        seed_dir / "onet",
        seed_dir / "incoming",
    ]


def check_output_dir(output_dir, seed_dir):
    """Refuse to write anywhere that holds existing curated, import-ready or source data."""
    out = Path(output_dir).resolve()
    for p in protected_dirs(seed_dir):
        p = p.resolve()
        if out == p or p in out.parents:
            raise ValueError(f"Refusing to write comparison output inside protected directory: {p}")
    for p in (seed_dir, seed_dir / "curated", seed_dir / "curated" / "comparison"):
        if out == p.resolve():
            raise ValueError(f"Output must be a dedicated sub-directory, not {p}")


def snapshot_hashes(seed_dir, output_dir):
    """SHA-256 of every protected file, so the run can prove nothing existing was changed."""
    out = Path(output_dir).resolve()
    roots = protected_dirs(seed_dir) + [seed_dir / "curated" / "comparison"]
    hashes = {}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or out in path.resolve().parents:
                continue
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            hashes[str(path)] = h.hexdigest()
    return hashes


class ConflictLog:
    def __init__(self):
        self.rows = []

    def add(self, conflict_type, severity, details, recommendation, c02_skill_id="",
            c02_label="", alias_value="", canonical_ids=(), index=None):
        conflict_id = f"C02-CF-{len(self.rows) + 1:06d}"
        ids = sorted(set(canonical_ids))
        names = [index.entities[i]["name"] for i in ids if index and i in index.entities]
        self.rows.append({
            "conflict_id": conflict_id,
            "conflict_type": conflict_type,
            "severity": severity,
            "c02_skill_id": c02_skill_id,
            "c02_preferred_label": c02_label,
            "alias_value": alias_value,
            "canonical_entity_ids": "|".join(ids),
            "canonical_names": "|".join(names),
            "details": details,
            "recommendation": recommendation,
            "review_status": "PENDING_REVIEW",
        })
        return conflict_id


class SsksIndex:
    """Lookup tables built from the existing import-ready package (read-only)."""

    def __init__(self, entities, external_ids, aliases, domains, curated_esco_skills=()):
        self.entities = {e["id"]: e for e in entities}
        self.skill_ids = {i for i, e in self.entities.items() if e.get("entity_type") == "SKILL"}

        self.uri_to_ids = defaultdict(set)
        self.entity_esco_uris = defaultdict(set)
        for x in external_ids:
            uri, cid = x["external_id"].strip(), x["canonical_entity_id"].strip()
            self.uri_to_ids[uri].add(cid)
            if x.get("source_system") == "ESCO":
                self.entity_esco_uris[cid].add(uri)

        # Label and alias indexes cover SKILL entities only, since C02 supplies skills only
        self.name_to_ids = defaultdict(set)
        self.loose_name_to_ids = defaultdict(set)
        for cid in self.skill_ids:
            name = self.entities[cid]["name"]
            self.name_to_ids[norm_label(name)].add(cid)
            for lk in {loose_key(name), loose_key(strip_qualifier(name))} - {""}:
                self.loose_name_to_ids[lk].add(cid)

        self.alias_to_ids = defaultdict(set)
        self.loose_alias_to_ids = defaultdict(set)
        self.entity_alias_norms = defaultdict(set)
        self.entity_alias_loose = defaultdict(set)
        for a in aliases:
            cid = a["canonical_entity_id"].strip()
            if cid not in self.skill_ids:
                continue
            self.alias_to_ids[norm_label(a["value"])].add(cid)
            if loose_key(a["value"]):
                self.loose_alias_to_ids[loose_key(a["value"])].add(cid)
            self.entity_alias_norms[cid].add(norm_label(a["value"]))
            self.entity_alias_loose[cid].add(loose_key(a["value"]))

        self.domains = {}
        for d in domains:
            self.domains[d["entity_id"].strip()] = {x.strip() for x in d["domains"].split(",") if x.strip()}

        # Aliases present in the curated ESCO source but absent from import-ready were removed on
        # purpose (alias scrubbing rules or manual edits) and must not be re-proposed.
        self.removed_aliases = defaultdict(set)
        for row in curated_esco_skills:
            for cid in self.uri_to_ids.get(row.get("esco_uri", "").strip(), ()):
                if cid not in self.skill_ids:
                    continue
                source = {norm_label(x) for x in split_ssks_labels(row.get("alternative_labels", ""))}
                kept = self.entity_alias_norms[cid] | {norm_label(self.entities[cid]["name"])}
                self.removed_aliases[cid] |= source - kept

        self.pl_names = {
            re.sub(r"\(computer programming\)", "", self.entities[c]["name"].lower()).strip()
            for c in self.skill_ids if self.entities[c].get("concept_kind") == "PROGRAMMING_LANGUAGE"
        }
        self.pl_names.update(FIXED_PL_NAMES)


def violates_ssks_alias_rules(entity_name, alias, pl_names):
    """Re-check the alias scrubbing rules used by prepare_import.py. Returns a reason or ''."""
    name = re.sub(r"\(computer programming\)", "", entity_name.lower()).strip()
    a = alias.lower().strip()
    if name == "computer programming":
        if a in pl_names or (len(a) < 20 and not any(w in a for w in ("programming", "code", "comput"))):
            return "'computer programming' must not take programming-language or short generic aliases"
    if name in C_FAMILY and a in C_FAMILY and name != a:
        return "C, C++ and C# must not alias each other"
    return ""


def find_identity_matches(rec, index):
    """Return (match_method, sorted canonical IDs) using the strongest evidence available."""
    sid = rec["skill_id"].strip()
    label = rec["preferred_label"]
    if not is_custom(sid):
        ids = index.uri_to_ids.get(sid, set())
        if ids:
            return "URI_EXACT", sorted(ids)
        merged = [u for u in split_c02_list(rec.get("merged_skill_ids", "")) if u != sid]
        ids = set()
        for u in merged:
            ids |= index.uri_to_ids.get(u, set())
        if ids:
            return "MERGED_URI", sorted(ids)

    key = norm_label(label)
    if index.name_to_ids.get(key):
        return "LABEL_EXACT", sorted(index.name_to_ids[key])
    if index.alias_to_ids.get(key):
        return "LABEL_MATCHES_EXISTING_ALIAS", sorted(index.alias_to_ids[key])
    ids = set()
    for lk in {loose_key(label), loose_key(strip_qualifier(label))} - {""}:
        ids |= index.loose_name_to_ids.get(lk, set())
    if ids:
        return "LABEL_NORMALIZED", sorted(ids)
    return "NONE", []


METHOD_CONFIDENCE = {
    "URI_EXACT": "HIGH",
    "MERGED_URI": "MEDIUM",
    "LABEL_EXACT": "MEDIUM",
    "LABEL_MATCHES_EXISTING_ALIAS": "LOW",
    "LABEL_NORMALIZED": "LOW",
}


def external_id_status(rec, cid, index):
    sid = rec["skill_id"].strip()
    if is_custom(sid):
        return "NOT_APPLICABLE_CUSTOM_ID", ""
    if cid in index.uri_to_ids.get(sid, ()):
        return "ALREADY_PRESENT", ""
    if index.entity_esco_uris.get(cid):
        return "ENTITY_HAS_OTHER_ESCO_URI", ""
    if index.uri_to_ids.get(sid):
        return "URI_USED_BY_OTHER_ENTITY", ""
    return "PROPOSED_AFTER_REVIEW", sid


def compare_entities(c02_skills, index, conflicts):
    """Match every C02 skill to existing canonical entities. Never creates new IDs."""
    matches, unmatched = [], []
    resolution = {}

    for rec in c02_skills:
        sid = rec["skill_id"].strip()
        label = rec["preferred_label"]
        method, ids = find_identity_matches(rec, index)

        if method == "NONE":
            unmatched.append(rec)
            resolution[sid] = {"method": "NONE", "canonical_ids": [], "confirmed": False}
            continue

        non_skill = [i for i in ids if i not in index.skill_ids]
        skill_hits = [i for i in ids if i in index.skill_ids]
        confirmed = method == "URI_EXACT" and len(skill_hits) == 1 and not non_skill
        resolution[sid] = {"method": method, "canonical_ids": skill_hits, "confirmed": confirmed}

        if non_skill:
            conflicts.add("URI_MAPS_TO_NON_SKILL_ENTITY", "HIGH",
                          f"C02 skill URI is registered on non-skill entities: {', '.join(non_skill)}",
                          "Check whether the external ID was attached to the wrong entity.",
                          sid, label, canonical_ids=non_skill, index=index)
        if len(skill_hits) > 1:
            kind = "URI_MAPS_TO_MULTIPLE_ENTITIES" if method in ("URI_EXACT", "MERGED_URI") \
                else "LABEL_MATCHES_MULTIPLE_ENTITIES"
            conflicts.add(kind, "HIGH" if kind.startswith("URI") else "MEDIUM",
                          f"{method} found {len(skill_hits)} candidate entities.",
                          "Pick the correct entity or confirm the existing entities are duplicates.",
                          sid, label, canonical_ids=skill_hits, index=index)

        for cid in skill_hits:
            ent = index.entities[cid]
            ext_status, proposed_ext = external_id_status(rec, cid, index)
            notes = []
            if method == "URI_EXACT":
                recommendation = "REUSE_EXISTING_ID" if confirmed else "RESOLVE_AMBIGUITY"
                notes.append(f"ESCO URI already maps to {cid}; keep the existing canonical ID.")
                if norm_label(label) != norm_label(ent["name"]):
                    notes.append(f"Label differs: C02 '{label}' vs SSKS '{ent['name']}' (SSKS name kept).")
                others = index.name_to_ids.get(norm_label(label), set()) - {cid}
                if others:
                    conflicts.add("URI_MATCH_LABEL_POINTS_TO_OTHER_ENTITY", "MEDIUM",
                                  f"URI resolves to {cid} but the C02 label equals the name of "
                                  f"{', '.join(sorted(others))}. Possible duplicate concept in SSKS.",
                                  "Check whether the entities describe the same concept.",
                                  sid, label, canonical_ids=others | {cid}, index=index)
            elif method == "MERGED_URI":
                recommendation = "REVIEW_MERGED_URI_MATCH"
                notes.append("C02 merged this ESCO URI into another record with the same label.")
            else:
                recommendation = "RESOLVE_AMBIGUITY" if len(skill_hits) > 1 else {
                    "LABEL_EXACT": "REVIEW_LABEL_MATCH",
                    "LABEL_MATCHES_EXISTING_ALIAS": "REVIEW_ALIAS_LABEL_MATCH",
                    "LABEL_NORMALIZED": "REVIEW_NORMALIZED_MATCH",
                }[method]
                notes.append("Label-based match only; a matching label does not prove the concepts are equivalent.")
                if is_custom(sid):
                    notes.append("C02 custom skill; the custom ID is C02-internal and is not an SSKS external ID.")
                if ext_status == "ENTITY_HAS_OTHER_ESCO_URI":
                    conflicts.add("LABEL_MATCH_DIFFERENT_ESCO_URI", "MEDIUM",
                                  f"Label matches {cid}, which already has ESCO URI "
                                  f"{', '.join(sorted(index.entity_esco_uris[cid]))}.",
                                  "Likely different ESCO concepts with similar labels; do not merge without review.",
                                  sid, label, canonical_ids=[cid], index=index)
                if proposed_ext:
                    notes.append("If the match is confirmed, the C02 ESCO URI could be added as ESCO external ID evidence.")

            matches.append({
                "c02_skill_id": sid,
                "c02_preferred_label": label,
                "c02_origin": record_origin(rec),
                "c02_skill_type": rec.get("skill_type", ""),
                "canonical_entity_id": cid,
                "canonical_name": ent["name"],
                "canonical_entity_type": ent.get("entity_type", ""),
                "canonical_concept_kind": ent.get("concept_kind", ""),
                "canonical_review_status": ent.get("review_status", ""),
                "match_method": method,
                "match_confidence": METHOD_CONFIDENCE[method],
                "candidate_count": len(skill_hits),
                "external_id_status": ext_status,
                "proposed_external_id": proposed_ext,
                "proposed_source_system": "ESCO" if proposed_ext else "",
                "recommendation": recommendation,
                "review_status": "PENDING_REVIEW",
                "explanation": " ".join(notes),
            })

    # Several C02 records pointing at one entity suggests duplicate concepts
    by_entity = defaultdict(set)
    for m in matches:
        by_entity[m["canonical_entity_id"]].add(m["c02_skill_id"])
    for cid, sids in sorted(by_entity.items()):
        if len(sids) > 1:
            conflicts.add("MULTIPLE_C02_RECORDS_MATCH_SAME_ENTITY", "MEDIUM",
                          f"{len(sids)} C02 records resolve to {cid}: {' | '.join(sorted(sids))}",
                          "Decide which record is equivalent; the others may be distinct concepts or aliases.",
                          canonical_ids=[cid], index=index)

    return matches, unmatched, resolution


def suggest_domains(rec):
    """Conservative SSKS domain suggestions. Returns a list of (domain, status, reason)."""
    tag = rec.get("domain_tag", "")
    l1 = rec.get("category_level1", "")
    l2 = rec.get("category_level2", "")
    digital = rec.get("is_digital") == "True"
    transversal = rec.get("is_transversal") == "True"
    language = rec.get("is_language") == "True" or tag == "Language"
    label = norm_label(rec.get("preferred_label", ""))

    if language:
        return []
    if transversal and not digital:
        return []

    out = {}
    if tag == "Business/Finance":
        out["BUSINESS"] = ("SUPPORTED", "C02 custom tag Business/Finance")
    if digital or tag == "IT/Digital":
        if "BUSINESS" not in out:
            if transversal:
                out["IT"] = ("UNCERTAIN", "digital but transversal")
            else:
                out["IT"] = ("SUPPORTED", "ESCO digital skill collection / IT/Digital tag")
    elif l1 == "information and communication technologies (icts)":
        out["IT"] = ("SUPPORTED", "ESCO ICT knowledge group")
    elif tag == "working with computers":
        out["IT"] = ("UNCERTAIN", "ESCO 'working with computers' group is broad")

    if l2 == "recruiting and hiring":
        out["HR"] = ("SUPPORTED", "ESCO 'recruiting and hiring' group")
    elif HR_KEYWORDS.search(label):
        out["HR"] = ("UNCERTAIN", "HR keyword in label")

    if "BUSINESS" not in out:
        if l1 == "business, administration and law" and l2 == "business and administration":
            out["BUSINESS"] = ("SUPPORTED", "ESCO 'business and administration' knowledge group")
        elif l1 == "business, administration and law" and l2 != "law":
            out["BUSINESS"] = ("UNCERTAIN", f"ESCO group '{l2}'")
        elif l1 == "management skills" and l2 in BUSINESS_UNCERTAIN_MGMT:
            out["BUSINESS"] = ("UNCERTAIN", f"ESCO management group '{l2}'")

    return [(d, s, r) for d, (s, r) in sorted(out.items())]


def no_suggestion_reason(rec):
    if rec.get("is_language") == "True" or rec.get("domain_tag") == "Language":
        return "Language skill; not mapped to IT/HR/BUSINESS."
    if rec.get("is_transversal") == "True":
        return "Transversal skill; applies across domains, so no single domain is suggested."
    return f"No defensible mapping from C02 tag '{rec.get('domain_tag', '')}'."


def compare_domains(c02_skills, resolution, index, conflicts):
    rows = []
    for rec in c02_skills:
        sid = rec["skill_id"].strip()
        res = resolution.get(sid, {"method": "NONE", "canonical_ids": [], "confirmed": False})
        suggestions = suggest_domains(rec)
        supported = [d for d, s, _ in suggestions if s == "SUPPORTED"]
        uncertain = [d for d, s, _ in suggestions if s == "UNCERTAIN"]
        status = "SUPPORTED" if supported else ("UNCERTAIN" if uncertain else "NO_SUGGESTION")
        reasons = "; ".join(f"{d} {s.lower()}: {r}" for d, s, r in suggestions) or no_suggestion_reason(rec)

        cid = res["canonical_ids"][0] if len(res["canonical_ids"]) == 1 else ""
        existing = index.domains.get(cid, set()) if cid else set()
        suggested = {d for d, _, _ in suggestions}

        if not res["canonical_ids"]:
            comparison, recommendation = "NEW_CANDIDATE", (
                "USE_WHEN_REVIEWING_NEW_CANDIDATE" if suggestions else "NO_ACTION")
        elif not res["confirmed"]:
            comparison, recommendation = "ENTITY_UNCONFIRMED", (
                "CONFIRM_ENTITY_MATCH_FIRST" if suggestions else "NO_ACTION")
        elif not suggestions:
            comparison = "KEEP_EXISTING" if existing else "NO_DATA"
            recommendation = "NO_ACTION"
        elif suggested <= existing:
            comparison, recommendation = "AGREES_WITH_EXISTING", "NO_ACTION"
        elif not existing:
            comparison = "PROPOSED_ADDITION"
            recommendation = "REVIEW_FOR_ADDITION" if supported else "REVIEW_UNCERTAIN"
        else:
            comparison, recommendation = "DIFFERS_FROM_EXISTING", "REVIEW_KEEP_EXISTING_UNLESS_CONFIRMED"
            conflicts.add("DOMAIN_DIFFERS_FROM_EXISTING", "LOW",
                          f"Existing domains {', '.join(sorted(existing))}; C02 suggests "
                          f"{', '.join(sorted(suggested - existing))} ({reasons}).",
                          "Keep the existing domain assignment unless a reviewer confirms the addition.",
                          sid, rec["preferred_label"], canonical_ids=[cid], index=index)

        rows.append({
            "c02_skill_id": sid,
            "c02_preferred_label": rec["preferred_label"],
            "canonical_entity_id": cid,
            "entity_match_method": res["method"],
            "existing_domains": ", ".join(sorted(existing)),
            "c02_domain_tag": rec.get("domain_tag", ""),
            "category_level0": rec.get("category_level0", ""),
            "category_level1": rec.get("category_level1", ""),
            "category_level2": rec.get("category_level2", ""),
            "is_digital": rec.get("is_digital", ""),
            "is_transversal": rec.get("is_transversal", ""),
            "is_language": rec.get("is_language", ""),
            "suggested_domains": ", ".join(sorted(suggested)),
            "supported_domains": ", ".join(supported),
            "uncertain_domains": ", ".join(uncertain),
            "suggestion_status": status,
            "comparison_with_existing": comparison,
            "recommendation": recommendation,
            "review_status": "PENDING_REVIEW",
            "explanation": reasons,
        })
    return rows


def build_original_casing(c02_skills):
    """alias_map.csv stores lower-cased names; recover the original spelling from clean_skills.csv."""
    casing = {}
    for rec in c02_skills:
        sid = rec["skill_id"].strip()
        for value in [rec["preferred_label"]] + split_c02_list(rec.get("aliases")) + \
                split_c02_list(rec.get("hidden_aliases")):
            casing.setdefault((sid, norm_label(value)), value)
    return casing


def build_custom_alias_pairs(supplement_rows):
    """(normalized label, normalized alias) pairs that C02 added by hand, not taken from ESCO."""
    pairs = set()
    for row in supplement_rows:
        label = norm_label(row.get("preferredLabel", ""))
        for a in re.split(r"\n|\|", row.get("aliases", "")):
            if a.strip():
                pairs.add((label, norm_label(a)))
    return pairs


def build_contested_names(dedup_rows):
    """Names that C02 had to remove from competing skills (its own disambiguation decisions)."""
    contested = defaultdict(set)
    for row in dedup_rows:
        if row.get("action") == "removed name from skill":
            contested[norm_label(row["name"])].add(row["removed_from_skill_id"].strip())
    return contested


ALIAS_RECOMMENDATIONS = {
    "MATCHES_CANONICAL_NAME": "NO_ACTION",
    "DUPLICATE_EXACT": "NO_ACTION",
    "DUPLICATE_NORMALIZED": "NO_ACTION_OPTIONAL_VARIANT",
    "PROPOSED_ALIAS": "REVIEW_FOR_ADDITION",
    "PROPOSED_PREFERRED_LABEL_VARIANT": "REVIEW_FOR_ADDITION",
    "PROPOSED_HIDDEN_ALIAS": "REVIEW_HIDDEN_ALIAS",
    "AMBIGUOUS_IN_C02": "REVIEW_AMBIGUOUS",
    "CONFLICT": "RESOLVE_CONFLICT",
    "TARGET_UNCONFIRMED": "CONFIRM_ENTITY_MATCH_FIRST",
    "TARGET_AMBIGUOUS": "RESOLVE_ENTITY_AMBIGUITY_FIRST",
}


def classify_alias(key, kind, cid, index):
    """Return (status, conflict_type, details) for an alias whose target entity is confirmed."""
    ent = index.entities[cid]
    if key == norm_label(ent["name"]):
        return "MATCHES_CANONICAL_NAME", "", "Already the SSKS preferred name."
    if key in index.entity_alias_norms[cid]:
        return "DUPLICATE_EXACT", "", "Already an alias of this entity."
    lk = loose_key(key)
    if lk and (lk in index.entity_alias_loose[cid] or lk == loose_key(ent["name"])):
        return "DUPLICATE_NORMALIZED", "", "Spacing/punctuation variant of an existing name or alias."

    rule = violates_ssks_alias_rules(ent["name"], key, index.pl_names)
    if rule:
        return "CONFLICT", "ALIAS_VIOLATES_SSKS_RULE", rule
    if key in index.removed_aliases.get(cid, ()):
        return "CONFLICT", "ALIAS_PREVIOUSLY_REMOVED", \
            "Alias was in the curated ESCO source but was removed from the SSKS alias data."
    other_alias = index.alias_to_ids.get(key, set()) - {cid}
    if other_alias:
        return "CONFLICT", "ALIAS_POINTS_TO_DIFFERENT_ENTITY", \
            f"SSKS already uses this alias for {', '.join(sorted(other_alias))}."
    other_name = index.name_to_ids.get(key, set()) - {cid}
    if other_name:
        return "CONFLICT", "ALIAS_EQUALS_OTHER_ENTITY_NAME", \
            f"Alias equals the preferred name of {', '.join(sorted(other_name))}."
    other_loose = (index.loose_alias_to_ids.get(lk, set()) | index.loose_name_to_ids.get(lk, set())) - {cid}
    if lk and other_loose:
        return "CONFLICT", "ALIAS_NORMALIZED_COLLISION", \
            f"Normalized form collides with names/aliases of {', '.join(sorted(other_loose))}."
    if kind == "hidden":
        return "PROPOSED_HIDDEN_ALIAS", "", \
            "ESCO hidden label (often a misspelling); SSKS has no hidden alias type yet."
    if kind == "preferred":
        return "PROPOSED_PREFERRED_LABEL_VARIANT", "", "C02/ESCO preferred label differs from the SSKS name."
    return "PROPOSED_ALIAS", "", "New alias for an existing entity."


def compare_aliases(alias_rows, c02_by_id, resolution, index, conflicts,
                    contested, custom_pairs, casing):
    candidates = []
    stats = Counter()
    possible_existing = defaultdict(set)

    for row in alias_rows:
        sid = row["skill_id"].strip()
        key = norm_label(row["name"])
        kind = row["match_type"].strip()
        stats["examined"] += 1
        if sid not in c02_by_id:
            stats["orphan_rows"] += 1
            continue
        rec = c02_by_id[sid]
        res = resolution[sid]

        if not res["canonical_ids"]:
            stats["target_not_in_ssks"] += 1
            if kind != "preferred":
                hits = index.name_to_ids.get(key, set()) | index.alias_to_ids.get(key, set())
                if hits:
                    possible_existing[sid] |= hits
                    stats["target_not_in_ssks_name_exists"] += 1
                    conflicts.add("ALIAS_TARGET_NOT_IN_SSKS", "LOW",
                                  f"C02 maps '{key}' to a skill SSKS does not have, but SSKS already "
                                  f"uses this name for {', '.join(sorted(hits))}.",
                                  "Check whether the C02 skill is a duplicate of the existing entity.",
                                  sid, rec["preferred_label"], key, hits, index)
            continue

        value = casing.get((sid, key), row["name"])
        provenance = "C02_CUSTOM" if is_custom(sid) or \
            (norm_label(rec["preferred_label"]), key) in custom_pairs else "ESCO_VIA_C02"
        flags = []
        if len(loose_key(key)) <= 2:
            flags.append("SHORT_ALIAS")
        if ";" in key:
            flags.append("CONTAINS_SEPARATOR")
        if provenance == "C02_CUSTOM":
            flags.append("C02_CUSTOM_ALIAS")

        conflict_id = ""
        cid = ""
        if len(res["canonical_ids"]) > 1:
            status = "TARGET_AMBIGUOUS"
            details = f"C02 skill matches several entities: {', '.join(res['canonical_ids'])}."
        elif not res["confirmed"]:
            cid = res["canonical_ids"][0]
            status = "TARGET_UNCONFIRMED"
            details = f"Target resolved only by {res['method']}; confirm the entity match first."
        else:
            cid = res["canonical_ids"][0]
            status, conflict_type, details = classify_alias(key, kind, cid, index)
            if conflict_type:
                involved = {cid} | index.alias_to_ids.get(key, set()) | index.name_to_ids.get(key, set())
                conflict_id = conflicts.add(conflict_type, "HIGH" if conflict_type != "ALIAS_NORMALIZED_COLLISION"
                                            else "MEDIUM", details,
                                            "Do not add this alias unless a reviewer resolves the conflict.",
                                            sid, rec["preferred_label"], key, involved, index)
            elif status.startswith("PROPOSED") and kind != "preferred" and key in contested:
                losers = contested[key]
                loser_ids = sorted({c for l in losers for c in resolution.get(l, {}).get("canonical_ids", [])})
                status = "AMBIGUOUS_IN_C02"
                details = (f"C02 removed this name from {len(losers)} competing skill(s) to keep it here"
                           + (f"; competing skills map to SSKS {', '.join(loser_ids)}." if loser_ids else "."))

        stats[status] += 1
        is_proposal = status.startswith("PROPOSED") or status == "AMBIGUOUS_IN_C02"
        recommendation = ALIAS_RECOMMENDATIONS[status]
        if is_proposal and "SHORT_ALIAS" in flags:
            recommendation = "REVIEW_CAREFULLY_SHORT_ALIAS"
        candidates.append({
            "candidate_key": stable_key(cid or sid, key),
            "canonical_entity_id": cid,
            "canonical_name": index.entities[cid]["name"] if cid else "",
            "alias_value": value,
            "alias_normalized": key,
            "c02_match_type": kind,
            "c02_skill_id": sid,
            "c02_preferred_label": rec["preferred_label"],
            "alias_provenance": provenance,
            "target_match_method": res["method"],
            "alias_status": status,
            "proposed_record_type": ("HIDDEN_ALIAS" if status == "PROPOSED_HIDDEN_ALIAS"
                                     else "ALIAS" if is_proposal else ""),
            "proposed_is_verified": "FALSE" if is_proposal else "",
            "risk_flags": "|".join(flags),
            "conflict_id": conflict_id,
            "recommendation": recommendation,
            "review_status": "PENDING_REVIEW",
            "explanation": details,
        })
    return candidates, stats, possible_existing


def build_new_candidates(unmatched, index, domain_rows_by_id, possible_existing):
    rows = []
    for rec in unmatched:
        sid = rec["skill_id"].strip()
        dom = domain_rows_by_id[sid]
        origin = record_origin(rec)
        parent_ids = sorted(i for i in index.uri_to_ids.get(rec.get("parent_skill_id", "").strip(), ())
                            if i in index.skill_ids)
        hints = sorted(possible_existing.get(sid, ()))

        if origin == "C02_CUSTOM":
            priority = "HIGH"
        elif dom["suggestion_status"] == "SUPPORTED":
            priority = "MEDIUM"
        elif dom["suggestion_status"] == "UNCERTAIN":
            priority = "LOW"
        else:
            priority = "OUT_OF_SCOPE_LIKELY"

        notes = []
        if hints:
            recommendation = "REVIEW_POSSIBLE_EXISTING_ENTITY"
            notes.append(f"Some C02 aliases already belong to SSKS entities {', '.join(hints)}.")
        elif priority == "OUT_OF_SCOPE_LIKELY":
            recommendation = "NO_ACTION_UNLESS_SCOPE_EXPANDS"
            notes.append("No ESCO URI or label match, and no IT/HR/BUSINESS signal.")
        else:
            recommendation = "REVIEW_AS_NEW_CONCEPT"
            notes.append("No ESCO URI or label match in SSKS.")
        if origin == "C02_CUSTOM":
            notes.append("C02 custom skill; no canonical ID is created by this comparison.")
        if parent_ids:
            notes.append(f"C02 parent resolves to SSKS {', '.join(parent_ids)}.")

        rows.append({
            "c02_skill_id": sid,
            "c02_preferred_label": rec["preferred_label"],
            "c02_origin": origin,
            "skill_type": rec.get("skill_type", ""),
            "reuse_level": rec.get("reuse_level", ""),
            "c02_domain_tag": rec.get("domain_tag", ""),
            "category_level0": rec.get("category_level0", ""),
            "category_level1": rec.get("category_level1", ""),
            "category_level2": rec.get("category_level2", ""),
            "is_digital": rec.get("is_digital", ""),
            "is_transversal": rec.get("is_transversal", ""),
            "is_language": rec.get("is_language", ""),
            "alias_count": len(split_c02_list(rec.get("aliases"))),
            "parent_skill_id": rec.get("parent_skill_id", ""),
            "parent_skill_label": rec.get("parent_skill_label", ""),
            "parent_canonical_entity_id": "|".join(parent_ids),
            "suggested_domains": dom["suggested_domains"],
            "domain_suggestion_status": dom["suggestion_status"],
            "possible_existing_entity_ids": "|".join(hints),
            "priority": priority,
            "recommendation": recommendation,
            "review_status": "PENDING_REVIEW",
            "explanation": " ".join(notes),
        })
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "OUT_OF_SCOPE_LIKELY": 3}
    rows.sort(key=lambda r: (priority_order[r["priority"]], r["c02_preferred_label"].lower()))
    return rows


def validate_references(index, outputs):
    """Every canonical ID referenced in the outputs must already exist in canonical_entities.csv."""
    invalid = []
    for name, rows, columns in outputs:
        for r in rows:
            for col in columns:
                for cid in filter(None, r.get(col, "").split("|")):
                    if cid not in index.entities:
                        invalid.append((name, col, cid))
    return invalid


def pick_alias_file(import_ready_dir, override=None):
    if override:
        return Path(override)
    for name in ("aliases_unlocked.csv", "aliases.csv"):
        if (import_ready_dir / name).exists():
            return import_ready_dir / name
    raise FileNotFoundError(f"No alias file found in {import_ready_dir}")


def run(c02_dir, import_ready_dir, curated_esco_skills, output_dir, aliases_file=None, seed_dir=SEED_DIR):
    c02_dir, import_ready_dir, output_dir = Path(c02_dir), Path(import_ready_dir), Path(output_dir)
    seed_dir = Path(seed_dir)
    check_output_dir(output_dir, seed_dir)
    before = snapshot_hashes(seed_dir, output_dir)

    alias_path = pick_alias_file(import_ready_dir, aliases_file)
    inputs = {
        "c02_clean_skills": c02_dir / "clean_skills.csv",
        "c02_alias_map": c02_dir / "alias_map.csv",
        "c02_custom_supplement": c02_dir / "custom_skills_supplement.csv",
        "c02_dedup_report": c02_dir / "dedup_report.csv",
        "canonical_entities": import_ready_dir / "canonical_entities.csv",
        "external_ids": import_ready_dir / "external_ids.csv",
        "aliases": alias_path,
        "entity_domains": import_ready_dir / "entity_domains.csv",
        "curated_esco_skills": Path(curated_esco_skills) if curated_esco_skills else None,
    }
    for key in ("c02_clean_skills", "c02_alias_map", "canonical_entities", "external_ids"):
        if not inputs[key].exists():
            raise FileNotFoundError(f"Required input missing: {inputs[key]}")

    c02_skills = load_rows(inputs["c02_clean_skills"])
    alias_rows = load_rows(inputs["c02_alias_map"])
    index = SsksIndex(
        load_rows(inputs["canonical_entities"]),
        load_rows(inputs["external_ids"]),
        load_rows(inputs["aliases"]),
        load_rows(inputs["entity_domains"]),
        load_rows(inputs["curated_esco_skills"]),
    )
    c02_by_id = {r["skill_id"].strip(): r for r in c02_skills}

    conflicts = ConflictLog()
    matches, unmatched, resolution = compare_entities(c02_skills, index, conflicts)
    alias_candidates, alias_stats, possible_existing = compare_aliases(
        alias_rows, c02_by_id, resolution, index, conflicts,
        build_contested_names(load_rows(inputs["c02_dedup_report"])),
        build_custom_alias_pairs(load_rows(inputs["c02_custom_supplement"])),
        build_original_casing(c02_skills),
    )
    domain_rows = compare_domains(c02_skills, resolution, index, conflicts)
    new_candidates = build_new_candidates(
        unmatched, index, {r["c02_skill_id"]: r for r in domain_rows}, possible_existing)

    files = {
        "c02_entity_matches.csv": (matches, ENTITY_MATCH_FIELDS),
        "c02_alias_candidates.csv": (alias_candidates, ALIAS_FIELDS),
        "c02_new_skill_candidates.csv": (new_candidates, NEW_CANDIDATE_FIELDS),
        "c02_domain_suggestions.csv": (domain_rows, DOMAIN_FIELDS),
        "c02_conflicts.csv": (conflicts.rows, CONFLICT_FIELDS),
    }
    for name, (rows, fields) in files.items():
        write_csv(output_dir / name, rows, fields)

    invalid_refs = validate_references(index, [
        ("entity_matches", matches, ["canonical_entity_id"]),
        ("alias_candidates", alias_candidates, ["canonical_entity_id"]),
        ("new_candidates", new_candidates, ["parent_canonical_entity_id", "possible_existing_entity_ids"]),
        ("domain_suggestions", domain_rows, ["canonical_entity_id"]),
        ("conflicts", conflicts.rows, ["canonical_entity_ids"]),
    ])
    after = snapshot_hashes(seed_dir, output_dir)
    changed = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))

    summary = summarise(c02_skills, alias_rows, matches, resolution, alias_stats, new_candidates,
                        domain_rows, conflicts.rows, invalid_refs, changed, len(before), inputs, index)
    write_report(output_dir / "c02_comparison_report.txt", summary, inputs)
    return summary


def summarise(c02_skills, alias_rows, matches, resolution, alias_stats, new_candidates,
              domain_rows, conflict_rows, invalid_refs, changed, protected_count, inputs, index):
    methods = Counter(r["method"] for r in resolution.values())
    uri_entities = {m["canonical_entity_id"] for m in matches if m["match_method"] == "URI_EXACT"}
    confirmed = sum(1 for r in resolution.values() if r["confirmed"])
    label_methods = ("LABEL_EXACT", "LABEL_MATCHES_EXISTING_ALIAS", "LABEL_NORMALIZED", "MERGED_URI")
    proposed = sum(alias_stats[s] for s in ("PROPOSED_ALIAS", "PROPOSED_PREFERRED_LABEL_VARIANT"))
    return {
        "c02_skill_records": len(c02_skills),
        "c02_custom_records": sum(1 for r in c02_skills if is_custom(r["skill_id"])),
        "c02_alias_mappings": len(alias_rows),
        "ssks_canonical_entities": len(index.entities),
        "ssks_skill_entities": len(index.skill_ids),
        "match_methods": dict(methods),
        "records_confirmed_by_uri": confirmed,
        "entities_matched_by_uri": len(uri_entities),
        "label_match_records": sum(methods[m] for m in label_methods),
        "unresolved_records": sum(1 for r in resolution.values() if len(r["canonical_ids"]) > 1),
        "custom_records_matched": sum(1 for s, r in resolution.items() if is_custom(s) and r["canonical_ids"]),
        "new_candidates": len(new_candidates),
        "new_candidate_priority": dict(Counter(r["priority"] for r in new_candidates)),
        "new_candidate_recommendation": dict(Counter(r["recommendation"] for r in new_candidates)),
        "new_custom_candidates": sum(1 for r in new_candidates if r["c02_origin"] == "C02_CUSTOM"),
        "alias_stats": dict(alias_stats),
        "aliases_proposed": proposed,
        "aliases_hidden_proposed": alias_stats["PROPOSED_HIDDEN_ALIAS"],
        "aliases_duplicates": sum(alias_stats[s] for s in
                                  ("MATCHES_CANONICAL_NAME", "DUPLICATE_EXACT", "DUPLICATE_NORMALIZED")),
        "aliases_conflicting": alias_stats["CONFLICT"],
        "domain_status": dict(Counter(r["suggestion_status"] for r in domain_rows)),
        "domain_comparison": dict(Counter(r["comparison_with_existing"] for r in domain_rows)),
        "conflict_types": dict(Counter(r["conflict_type"] for r in conflict_rows)),
        "conflicts_total": len(conflict_rows),
        "invalid_references": invalid_refs,
        "protected_files_checked": protected_count,
        "protected_files_changed": changed,
        "input_files": {k: str(v) for k, v in inputs.items() if v},
    }


def write_report(path, s, inputs):
    def block(title, counts):
        lines = [title]
        for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"  {k}: {v}")
        return lines

    lines = [
        "C02 Skill Data Comparison Report",
        "",
        "Source: Component 02 (C02), Component02_Clean_Skills.zip (stored in seed/incoming/c02/).",
        "All outputs are review proposals. No canonical IDs were created, no statuses were changed",
        "and nothing was written to seed/import_ready.",
        "",
        "Inputs:",
    ] + [f"  {k}: {v}" for k, v in s["input_files"].items()] + [
        "",
        "Totals:",
        f"  C02 skill records examined: {s['c02_skill_records']} (custom: {s['c02_custom_records']})",
        f"  C02 alias mappings examined: {s['c02_alias_mappings']}",
        f"  SSKS canonical entities: {s['ssks_canonical_entities']} (skills: {s['ssks_skill_entities']})",
        "",
        "Entity matching:",
        f"  Existing canonical entities matched by ESCO URI: {s['entities_matched_by_uri']}",
        f"  C02 records confirmed by URI (single entity): {s['records_confirmed_by_uri']}",
        f"  Additional label-based matches (need review): {s['label_match_records']}",
        f"  Unresolved records (several candidate entities): {s['unresolved_records']}",
        f"  C02 custom records with a possible existing match: {s['custom_records_matched']}",
    ] + block("  Records by match method:", s["match_methods"]) + [
        "",
        "New candidate concepts (no canonical IDs created):",
        f"  Total: {s['new_candidates']} (C02 custom: {s['new_custom_candidates']})",
    ] + block("  By priority:", s["new_candidate_priority"]) \
      + block("  By recommendation:", s["new_candidate_recommendation"]) + [
        "",
        "Aliases:",
        f"  Proposed aliases (ordinary + preferred-label variants): {s['aliases_proposed']}",
        f"  Proposed hidden aliases (kept separate): {s['aliases_hidden_proposed']}",
        f"  Duplicates of existing names/aliases: {s['aliases_duplicates']}",
        f"  Conflicting mappings: {s['aliases_conflicting']}",
    ] + block("  By alias status:", s["alias_stats"]) + [
        "",
    ] + block("Domain suggestions by status:", s["domain_status"]) \
      + block("Domain suggestions vs existing:", s["domain_comparison"]) + [
        "",
        f"Conflicts: {s['conflicts_total']}",
    ] + block("  By type:", s["conflict_types"]) + [
        "",
        "Validation:",
        f"  [{'PASS' if not s['invalid_references'] else 'FAIL'}] All referenced canonical IDs exist "
        f"({len(s['invalid_references'])} invalid).",
        f"  [{'PASS' if not s['protected_files_changed'] else 'FAIL'}] Protected files unchanged "
        f"({s['protected_files_checked']} checked, {len(s['protected_files_changed'])} changed).",
    ]
    for p in s["protected_files_changed"]:
        lines.append(f"    changed: {p}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Compare C02 skill data with the SSKS import-ready package.")
    parser.add_argument("--c02-dir", default=str(SEED_DIR / "incoming" / "c02"))
    parser.add_argument("--import-ready-dir", default=str(SEED_DIR / "import_ready"))
    parser.add_argument("--aliases-file", default=None,
                        help="Defaults to aliases_unlocked.csv (falls back to aliases.csv).")
    parser.add_argument("--curated-esco-skills",
                        default=str(SEED_DIR / "curated" / "esco" / "esco_skills_candidates.csv"))
    parser.add_argument("--output-dir", default=str(SEED_DIR / "curated" / "comparison" / "c02"))
    args = parser.parse_args()

    s = run(args.c02_dir, args.import_ready_dir, args.curated_esco_skills, args.output_dir, args.aliases_file)
    print(f"C02 records: {s['c02_skill_records']}, alias mappings: {s['c02_alias_mappings']}")
    print(f"Entities matched by URI: {s['entities_matched_by_uri']}, label matches: {s['label_match_records']}, "
          f"new candidates: {s['new_candidates']}")
    print(f"Aliases proposed: {s['aliases_proposed']}, hidden: {s['aliases_hidden_proposed']}, "
          f"duplicates: {s['aliases_duplicates']}, conflicts: {s['aliases_conflicting']}")
    print(f"Invalid references: {len(s['invalid_references'])}, "
          f"protected files changed: {len(s['protected_files_changed'])}")
    print(f"Report: {Path(args.output_dir) / 'c02_comparison_report.txt'}")


if __name__ == "__main__":
    main()
