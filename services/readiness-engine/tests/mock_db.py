import json
import operator
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.sql.elements import (
    BinaryExpression,
    BooleanClauseList,
    Grouping,
    UnaryExpression,
)
from sqlalchemy.sql.selectable import Select
from sqlalchemy.sql.dml import Update

from app.models.analysis import (
    Analysis,
    AnalysisPrioritySkill,
    AnalysisReport,
    AnalysisSkillResult,
    CandidateDiscoveryRun,
)
from app.models.cache import (
    CachedAlias,
    CachedRelationship,
    CachedSkill,
    KnowledgeSnapshot,
)
from app.models.profiles import (
    IndustryProfile,
    IndustryProfileRequirement,
    UserSkillProfile,
    UserSkillProfileSkill,
)

SEED_DIR = Path(__file__).resolve().parents[1] / "seed"
DEFAULT_TEST_USER_ID = uuid.UUID("1f40007d-6a6c-49ff-b8cc-dea297d258f2")
DEFAULT_SNAPSHOT_ID = uuid.UUID("49a854a1-af7f-5ed0-b0e4-f45ade951008")


class MockResult:
    def __init__(self, items: list[Any]):
        self._items = list(items)

    def scalars(self) -> "MockScalarResult":
        return MockScalarResult(self._items)

    def scalar(self) -> Any:
        return self._items[0] if self._items else None

    def scalar_one(self) -> Any:
        if not self._items:
            raise ValueError("No items in query result for scalar_one()")
        return self._items[0]

    def scalar_one_or_none(self) -> Any:
        if not self._items:
            return None
        if len(self._items) > 1:
            raise ValueError(f"Multiple items ({len(self._items)}) in scalar_one_or_none()")
        return self._items[0]

    def first(self) -> Any:
        if not self._items:
            return None
        item = self._items[0]
        return (item,) if not isinstance(item, tuple) else item

    def all(self) -> list[Any]:
        return [(item,) if not isinstance(item, tuple) else item for item in self._items]


class MockScalarResult:
    def __init__(self, items: list[Any]):
        self._items = list(items)

    def first(self) -> Any:
        return self._items[0] if self._items else None

    def all(self) -> list[Any]:
        return list(self._items)

    def one(self) -> Any:
        if len(self._items) != 1:
            raise ValueError(f"Expected 1 item, got {len(self._items)}")
        return self._items[0]

    def one_or_none(self) -> Any:
        if not self._items:
            return None
        if len(self._items) > 1:
            raise ValueError(f"Expected at most 1 item, got {len(self._items)}")
        return self._items[0]


def eval_expr(clause: Any, item: Any, store: "MockDataStore") -> bool:
    if clause is None:
        return True

    if isinstance(clause, Grouping):
        return eval_expr(clause.element, item, store)

    if isinstance(clause, BooleanClauseList):
        op_str = str(clause.operator).upper()
        if "AND" in op_str:
            return all(eval_expr(c, item, store) for c in clause.clauses)
        elif "OR" in op_str:
            return any(eval_expr(c, item, store) for c in clause.clauses)

    if isinstance(clause, BinaryExpression):
        left_attr = getattr(clause.left, "key", getattr(clause.left, "name", None))
        val = getattr(item, left_attr, None) if left_attr else None

        # Check joined table attributes (e.g. Analysis -> IndustryProfile)
        if val is None and isinstance(item, Analysis) and left_attr:
            ind = store.industry_profiles.get(item.industry_profile_id)
            if ind is not None:
                val = getattr(ind, left_attr, None)

        right = clause.right
        r_val = right.value if hasattr(right, "value") else right

        # Subquery handling (e.g. UserSkillProfile.id.in_(subquery))
        if hasattr(right, "element") and isinstance(right.element, Select):
            sub_col = right.element.column_descriptions[0]
            if sub_col.get("entity") == UserSkillProfile:
                # Find matching user profile IDs for user_id in subquery
                r_val = {
                    p.id
                    for p in store.user_profiles.values()
                    if all(eval_expr(c, p, store) for c in right.element._where_criteria)
                }

        op = clause.operator
        op_name = getattr(op, "__name__", str(op)).lower()

        if op == operator.eq or op_name in ("eq", "="):
            if isinstance(val, uuid.UUID) or isinstance(r_val, uuid.UUID):
                return str(val) == str(r_val)
            if isinstance(val, str) and isinstance(r_val, str):
                return val.strip().lower() == r_val.strip().lower()
            return val == r_val
        elif op == operator.ne or op_name in ("ne", "!="):
            if isinstance(val, uuid.UUID) or isinstance(r_val, uuid.UUID):
                return str(val) != str(r_val)
            return val != r_val
        elif "is" in op_name:
            if "not" in op_name:
                return val is not r_val
            return val is r_val or val == r_val
        elif "in" in op_name:
            if hasattr(r_val, "__iter__") and not isinstance(r_val, (str, bytes)):
                str_targets = {str(x) for x in r_val}
                return str(val) in str_targets
            return False

    if isinstance(clause, UnaryExpression):
        attr = getattr(clause.element, "key", getattr(clause.element, "name", None))
        val = getattr(item, attr, None) if attr else None
        modifier = str(getattr(clause, "modifier", getattr(clause, "operator", ""))).lower()
        if "is not" in modifier:
            return val is not None
        elif "is" in modifier:
            return val is None
        elif "not" in modifier:
            return not bool(val)

    return True


class MockDataStore:
    def __init__(self) -> None:
        self.industry_profiles: dict[uuid.UUID, IndustryProfile] = {}
        self.user_profiles: dict[uuid.UUID, UserSkillProfile] = {}
        self.snapshots: dict[uuid.UUID, KnowledgeSnapshot] = {}
        self.cached_aliases: list[CachedAlias] = []
        self.cached_relationships: list[CachedRelationship] = []
        self.cached_skills: list[CachedSkill] = []
        self.analyses: dict[uuid.UUID, Analysis] = {}
        self.skill_results: dict[uuid.UUID, AnalysisSkillResult] = {}
        self.priority_skills: dict[uuid.UUID, AnalysisPrioritySkill] = {}
        self.reports: dict[uuid.UUID, AnalysisReport] = {}
        self.candidate_runs: dict[uuid.UUID, CandidateDiscoveryRun] = {}

        self.initial_industry_profiles: dict[uuid.UUID, IndustryProfile] = {}
        self.initial_user_profiles: dict[uuid.UUID, UserSkillProfile] = {}
        self._load_seed_data()

    def _load_seed_data(self) -> None:
        # 1. Load seed industry profiles
        ind_dir = SEED_DIR / "industry-role-profiles"
        if ind_dir.exists():
            for fpath in ind_dir.glob("*.json"):
                try:
                    with open(fpath, encoding="utf-8") as f:
                        data = json.load(f)
                    role_data = data.get("data", {}).get(
                        "industry_role_profile",
                        data.get("data", {}).get("industryRoleProfile", {}),
                    )
                    if not role_data:
                        continue

                    profile_id = uuid.uuid4()
                    role_id = role_data.get("role_id") or role_data.get("roleId")
                    title = role_data.get("primary_observed_title", "Role Title")
                    domain_obj = role_data.get("domain", {})

                    role = IndustryProfile(
                        id=profile_id,
                        role_id=role_id,
                        candidate_role_id=role_data.get("candidate_role_id")
                        or role_data.get("candidateRoleId"),
                        role_name=title,
                        primary_observed_title=title,
                        observed_titles=role_data.get("observed_titles", []),
                        mapping_status=role_data.get("mapping_status", "verified"),
                        career_level=role_data.get("career_level", "ENTRY_LEVEL"),
                        profile_version=role_data.get("profile_version", "1.0"),
                        domain_id=domain_obj.get("domain_id", "DOM-IT"),
                        domain_name=domain_obj.get("domain_name", "Information Technology"),
                        profile_status=role_data.get("profile_status", "active"),
                        source_message_id=data.get("message_id", "SEED-MSG"),
                        raw_payload=data,
                        received_at=datetime.now(UTC),
                    )

                    for req_item in role_data.get("requirements", []):
                        req = IndustryProfileRequirement(
                            id=uuid.uuid4(),
                            industry_profile_id=role.id,
                            skill_id=req_item.get("skill_id") or req_item.get("skillId"),
                            candidate_skill_id=req_item.get("candidate_skill_id")
                            or req_item.get("candidateSkillId"),
                            standard_name=req_item.get("standard_name", ""),
                            primary_observed_term=req_item.get(
                                "primary_observed_term", req_item.get("standard_name", "")
                            ),
                            observed_terms=req_item.get("observed_terms", []),
                            mapping_status=req_item.get("mapping_status", "verified"),
                            skill_type=req_item.get("skill_type", "TECHNICAL"),
                            required_proficiency_level=req_item.get(
                                "required_proficiency_level"
                            )
                            or (
                                req_item.get("required_proficiency", {}).get("level")
                                if isinstance(req_item.get("required_proficiency"), dict)
                                else None
                            )
                            or "INTERMEDIATE",
                            required_proficiency_score=float(
                                req_item.get("required_proficiency_score")
                                if "required_proficiency_score" in req_item
                                else (
                                    req_item.get("required_proficiency", {}).get("score", 0.5)
                                    if isinstance(req_item.get("required_proficiency"), dict)
                                    else 0.5
                                )
                            ),
                            demand_weight=float(
                                req_item.get("demand_weight")
                                if "demand_weight" in req_item
                                else req_item.get("DemandWeight", 1.0)
                            ),
                        )
                        role.requirements.append(req)

                    self.industry_profiles[role.id] = role
                    self.initial_industry_profiles[role.id] = role
                except Exception as err:  # noqa: BLE001
                    print(f"Warning: Failed to load industry seed fixture {fpath}: {err}", file=sys.stderr)

        # 2. Load seed user profiles
        usr_dir = SEED_DIR / "user-skill-profiles"
        if usr_dir.exists():
            for fpath in usr_dir.glob("*.json"):
                try:
                    with open(fpath, encoding="utf-8") as f:
                        data = json.load(f)
                    usr_data = data.get("data", {}).get(
                        "user_skill_profile",
                        data.get("data", {}).get("userSkillProfile", {}),
                    )
                    if not usr_data:
                        continue

                    raw_user_id = usr_data.get("user_id") or usr_data.get("userId")
                    user_id = (
                        uuid.UUID(str(raw_user_id))
                        if raw_user_id
                        else DEFAULT_TEST_USER_ID
                    )

                    u_prof = UserSkillProfile(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        profile_version=usr_data.get("profile_version", "1.0"),
                        domain_id="DOM-IT",
                        domain_name="Information Technology",
                        completeness_score=0.9,
                        raw_payload=data,
                        received_at=datetime.now(UTC),
                    )

                    for s_item in usr_data.get("skills", []):
                        prof_obj = s_item.get("proficiency", {})
                        prof_level = (
                            s_item.get("proficiency_level")
                            or (prof_obj.get("level") if isinstance(prof_obj, dict) else None)
                            or "INTERMEDIATE"
                        )
                        prof_score = (
                            s_item.get("proficiency_score")
                            if "proficiency_score" in s_item
                            else (
                                prof_obj.get("score")
                                if isinstance(prof_obj, dict)
                                else 0.5
                            )
                        )
                        conf = s_item.get("evidence_confidence", 1.0)

                        skill = UserSkillProfileSkill(
                            id=uuid.uuid4(),
                            user_skill_profile_id=u_prof.id,
                            skill_id=s_item.get("skill_id") or s_item.get("skillId"),
                            candidate_skill_id=s_item.get("candidate_skill_id")
                            or s_item.get("candidateSkillId"),
                            standard_name=s_item.get("standard_name", ""),
                            primary_observed_term=s_item.get(
                                "primary_observed_term", s_item.get("standard_name", "")
                            ),
                            observed_terms=s_item.get("observed_terms", []),
                            mapping_status=s_item.get("mapping_status", "verified"),
                            skill_type=s_item.get("skill_type", "TECHNICAL"),
                            proficiency_level=prof_level,
                            proficiency_score=float(prof_score),
                            evidence_confidence=float(conf),
                            verification_status="VERIFIED",
                        )
                        u_prof.skills.append(skill)

                    self.user_profiles[u_prof.id] = u_prof
                    self.initial_user_profiles[u_prof.id] = u_prof
                except Exception as err:  # noqa: BLE001
                    print(f"Warning: Failed to load user seed fixture {fpath}: {err}", file=sys.stderr)

        # 3. Load active Knowledge Snapshot
        snap_path = SEED_DIR / "knowledge-snapshots" / "snapshot_001.json"
        snapshot = KnowledgeSnapshot(
            snapshot_id=DEFAULT_SNAPSHOT_ID,
            version="v20261018-089da5f14d4a",
            ssks_snapshot_id="SNAP-FIXTURE-001",
            consumer="ReadinessEngine",
            generated_at=datetime.now(UTC),
            status="ACTIVE",
            is_active=True,
        )
        self.snapshots[snapshot.snapshot_id] = snapshot

        if snap_path.exists():
            try:
                with open(snap_path, encoding="utf-8") as f:
                    snap_data = json.load(f)

                for a_item in snap_data.get("aliases", []):
                    alias = CachedAlias(
                        snapshot_id=snapshot.snapshot_id,
                        alias_id=a_item.get("alias_id", str(uuid.uuid4())),
                        skill_id=a_item["skill_id"],
                        alias_text=a_item.get("alias_text", ""),
                        normalized_alias=a_item.get("normalized_alias", ""),
                    )
                    self.cached_aliases.append(alias)

                for r_item in snap_data.get("relationships", []):
                    rel = CachedRelationship(
                        snapshot_id=snapshot.snapshot_id,
                        relationship_id=r_item.get("relationship_id", str(uuid.uuid4())),
                        source_skill_id=r_item["source_skill_id"],
                        target_skill_id=r_item["target_skill_id"],
                        relationship_type=r_item["relationship_type"],
                        verification_status=r_item.get("verification_status", "VERIFIED"),
                        evidence_note=r_item.get("evidence_note"),
                    )
                    self.cached_relationships.append(rel)
            except Exception as err:  # noqa: BLE001
                print(f"Warning: Failed to load snapshot JSON {snap_path}: {err}", file=sys.stderr)

    def reset(self) -> None:
        self.analyses.clear()
        self.skill_results.clear()
        self.priority_skills.clear()
        self.reports.clear()
        self.candidate_runs.clear()

        # Restore initial industry and user profiles
        self.industry_profiles = dict(self.initial_industry_profiles)
        self.user_profiles = dict(self.initial_user_profiles)


class MockAsyncSession:
    def __init__(self, store: MockDataStore) -> None:
        self.store = store
        self._new_items: list[Any] = []

    def add(self, item: Any) -> None:
        self._new_items.append(item)
        self._persist_item(item)

    def add_all(self, items: list[Any]) -> None:
        for it in items:
            self.add(it)

    def _persist_item(self, item: Any) -> None:
        if isinstance(item, IndustryProfile):
            self.store.industry_profiles[item.id] = item
        elif isinstance(item, UserSkillProfile):
            self.store.user_profiles[item.id] = item
        elif isinstance(item, KnowledgeSnapshot):
            self.store.snapshots[item.snapshot_id] = item
        elif isinstance(item, Analysis):
            if getattr(item, "matching_method", None) is None:
                item.matching_method = "RELATIONSHIP_AWARE"
            if getattr(item, "scoring_config_version", None) is None:
                item.scoring_config_version = "1.0"
            if getattr(item, "started_at", None) is None:
                item.started_at = datetime.now(UTC)
            self.store.analyses[item.analysis_id] = item
        elif isinstance(item, AnalysisSkillResult):
            self.store.skill_results[item.id] = item
        elif isinstance(item, AnalysisPrioritySkill):
            self.store.priority_skills[item.id] = item
        elif isinstance(item, AnalysisReport):
            self.store.reports[item.id] = item
        elif isinstance(item, CandidateDiscoveryRun):
            self.store.candidate_runs[item.run_id] = item

    async def commit(self) -> None:
        self._new_items.clear()

    async def flush(self) -> None:
        pass

    async def rollback(self) -> None:
        # Revert uncommitted items from store
        for item in self._new_items:
            if isinstance(item, AnalysisSkillResult) and item.id in self.store.skill_results:
                del self.store.skill_results[item.id]
            elif isinstance(item, AnalysisPrioritySkill) and item.id in self.store.priority_skills:
                del self.store.priority_skills[item.id]
            elif isinstance(item, AnalysisReport) and item.id in self.store.reports:
                del self.store.reports[item.id]
        self._new_items.clear()

    async def close(self) -> None:
        pass

    async def __aenter__(self) -> "MockAsyncSession":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def scalar(self, stmt: Any) -> Any:
        res = await self.execute(stmt)
        return res.scalar()

    async def scalars(self, stmt: Any) -> MockScalarResult:
        res = await self.execute(stmt)
        return res.scalars()

    async def execute(self, stmt: Any) -> MockResult:
        if isinstance(stmt, Update):
            table_name = getattr(stmt.table, "name", "")
            if table_name == "analyses":
                target_analyses = [
                    a for a in self.store.analyses.values()
                    if all(eval_expr(c, a, self.store) for c in stmt._where_criteria)
                ]
                for analysis in target_analyses:
                    for k, v in stmt._values.items():
                        attr = getattr(k, "key", getattr(k, "name", str(k)))
                        val = getattr(v, "value", v)
                        setattr(analysis, attr, val)
            return MockResult([])

        if not isinstance(stmt, Select):
            return MockResult([])

        col_descs = getattr(stmt, "column_descriptions", [])
        if not col_descs:
            return MockResult([])

        col = col_descs[0]
        entity = col.get("entity") or col.get("type")
        is_count = col.get("name") == "count" or "count" in str(col.get("expr", "")).lower()

        # Select candidate list based on entity
        if entity == IndustryProfile or col.get("type") == IndustryProfile:
            items = list(self.store.industry_profiles.values())
        elif entity == UserSkillProfile or col.get("type") == UserSkillProfile:
            items = list(self.store.user_profiles.values())
        elif entity == KnowledgeSnapshot or col.get("type") == KnowledgeSnapshot:
            items = list(self.store.snapshots.values())
        elif entity == CachedAlias or col.get("type") == CachedAlias:
            items = list(self.store.cached_aliases)
        elif entity == CachedRelationship or col.get("type") == CachedRelationship:
            items = list(self.store.cached_relationships)
        elif entity == Analysis or col.get("type") == Analysis:
            items = list(self.store.analyses.values())
        elif entity == AnalysisSkillResult or col.get("type") == AnalysisSkillResult:
            items = list(self.store.skill_results.values())
        elif entity == AnalysisPrioritySkill or col.get("type") == AnalysisPrioritySkill:
            items = list(self.store.priority_skills.values())
        elif entity == AnalysisReport or col.get("type") == AnalysisReport:
            items = list(self.store.reports.values())
        elif entity == CandidateDiscoveryRun or col.get("type") == CandidateDiscoveryRun:
            items = list(self.store.candidate_runs.values())
        else:
            items = []

        # Filter items
        where_criteria = getattr(stmt, "_where_criteria", ())
        if where_criteria:
            items = [it for it in items if all(eval_expr(c, it, self.store) for c in where_criteria)]

        if is_count:
            return MockResult([len(items)])

        # Sorting
        order_clauses = getattr(stmt, "_order_by_clauses", ())
        if order_clauses:
            for clause in reversed(order_clauses):
                element = getattr(clause, "element", clause)
                attr = getattr(element, "key", getattr(element, "name", None))
                if attr:
                    is_desc = "desc" in str(clause).lower()
                    items.sort(
                        key=lambda x: (getattr(x, attr, None) is None, getattr(x, attr, None)),
                        reverse=is_desc,
                    )

        # Pagination
        offset = getattr(stmt, "_offset", None)
        if offset is not None:
            items = items[offset:]
        limit = getattr(stmt, "_limit", None)
        if limit is not None:
            items = items[:limit]

        # Attach relation navigation attributes on Analysis records
        for it in items:
            if isinstance(it, Analysis):
                it.industry_profile = self.store.industry_profiles.get(it.industry_profile_id)
                it.reports = [r for r in self.store.reports.values() if r.analysis_id == it.analysis_id]
                it.skill_results = [sr for sr in self.store.skill_results.values() if sr.analysis_id == it.analysis_id]
                it.priority_skills = [ps for ps in self.store.priority_skills.values() if ps.analysis_id == it.analysis_id]

        return MockResult(items)


# Global singleton store for test session
_global_mock_store = MockDataStore()


def get_mock_store() -> MockDataStore:
    return _global_mock_store


def create_mock_session() -> MockAsyncSession:
    return MockAsyncSession(_global_mock_store)


class MockSessionMaker:
    def __call__(self) -> MockAsyncSession:
        return create_mock_session()
