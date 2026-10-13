"""
Finalize SSKS import-ready seed data using reviewed C02 additions.

Preserves all existing canonical IDs, manual edits, and review decisions.
Applies reviewed additions:
- 11 new canonical skills (SK-001870 to SK-001880) with IT/BUSINESS domains and C02 external IDs.
- 5 approved aliases for existing skills (ECMAScript, ES6, JS, SEO, TS) + 16 aliases for new skills.
- Appends review items to review_required.csv for unresolved C02 candidates, conflicts, and hidden aliases.
- Updates import_manifest.json and import_validation_report.txt.
"""
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
IMPORT_READY_DIR = BASE_DIR / "seed" / "import_ready"

NEW_SKILLS = [
    {
        "c02_id": "custom:adobe-xd",
        "name": "Adobe XD",
        "description": "Vector-based user experience and interaction design tool for web and mobile apps.",
        "skill_type": "Software",
        "concept_kind": "SOFTWARE_OR_TOOL",
        "domain": "IT",
        "aliases": ["XD"],
    },
    {
        "c02_id": "custom:dart",
        "name": "Dart",
        "description": "Client-optimized programming language for multi-platform apps developed by Google.",
        "skill_type": "knowledge",
        "concept_kind": "PROGRAMMING_LANGUAGE",
        "domain": "IT",
        "aliases": ["Dart programming"],
    },
    {
        "c02_id": "custom:data-structures-and-algorithms",
        "name": "Data structures and algorithms",
        "description": "Fundamental computer science concepts for organizing, storing, and efficiently processing data.",
        "skill_type": "knowledge",
        "concept_kind": "KNOWLEDGE",
        "domain": "IT",
        "aliases": ["DSA", "data structures & algorithms"],
    },
    {
        "c02_id": "custom:express-js",
        "name": "Express.js",
        "description": "Fast, unopinionated, minimalist web framework for Node.js.",
        "skill_type": "Software",
        "concept_kind": "SOFTWARE_OR_TOOL",
        "domain": "IT",
        "aliases": ["ExpressJS", "Express JS"],
    },
    {
        "c02_id": "custom:fastapi",
        "name": "FastAPI",
        "description": "Modern, fast, high-performance web framework for building APIs with Python.",
        "skill_type": "Software",
        "concept_kind": "SOFTWARE_OR_TOOL",
        "domain": "IT",
        "aliases": ["Fast API"],
    },
    {
        "c02_id": "custom:firebase",
        "name": "Firebase",
        "description": "App development platform by Google providing backend cloud services and real-time databases.",
        "skill_type": "Software",
        "concept_kind": "SOFTWARE_OR_TOOL",
        "domain": "IT",
        "aliases": ["Google Firebase"],
    },
    {
        "c02_id": "custom:flutter",
        "name": "Flutter",
        "description": "Open-source UI software development kit created by Google for cross-platform applications.",
        "skill_type": "Software",
        "concept_kind": "SOFTWARE_OR_TOOL",
        "domain": "IT",
        "aliases": ["Flutter SDK"],
    },
    {
        "c02_id": "custom:laravel",
        "name": "Laravel",
        "description": "Web application framework with expressive, elegant syntax for PHP.",
        "skill_type": "Software",
        "concept_kind": "SOFTWARE_OR_TOOL",
        "domain": "IT",
        "aliases": ["Laravel Framework"],
    },
    {
        "c02_id": "custom:next-js",
        "name": "Next.js",
        "description": "React framework for server-side rendering and static web application development.",
        "skill_type": "Software",
        "concept_kind": "SOFTWARE_OR_TOOL",
        "domain": "IT",
        "aliases": ["NextJS"],
    },
    {
        "c02_id": "custom:tailwind-css",
        "name": "Tailwind CSS",
        "description": "Utility-first CSS framework for rapid custom user interface development.",
        "skill_type": "Software",
        "concept_kind": "SOFTWARE_OR_TOOL",
        "domain": "IT",
        "aliases": ["TailwindCSS", "Tailwind"],
    },
    {
        "c02_id": "custom:tally",
        "name": "Tally",
        "description": "Enterprise resource planning and accounting software used for financial and business management.",
        "skill_type": "Software",
        "concept_kind": "SOFTWARE_OR_TOOL",
        "domain": "BUSINESS",
        "aliases": ["Tally ERP", "TallyPrime", "Tally ERP 9"],
    },
]

EXISTING_ENTITY_ALIASES = [
    {"canonical_entity_id": "SK-000165", "value": "ECMAScript"},
    {"canonical_entity_id": "SK-000165", "value": "ES6"},
    {"canonical_entity_id": "SK-000165", "value": "JS"},
    {"canonical_entity_id": "SK-000676", "value": "SEO"},
    {"canonical_entity_id": "SK-000390", "value": "TS"},
]

C02_REVIEW_ITEMS = [
    {
        "review_category": "DUPLICATE_CONCEPT",
        "entity_type": "SKILL",
        "entity_id": "SK-000790",
        "issue": "C02 custom skill 'Amazon Web Services' (custom:amazon-web-services) is a duplicate of existing entity SK-000790 (Amazon Web Services AWS software). Not created as new entity.",
        "source": "C02_REVIEW",
    },
    {
        "review_category": "DUPLICATE_CONCEPT",
        "entity_type": "SKILL",
        "entity_id": "SK-001541",
        "issue": "C02 custom skill 'Google Cloud Platform' (custom:google-cloud-platform) is a duplicate of existing entity SK-001541 (Google Cloud software). Not created as new entity.",
        "source": "C02_REVIEW",
    },
    {
        "review_category": "DUPLICATE_CONCEPT",
        "entity_type": "SKILL",
        "entity_id": "SK-000836",
        "issue": "C02 custom skill 'HTML' (custom:html) is a duplicate of existing entity SK-000836 (Hypertext markup language HTML). Not created as new entity.",
        "source": "C02_REVIEW",
    },
    {
        "review_category": "DUPLICATE_CONCEPT",
        "entity_type": "SKILL",
        "entity_id": "SK-000802",
        "issue": "C02 custom skill 'Jira' (custom:jira) is a duplicate of existing entity SK-000802 / SK-001666 (Atlassian JIRA). Not created as new entity.",
        "source": "C02_REVIEW",
    },
    {
        "review_category": "DUPLICATE_CONCEPT",
        "entity_type": "SKILL",
        "entity_id": "SK-000860",
        "issue": "C02 custom skill 'Microsoft Azure' (custom:microsoft-azure) is a duplicate of existing entity SK-000860 (Microsoft Azure software). Not created as new entity.",
        "source": "C02_REVIEW",
    },
    {
        "review_category": "DUPLICATE_CONCEPT",
        "entity_type": "SKILL",
        "entity_id": "SK-000257",
        "issue": "C02 custom skill 'Object-oriented programming' (custom:object-oriented-programming) is a duplicate of existing entity SK-000257 (use object-oriented programming). Not created as new entity.",
        "source": "C02_REVIEW",
    },
    {
        "review_category": "DUPLICATE_CONCEPT",
        "entity_type": "SKILL",
        "entity_id": "SK-001215",
        "issue": "C02 custom skill 'Power BI' (custom:power-bi) is a duplicate of existing entity SK-001215 (Microsoft Power BI). Not created as new entity.",
        "source": "C02_REVIEW",
    },
    {
        "review_category": "DUPLICATE_CONCEPT",
        "entity_type": "SKILL",
        "entity_id": "SK-000844",
        "issue": "C02 custom skill 'QuickBooks' (custom:quickbooks) is a duplicate of existing entity SK-000844 (Intuit QuickBooks). Not created as new entity.",
        "source": "C02_REVIEW",
    },
    {
        "review_category": "DUPLICATE_CONCEPT",
        "entity_type": "SKILL",
        "entity_id": "SK-001614",
        "issue": "C02 custom skill 'REST API' (custom:rest-api) is a duplicate of existing entity SK-001614 (RESTful API). Not created as new entity.",
        "source": "C02_REVIEW",
    },
    {
        "review_category": "DUPLICATE_CONCEPT",
        "entity_type": "SKILL",
        "entity_id": "SK-000354",
        "issue": "C02 custom skill 'Unit testing' (custom:unit-testing) is a duplicate of existing entities SK-000354 (perform software unit testing) and SK-001645 (Unit testing software). Not created as new entity.",
        "source": "C02_REVIEW",
    },
    {
        "review_category": "CONCEPT_OVERLAP",
        "entity_type": "SKILL",
        "entity_id": "SK-001746",
        "issue": "C02 custom skill 'CI/CD' (custom:ci-cd) overlaps with existing entity SK-001746 (Continuous integration software). Left out of canonical entities pending review.",
        "source": "C02_REVIEW",
    },
    {
        "review_category": "OUT_OF_SCOPE",
        "entity_type": "SKILL",
        "entity_id": "custom:sinhala",
        "issue": "C02 custom skill 'Sinhala' (custom:sinhala) is a natural language and out of scope for IT/HR/BUSINESS vocabulary.",
        "source": "C02_REVIEW",
    },
    {
        "review_category": "HIDDEN_ALIAS_SCHEMA",
        "entity_type": "ALIAS",
        "entity_id": "C02_HIDDEN_ALIASES",
        "issue": "66 proposed ESCO hidden aliases (common misspellings/variants) retained in review records pending schema support for hidden labels.",
        "source": "C02_REVIEW",
    },
]


def load_csv(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save_csv(records, path, fieldnames):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def finalize():
    print("Reading current import-ready CSVs...")
    entities_path = IMPORT_READY_DIR / "canonical_entities.csv"
    ext_path = IMPORT_READY_DIR / "external_ids.csv"
    alias_path = IMPORT_READY_DIR / "aliases_unlocked.csv"
    domains_path = IMPORT_READY_DIR / "entity_domains.csv"
    review_path = IMPORT_READY_DIR / "review_required.csv"

    entities = load_csv(entities_path)
    external_ids = load_csv(ext_path)
    aliases = load_csv(alias_path)
    entity_domains = load_csv(domains_path)
    review_required = load_csv(review_path)

    orig_counts = {
        "canonical_entities": len(entities),
        "external_ids": len(external_ids),
        "aliases": len(aliases),
        "entity_domains": len(entity_domains),
        "review_required": len(review_required),
    }

    max_sk = max(int(e["id"].split("-")[1]) for e in entities if e["id"].startswith("SK-"))
    max_ext = max(int(x["id"].split("-")[1]) for x in external_ids if x["id"].startswith("EXT-"))
    max_al = max(int(a["id"].split("-")[1]) for a in aliases if a["id"].startswith("AL-"))

    print(f"Original counts: {orig_counts}")
    print(f"Current max IDs: SK-{max_sk:06d}, EXT-{max_ext:06d}, AL-{max_al:06d}")

    # 1. Add 11 new canonical skills
    new_entity_records = []
    new_ext_records = []
    new_domain_records = []
    new_alias_records = []

    curr_sk = max_sk
    curr_ext = max_ext
    curr_al = max_al

    for item in NEW_SKILLS:
        curr_sk += 1
        new_sk_id = f"SK-{curr_sk:06d}"

        new_entity_records.append({
            "id": new_sk_id,
            "entity_type": "SKILL",
            "name": item["name"],
            "description": item["description"],
            "skill_type": item["skill_type"],
            "concept_kind": item["concept_kind"],
            "review_status": "PENDING_REVIEW",
        })

        curr_ext += 1
        new_ext_records.append({
            "id": f"EXT-{curr_ext:06d}",
            "canonical_entity_id": new_sk_id,
            "source_system": "C02_CUSTOM",
            "external_id": item["c02_id"],
            "source_version": "1.0",
        })

        new_domain_records.append({
            "entity_id": new_sk_id,
            "domains": item["domain"],
        })

        for alias_val in item["aliases"]:
            curr_al += 1
            new_alias_records.append({
                "id": f"AL-{curr_al:06d}",
                "canonical_entity_id": new_sk_id,
                "record_type": "ALIAS",
                "value": alias_val,
                "is_verified": "FALSE",
            })

    # 2. Add 5 approved aliases for existing skills
    for item in EXISTING_ENTITY_ALIASES:
        curr_al += 1
        new_alias_records.append({
            "id": f"AL-{curr_al:06d}",
            "canonical_entity_id": item["canonical_entity_id"],
            "record_type": "ALIAS",
            "value": item["value"],
            "is_verified": "FALSE",
        })

    # Combine datasets
    updated_entities = entities + new_entity_records
    updated_ext = external_ids + new_ext_records
    updated_aliases = aliases + new_alias_records
    updated_domains = entity_domains + new_domain_records
    updated_review = review_required + C02_REVIEW_ITEMS

    # Save CSVs
    print("Writing updated CSVs...")
    save_csv(updated_entities, entities_path, ["id", "entity_type", "name", "description", "skill_type", "concept_kind", "review_status"])
    save_csv(updated_ext, ext_path, ["id", "canonical_entity_id", "source_system", "external_id", "source_version"])
    save_csv(updated_aliases, alias_path, ["id", "canonical_entity_id", "record_type", "value", "is_verified"])
    save_csv(updated_domains, domains_path, ["entity_id", "domains"])
    save_csv(updated_review, review_path, ["review_category", "entity_type", "entity_id", "issue", "source"])

    # Validation checks
    val_lines = ["Import Data Validation Report", "=============================", ""]

    all_ent_ids = [e["id"] for e in updated_entities]
    if len(all_ent_ids) == len(set(all_ent_ids)):
        val_lines.append("[PASS] Entity IDs are unique.")
    else:
        val_lines.append("[ERROR] Duplicate Entity IDs found.")

    all_ext_ids = [x["id"] for x in updated_ext]
    if len(all_ext_ids) == len(set(all_ext_ids)):
        val_lines.append("[PASS] External IDs are unique.")
    else:
        val_lines.append("[ERROR] Duplicate External IDs found.")

    all_al_ids = [a["id"] for a in updated_aliases]
    if len(all_al_ids) == len(set(all_al_ids)):
        val_lines.append("[PASS] Alias IDs are unique.")
    else:
        val_lines.append("[ERROR] Duplicate Alias IDs found.")

    ent_id_set = set(all_ent_ids)
    fk_errors = 0
    for x in updated_ext:
        if x["canonical_entity_id"] not in ent_id_set:
            fk_errors += 1
            val_lines.append(f"[ERROR] Invalid canonical_entity_id in external_ids: {x['canonical_entity_id']}")
    for a in updated_aliases:
        if a["canonical_entity_id"] not in ent_id_set:
            fk_errors += 1
            val_lines.append(f"[ERROR] Invalid canonical_entity_id in aliases: {a['canonical_entity_id']}")
    for d in updated_domains:
        if d["entity_id"] not in ent_id_set:
            fk_errors += 1
            val_lines.append(f"[ERROR] Invalid entity_id in entity_domains: {d['entity_id']}")
        for code in d["domains"].split(", "):
            if code not in ("IT", "HR", "BUSINESS"):
                fk_errors += 1
                val_lines.append(f"[ERROR] Invalid domain code '{code}' in entity_domains")

    domain_ent_ids = [d["entity_id"] for d in updated_domains]
    if len(domain_ent_ids) != len(set(domain_ent_ids)):
        fk_errors += 1
        val_lines.append("[ERROR] Duplicate entity IDs in entity_domains.")

    if fk_errors == 0:
        val_lines.append("[PASS] All foreign keys and domain codes are consistent.")

    val_report_path = IMPORT_READY_DIR / "import_validation_report.txt"
    val_report_path.write_text("\n".join(val_lines) + "\n", encoding="utf-8")

    # Update manifest
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "canonical_entities": len(updated_entities),
            "external_ids": len(updated_ext),
            "aliases": len(updated_aliases),
            "entity_domains": len(updated_domains),
            "review_required": len(updated_review),
        },
        "review_status": {
            "pending_entities": sum(1 for e in updated_entities if e["review_status"] != "APPROVED"),
            "review_required_items": len(updated_review),
        },
    }
    manifest_path = IMPORT_READY_DIR / "import_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    new_counts = manifest["counts"]
    print(f"\nFinal counts: {new_counts}")
    print(f"Net changes:")
    for k, v in new_counts.items():
        print(f"  {k}: {orig_counts[k]} -> {v} (+{v - orig_counts[k]})")

    return orig_counts, new_counts


if __name__ == "__main__":
    finalize()
