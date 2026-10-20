import { requireAdmin } from "@/lib/auth";
import {
  fetchSsksCandidateRelationships,
  fetchSsksSkillsAll,
  type CandidateRelationshipItem,
  type SkillItem,
} from "@/lib/ssksApi";
import { AdminCandidatesView } from "@/components/admin/AdminCandidatesView";

export const metadata = {
  title: "Candidate Management — Skillaro Admin",
  description: "Review, approve, and reject proposed skill relationships and entity submissions.",
};

export default async function AdminCandidatesPage() {
  const user = await requireAdmin("/admin/candidates");

  let candidates: CandidateRelationshipItem[] = [];
  try {
    candidates = await fetchSsksCandidateRelationships({ limit: 500 });
  } catch (error) {
    console.error("Failed to load candidate relationships:", error);
  }

  let skills: SkillItem[] = [];
  try {
    skills = await fetchSsksSkillsAll();
  } catch (error) {
    console.error("Failed to load canonical skills for candidates:", error);
  }

  return (
    <AdminCandidatesView
      initialCandidates={candidates}
      initialSkills={skills}
      reviewerId={user.id || user.email || "admin-reviewer"}
    />
  );
}
