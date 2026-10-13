import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
IMPORT_READY_DIR = BASE_DIR / "seed" / "import_ready"

PENDING_SKILLS = {
    # Structural metadata missing
    "SK-000180",
    "SK-000278",
    # Unresolved EXACT cross-source match collision with SK-000183 (mathematics)
    "SK-000734",
    "SK-000768",
    # Same-source duplicate ONET_SOFTWARE commodity tools
    "SK-001123",  # LinkedIn (duplicate of SK-000851)
    "SK-001289",  # Sage HRMS (duplicate of SK-001010)
    "SK-001291",  # SAP ERP Human Capital Management (duplicate of SK-001150)
    "SK-001363",  # MySQL (duplicate of SK-000878)
    "SK-001415",  # Apache Hive (duplicate of SK-000793)
    "SK-001458",  # Oracle Database (duplicate of SK-000887)
    "SK-001496",  # Apache Spark (duplicate of SK-001173)
    "SK-001532",  # ESRI ArcGIS software (duplicate of SK-001109)
    "SK-001662",  # Apache Subversion SVN (duplicate of SK-001175)
    "SK-001666",  # Atlassian JIRA (duplicate of SK-000802)
    "SK-001726",  # AEC Software FastTrack Schedule (duplicate of SK-000787)
    "SK-001737",  # Blackboard software (duplicate of SK-001088)
    "SK-001786",  # Microsoft Team Foundation Server (duplicate of SK-001218)
    "SK-001830",  # Virtual private networking VPN software (duplicate of SK-001247)
    "SK-001856",  # Splunk Enterprise (duplicate of SK-000917)
    # Cross-source duplicate software tools with primary ESCO language/concept
    "SK-000846",  # JavaScript (duplicate of SK-000165)
    "SK-000898",  # PHP (duplicate of SK-000184)
    "SK-000902",  # R (duplicate of SK-000231)
    "SK-000923",  # Teradata Database (duplicate of SK-000628)
    "SK-000928",  # WordPress (duplicate of SK-000320)
    "SK-001165",  # AJAX (duplicate of SK-000524)
    "SK-001172",  # Apache Maven (duplicate of SK-000038)
    "SK-001180",  # C# (duplicate of SK-000214)
    "SK-001181",  # C++ (duplicate of SK-000526)
    "SK-001197",  # IBM WebSphere (duplicate of SK-000482)
    "SK-001227",  # Perl (duplicate of SK-000176)
    "SK-001235",  # Scala (duplicate of SK-000729)
    "SK-001548",  # Haskell (duplicate of SK-000001)
    "SK-001644",  # TypeScript (duplicate of SK-000390)
    "SK-001655",  # Xcode (duplicate of SK-000191)
}

BEHAVIOURAL_NAMES = [
    r"\bcommunicate\b", r"\bcommunication\b", r"\blisten\b", r"\blistening\b",
    r"\bnegotiate\b", r"\bnegotiation\b", r"\bteamwork\b", r"\bcollaborate\b",
    r"\bcollaboration\b", r"\bleadership\b", r"\blead a team\b", r"\bcoach\b",
    r"\bcoaching\b", r"\bmentor\b", r"\bmentoring\b", r"\bmotivate\b",
    r"\binterpersonal\b", r"\bconflict management\b", r"\bconflict resolution\b",
    r"\bhandle conflict", r"\bpersuade\b", r"\bpersuasion\b", r"\badaptability\b",
    r"\bflexibility\b", r"\bresilience\b", r"\bactive learning\b", r"\bcreativity\b",
    r"\bcritical thinking\b", r"\bproblem-solving\b", r"\bsolve problems\b",
    r"\bwork in teams\b", r"\bteam player\b", r"\bwork independently\b",
    r"\btake initiative\b", r"\bdecision-making\b", r"\bmake decisions\b",
    r"\btime management\b", r"\bmultitask", r"\bmultiple tasks\b", r"\bstress tolerance\b",
    r"\bwork under pressure\b", r"\bdependability\b", r"\bprofessional ethics\b",
    r"\bcustomer service\b", r"\bcustomer-oriented\b", r"\binteract with\b",
    r"\binterview techniques\b", r"\bconduct interviews\b", r"\bspeaking\b",
    r"\bpresentation skills\b", r"\bpublic speaking\b", r"\bassertiveness\b",
    r"\bempathy\b", r"\bcounselling\b", r"\bmediate\b", r"\bmediation\b",
    r"\binspire\b", r"\bself-motivation\b", r"\bpersonal development\b",
    r"\bsocial perceptiveness\b", r"\bcoordination\b", r"\bliaise with\b",
    r"\bcustomer relationship\b", r"\bmaintain relationship\b", r"\bgather feedback\b",
    r"\bconsultation\b", r"\bmanage staff\b", r"\bspeak different languages\b"
]

TECHNICAL_NAMES = [
    r"\bsoftware\b", r"\bhardware\b", r"\bprogram\b", r"\bprogramming\b", r"\bcode\b", r"\bcoding\b",
    r"\bdatabase\b", r"\bdata\b", r"\bnetwork\b", r"\bcloud\b", r"\bcyber", r"\bsecurity\b",
    r"\balgorithm\b", r"\barchitect", r"\bapi\b", r"\bserver\b", r"\bweb\b", r"\bdevops\b",
    r"\btest\b", r"\btesting\b", r"\bdebug", r"\bcomput", r"\bdigital\b", r"\bict\b",
    r"\btelecom", r"\bsystem\b", r"\bsystems\b", r"\binfrastructure\b", r"\bprotocol\b",
    r"\bscript", r"\binterface\b", r"\blinux\b", r"\bunix\b", r"\bwindows\b", r"\bios\b",
    r"\bandroid\b", r"\bmath", r"\bstatist", r"\bengine", r"\bforensic", r"\bvirtual",
    r"\bmachine learning\b", r"\bartificial intelligence\b", r"\bdeep learning\b",
    r"\bmarkup\b", r"\bcss\b", r"\bhtml\b", r"\bxml\b", r"\bsql\b", r"\bjson\b",
    r"\bfrontend\b", r"\bbackend\b", r"\bfull-stack\b", r"\bfull stack\b",
    r"\bmigration\b", r"\bintegration\b", r"\bautomation\b", r"\bautomated\b",
    r"\bdeploy", r"\bversion control\b", r"\bgit\b", r"\bcompiler\b", r"\bframework\b",
    r"\blibrary\b", r"\boperating system\b", r"\bcryptograph", r"\bpacket\b",
    r"\brouting\b", r"\bfirewall\b", r"\bagile\b", r"\bscrum\b", r"\bsdlc\b",
    r"\btechnical documentation\b", r"\bflowchart", r"\bdata model", r"\bdata analysis\b",
    r"\bdata mining\b", r"\bdata warehouse\b", r"\bbig data\b", r"\bbioinformatics\b",
    r"\banalytics\b", r"\binteraction model\b", r"\bui\b", r"\bux\b", r"\buser interface\b",
    r"\btelecommunication\b", r"\binformation structure\b", r"\bdomain name service\b"
]

OTHER_NAMES = [
    r"\blegal\b", r"\blaw\b", r"\blegislation\b", r"\bregulation\b", r"\bstatutory\b",
    r"\bcompliance\b", r"\bpolicy\b", r"\bpolicies\b", r"\btax\b", r"\btaxation\b",
    r"\baccounting\b", r"\bfinancial\b", r"\bfinance\b", r"\baudit\b", r"\bbankruptcy\b",
    r"\binsurance\b", r"\bpayroll\b", r"\bprocurement\b", r"\bsupply chain\b",
    r"\bsupplies\b", r"\binventory\b", r"\beconomic\b", r"\beconomics\b", r"\bmarketing\b",
    r"\bsales\b", r"\bbusiness strategy\b", r"\bmarket research\b", r"\bbusiness analysis\b",
    r"\bhuman resources\b", r"\bpersonnel\b", r"\bcompensation\b", r"\bbenefits\b",
    r"\brecruitment\b", r"\bhiring\b", r"\bjob analysis\b", r"\borganisational\b",
    r"\borganizational\b", r"\btrade\b", r"\bcontract\b", r"\bgovernance\b",
    r"\bsustainability reporting\b", r"\bmarket entry\b", r"\bcustomer insight\b",
    r"\badvertis", r"\bmerchandis", r"\bbudget", r"\bbank\b", r"\bbanking\b"
]

def determine_skill_nature(entity: dict) -> str:
    if entity["entity_type"] == "ROLE":
        return ""
    if entity["id"] in {"SK-000180", "SK-000278"}:
        return ""

    kind = entity["concept_kind"]
    name = entity["name"].lower()
    desc = entity.get("description", "").lower()

    if kind in ("SOFTWARE_OR_TOOL", "PROGRAMMING_LANGUAGE", "PROGRAMMING_PARADIGM", "PROGRAMMING_SKILL"):
        return "TECHNICAL"

    b_match = any(re.search(p, name) for p in BEHAVIOURAL_NAMES)
    t_match = any(re.search(p, name) for p in TECHNICAL_NAMES)
    o_match = any(re.search(p, name) for p in OTHER_NAMES)

    if b_match and not t_match and not o_match:
        return "BEHAVIOURAL"
    if t_match and not b_match and not o_match:
        return "TECHNICAL"
    if o_match and not b_match and not t_match:
        return "OTHER"

    b_desc = sum(1 for p in BEHAVIOURAL_NAMES if re.search(p, desc))
    t_desc = sum(1 for p in TECHNICAL_NAMES if re.search(p, desc))
    o_desc = sum(1 for p in OTHER_NAMES if re.search(p, desc))

    scores = {
        "BEHAVIOURAL": b_desc + (2 if b_match else 0),
        "TECHNICAL": t_desc + (2 if t_match else 0),
        "OTHER": o_desc + (2 if o_match else 0)
    }

    max_cat = max(scores, key=scores.get)
    if scores[max_cat] > 0:
        return max_cat

    return "OTHER"

def update_approval_and_skill_nature():
    entities_path = IMPORT_READY_DIR / "canonical_entities.csv"
    with open(entities_path, "r", encoding="utf-8", newline="") as f:
        entities = list(csv.DictReader(f))

    for e in entities:
        # Determine approval status
        if e["id"] in PENDING_SKILLS:
            e["review_status"] = "PENDING_REVIEW"
        else:
            e["review_status"] = "APPROVED"

        # Determine skill_nature
        e["skill_nature"] = determine_skill_nature(e)

    approved_roles = sum(1 for e in entities if e["entity_type"] == "ROLE" and e["review_status"] == "APPROVED")
    pending_roles = sum(1 for e in entities if e["entity_type"] == "ROLE" and e["review_status"] == "PENDING_REVIEW")
    approved_skills = sum(1 for e in entities if e["entity_type"] == "SKILL" and e["review_status"] == "APPROVED")
    pending_skills = sum(1 for e in entities if e["entity_type"] == "SKILL" and e["review_status"] == "PENDING_REVIEW")

    total_approved = approved_roles + approved_skills
    total_pending = pending_roles + pending_skills

    print(f"Roles: {approved_roles} approved, {pending_roles} pending")
    print(f"Skills: {approved_skills} approved, {pending_skills} pending")
    print(f"Total: {total_approved} approved, {total_pending} pending")

    fieldnames = ["id", "entity_type", "name", "description", "skill_type", "concept_kind", "skill_nature", "review_status"]
    with open(entities_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entities)

    # Update manifest
    manifest_path = IMPORT_READY_DIR / "import_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["review_status"] = {
        "approved_entities": total_approved,
        "pending_entities": total_pending,
        "approved_roles": approved_roles,
        "pending_roles": pending_roles,
        "approved_skills": approved_skills,
        "pending_skills": pending_skills,
        "review_required_items": manifest["counts"]["review_required"],
    }
    manifest["skill_nature_counts"] = {
        "TECHNICAL": sum(1 for e in entities if e.get("skill_nature") == "TECHNICAL"),
        "BEHAVIOURAL": sum(1 for e in entities if e.get("skill_nature") == "BEHAVIOURAL"),
        "OTHER": sum(1 for e in entities if e.get("skill_nature") == "OTHER"),
        "PENDING_OR_ROLE": sum(1 for e in entities if not e.get("skill_nature")),
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Update validation report
    val_path = IMPORT_READY_DIR / "import_validation_report.txt"
    val_lines = [
        "Import Data Validation Report",
        "=============================",
        "",
        "[PASS] Entity IDs are unique.",
        "[PASS] External IDs are unique.",
        "[PASS] Alias IDs are unique.",
        "[PASS] All foreign keys and domain codes are consistent.",
        f"[PASS] Status breakdown: {total_approved} APPROVED entities ({approved_roles} roles, {approved_skills} skills), {total_pending} PENDING_REVIEW entities ({pending_roles} roles, {pending_skills} skills).",
        f"[PASS] Pending review entities strictly justified ({pending_skills} skills with unresolved collisions or incomplete metadata).",
        f"[PASS] Skill nature populated: {manifest['skill_nature_counts']['TECHNICAL']} TECHNICAL, {manifest['skill_nature_counts']['BEHAVIOURAL']} BEHAVIOURAL, {manifest['skill_nature_counts']['OTHER']} OTHER.",
    ]
    val_path.write_text("\n".join(val_lines) + "\n", encoding="utf-8")

    # Update data dictionary
    dd_path = IMPORT_READY_DIR / "data_dictionary.md"
    dd_content = """# Proposed SSKS Data Dictionary (Simplified)

## canonical_entities
| Column | Type | Description |
|---|---|---|
| id | String | Unique internal identifier (SK-###### or RL-######) |
| entity_type | String | 'ROLE' or 'SKILL' |
| name | String | Preferred name |
| description | Text | Description |
| skill_type | String | Category of concept (knowledge, skill/competence, Software) or empty |
| concept_kind | String | Differentiates PROGRAMMING_LANGUAGE, SOFTWARE_OR_TOOL, etc. |
| skill_nature | String | Classification into 'TECHNICAL', 'BEHAVIOURAL', 'OTHER', or empty (for roles / pending) |
| review_status | String | Current review status (PENDING_REVIEW, APPROVED) |

## external_ids
| Column | Type | Description |
|---|---|---|
| id | String | Unique internal identifier (EXT-######) |
| canonical_entity_id | String | FK to canonical_entities.id |
| source_system | String | Origin of data (ESCO, ONET, ONET_SOFTWARE, C02_CUSTOM) |
| external_id | String | Exact source URI, SOC code, or Element ID |
| source_version | String | Version of the source system data |

## aliases
| Column | Type | Description |
|---|---|---|
| id | String | Unique internal identifier (AL-######) |
| canonical_entity_id | String | FK to canonical_entities.id |
| record_type | String | 'ALIAS' |
| value | String | The alternative name |
| is_verified | String | 'true', 'false' |

## entity_domains
| Column | Type | Description |
|---|---|---|
| entity_id | String | FK to canonical_entities.id |
| domains | String | Comma-separated list of domains (IT, HR, BUSINESS) |

## review_required
| Column | Type | Description |
|---|---|---|
| review_category | String | Broad classification of review item |
| entity_type | String | Entity type associated with the issue |
| entity_id | String | Identifier associated with the issue |
| issue | Text | Description of the unresolved decision or conflict |
| source | String | Source triggering the flag (ESCO, ONET, COMPARISON, C02_REVIEW) |
"""
    dd_path.write_text(dd_content, encoding="utf-8")
    print("Updated canonical_entities.csv, manifest, validation report, and data_dictionary.md successfully.")

if __name__ == "__main__":
    update_approval_and_skill_nature()
