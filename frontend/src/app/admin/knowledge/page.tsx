import { requireAdmin } from "@/lib/auth";
import {
  fetchSsksDomains,
  fetchSsksRoles,
  fetchSsksSkills,
  fetchSsksRelationships,
  type DomainItem,
  type RoleItem,
  type SkillItem,
  type SkillRelationshipItem,
} from "@/lib/ssksApi";
import { SharedKnowledgeView } from "@/components/admin/SharedKnowledgeView";

export const metadata = {
  title: "Shared Knowledge Management — Skillaro Admin",
  description: "Manage domains, roles, skills, and semantic relationships in the SSKS knowledge base.",
};

export default async function AdminKnowledgePage() {
  await requireAdmin("/admin/knowledge");

  let domains: DomainItem[] = [];
  let roles: RoleItem[] = [];
  let skills: SkillItem[] = [];
  let relationships: SkillRelationshipItem[] = [];

  try {
    const [d, r, s, rel] = await Promise.all([
      fetchSsksDomains().catch(() => [] as DomainItem[]),
      fetchSsksRoles({ limit: 500 }).catch(() => [] as RoleItem[]),
      fetchSsksSkills({ limit: 500 }).catch(() => [] as SkillItem[]),
      fetchSsksRelationships({ limit: 500 }).catch(() => [] as SkillRelationshipItem[]),
    ]);
    domains = d;
    roles = r;
    skills = s;
    relationships = rel;
  } catch (err) {
    console.error("Failed to load knowledge records:", err);
  }

  return (
    <SharedKnowledgeView
      initialDomains={domains}
      initialRoles={roles}
      initialSkills={skills}
      initialRelationships={relationships}
    />
  );
}
