import uuid

import pytest

from app.algorithms.matching import (
    AliasInput,
    MatchingMethod,
    MatchingPolicy,
    MatchResultStatus,
    MatchType,
    RelationshipInput,
    RelationshipType,
    RequirementInput,
    StudentSkillInput,
    match_skills,
)


def test_01_exact_canonical_skill_id_match():
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000001",
        standard_name="Python",
        mapping_status="RESOLVED",
    )
    student_skill = StudentSkillInput(
        skill_record_id=uuid.uuid4(), skill_id="SK-000001", standard_name="Python"
    )

    results = match_skills([req], [student_skill])
    assert len(results) == 1
    res = results[0]
    assert res.match_type == MatchType.EXACT.value
    assert res.coverage_credit == 1.0
    assert res.result_status == MatchResultStatus.MATCHED.value
    assert res.matched_canonical_skill_id == "SK-000001"
    assert res.selected_student_skill_id == student_skill.skill_record_id


def test_02_verified_alias_normalization_to_same_canonical_id():
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000458",
        standard_name="JavaScript",
        mapping_status="RESOLVED",
    )
    # Student skill does not have a canonical ID directly, but observed term is 'JS'
    student_skill = StudentSkillInput(
        skill_record_id=uuid.uuid4(),
        skill_id=None,
        standard_name="JS",
        primary_observed_term="JS",
        observed_terms=["JS", "Javascript language"],
    )
    alias = AliasInput(
        alias_id="AL-001", skill_id="SK-000458", alias_text="JS", normalized_alias="js"
    )

    results = match_skills([req], [student_skill], aliases=[alias])

    assert len(results) == 1
    res = results[0]
    assert res.match_type == MatchType.ALIAS.value
    assert res.coverage_credit == 1.0
    assert res.result_status == MatchResultStatus.MATCHED.value
    assert res.matched_canonical_skill_id == "SK-000458"


def test_03_exact_baseline_does_not_award_credit_from_relationship():
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000458",
        standard_name="JavaScript",
        mapping_status="RESOLVED",
    )
    student_skill = StudentSkillInput(
        skill_record_id=uuid.uuid4(), skill_id="SK-001606", standard_name="React"
    )
    rel = RelationshipInput(
        relationship_id="REL-001",
        source_skill_id="SK-001606",
        target_skill_id="SK-000458",
        relationship_type=RelationshipType.NARROWER_THAN.value,
        verification_status="VERIFIED",
    )
    policy = MatchingPolicy(
        method=MatchingMethod.EXACT_BASELINE,
        partial_coefficients={("NARROWER_THAN", "STUDENT_IS_SOURCE"): 0.7},
    )

    results = match_skills([req], [student_skill], relationships=[rel], policy=policy)

    assert len(results) == 1
    res = results[0]
    # In exact baseline, relationship matches are ignored
    assert res.match_type == MatchType.MISSING.value
    assert res.coverage_credit == 0.0
    assert res.result_status == MatchResultStatus.MISSING.value
    assert res.selected_student_skill_id is None


def test_04_verified_equivalent_relationship_in_relationship_aware_method():
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000100",
        standard_name="Golang",
        mapping_status="RESOLVED",
    )
    student_skill = StudentSkillInput(
        skill_record_id=uuid.uuid4(),
        skill_id="SK-000200",
        standard_name="Go Programming Language",
    )
    rel = RelationshipInput(
        relationship_id="REL-EQ-1",
        source_skill_id="SK-000200",
        target_skill_id="SK-000100",
        relationship_type=RelationshipType.EQUIVALENT_TO.value,
        verification_status="VERIFIED",
    )
    policy = MatchingPolicy(method=MatchingMethod.RELATIONSHIP_AWARE)

    results = match_skills([req], [student_skill], relationships=[rel], policy=policy)

    assert len(results) == 1
    res = results[0]
    assert res.match_type == MatchType.EQUIVALENT.value
    assert res.coverage_credit == 1.0
    assert res.result_status == MatchResultStatus.MATCHED.value
    assert res.selected_relationship_id == "REL-EQ-1"


def test_05_valid_partial_relationship_in_supported_direction():
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000458",
        standard_name="JavaScript",
        mapping_status="RESOLVED",
    )
    student_skill = StudentSkillInput(
        skill_record_id=uuid.uuid4(), skill_id="SK-001606", standard_name="React"
    )
    # React is narrower than JavaScript; student possesses specialized skill (React)
    rel = RelationshipInput(
        relationship_id="REL-001",
        source_skill_id="SK-001606",
        target_skill_id="SK-000458",
        relationship_type=RelationshipType.NARROWER_THAN.value,
        verification_status="VERIFIED",
    )
    policy = MatchingPolicy(
        method=MatchingMethod.RELATIONSHIP_AWARE,
        partial_coefficients={("NARROWER_THAN", "STUDENT_IS_SOURCE"): 0.75},
    )

    results = match_skills([req], [student_skill], relationships=[rel], policy=policy)

    assert len(results) == 1
    res = results[0]
    assert res.match_type == MatchType.PARTIAL_RELATIONSHIP.value
    assert res.coverage_credit == 0.75
    assert res.result_status == MatchResultStatus.PARTIALLY_COVERED.value
    assert res.selected_student_skill_id == student_skill.skill_record_id
    assert res.selected_relationship_id == "REL-001"
    assert res.relationship_source_skill_id == "SK-001606"
    assert res.relationship_target_skill_id == "SK-000458"


def test_06_inverse_relationship_direction_receives_no_credit():
    # Industry requires React; student only has JavaScript
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-001606",
        standard_name="React",
        mapping_status="RESOLVED",
    )
    student_skill = StudentSkillInput(
        skill_record_id=uuid.uuid4(), skill_id="SK-000458", standard_name="JavaScript"
    )
    # React is narrower than JavaScript; here student is target (JavaScript)
    rel = RelationshipInput(
        relationship_id="REL-001",
        source_skill_id="SK-001606",
        target_skill_id="SK-000458",
        relationship_type=RelationshipType.NARROWER_THAN.value,
        verification_status="VERIFIED",
    )
    # Only STUDENT_IS_SOURCE is permitted to award coverage
    policy = MatchingPolicy(
        method=MatchingMethod.RELATIONSHIP_AWARE,
        partial_coefficients={("NARROWER_THAN", "STUDENT_IS_SOURCE"): 0.75},
    )

    results = match_skills([req], [student_skill], relationships=[rel], policy=policy)

    assert len(results) == 1
    res = results[0]
    # General skill does not satisfy specialized skill requirement
    assert res.match_type == MatchType.MISSING.value
    assert res.coverage_credit == 0.0
    assert res.result_status == MatchResultStatus.MISSING.value


def test_07_related_to_receives_zero_direct_credit():
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000010",
        standard_name="Docker",
        mapping_status="RESOLVED",
    )
    student_skill = StudentSkillInput(
        skill_record_id=uuid.uuid4(), skill_id="SK-000020", standard_name="Kubernetes"
    )
    rel = RelationshipInput(
        relationship_id="REL-REL-1",
        source_skill_id="SK-000020",
        target_skill_id="SK-000010",
        relationship_type=RelationshipType.RELATED_TO.value,
        verification_status="VERIFIED",
    )
    policy = MatchingPolicy(method=MatchingMethod.RELATIONSHIP_AWARE)

    results = match_skills([req], [student_skill], relationships=[rel], policy=policy)

    assert len(results) == 1
    res = results[0]
    assert res.coverage_credit == 0.0
    assert res.result_status == MatchResultStatus.MISSING.value


def test_08_prerequisite_of_receives_zero_direct_credit():
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000030",
        standard_name="Deep Learning",
        mapping_status="RESOLVED",
    )
    student_skill = StudentSkillInput(
        skill_record_id=uuid.uuid4(),
        skill_id="SK-000031",
        standard_name="Linear Algebra",
    )
    # Linear algebra is prerequisite of Deep Learning
    rel = RelationshipInput(
        relationship_id="REL-PRE-1",
        source_skill_id="SK-000031",
        target_skill_id="SK-000030",
        relationship_type=RelationshipType.PREREQUISITE_OF.value,
        verification_status="VERIFIED",
    )
    policy = MatchingPolicy(method=MatchingMethod.RELATIONSHIP_AWARE)

    results = match_skills([req], [student_skill], relationships=[rel], policy=policy)

    assert len(results) == 1
    res = results[0]
    assert res.coverage_credit == 0.0
    assert res.result_status == MatchResultStatus.MISSING.value


def test_09_unverified_relationship_receives_zero_credit():
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000100",
        standard_name="Skill A",
        mapping_status="RESOLVED",
    )
    student_skill = StudentSkillInput(
        skill_record_id=uuid.uuid4(), skill_id="SK-000200", standard_name="Skill B"
    )
    rel = RelationshipInput(
        relationship_id="REL-UNV-1",
        source_skill_id="SK-000200",
        target_skill_id="SK-000100",
        relationship_type=RelationshipType.EQUIVALENT_TO.value,
        verification_status="UNVERIFIED",
    )
    policy = MatchingPolicy(method=MatchingMethod.RELATIONSHIP_AWARE)

    results = match_skills([req], [student_skill], relationships=[rel], policy=policy)

    assert len(results) == 1
    res = results[0]
    assert res.coverage_credit == 0.0
    assert res.result_status == MatchResultStatus.MISSING.value


def test_10_embedding_similarity_alone_receives_zero_credit():
    # Embedding similarity alone is an unverified candidate discovery signal
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000458",
        standard_name="JavaScript",
        mapping_status="RESOLVED",
    )
    student_skill = StudentSkillInput(
        skill_record_id=uuid.uuid4(), skill_id="SK-000500", standard_name="TypeScript"
    )
    # No verified relationship exists; high vector similarity alone awards no coverage
    policy = MatchingPolicy(method=MatchingMethod.RELATIONSHIP_AWARE)

    results = match_skills([req], [student_skill], relationships=[], policy=policy)

    assert len(results) == 1
    res = results[0]
    assert res.coverage_credit == 0.0
    assert res.result_status == MatchResultStatus.MISSING.value


def test_11_missing_student_skill_produces_missing_result():
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000999",
        standard_name="Rust Programming",
        mapping_status="RESOLVED",
    )
    student_skill = StudentSkillInput(
        skill_record_id=uuid.uuid4(), skill_id="SK-000100", standard_name="Python"
    )

    results = match_skills([req], [student_skill])

    assert len(results) == 1
    res = results[0]
    assert res.match_type == MatchType.MISSING.value
    assert res.coverage_credit == 0.0
    assert res.result_status == MatchResultStatus.MISSING.value
    assert res.selected_student_skill_id is None


def test_12_unresolved_industry_requirement_produces_unassessed():
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id=None,
        standard_name="Custom Vendor Tool",
        mapping_status="UNRESOLVED",
    )
    student_skill = StudentSkillInput(
        skill_record_id=uuid.uuid4(), skill_id="SK-000001", standard_name="Python"
    )

    results = match_skills([req], [student_skill])

    assert len(results) == 1
    res = results[0]
    assert res.match_type == MatchType.UNASSESSED.value
    assert res.coverage_credit == 0.0
    assert res.result_status == MatchResultStatus.UNASSESSED.value
    assert res.selected_student_skill_id is None


def test_13_multiple_eligible_student_skills_produce_one_deterministic_winning_match():
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000458",
        standard_name="JavaScript",
        mapping_status="RESOLVED",
    )
    # Student skill 1: exact match
    skill_exact = StudentSkillInput(
        skill_record_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        skill_id="SK-000458",
        standard_name="JavaScript",
    )
    # Student skill 2: partial relationship
    skill_partial = StudentSkillInput(
        skill_record_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        skill_id="SK-001606",
        standard_name="React",
    )
    rel = RelationshipInput(
        relationship_id="REL-001",
        source_skill_id="SK-001606",
        target_skill_id="SK-000458",
        relationship_type=RelationshipType.NARROWER_THAN.value,
        verification_status="VERIFIED",
    )
    policy = MatchingPolicy(
        method=MatchingMethod.RELATIONSHIP_AWARE,
        partial_coefficients={("NARROWER_THAN", "STUDENT_IS_SOURCE"): 0.75},
    )

    results = match_skills(
        [req],
        [skill_partial, skill_exact],
        relationships=[rel],
        policy=policy,
    )

    assert len(results) == 1
    res = results[0]
    # Exact match (priority 1) wins over partial relationship (priority 4)
    assert res.match_type == MatchType.EXACT.value
    assert res.coverage_credit == 1.0
    assert res.selected_student_skill_id == skill_exact.skill_record_id
    assert len(res.candidate_diagnostics) == 2


def test_14_multiple_student_skills_never_summed():
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000458",
        standard_name="JavaScript",
        mapping_status="RESOLVED",
    )
    # Two distinct partial skills
    skill1 = StudentSkillInput(
        skill_record_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        skill_id="SK-001606",
        standard_name="React",
    )
    skill2 = StudentSkillInput(
        skill_record_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        skill_id="SK-001607",
        standard_name="Vue.js",
    )
    rel1 = RelationshipInput(
        relationship_id="REL-001",
        source_skill_id="SK-001606",
        target_skill_id="SK-000458",
        relationship_type=RelationshipType.NARROWER_THAN.value,
        verification_status="VERIFIED",
    )
    rel2 = RelationshipInput(
        relationship_id="REL-002",
        source_skill_id="SK-001607",
        target_skill_id="SK-000458",
        relationship_type=RelationshipType.NARROWER_THAN.value,
        verification_status="VERIFIED",
    )
    policy = MatchingPolicy(
        method=MatchingMethod.RELATIONSHIP_AWARE,
        partial_coefficients={("NARROWER_THAN", "STUDENT_IS_SOURCE"): 0.5},
    )

    results = match_skills(
        [req], [skill1, skill2], relationships=[rel1, rel2], policy=policy
    )

    assert len(results) == 1
    res = results[0]
    # Winning score is exactly 0.5, NOT 0.5 + 0.5 = 1.0
    assert res.coverage_credit == 0.5
    assert res.result_status == MatchResultStatus.PARTIALLY_COVERED.value


def test_15_extra_student_skills_do_not_create_extra_requirement_results():
    req1 = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000001",
        standard_name="Python",
        mapping_status="RESOLVED",
    )
    req2 = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000002",
        standard_name="SQL",
        mapping_status="RESOLVED",
    )

    # Student possesses 5 skills (3 are unrequested extras)
    student_skills = [
        StudentSkillInput(
            skill_record_id=uuid.uuid4(), skill_id="SK-000001", standard_name="Python"
        ),
        StudentSkillInput(
            skill_record_id=uuid.uuid4(), skill_id="SK-000002", standard_name="SQL"
        ),
        StudentSkillInput(
            skill_record_id=uuid.uuid4(), skill_id="SK-000003", standard_name="Ruby"
        ),
        StudentSkillInput(
            skill_record_id=uuid.uuid4(), skill_id="SK-000004", standard_name="Haskell"
        ),
        StudentSkillInput(
            skill_record_id=uuid.uuid4(), skill_id="SK-000005", standard_name="Cobol"
        ),
    ]

    results = match_skills([req1, req2], student_skills)

    # Exactly 2 requirement results returned, matching the 2 industry requirements
    assert len(results) == 2
    assert {r.required_canonical_skill_id for r in results} == {
        "SK-000001",
        "SK-000002",
    }


def test_16_role_with_zero_requirements_handled_explicitly():
    student_skills = [
        StudentSkillInput(
            skill_record_id=uuid.uuid4(), skill_id="SK-000001", standard_name="Python"
        )
    ]
    results = match_skills([], student_skills)
    assert results == []


def test_17_invalid_ids_malformed_relationships_and_invalid_coefficients():
    # 1. Invalid coefficient validation
    with pytest.raises(ValueError, match="strictly between 0 and 1"):
        MatchingPolicy(
            partial_coefficients={("NARROWER_THAN", "STUDENT_IS_SOURCE"): 1.5}
        )

    with pytest.raises(ValueError, match="strictly between 0 and 1"):
        MatchingPolicy(
            partial_coefficients={("NARROWER_THAN", "STUDENT_IS_SOURCE"): 0.0}
        )

    with pytest.raises(ValueError, match="cannot award direct readiness coverage"):
        MatchingPolicy(partial_coefficients={("RELATED_TO", "STUDENT_IS_SOURCE"): 0.5})

    # 2. Malformed relationships handled safely without crashing
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000001",
        standard_name="Skill 1",
        mapping_status="RESOLVED",
    )
    student_skill = StudentSkillInput(
        skill_record_id=uuid.uuid4(),
        skill_id="SK-000002",
        standard_name="Skill 2",
    )
    malformed_rel = RelationshipInput(
        relationship_id="REL-BAD",
        source_skill_id="",
        target_skill_id="",
        relationship_type="",
    )

    results = match_skills([req], [student_skill], relationships=[malformed_rel])
    assert len(results) == 1
    assert results[0].match_type == MatchType.MISSING.value


def test_18_idempotent_and_deterministic_outputs():
    req = RequirementInput(
        requirement_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        skill_id="SK-000458",
        standard_name="JavaScript",
        mapping_status="RESOLVED",
    )
    skill1 = StudentSkillInput(
        skill_record_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        skill_id="SK-001606",
        standard_name="React",
    )
    skill2 = StudentSkillInput(
        skill_record_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        skill_id="SK-001607",
        standard_name="Vue.js",
    )
    rel1 = RelationshipInput(
        relationship_id="REL-001",
        source_skill_id="SK-001606",
        target_skill_id="SK-000458",
        relationship_type=RelationshipType.NARROWER_THAN.value,
        verification_status="VERIFIED",
    )
    rel2 = RelationshipInput(
        relationship_id="REL-002",
        source_skill_id="SK-001607",
        target_skill_id="SK-000458",
        relationship_type=RelationshipType.NARROWER_THAN.value,
        verification_status="VERIFIED",
    )
    policy = MatchingPolicy(
        method=MatchingMethod.RELATIONSHIP_AWARE,
        partial_coefficients={("NARROWER_THAN", "STUDENT_IS_SOURCE"): 0.7},
    )

    run1 = match_skills(
        [req], [skill1, skill2], relationships=[rel1, rel2], policy=policy
    )
    run2 = match_skills(
        [req], [skill2, skill1], relationships=[rel2, rel1], policy=policy
    )

    assert run1[0].selected_student_skill_id == run2[0].selected_student_skill_id
    assert run1[0].coverage_credit == run2[0].coverage_credit
    assert run1[0].match_type == run2[0].match_type
