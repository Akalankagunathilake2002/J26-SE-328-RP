// Test script verifying readiness classification logic for analysis responses
import assert from "node:assert";

// Mock payload representing analysis e07cddac-a5ae-4d14-8e3c-0cfe9148ad6b
const mockAnalysis = {
  readiness_score: 75.705,
  baseline_readiness_score: 75.705,
  skill_results: [
    { required_skill_name: "Python", match_type: "EXACT", coverage_credit: 1.0, evidence_confidence: 0.75, satisfaction: 0.75, gap: 0.0, result_status: "COVERED" },
    { required_skill_name: "SQL", match_type: "EXACT", coverage_credit: 1.0, evidence_confidence: 0.86, satisfaction: 0.86, gap: 0.0, result_status: "COVERED" },
    { required_skill_name: "Docker", match_type: "EXACT", coverage_credit: 1.0, evidence_confidence: 0.62, satisfaction: 0.62, gap: 0.0, result_status: "COVERED" },
    { required_skill_name: "Git", match_type: "EXACT", coverage_credit: 1.0, evidence_confidence: 0.80, satisfaction: 0.80, gap: 0.0, result_status: "COVERED" },
    { required_skill_name: "REST APIs", match_type: "EXACT", coverage_credit: 1.0, evidence_confidence: 0.82, satisfaction: 0.82, gap: 0.0, result_status: "COVERED" },
    { required_skill_name: "FastAPI", match_type: "EXACT", coverage_credit: 1.0, evidence_confidence: 0.69, satisfaction: 0.69, gap: 0.0, result_status: "COVERED" },
  ],
  priority_skills: [],
};

// Classification logic implemented in frontend readinessApi.ts
function deriveCounts(detail) {
  const skills = detail.skill_results;
  const totalRequirements = skills.length;

  const satisfiedCount = skills.filter((s) =>
    s.satisfaction !== null && s.satisfaction !== undefined
      ? s.satisfaction >= 0.999
      : s.result_status === "SATISFIED"
  ).length;

  const partialCount = skills.filter((s) =>
    s.satisfaction !== null && s.satisfaction !== undefined
      ? s.satisfaction > 0 && s.satisfaction < 0.999
      : s.result_status === "PARTIAL" || s.result_status === "PARTIALLY_COVERED"
  ).length;

  const missingCount = skills.filter(
    (s) => s.result_status === "MISSING" || s.result_status === "DEFICIENT" || s.match_type === "MISSING"
  ).length;

  const matchedCount = skills.filter(
    (s) => s.match_type !== "MISSING" && s.match_type !== "UNASSESSED" && (s.coverage_credit > 0 || s.result_status !== "MISSING")
  ).length;

  return { totalRequirements, satisfiedCount, partialCount, missingCount, matchedCount };
}

const counts = deriveCounts(mockAnalysis);

// 1. Verify not treating COVERED skills as fully satisfied if satisfaction < 1.0
assert.strictEqual(counts.satisfiedCount, 0, "Satisfied count must be 0 when all satisfaction values are below 1.0");

// 2. Verify all 6 skills are recognized as partially satisfied due to evidence confidence
assert.strictEqual(counts.partialCount, 6, "Partial count must be 6 reflecting developing evidence confidence");

// 3. Verify zero missing skills
assert.strictEqual(counts.missingCount, 0, "Missing count must be 0");

// 4. Verify all 6 skills are recognized as matched
assert.strictEqual(counts.matchedCount, 6, "Matched count must be 6");

// 5. Verify total requirements
assert.strictEqual(counts.totalRequirements, 6, "Total requirements must be 6");

console.log("All frontend classification tests passed successfully:", counts);
